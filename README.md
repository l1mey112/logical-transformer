# logical-transformer

logical transformer implemented for INFO1110. article to come soon.

- [thought process document used throughout the project to plan my ideas](THOUGHTPROCESS.md)

---

**run with `python3 transformer.py <file>.py`**

```py
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
```

```py
class _And:
	__init__ = lambda self, lhs=None : setattr(self, "lhs", lhs)
	__rxor__ = lambda self, lhs: _And(lhs)
	__xor__ = lambda self, rhs: (self.impl_and(rhs), self.op_ret)[1]
	def impl_and(self, rhs):
		passed = True
		if self.lhs:
			self.op_ret = rhs
			passed = False
		if passed:
			self.op_ret = self.lhs
_and = _And()
def _fizzbuzz0(limit):
	global _ret_fizzbuzz0
	_ret_fizzbuzz0 = None
	fb_count = 0
	_iter0 = iter(range(1, limit + 1))
	_for0 = True
	while _for0:
		try:
			num = next(_iter0)
		except StopIteration:
			_for0 = False
			continue 
		_if0 = True
		if (num % 3 == 0) ^_and^ (num % 5 == 0):
			_if0 = False
			print("FizzBuzz")
			fb_count += 1
		if _if0 ^_and^ (num % 3 == 0):
			_if0 = False
			print("Fizz")
		if _if0 ^_and^ (num % 5 == 0):
			_if0 = False
			print("Buzz")
		if _if0:
			print(num)
	_ret_fizzbuzz0 = fb_count
	yield
	yield
fizzbuzz = lambda limit : (next(_fizzbuzz0(limit)), _ret_fizzbuzz0)[1]
def _main0():
	global _ret_main0
	_ret_main0 = None
	n = 15
	print("Playing FizzBuzz game up to", n)
	fb_count = fizzbuzz(n)
	print("Total FizzBuzz:", fb_count)
	yield
main = lambda : (next(_main0()), _ret_main0)[1]
if __name__ == "__main__":
	main()
```