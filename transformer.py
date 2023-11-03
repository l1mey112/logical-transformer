import sys
from ir import *

# --- Just. Remove. Everything.
#
# l-m>   Will I lose marks for removing things I am not supposed to?
# Ankit> No
# l-m>   So I can just ignore the keywords file and just rip everything out?
# Ankit> I mean, technically yes, but you’re just making life harder for yourself.

# python3 transformer.py <path_to_python_script.py> <keywords_text_file.txt>
#         ^^^^^^^^^^^^^^ ^^^^^^^^^^^^^^^^^^^^^^^^^^ ^^^^^^^^^^^^^^^^^^^^^^^^
#         argv[0]        argv[1]                    argv[2]

def main():
	# yeah, we don't need this
	# passes = get_passes(sys.argv[2])

	with open(sys.argv[1], "r") as f:
		python_src = f.read()

	program = Program(python_src)
	program.transform()
	new_src = program.transpile()

	with open(sys.argv[1], "w") as f:
		f.write(new_src)

if __name__ == "__main__":
	main()
