class _Infix:
	__init__ = lambda self, function : setattr(self, "function", function)
	__ror__ = lambda self, other : _Infix(lambda x, self=self, other=other: self.function(other, x))
	__or__ = lambda self, other : self.function(other)
_and = _Infix(lambda x, y: y if x else x)
_or = _Infix(lambda x, y: x if x else y)

class _Prefix:
	__init__ = lambda self, function : setattr(self, "function", function)
	__xor__ = lambda self, other : self.function(other)
_not = _Prefix(lambda x: False == x)

print(not not 0)
print(_not^_not)
print(_not^ _not^ 0)

print('------')

print(1 |_or| 2 |_and| _not^ _not^ 0)
print(1 or 2 and not not 0)
print(1 or 2 and False)
print(1 or 2)
