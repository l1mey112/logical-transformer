def fizzbuzz(limit):
	fb_count = 0
	for num in range(1, limit + 1):
		if (num % 3 == 0) and (num % 5 == 0):
			print("FizzBuzz")
			fb_count += 1
		elif num % 3 == 0:
			print("Fizz")
		elif num % 5 == 0:
			print("Buzz")
		else:
			print(num)
	return fb_count

def main():
	n = 15
	print("Playing FizzBuzz game up to", n)
	fb_count = fizzbuzz(n)
	print("Total FizzBuzz:", fb_count)

if __name__ == "__main__":
	main()