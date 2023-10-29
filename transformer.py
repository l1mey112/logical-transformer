import sys
from dataclasses import dataclass
from ir import *

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

def get_passes(keywords_file: str) -> Transformations:
	passes = Transformations(0)
	
	f = open(keywords_file)
	keywords = f.readlines()
	
	for keyword in keywords:
		passes |= Transformations[keyword.strip().upper()]
	
	return passes

def main():
	python_src = open(sys.argv[1]).read()
	passes = get_passes(sys.argv[2])

	program = Program(python_src)
	program.transform(passes)

	print(program.transpile(), end="")

if __name__ == "__main__":
	main()