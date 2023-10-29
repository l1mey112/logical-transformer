import sys
from dataclasses import dataclass
from ir import *

def get_keywords(keywords_file: str):
	"""
	This function takes in the file containing the list of keywords as an 
	argument and returns the list of keywords.
	"""
	f = open(keywords_file)
	keywords = f.readlines()
	
	# Remove newline characters
	i = 0
	while i < len(keywords):
		keywords[i] = keywords[i].strip()
		i += 1
		
	# Uncomment out this line to print the list of keywords
	print(keywords)
	
	# Return the list of keywords
	return keywords

def main():
	# keywords = get_keywords(sys.argv[2]) 
#	program = Program("""a = 5
#b = 7
#
#if a > 2 and b < 3:
#	print("Hello, world!")
#	if a > 2 and b < 3:
#		print("Hello, world!")
#
#print("test")""")
	program = Program("""a = 5
b = 7

def test(a, b):
	return a + b

if a > 2 and b < 3:
	print("Hello, world!")
	if a > 2 and b < 3:
		print("Hello, world!")
	print("test")
else:
	print("test2")

assert True, 'fart'

while True:
	pass""")

	print(program.program_src)
	print("---------------------------")
	print(program.transpile())
	
if __name__ == "__main__":
	main()