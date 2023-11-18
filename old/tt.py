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