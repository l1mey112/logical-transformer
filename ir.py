from typing import *
from dataclasses import dataclass
import keyword
import sys
import re

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
class IRUnitStmt:
	token: str
	expr: 'IRNode'

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

IRNode = IRUnit | IRUnitStmt | IRIf | IRElif | IRElse | IRIndent | IRAssert | IRWhile | IRFor | IRBreak | IRReturn | IRFn

def tokenise_first(line: str) -> str:
	# will strip the end, taking the start
	#
	# assert tokenise_first("if(") == "if"	

	i = 0
	while i < len(line) and line[i].isidentifier():
		i += 1
	
	return line[:i]

def iter_skip(v: Iterator[Any], amount: int):
	while amount > 0:
		next(v)
		amount -= 1

def find_inner_parens(src: str, start: int) -> int:
	# assume all parens are balanced, don't bother checking `len()`
	# this fails on string arguments, goddammit
	
	paren_lim = 1
	i = start + 1
	while paren_lim > 0:
		if src[i] == "(":
			paren_lim += 1
		elif src[i] == ")":
			paren_lim -= 1
		i += 1
	
	return i

class Program:
	def __init__(self, program_src):
		self.program_src = program_src
		self.lines = program_src.split("\n")
		self.index = 0
		self.lines_iterator = iter(self.line_next, None)
		#
		self.function_decls = {}
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
	
	def construct_expr(self, expr: str) -> IRNode:
		# possibly deprecate
		return IRUnit(expr)
	
	def construct_ir(self, last_indent: int) -> List[IRNode]:
		stmts = []

		first_line = self.lines[self.index]
		current_indent = len(first_line) - len(first_line.lstrip())
		indent_diff = current_indent - last_indent

		for line in self.lines_iterator:
			# fuckit: we won't get multiline strings, or malformed indentation

			if line.isspace() or line == "":
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
					# assert expr0, expr1
					#        ^^^^^  ^^^^^
					# assert does not allow comma expressions in expr0
					#
					# this will fail on assertations with strings containing commas
					# -- i like to pick and choose.
					
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
					# for lhs in rhs:
					#     ^^^    ^^^
					# a well formed `lhs` will never contain a keyword like `in`
					#     -- use              : `.split("in", 1)`
					#     -- will not fail on : `v in "hello in this"`

					expr_strs = dedented_line[len(token):].strip().removesuffix(":").split("in", 1)
					assert len(expr_strs) == 2
					expr_strs[0] = expr_strs[0].strip()
					expr_strs[1] = expr_strs[1].strip()
					body = self.construct_ir(current_indent)
					stmts.append(IRFor(self.construct_expr(expr_strs[0]), self.construct_expr(expr_strs[1]), body))
				case 'break':
					stmts.append(IRBreak())
				case expr:
					dedented_line_no_comments = dedented_line.split('#', 1)[0].strip()
					
					if dedented_line_no_comments[len(dedented_line_no_comments) - 1:] == ":":
						assert keyword.iskeyword(token), token # it should be.
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
		i = start + 1
		while i < len(body):
			match body[i]:
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
			transformed = self.transform_stmts_recurse(node.body)
			node.body = transformed
			return [node]

		nbody = []
		temp_var = self.transform_new_temp_var("if")

		nbody.append(IRUnit(f"{temp_var} = True"))
		for op in body:
			match op:
				case IRIf(expr, body):
					transformed = self.transform_stmts_recurse(op.body)
					tbody = [IRUnit(f"{temp_var} = False")] + transformed
					nbody.append(IRIf(expr, tbody))
				case IRElif(expr, body):
					transformed = self.transform_stmts_recurse(op.body)
					tcond = IRUnit(f"{temp_var} and {expr.src}")
					tbody = [IRUnit(f"{temp_var} = False")] + transformed
					nbody.append(IRIf(tcond, tbody))
				case IRElse(body):
					transformed = self.transform_stmts_recurse(op.body)
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
		
		transformed = self.transform_stmts_recurse(node.body)

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
		transformed = self.transform_stmts_recurse(node.body)
		self.tmp_break_stack.pop()

		# TRY EXCEPT StopIteration
		wnbody = [
			IRIndent('try', IRUnit(''), [
				IRUnit(f"{node.lhs.src} = next({iter_tmp})")
			]),
			IRIndent('except', IRUnit('StopIteration'), [
				IRUnit(f"{for_tmp} = False"),
				IRUnitStmt(f"continue", IRUnit('')),
			]),
		] + transformed

		nbody.append(IRUnit(f"{iter_tmp} = iter({node.rhs.src})"))
		nbody.append(IRUnit(f"{for_tmp} = True"))
		nbody.append(IRWhile(IRUnit(f"{for_tmp}"), wnbody))

		return nbody
	
	def transform_stmts_recurse(self, abody: List[IRNode]) -> List[IRNode]:
		nbody = []

		# work on stmts, this will shuffle expressions
		vals = enumerate(abody)
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
					if_stmts = self.transform_find_bounds_of_if(index, abody)
					nbody += self.transform_walk_if(if_stmts)
					iter_skip(vals, len(if_stmts) - 1) # skip these
				case IRBreak():
					top_tmp = self.tmp_break_stack[len(self.tmp_break_stack) - 1]
					nbody.append(IRUnit(f"{top_tmp} = False"))
					nbody.append(IRUnitStmt(f"continue", IRUnit('')))
				case IRReturn(expr):
					expr = IRUnit(self.transpile_expr(expr))
					nbody.append(IRUnitStmt('yield', expr))
				case IRFn(name, src, body):
					transformed = self.transform_stmts_recurse(body)
					nbody.append(IRFn(
						name, src, transformed + [IRUnitStmt(f"yield", IRUnit('None'))]
					))
				case IRUnit():
					nbody.append(op) # not transforming expressions yet
				case other:
					assert False, other

		# work on expressions, to remove keywords introduced by previous stmt transformations
		return nbody

	def transform_expr_nested_calls_str(self, src: str, pattern: re.Pattern) -> str:
		# a recursive descent parser using regex is never a good idea
		#
		# call(another(), expr)
		#      ^^^^^^^^^
		# ^^^^^^^^^^^^^^^^^^^^^
		# if call is "ours", replace with `next(expr())`
		#
		# hello()
		# |    \ start searching for bounds of ()
		# \ start of function name
		#
		#                     hello ( hello() + hello() )
		# 1.          find -> ^^^^^ /^^^^^^^^^^^^^^^^^^^^
		# 2. locate bounds -> -----/
		# 3. recurse       -\
		#
		#                     hello() + hello()
		# 1.          find -> ^^^^^/^
		# 2. locate bounds -> ----/
		# 3. recurse       -\
		#                   empty inner, stop.
		#
		# ---- after recursion onto inner bounds, iterate to next.
		#      march along the string applying transformations.
		nstr = ''
		start = 0
		while start < len(src):
			print(f"searching: {src[start:]}")
			rmatch = pattern.search(src, start)
			if not rmatch:
				nstr += src[start:]
				break

			start_all = rmatch.start(1)
			func_str = src[start_all:rmatch.end(1)]
			start_inner = rmatch.start(2)
			end_inner = find_inner_parens(src, start_inner)
			inner = src[start_inner + 1:end_inner - 1]
			# [start_inner:end_inner] == "..."
			#                             ^^^
			# recurse downwards
			tinner = self.transform_expr_nested_calls_str(inner, pattern)

			nstr += src[start:start_all] # add all before
			nstr += f"next({func_str}({tinner}))"
			start = end_inner

		return nstr

	def transform_expr_str(self, src: str) -> str:
		# precedence:
		#   1. not
		#   2. in, not in, or, and
		#   3. call()

		rep = {
			'and': '&',
			'or': '|',
			'not': 'False ==',
		}
		src = re.sub(r'\b(and|or|not)\b', lambda match: rep[match.group(0)], src)

		print(f"------- {src}")
		
		# replace list: "func1|func2|func3" -> insert inside regex
		replace_list = '|'.join(self.function_decls.keys())
		if replace_list == '':
			# no need to convert any functions
			return src

		pattern = re.compile(fr'\b({replace_list})\s*(\()')

		src = self.transform_expr_nested_calls_str(src, pattern)
		return src

	def transform_skip_over_undesirables_iter(self, src: str) -> Generator[Tuple[bool, str]]:
		# may contain comments, may contain strings. parse them out

		start = 0
		strch = None
		inside_string = False
		while start < len(src):
			ch = src[start]
			
			if ch.isspace():
				start += 1
				continue

			if strch is None and (ch == "'" or ch == '"'):
				strch = ch
			
			nindex = index + 1
			if ch == strch or nindex >= len(src):
				inside_string = not inside_string

				if inside_string:
					# string starting, handle text before
					# entire line ended, handle text before
					yield (True, src[start:nindex])
				else:
					# string over
					strch = None
					yield (False, src[start:nindex])

				start = nindex
				continue
			elif ch == "#":
				# handle comments
				yield (False, src[start:])
				break
			if inside_string:
				if ch == "\\":
					next(vals) # skip \n
				continue

	def transform_expr_str_recurse(self, src: str) -> str:
		# precedence:
		#   1. not
		#   2. in, not in, or, and
		#   3. call()

		nstr = ''
		start = 0
		while start < len(src):
			

		return nstr
		
		pass

	# this only works with binops, not function calls that group expressions!
	def transform_expr(self, node: IRUnit):
		src = node.src
		nsrc = ''

		# may contain comments, may contain strings. parse them out

		start = 0
		inside_string = False
		vals = enumerate(src)
		for index, ch in vals:
			nindex = index + 1
			if ch == "'" or ch == '"' or nindex >= len(src):
				inside_string = not inside_string

				if inside_string:
					# string starting, handle text before
					# entire line ended, handle text before
					nsrc += self.transform_expr_str(src[start:nindex])
				else:
					# string over
					nsrc += src[start:nindex]

				start = nindex
				continue
			elif ch == "#":
				# handle comments
				nsrc += src[start:]
				break
			if inside_string:
				if ch == "\\":
					next(vals) # skip \n
				continue
		
		node.src = nsrc
	
	def transform_exprs_recurse(self, abody: List[IRNode]):
		for op in abody:
			match op:
				case IRIf(cond, body):
					self.transform_expr(cond)
					self.transform_exprs_recurse(body)
				case IRElif(cond, body):
					self.transform_expr(cond)
					self.transform_exprs_recurse(body)
				case IRElse(body):
					self.transform_exprs_recurse(body)
				case IRIndent(_, expr, body):
					self.transform_expr(expr)
					self.transform_exprs_recurse(body)
				case IRAssert(exprs):
					self.transform_exprs_recurse(exprs)
				case IRWhile(cond, body):
					self.transform_expr(cond)
					self.transform_exprs_recurse(body)
				case IRFor(_, rhs, body):
					self.transform_expr(rhs)
					self.transform_exprs_recurse(cond)
				case IRBreak():
					pass
				case IRReturn(expr):
					self.transform_expr(expr)
				case IRFn(_, _, body):
					self.transform_exprs_recurse(body)
				case IRUnitStmt(_, expr):
					self.transform_expr(expr)
				case IRUnit():
					self.transform_expr(op)
				case other:
					assert False, other
	
	def transform(self):
		# transform all statements, may introduce forbidden keywords in expressions
		nprogram = self.transform_stmts_recurse(self.program)
		# transform all expressions, doesn't require context
		self.transform_exprs_recurse(nprogram)
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
				case IRUnitStmt(token, expr):
					code.append(f"{indent_line}{token} {self.transpile_expr(expr)}")
				case IRUnit(src):
					code.append(f"{indent_line}{src}")
				case other:
					assert False, other
		return code

	def transpile(self) -> str:
		return "\n".join(self.transpile_recurse(self.program, 0))