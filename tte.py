class _Infix:
    __init__ = lambda self, function : setattr(self, "function", function)
    __ror__ = lambda self, other : _Infix(lambda x, self=self, other=other: self.function(other, x))
    __or__ = lambda self, other : self.function(other)

_and = _Infix(lambda x, y: bool(x) & bool(y))
_or = _Infix(lambda x, y: bool(x) | bool(y))

print(True |_and| True)
print(False |_or| True)