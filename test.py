#if cond():
#	print('test0')
#elif cond():
#	print('test1')
#elif cond():
#	print('test2')
#else:
#	print('test3')
#
#assert cond(), 'ahahahah'
#
#while cond():
#	print('hello')
#	if expr():
#		while cond():
#			print('hello')
#			if expr():
#				print('hello')
#		break
#	print('hello')
#
#while cond():
#	pass

for v in range(0, 15):
	if v == 2:
		break
	print(v)

for v in cond():
	pass