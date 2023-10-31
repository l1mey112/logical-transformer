def skip_to_identifers(src: str, start: int) -> int:
	# a = "'hello' + 20"
	# assert a[skip_to_identifers(a, 0):] == "+ 20"

	i = start
	strch = None

	while i < len(src):
		ch = src[i]
		
		if ch.isspace():
			i += 1
			continue
			
		if strch is None:
			if ch == "'" or ch == '"':
				strch = ch
			elif ch == "#":
				return len(src)
			else:
				return i
		else:
			if ch == "\\":
				i += 1
			elif ch == strch:
				strch = None
		
		i += 1

	return i