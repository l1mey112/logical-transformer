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
class _Or:
	__init__ = lambda self, lhs=None: setattr(self, "lhs", lhs)
	__ror__ = lambda self, lhs: _Or(lhs)
	__or__ = lambda self, rhs: (self.impl_or(rhs), self.op_ret)[1]
	def impl_or(self, rhs):
		passed = True
		if self.lhs:
			self.op_ret = self.lhs
			passed = False
		if passed:
			self.op_ret = rhs
class _Not:
	__init__ = lambda self: setattr(self, "dup", 1)
	__and__ = lambda self, other: (self.impl_not(other), self.op_ret)[1]
	def impl_not(self, other):
		is_inst = isinstance(other, _Not)
		if is_inst:
			self.dup += 1
			self.op_ret = self
		if False == is_inst:
			self.impl_operate(other)
	def impl_operate(self, other):
		ret = other
		while self.dup > 0:
			ret = False == bool(ret)
			self.dup -= 1
		self.op_ret = ret
class _In:
	__init__ = lambda self, notin, lhs=None: (setattr(self, "notin", notin), setattr(self, "lhs", lhs), None)[2]
	__rand__ = lambda self, lhs: _In(self.notin, lhs)
	__and__ = lambda self, rhs: any(filter(lambda _x: _x == self.lhs, rhs)) ^ self.notin

_not = _Not()
_and = _And()
_or = _Or()
_in = _In(False)
_notin = _In(True)

print(2 &_notin& [3, 2, 5])

print('------')

print(1 |_or| 2 ^_and^ _not& _not& 0)
print(1 or 2 and not not 0)
print(False |_or| True ^_and^ False)