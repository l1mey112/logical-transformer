memo = {}

def fib(n):
	if n <= 1:
		return n
	
	if n not in memo:
		memo[n] = fib(n - 1) + fib(n - 2)
	
	return memo[n]


def main():
	v = fib(10)
	print(v)

if __name__ == "__main__":
	main()