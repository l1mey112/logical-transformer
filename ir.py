from typing import *
from dataclasses import dataclass
from enum import Flag, auto
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

IRNode = IRUnit | IRIf | IRElif | IRElse | IRIndent | IRAssert | IRBreak | IRReturn | IRFn

class Transformations(Flag):
	# logical
	AND = auto()
	OR = auto()
	NOT = auto()
	# expr
	IN = auto()
	# control flow
	FOR = auto()
	ELSE = auto()
	ELIF = auto()
	RETURN = auto()
	BREAK = auto()
	# stmts
	ASSERT = auto()

def tokenise_first(line: str) -> str:
	"""
	assert tokenise_first("if(") == "if"
	"""

	i = 0
	while i < len(line) and line[i].isidentifier():
		i += 1
	
	return line[:i]

class Program:
	def __init__(self, program_src):
		self.program_src = program_src
		self.lines = program_src.split("\n")
		self.index = 0
		self.lines_iterator = iter(self.line_next, None)
		self.function_decls = {}
		#
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
				#case 'break':
				#	stmts.append(IRBreak())
				#case 'for':
				#	# for expr in expr:
				#	#     ^^^^    ^^^^
				#	expr = dedented_line[len(token):].strip().removesuffix(":")
				case expr:
					# handle while, it may have exprs
					
					if ":" in dedented_line:
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
	
	def transform_recurse(self, body: List[IRNode], passes: Transformations):
		"""transform: walk the entire IR, apply transformations"""

		# work on stmts, this will shuffle expressions
		for index, op in enumerate(body):
			match op:
				case IRAssert(exprs):
					if Transformations.ASSERT not in passes:
						continue
					raise_str = "raise AssertionError" if len(exprs) == 1 else f"raise AssertionError({self.transpile_expr(exprs[1])})"
					self.program[index] = IRIf(IRUnit(f"not {self.transpile_expr(exprs[0])}"), [IRUnit(raise_str)])
				
				case other:
					print(f"unhandled IR: {other}", file=sys.stderr)
		
		# work on expressions, to remove keywords introduced by previous stmt transformations
	
	def transform(self, passes: Transformations):
		"""transform: walk the entire IR, apply transformations"""
		self.transform_recurse(passes, self.program)

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
					# todo: repr for cond, which is an IRUnit
					code.append(f"{indent_line}if {self.transpile_expr(cond)}:")
					code += self.transpile_recurse(body, indent + 1)
				case IRElse(body):
					code.append(f"{indent_line}else:")
					code += self.transpile_recurse(body, indent + 1)
				case IRIndent(token, expr, body):
					code.append(f"{indent_line}{token} {self.transpile_expr(expr)}:")
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