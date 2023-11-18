from typing import *
from dataclasses import dataclass
import keyword
import re

@dataclass
class IRIndent:
	token: str
	expr: 'IRNode'
	body: List['IrNode']

@dataclass
class IRFn:
	name: str
	params: str
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

def iter_to_identifers(src: str):
	# return iterator, yielding (bool, int, int)

	start = 0
	i = 0
	strch = None

	while True:
		if i >= len(src):
			yield (True, start, len(src)) # valid searchable text
			return
		
		ch = src[i]
		
		if ch.isspace():
			pass	
		elif strch is None:
			if ch == "'" or ch == '"':
				strch = ch
				yield (True, start, i) # valid searchable text
				start = i
			elif ch == "#":
				if src[start:i] != '':
					yield (True, start, i) # valid searchable text
				yield (False, i, len(src)) # invalid searchable text
				return
		else:
			if ch == "\\":
				i += 1
			elif ch == strch:
				strch = None
				yield (False, start, i + 1) # invalid searchable text
				start = i + 1		
		i += 1

def walk_expr_str(src: str) -> int | None:
	# walk till `,` or EOL
	# skipping past parens and strings
	#
	# pos = walk_expr_str("test(hello, 'along'), test")
	# assert src[pos:].strip() == 'test'

	parens = 0

	for valid, start, end in iter_to_identifers(src):
		if not valid:
			continue

		while start < end:
			ch = src[start]
			if ch == "(":
				parens += 1
			elif ch == ")":
				parens -= 1
			start += 1

			if parens == 0 and ch == ",":
				return start

def rstrip_str(src: str, strip: str) -> str:
	index = src.rfind(strip)
	if index != -1:
		return src[:index].strip()
	return src.strip()

class Program:
	def __init__(self, program_src):
		self.program_src = program_src
		self.lines = program_src.split("\n")
		self.index = 0
		self.lines_iterator = iter(self.line_next, None)
		#
		self.use_inhelper = False
		self.use_notinhelper = False
		self.use_andhelper = False
		self.use_orhelper = False
		self.use_nothelper = False
		self.tmp_break_stack = []
		self.tmp_counter_prefix = {}
		self.current_fn_ret = None
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
		# possibly deprecate?
		return IRUnit(expr)
	
	def construct_ir(self, last_indent: int) -> List[IRNode]:
		stmts = []

		first_line = self.lines[self.index]
		current_indent = len(first_line) - len(first_line.lstrip())
		indent_diff = current_indent - last_indent

		for line in self.lines_iterator:
			# fuckit: we won't get multiline strings, or malformed indentation

			if line.isspace() or line == "":
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
					expr_str = rstrip_str(dedented_line[len(token):], ":")
					body = self.construct_ir(current_indent)
					stmts.append(IRIf(self.construct_expr(expr_str), body))
				case 'elif':
					# elif expr:
					#      ^^^^
					expr_str = rstrip_str(dedented_line[len(token):], ":")
					body = self.construct_ir(current_indent)
					stmts.append(IRElif(self.construct_expr(expr_str), body))
				case 'else':
					stmts.append(IRElse(self.construct_ir(current_indent)))
				case 'def':
					components = dedented_line[len(token):].split('(', 1)
					components[1] = rstrip_str(components[1], "):")
					name = components[0].strip()
					params = components[1]
					body = self.construct_ir(current_indent)
					func = IRFn(name, params, body)
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
					expr_strs = dedented_line[len(token):]
					pos = walk_expr_str(expr_strs)

					if pos is None:
						exprs.append(self.construct_expr(expr_strs.strip()))
					else:
						exprs.append(self.construct_expr(expr_strs[:pos - 1].strip()))
						exprs.append(self.construct_expr(expr_strs[pos:].strip()))
					stmts.append(IRAssert(exprs))
				case 'while':
					# while expr:
					#       ^^^^
					expr_str = rstrip_str(dedented_line[len(token):], ":")
					body = self.construct_ir(current_indent)
					stmts.append(IRWhile(self.construct_expr(expr_str), body))
				case 'for':
					# for lhs in rhs:
					#     ^^^    ^^^
					# a well formed `lhs` will never contain a keyword like `in`
					#     -- use              : `.split("in", 1)`
					#     -- will not fail on : `v in "hello in this"`

					expr_strs = rstrip_str(dedented_line[len(token):], ":").split("in", 1)
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
						expr_str = rstrip_str(dedented_line[len(token):], ":")
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
					tcond = IRUnit(f"{temp_var} and ({expr.src})") # quoted expr
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
			expr_str = f"{tmp} and ({node.cond.src})"
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
					new_expr = IRIf(IRUnit(f"not ({self.transpile_expr(exprs[0])})"), [IRUnit(raise_str)])
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
					nsrc = self.transpile_expr(expr)
					nbody.append(IRUnit(f'{self.current_fn_ret} = {nsrc}'))
					nbody.append(IRUnit('yield'))
				case IRFn(name, params, body):
					assert self.current_fn_ret == None
					new_fn_name = self.transform_new_temp_var(name)
					self.current_fn_ret = self.transform_new_temp_var(f"ret_{name}")
					transformed = self.transform_stmts_recurse(body)
					# global _ret_func0, set _ret_func0 to None, force to be iterator
					transformed = [IRUnit(f"global {self.current_fn_ret}"), IRUnit(f"{self.current_fn_ret} = None")] + transformed + [IRUnit("yield")]
					nbody.append(IRFn(new_fn_name, params, transformed))
					paramsrc = '' if params == '' else f' {params}'
					nbody.append(IRUnit(f"{name} = lambda{paramsrc} : (next({new_fn_name}({params})), {self.current_fn_ret})[1]"))
					self.current_fn_ret = None
				case IRIndent(token, expr, body):
					transformed = self.transform_stmts_recurse(body)
					nbody.append(IRIndent(token, expr, transformed))
				case IRUnit():
					nbody.append(op) # not transforming expressions yet
				case other:
					assert False, other

		# work on expressions, to remove keywords introduced by previous stmt transformations
		return nbody

	def transform_expr(self, node: IRUnit):
		src = node.src

		# ---- remove all `not` + `and` + `or` + `in` + `not in`
		rep = {
			'and': '^_and^',
			'or': '|_or|',
			'not in': '&_notin&',
			'in': '&_in&',
			'not': '_not&',
		}
		
		nsrc = ''
		for valid, start, end in iter_to_identifers(src):
			v = src[start:end]
			if valid:
				def matchfn(match):
					string = match.group(0)
					if string == 'not':
						self.use_nothelper = True
					elif string == 'and':
						self.use_andhelper = True
					elif string == 'or':
						self.use_orhelper = True
					elif string == 'in':
						self.use_inhelper = True
					elif string == 'not in':
						self.use_notinhelper = True
					return rep[string]
				nsrc += re.sub(r'\b(not in|and|or|not|in)\b', matchfn, v)
			else:
				nsrc += v

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
				case IRIndent(_, expr, body):
					self.transform_expr(expr)
					self.transform_exprs_recurse(body)
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
				case IRFn(name, params, body):
					code.append(f"{indent_line}def {name}({params}):")
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
		program_str = "\n".join(self.transpile_recurse(self.program, 0))

		prelude_str = ""

		if self.use_inhelper or self.use_notinhelper:
			inclass = (
				'class _In:\n'
				'	__init__ = lambda self, notin, lhs=None: (setattr(self, "notin", notin), setattr(self, "lhs", lhs), None)[2]\n'
				'	__rand__ = lambda self, lhs: _In(self.notin, lhs)\n'
				'	__and__ = lambda self, rhs: any(filter(lambda _x: _x == self.lhs, rhs)) ^ self.notin\n'
			)
			prelude_str += inclass
		if self.use_inhelper:
			prelude_str += '_in = _In(False)\n'
		if self.use_notinhelper:
			prelude_str += '_notin = _In(True)\n'
		if self.use_andhelper:
			andclass = (
				'class _And:\n'
				'	__init__ = lambda self, lhs=None : setattr(self, "lhs", lhs)\n'
				'	__rxor__ = lambda self, lhs: _And(lhs)\n'
				'	__xor__ = lambda self, rhs: (self.impl_and(rhs), self.op_ret)[1]\n'
				'	def impl_and(self, rhs):\n'
				'		passed = True\n'
				'		if self.lhs:\n'
				'			self.op_ret = rhs\n'
				'			passed = False\n'
				'		if passed:\n'
				'			self.op_ret = self.lhs\n'
			)
			prelude_str += andclass
			prelude_str += '_and = _And()\n'
		if self.use_orhelper:
			orclass = (
				'class _Or:\n'
				'	__init__ = lambda self, lhs=None: setattr(self, "lhs", lhs)\n'
				'	__ror__ = lambda self, lhs: _Or(lhs)\n'
				'	__or__ = lambda self, rhs: (self.impl_or(rhs), self.op_ret)[1]\n'
				'	def impl_or(self, rhs):\n'
				'		passed = True\n'
				'		if self.lhs:\n'
				'			self.op_ret = self.lhs\n'
				'			passed = False\n'
				'		if passed:\n'
				'			self.op_ret = rhs\n'
			)
			prelude_str += orclass
			prelude_str += '_or = _Or()\n'
		if self.use_nothelper:
			notclass = (
				'class _Not:\n'
				'	__init__ = lambda self: setattr(self, "dup", 1)\n'
				'	__and__ = lambda self, other: (self.impl_not(other), self.op_ret)[1]\n'
				'	def impl_not(self, other):\n'
				'		is_inst = isinstance(other, _Not)\n'
				'		if is_inst:\n'
				'			self.dup += 1\n'
				'			self.op_ret = self\n'
				'		if False == is_inst:\n'
				'			self.impl_operate(other)\n'
				'	def impl_operate(self, other):\n'
				'		ret = other\n'
				'		while self.dup > 0:\n'
				'			ret = False == bool(ret)\n'
				'			self.dup -= 1\n'
				'		self.op_ret = ret\n'
			)
			prelude_str += notclass
			prelude_str += '_not = _Not()\n'
		return prelude_str + program_str