class CustomAnd:
	def __init__(self, function):
		self.function = function

	def __ror__(self, other):
		return CustomAnd(lambda x, self=self, other=other: self.function(other, x))

	def __eq__(self, other):
		return self.function(other)

# Examples
x = CustomAnd(lambda x, y: bool(x) & bool(y))

# result_and = True |x== True
# print(result_and)

_if0 = True
num = 3

print(_if0 |x== (num % 3 == 0))

