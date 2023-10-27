from typing import *
from dataclasses import dataclass

@dataclass
class IRIndent:
	src: str
	body: List['IrNode']

@dataclass
class IRUnit:
	src: str

@dataclass
class IRBreak:
	pass

@dataclass
class IRIf:
	cond: 'IRNode'
	body: List['IrNode']

@dataclass
class IRElse:
	body: List['IrNode']

@dataclass
class IRAssert:
	exprs: List['IrNode']

IRNode = IRUnit | IRIf | IRElse | IRIndent | IRAssert | IRBreak

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
		self.program = self.construct_ir(0)
		self.expected_indent = 0
	
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

		pass
	
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
					expr = dedented_line[len(token):].strip().removesuffix(":")
					body = self.construct_ir(current_indent)
					stmts.append(IRIf(IRUnit(expr), body))
				case 'assert':
					# assert expr, expr
					#        ^^^^  ^^^^
					#
					# assert does not allow comma expressions in expr0
					exprs = map(str.strip, dedented_line[len(token):].split(","))
					stmts.append(IRAssert(exprs))	
				#case 'break':
				#	stmts.append(IRBreak())
				#case 'for':
				#	# for expr in expr:
				#	#     ^^^^    ^^^^
				#	expr = dedented_line[len(token):].strip().removesuffix(":")
				case expr:
					if ":" in dedented_line:
						body = self.construct_ir(current_indent)
						stmts.append(IRIndent(dedented_line, body))
					else:
						stmts.append(IRUnit(dedented_line))

					# assert False, expr
					# todo: everything else
		
		return stmts

	# todo: move to a transpile stmts, which is [], applying indent
	# todo: then move to expr, which is just IRNode
	def transpile_recurse(self, body: List[IRNode], indent: int) -> List[str]:
		code = []
		indent_line = "\t" * indent
		
		for node in body:
			match node:
				case IRUnit(src):
					code.append(f"{indent_line}{src}")
				case IRIf(cond, body):
					# todo: repr for cond, which is an IRUnit
					code.append(f"{indent_line}if {cond.src}:")
					code += self.transpile_recurse(body, indent + 1)
				case IRIndent(src, body):
					code.append(f"{indent_line}{src}")
					code += self.transpile_recurse(body, indent + 1)
				case IRAssert(exprs):
					exprs_str = ", ".join(exprs)
					code.append(f"{indent_line}assert {exprs_str}")
				case _:
					assert False, _
		
		return code

	# def transform
	def transpile(self) -> str:
		return "\n".join(self.transpile_recurse(self.program, 0))