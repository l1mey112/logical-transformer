import ir

def test_tokenise_first():
	# test the tokeniser to get the first identifier
	assert ir.tokenise_first("assert expr, 'hello'") == 'assert'
	assert ir.tokenise_first("if(expr):") == 'if'
	assert ir.tokenise_first("elif(expr):") == 'elif'
	assert ir.tokenise_first("def test():") == 'def'

def test_iter_to_identifers():
	# test the iterator to get the identifiers, and invalid ones
	def driver(src: str, expected):
		t1 = ir.iter_to_identifers(src)
		
		i = 0
		for valid, start, end in t1:
			assert expected[i] == (valid, src[start:end])
			i += 1
		
		assert i == len(expected)
	
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
	
	driver("test(hello, 'along'), test", " test")
	driver("test(hello, 'along')", None)

def test_rstrip_str():
	assert ir.rstrip_str("for guess in range(1, 101):  # Simulating guesses from 1 to 100", ":") == "for guess in range(1, 101)"
	assert ir.rstrip_str("none at all", ":") == "none at all"

def test_program_identity():
	# test the identity of parsing and transpilation of the IR
	def driver(src: str):
		assert src == ir.Program(src).transpile()
	
	driver(
		"assert test(hello, 'along'), test"
	)
	driver(
		"def test():\n"
		"	print('hello')\n"
		"	print('world')\n"
		"	print('!')"
	)
	driver(
		"while True:\n"
		"	break\n"
		"	print('hello')"
	)
	driver(
		"def test():\n"
		"	return 20"
	)

def test_program_transformations():
	# test stmt level transformations, but don't transform expressions	
	def driver(src: str, expected: str):
		prog = ir.Program(src)
		prog.program = prog.transform_stmts_recurse(prog.program)
		assert expected == prog.transpile()
	
	driver(
		"assert test(hello, 'along'), test",
		(
			"if not (test(hello, 'along')):\n"
			"	raise AssertionError(test)"
		)
	)

	driver(
		"assert test(hello, 'along'), test",
		(
			"if not (test(hello, 'along')):\n"
			"	raise AssertionError(test)"
		)
	)

if __name__ == "__main__":
	test_tokenise_first()
	test_iter_to_identifers()
	test_walk_expr_str()
	test_rstrip_str()
	test_program_identity()
	test_program_transformations()