import ir

def test_tokenise_first():
	# test the tokeniser to get the first identifier in various statements
	assert ir.tokenise_first("assert expr, 'hello'") == 'assert'
	assert ir.tokenise_first("if(expr):") == 'if'
	assert ir.tokenise_first("elif(expr):") == 'elif'
	assert ir.tokenise_first("def test():") == 'def'

def test_iter_to_identifers():
	# test the iterator to extract identifiers, handling valid and invalid ones
	def driver(src: str, expected):
		tokens = ir.iter_to_identifers(src)
		
		i = 0
		for valid, start, end in tokens:
			assert expected[i] == (valid, src[start:end])
			i += 1
		
		assert i == len(expected)
	
	# test with a complex expression and a line with comments
	driver("expr(20) + test", [(True, "expr(20) + test")])
	driver("a = print('test') # comment", [
		(True, "a = print("),
		(False, "'test'"),
		(True, ") "),
		(False, "# comment"),
	])

def test_walk_expr_str():
	# test walking a string to skip over an expression
	def driver(src: str, expected: str | None):
		pos = ir.walk_expr_str(src)
		if expected is None:
			assert pos is None
		else:
			assert src[pos:] == expected
	
	# test skipping an expression in a larger string
	driver("test(hello, 'along'), test", " test")
	# test when there's no expression to skip
	driver("test(hello, 'along')", None)

def test_rstrip_str():
	# test stripping a specific suffix from a string
	assert ir.rstrip_str("for guess in range(1, 101):  # Simulating guesses from 1 to 100", ":") == "for guess in range(1, 101)"
	# test when there's no suffix to strip
	assert ir.rstrip_str("none at all", ":") == "none at all"

def test_program_identity():
	# test parsing and transpilation identity for various code snippets
	def driver(src: str):
		assert src == ir.Program(src).transpile()
	
	# test a simple assert statement
	driver("assert test(hello, 'along'), test")
	# test a multiline function definition with print statements
	driver(
		"def test():\n"
		"	print('hello')\n"
		"	print('world')\n"
		"	print('!')"
	)
	# test a while loop with a break statement and print statement
	driver(
		"while True:\n"
		"	break\n"
		"	print('hello')"
	)
	# test a simple function with a return statement
	driver(
		"def test():\n"
		"	return 20"
	)

def test_program_transformations():
	# test stmt level transformations without transforming expressions	
	def driver(src: str, expected: str):
		prog = ir.Program(src)
		prog.program = prog.transform_stmts_recurse(prog.program)
		assert expected == prog.transpile()
	
	# test transforming an assert statement to raise an exception
	driver(
		"assert test(hello, 'along'), test",
		(
			"if not (test(hello, 'along')):\n"
			"	raise AssertionError(test)"
		)
	)

	# test transforming a function to a lambda definition
	driver(
		(
			"def test():\n"
			"	pass"
		),
		(
			"def _test0():\n"
			"	global _ret_test0\n"
			"	_ret_test0 = None\n"
			"	pass\n"
			"	yield\n"
			"test = lambda : (next(_test0()), _ret_test0)[1]"
		)
	)

	# test transforming a break statement and else
	driver(
		(
			"while cond():\n"
			"	if test():\n"
			"		break\n"
			"	else:\n"
			"		pass"
		),
		(
			"_while0 = True\n"
			"while _while0 and (cond()):\n"
			"	_if0 = True\n"
			"	if test():\n"
			"		_if0 = False\n"
			"		_while0 = False\n"
			"		continue \n"
			"	if _if0:\n"
			"		pass"
		)
	)

	# test transforming a break statement and else
	driver(
		(
			"vals = {'a': 1, 'b': 2, 'c': 3}\n"
			"for k, v in vals.items():\n"
			"	print(k, v)"
		),
		(
			"vals = {'a': 1, 'b': 2, 'c': 3}\n"
			"_iter0 = iter(vals.items())\n"
			"_for0 = True\n"
			"while _for0:\n"
			"	try:\n"
			"		k, v = next(_iter0)\n"
			"	except StopIteration:\n"
			"		_for0 = False\n"
			"		continue \n"
			"	print(k, v)"
		)
	)

if __name__ == "__main__":
	test_tokenise_first()
	test_iter_to_identifers()
	test_walk_expr_str()
	test_rstrip_str()
	test_program_identity()
	test_program_transformations()
