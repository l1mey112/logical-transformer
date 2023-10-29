from typing import *
from dataclasses import dataclass
import keyword
import sys

@dataclass
class IRIndent:
	token: str
	expr: 'IRNode'
	body: List['IrNode']

@dataclass
class IRFn:
	name: str
	src: str
	body: List['IrNode']

@dataclass
class IRUnit:
	src: str

@dataclass
class IRFor:
	lhs: 'IRNode'
	rhs: 'IRNode'
	body: List['IrNode']

@dataclass
class IRWhile:
	cond: 'IRNode'
	body: List['IrNode']

@dataclass
class IRBreak:
	pass

@dataclass
class IRReturn:
	expr: 'IRNode'

@dataclass
class IRIf:
	cond: 'IRNode'
	body: List['IrNode']

@dataclass
class IRElif:
	cond: 'IRNode'
	body: List['IrNode']

@dataclass
class IRElse:
	body: List['IrNode']

@dataclass
class IRAssert:
	exprs: List['IrNode']

IRNode = IRUnit | IRIf | IRElif | IRElse | IRIndent | IRAssert | IRWhile | IRFor | IRBreak | IRReturn | IRFn

def tokenise_first(line: str) -> str:
	"""
	assert tokenise_first("if(") == "if"
	"""

	i = 0
	while i < len(line) and line[i].isidentifier():
		i += 1
	
	return line[:i]

def iter_skip(v: Iterator[Any], amount: int):
	while amount > 0:
		next(v)
		amount -= 1

class Program:
	def __init__(self, program_src):
		self.program_src = program_src
		self.lines = program_src.split("\n")
		self.index = 0
		self.lines_iterator = iter(self.line_next, None)
		self.function_decls = {}
		#
		self.tmp_break_stack = []
		self.tmp_counter_prefix = {}
		self.program = self.construct_ir(0)
	
	def line_rewind(self):
		if self.index > 0:
			self.index -= 1
	
	def line_next(self) -> str | None:
		if self.index >= len(self.lines):
			return None
		line = self.lines[self.index]
		self.index += 1
		return line
	
	# todo: deprecate? operations on IRNodes will just be string ops
	def construct_expr(self, expr: str) -> IRNode:
		# precedence:
		#   1. not
		#   2. in
		#   3. or
		#   4. and

		# if test is function
		#   1. call()

		return IRUnit(expr)
	
	def construct_ir(self, last_indent: int) -> List[IRNode]:
		stmts = []

		first_line = self.lines[self.index]
		current_indent = len(first_line) - len(first_line.lstrip())
		indent_diff = current_indent - last_indent

		for line in self.lines_iterator:
			# fuckit: we won't get multiline strings, or malformed indentation

			if line.isspace():
				stmts.append(IRUnit(""))
				continue

			dedented_line = line.lstrip()
			line_indent = len(line) - len(dedented_line)

			if line_indent < current_indent:
				self.line_rewind()
				break

			token = tokenise_first(dedented_line)

			match token:
				case 'if':
					# if expr:
					#    ^^^^
					expr_str = dedented_line[len(token):].strip().removesuffix(":")
					body = self.construct_ir(current_indent)
					stmts.append(IRIf(self.construct_expr(expr_str), body))
				case 'elif':
					# elif expr:
					#      ^^^^
					expr_str = dedented_line[len(token):].strip().removesuffix(":")
					body = self.construct_ir(current_indent)
					stmts.append(IRElif(self.construct_expr(expr_str), body))
				case 'else':
					stmts.append(IRElse(self.construct_ir(current_indent)))
				case 'def':
					name = dedented_line[len(token):].split('(', 1)[0].strip()
					body = self.construct_ir(current_indent)
					func = IRFn(name, dedented_line, body)
					self.function_decls[name] = func
					stmts.append(func)
				case 'return':
					expr = self.construct_expr(dedented_line[len(token):].strip())
					stmts.append(IRReturn(expr))
				case 'assert':
					# assert expr, expr
					#        ^^^^  ^^^^
					#
					# assert does not allow comma expressions in expr0
					exprs = []
					for line in dedented_line[len(token):].split(","):
						exprs.append(self.construct_expr(line.strip()))
					stmts.append(IRAssert(exprs))
				case 'while':
					# while expr:
					#       ^^^^
					expr_str = dedented_line[len(token):].strip().removesuffix(":")
					body = self.construct_ir(current_indent)
					stmts.append(IRWhile(self.construct_expr(expr_str), body))
				case 'for':
					# for expr in expr:
					#     ^^^^    ^^^^
					expr_strs = dedented_line[len(token):].strip().removesuffix(":").split("in")
					assert len(expr_strs) == 2
					expr_strs[0] = expr_strs[0].strip()
					expr_strs[1] = expr_strs[1].strip()
					body = self.construct_ir(current_indent)
					stmts.append(IRFor(self.construct_expr(expr_strs[0]), self.construct_expr(expr_strs[1]), body))
				case 'break':
					stmts.append(IRBreak())
				#case 'for':
				#	# for expr in expr:
				#	#     ^^^^    ^^^^
				#	expr = dedented_line[len(token):].strip().removesuffix(":")
				case expr:
					dedented_line_no_comments = dedented_line.split('#', 1)[0]
					
					if ":" in dedented_line_no_comments:
						assert keyword.iskeyword(token) # it should be.
						expr_str = dedented_line[len(token):].strip().removesuffix(":")
						body = self.construct_ir(current_indent)
						stmts.append(IRIndent(token, self.construct_expr(expr_str), body))
					else:
						expr_str = dedented_line
						stmts.append(self.construct_expr(expr_str))

					# assert False, expr
					# todo: everything else
		
		return stmts
	
	def transform_find_bounds_of_if(self, start: int, body: List[IRNode]) -> List[IRNode]:
		i = start
		while i < len(body):
			match body[i]:
				case IRIf():
					i += 1
				case IRElif():
					i += 1
				case IRElse():
					i += 1
				case _:
					break
		return body[start:i]

	def transform_new_temp_var(self, relation: str) -> str:
		# relation: "while"
		# -> _while0

		if relation not in self.tmp_counter_prefix:
			self.tmp_counter_prefix[relation] = 0
		
		tmp = f"_{relation}{self.tmp_counter_prefix[relation]}"
		self.tmp_counter_prefix[relation] += 1
		return tmp

	def transform_walk_if(self, body: List[IRNode]) -> List[IRNode]:
		# check if it's a simplistic stmt
		if len(body) == 1:
			# body[0] must be a IRIf
			node = body[0]
			transformed = self.transform_recurse(node.body)
			node.body = transformed
			return [node]

		nbody = []
		temp_var = self.transform_new_temp_var("if")

		nbody.append(IRUnit(f"{temp_var} = True"))
		for op in body:
			match op:
				case IRIf(expr, body):
					transformed = self.transform_recurse(op.body)
					tbody = [IRUnit(f"{temp_var} = False")] + transformed
					nbody.append(IRIf(expr, tbody))
				case IRElif(expr, body):
					transformed = self.transform_recurse(op.body)
					tcond = IRUnit(f"{temp_var} and {expr.src}")
					tbody = [IRUnit(f"{temp_var} = False")] + transformed
					nbody.append(IRIf(tcond, tbody))
				case IRElse(body):
					transformed = self.transform_recurse(op.body)
					tcond = IRUnit(f"{temp_var}")
					nbody.append(IRIf(tcond, transformed))
				case other:
					assert False, other

		return nbody
	
	def transform_body_contains_break(self, node: IRWhile) -> bool:
		for op in node.body:
			match op:
				case IRWhile():
					pass # break doesn't refer to this while
				case IRFor():
					pass # break doesn't refer to this for
				case IRBreak():
					return True
				case other:
					if hasattr(other, 'body'):
						if self.transform_body_contains_break(other):
							return True
		
		return False

	def transform_while(self, node: IRWhile) -> List[IRNode]:
		contains_break = self.transform_body_contains_break(node)

		nbody = []

		if contains_break:
			tmp = self.transform_new_temp_var("while")
			self.tmp_break_stack.append(tmp)
		
		transformed = self.transform_recurse(node.body)

		if contains_break:	
			nbody.append(IRUnit(f"{tmp} = True"))
			expr_str = f"{tmp} and {node.cond.src}"
			self.tmp_break_stack.pop()
		else:
			expr_str = node.cond.src

		nbody.append(IRWhile(IRUnit(expr_str), transformed))
		
		return nbody
	
	def transform_for(self, node: IRFor) -> List[IRNode]:
		# always need break
		# contains_break = self.transform_body_contains_break(node)

		iter_tmp = self.transform_new_temp_var("iter")
		for_tmp = self.transform_new_temp_var("for")
		nbody = []

		self.tmp_break_stack.append(for_tmp)
		transformed = self.transform_recurse(node.body)
		self.tmp_break_stack.pop()

		# TRY EXCEPT StopIteration
		wnbody = [
			IRIndent('try', IRUnit(''), [
				IRUnit(f"{node.lhs.src} = next({iter_tmp})")
			]),
			IRIndent('except', IRUnit('StopIteration'), [
				IRUnit(f"{for_tmp} = False"),
				IRUnit(f"continue"),
			]),
		] + transformed

		nbody.append(IRUnit(f"{iter_tmp} = iter({node.rhs.src})"))
		nbody.append(IRUnit(f"{for_tmp} = True"))
		nbody.append(IRWhile(IRUnit(f"{for_tmp}"), wnbody))

		return nbody
	
	def transform_recurse(self, body: List[IRNode]) -> List[IRNode]:
		nbody = []

		# work on stmts, this will shuffle expressions
		vals = enumerate(body)
		for index, op in vals:
			match op:
				case IRAssert(exprs):
					raise_str = "raise AssertionError" if len(exprs) == 1 else f"raise AssertionError({self.transpile_expr(exprs[1])})"
					new_expr = IRIf(IRUnit(f"not {self.transpile_expr(exprs[0])}"), [IRUnit(raise_str)])
					nbody.append(new_expr)
				case IRWhile():
					nbody += self.transform_while(op)
				case IRFor():
					nbody += self.transform_for(op)
				case IRIf():
					if_stmts = self.transform_find_bounds_of_if(index, body)
					nbody += self.transform_walk_if(if_stmts)
					iter_skip(vals, len(if_stmts) - 1) # skip these
				case IRBreak():
					top_tmp = self.tmp_break_stack[len(self.tmp_break_stack) - 1]
					nbody.append(IRUnit(f"{top_tmp} = False"))
					nbody.append(IRUnit("continue"))
				case other:
					print(f"unhandled IR: {other}", file=sys.stderr)
					nbody.append(op)

		# work on expressions, to remove keywords introduced by previous stmt transformations
		return nbody
	
	def transform(self):
		nprogram = self.transform_recurse(self.program)
		self.program = nprogram

	def transpile_expr(self, expr: IRNode) -> str:
		match expr:
			case IRUnit(src):
				return src
			case other:
				assert False, other

	# todo: move to a transpile stmts, which is [], applying indent
	# todo: then move to expr, which is just IRNode
	def transpile_recurse(self, body: List[IRNode], indent: int) -> List[str]:
		code = []
		indent_line = "\t" * indent
		
		for node in body:
			match node:
				case IRIf(cond, body):
					code.append(f"{indent_line}if {self.transpile_expr(cond)}:")
					code += self.transpile_recurse(body, indent + 1)
				case IRElif(cond, body):
					code.append(f"{indent_line}elif {self.transpile_expr(cond)}:")
					code += self.transpile_recurse(body, indent + 1)
				case IRElse(body):
					code.append(f"{indent_line}else:")
					code += self.transpile_recurse(body, indent + 1)
				case IRWhile(cond, body):
					code.append(f"{indent_line}while {self.transpile_expr(cond)}:")
					code += self.transpile_recurse(body, indent + 1)
				case IRFor(lhs, rhs, body):
					code.append(f"{indent_line}while {self.transpile_expr(lhs)} in {self.transpile_expr(rhs)}:")
					code += self.transpile_recurse(body, indent + 1)
				case IRBreak():
					code.append(f"{indent_line}break")
				case IRIndent(token, expr, body):
					expr_str = self.transpile_expr(expr)
					if expr_str == '':
						code.append(f"{indent_line}{token}:")
					else:	
						code.append(f"{indent_line}{token} {expr_str}:")
					code += self.transpile_recurse(body, indent + 1)
				case IRAssert(exprs):
					exprs_str = ", ".join(map(self.transpile_expr, exprs))
					code.append(f"{indent_line}assert {exprs_str}")
				case IRFn(_, src, body):
					code.append(f"{indent_line}{src}")
					code += self.transpile_recurse(body, indent + 1)
				case IRReturn(expr):
					code.append(f"{indent_line}return {self.transpile_expr(expr)}")
				case other:
					code.append(f"{indent_line}{self.transpile_expr(other)}")
		return code

	def transpile(self) -> str:
		return "\n".join(self.transpile_recurse(self.program, 0))