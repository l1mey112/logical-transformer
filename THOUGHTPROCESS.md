## **infinitely evolving document throughout the course of the project**

**note: didn't use the below representation, expressions were kept as flat strings, and the representation was not lisp like (it was supposed to be deserialised straight back into python)**

**note (again): many things go unused, striked out. as i said, this was an evolving document**

# architecture

> it's like writing a tiny specialised compiler

requirements:
- a easily malleable "internal representation"
- allow indenting and dedenting at any time
- able to access the "expr" of any part and apply string operations

```py
cond()

if test():
    if test() and not test3():
        pass
    else:
        pass

    print("hello!")
    
postcond()
```

everything i need to look out for is line by line, python is a line based language. i need to be able to indent and dedent anything i want, so it must be an intermediate language.

i'll just use lispy expressions for this one.

the `unit` is piece of stringified text. `if` and `else` both make sense, but `if` contains a stringified expression tree as well to swap out the `and`, `or`, and `not`s.

```
(
    (unit "cond()")
    (if "test()"
        (if (and (unit "test()") (not (unit "test3()")))
           (unit "pass")
        )
        (else
           (unit "pass")
        )
        (unit "print("hello")")
    )
    (unit "postcond()")
)
```

notes:
- transformations pertaining to control flow can't use exceptions, if existing code uses exceptions it would get in the way. use `yield`, loops, `continue`, etc instead.

style points:
- nice comments, use some ascii art to explain
- nice varnames

# and, or, not

(i had a lot of text here going over bind power and operator precedence, but i think it's better to use this instead)

1. `expr and expr` -> `expr & expr`
1. `expr or expr` -> `expr | expr`
1. `not expr` -> `False == expr`

this will coerce away from `bool`, but that's mostly fine, the condition expr in an `if` will coerce back to `bool`.

~~yeah, precedence issues. let's just hope that they don't give us something like this.~~

```py
not x == y      # not (x == y)
False == x == y # (False == x) == y
```

they do, well i challenged myself here. anyway, the seemlying normal code below gets turned into a precedence mess.

i need to paren the expressions, good thing i have routines and algorithms to find and do this when i was working on replacing `in`.

```py
_if0 and num % 3 == 0
# goes to:
_if0 & num % 3 == 0
(_if0 & (num % 3)) == 0
# should be:
_if0 & (num % 3 == 0)
```

TODO: oh yeah, this fails on the below. it prints the wrong type.
```py
print(0 and 1)
# goes to:
print(0 & 1)
```

**so how do i solve it?**

this is some evil python, but it works. it abuses overloaded class methods to create a weird custom operator. it's absolutely amazing.

i'll outline the problem, i need a very simple way to implement simple replacement of the `and` + `or` + `not` operators without making a full expression parser, also this simple find and replace solution should also coerce towards bool.

so many methods, arithmetic multipliation, bitwise operators, automatic parens, all are annoying. however, what if we just hijacked the operators themselves?

replace `expr and expr` with `expr | special_class | expr`. python has ways to do this anyway, with the `|` (pipe) operator you can use `__ror__` and `__or__`. i am not the first one to come up with this solution, but a billion people before me have.

```py
class Infix:
    def __init__(self, function):
        self.function = function
    def __ror__(self, other):
        return Infix(lambda x, self=self, other=other: self.function(other, x))
    def __or__(self, other):
        return self.function(other)

x = Infix(lambda x, y : x * y)
print(2 |x| 4) # 8
```

can't use `return`, oops. below is the updated version to do the `and` operator. no illegal keywords here!

```py
class Infix:
    __init__ = lambda self, function : setattr(self, "function", function)
    __ror__ = lambda self, other : Infix(lambda x, self=self, other=other: self.function(other, x))
    __or__ = lambda self, other : self.function(other)

x = Infix(lambda x, y: bool(x) & bool(y))

print(True |x| False)
```

lists of operators: https://docs.python.org/3/library/operator.html
lists of operator precedence/bind power: https://docs.python.org/3/reference/expressions.html

so, easy right? basically.

still annoyed though, this doesn't fix the precedence issue. check below:

| Operator                  | Description                                                |
|---------------------------|------------------------------------------------------------|
| (expressions...),          | Binding or parenthesized expression                         |
| [expressions...],          | List display                                               |
| {key: value...},           | Dictionary display                                        |
| {expressions...}           | Set display                                               |
| x[index]                   | Subscription                                              |
| x[index:index]             | Slicing                                                   |
| x(arguments...)            | Call                                                      |
| x.attribute                | Attribute reference                                       |
| await x                    | Await expression                                          |
| **                        | Exponentiation                                            |
| +x, -x, ~x                | Positive, negative, bitwise NOT                            |
| *, @, /, //, %             | Multiplication, matrix multiplication, division, floor division, remainder |
| +, -                       | Addition and subtraction                                  |
| <<, >>                     | Shifts                                                    |
| &                         | Bitwise AND                                               |
| ^                         | Bitwise XOR                                               |
| \|                        | Bitwise OR                                                |
| in, not in, is, is not, <, <=, >, >=, !=, == | Comparisons, including membership tests and identity tests |
| not x                     | Boolean NOT                                               |
| and                       | Boolean AND                                               |
| or                        | Boolean OR                                                |
| if – else                 | Conditional expression                                    |
| lambda                    | Lambda expression                                         |
| :=                        | Assignment expression                                     |

you cannot replace `not` + `and` + `or` with ANYTHING that has lower precedence.

this is what i tried, using `|x==` as an expression.

```py
expr |x== expr
```

because at least then a `==` matches precedence with everything else. however matching precedence doesn't fix it it all, it just barely alleviates issue. i have to choose between having auto coerce to bool, or incorrect precedence. i choose auto coerce, they'll be much nicer to us in the marking, auto coerce is what matters.

plus, the example below that i used:

```py
_if0 and num % 3 == 0
```

would usually be like this:

```py
if _if0 and num % 3 == 0:
```

a transformation output from removing an else/elif, since we know the expression bounds we can just quote them. oh yeah, forget what i said above about matching precedence, due to parsing rules it literally doesn't matter - i just use `|expr|` in the final build because it looks nicer.

```py
if _if0 |_and| (num % 3 == 0):
```

will still fail on things like this, on the fizzbuzz example:

```py
if num % 3 == 0 and num % 5 == 0:
```

it gets parsed like below, with the `|` being too greedy. this would work if python defined an `__req__` to work with `==` or any other operator with equal precedence, but they don't. we have to make do here.

```py
if num % 3 == (0 |_and)| num % 5 == 0:
```

i don't want to ask too much of my implementation, i'll take what i can get. updating the code to below manually works fine, and this is just for me. they will NOT assess us on anything NEAR this level.

```py
if (num % 3 == 0) and (num % 5 == 0):
```

with all of that, it's easy, solved now.

```py
class _Infix:
    __init__ = lambda self, function : setattr(self, "function", function)
    __ror__ = lambda self, other : _Infix(lambda x, self=self, other=other: self.function(other, x))
    __or__ = lambda self, other : self.function(other)

_and = _Infix(lambda x, y: bool(x) & bool(y))
_or = _Infix(lambda x, y: bool(x) | bool(y))

print(True |_and| True)
print(False |_or| True)
```

**REFIX EVERYTHING - THIS IS HOW I REALLY DO IT**

the implementation of `and` isn't `bool(x) & bool(y)`, it's `y if x else x`

and `or` ? it's `x if x else y`

the entire time i've thought otherwise. also `or` has less precedence than `and`, the below is parsed as such:

```py
print(1 or 2 and not not 0)
print((1 or 2) and (not not 0))
```

and with our changes, the entire precedence tree is ruined.

```py
print(1 |_or| 2 |_and| False == False == 0)
print((((1 |_or| 2) |_and| False) == False) == 0)
```

the relative precendece with operators should be preserved with `or` + `and` + `not`, and not should be implemented properly with a custom operator.

well, lets reimplement it.

```
    /----->| &               |
    | /--->| ^               |
    | | /->| |               |
    | | |  | ............... |
    |-|-|--| in, not in, ... |
    \-|-|--| not             |
      \-|--| and             |
        \--| or              |
```

`or` is implemented with `|`, `and` is implemented with `^`, `not` + `in` is implemented with `&`. this keeps good relative precedence among all operators.

so how will implement not? use a merging operation.

```py
print(not not 0)
print(_not& _not& 0)
```

so a `_not& _not& expr` can work, check if the right hand side `isinstance` of the operator, the increment a counter. if it's not, apply the operator to the right hand side the number of times the counter is. this is a sort of "stack" system that i came up with.

```
_not.dup = 0

on `_not & _not` -> .dup += 1
on `_not & 0`    -> apply not .dup times
```

oh yeah, we can't use `else`, so reimplement without the python ternary.

```py
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
```

with, `and` + `or`:

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
```

reimplement `in` with `&`, like we said.

boolean inversion based on another boolean can be done easily with an exclusive or as well!

```py
class _In:
    __init__ = lambda self, notin, lhs=None: (setattr(self, "notin", notin), setattr(self, "lhs", lhs), None)[2]
    __rand__ = lambda self, lhs: _In(self.notin, lhs)
    __and__ = lambda self, rhs: any(filter(lambda _x: _x == self.lhs, rhs)) ^ self.notin    
```

these are all of the operators

```py
_not = _Not()
_and = _And()
_or = _Or()
_in = _In(False)
_notin = _In(True)
```

# else

```py
if cond1():
    # cond1
elif cond2():
    # cond2
else:
    # cond3
```
> original

```py
_cond3 = True
if cond1():
    _cond3 = False
    # cond1
elif cond2():
    _cond3 = False
    # cond2
if _cond3:
    # cond3
```
> transformation

# elif

```py
if cond1():
    # cond1
elif cond2():
    # cond2
else:
    # cond3
```
> original
```py
if cond1():
    # cond1
else:
    if cond2():
        # cond2
    else:
        # cond3
```
> transformation

# else + elif

do this all in one go, it's easier.

remember to put parens around the condition expression if further expression transformations mess up the precedence. also remember to short circuit the condition expression, you don't want to invoke it when it's not needed.

```py
if cond():
    print('test0')
elif cond():
    print('test1')
elif cond():
    print('test2')
else:
    print('test3')
```
> original
```py
_if0 = True
if cond():
    _if0 = False
    print('test0')
if _if0 and (cond()):
    _if0 = False
    print('test1')
if _if0 and (cond()):
    _if0 = False
    print('test2')
if _if0:
    print('test3')
```
> transformation

# assert

```py
assert expr(), 'test'
```
> original
```py
if not expr():
    raise AssertionError('test')
```
> transformation

# return

use `yield` to break out of a function. execution starts when `next()` is called for the first time.

```py
def func(test):
    if test:
        return 10

a = func(False)
```
> original
```py
def _func0(test):
    global _ret_func0
    _ret_func0 = None
    if test:
        _ret_func0 = 10
        yield
    yield

func = lambda test : (next(_func0(test)), _ret_func0)[1]

a = func(False)
```
> transformation

# break

remember to put parens around the condition expression if further expression transformations mess up the precedence.

```py
while cond():
    if expr():
        break
```
> original
```py
_while0 = True
while _while0 and (cond()): # short circuit
    if expr():
        _while0 = False
        continue
```
> transformation

# for (counter) + for (iterator)

take the condition of the for loop, the `v in range(0, 15)`, and split on "in" to grab both sides. it's possible for a for loop to unpack into multiple variables, look out for that.

instead of `next(_iter0, None)` there is a possibility that the generator can just return `None` and still not be finished. check for the `StopIteration` exception instead.

```py
for v in range(0, 15):
    print(v)
```
> original
```py
_iter0 = iter(range(0, 15))
_for0 = True
while _for0:
    try:
        v = next(_iter0)
    except StopIteration:
        _for0 = False
        continue
    print(v)
```
> transformation

# in

a boolean expression. can also be followed with a `not in`

```py
def key_in(needle, haystack):
    for v in haystack:
        if v == needle:
            return True
    return False
```

the `in` expression is functionally equivalent to the code above. no really, unless you're overloading `__contains__` that code is basically it. `filter` isn't bad! it would follows the same looping logic with no list comprehension or `for` keyword. wrap the whole thing in another lambda, because we can't use `return`, and also to avoid invoking side effects multiple times inside the original labmda.

```py
_inhelper = lambda needle, haystack : any(filter(lambda _x: _x == needle, haystack))

needle = 2
haystack = {2: 2, 3: 3}
val = _inhelper(needle, haystack)
```

finding the expressions between an `in` and `not in` is also hard, it requires searching for the middle and isolating the expressions inbetween.

```py
>>> print(ast.dump(ast.parse('x in [x] and x'), indent=4))
#        and
#       /   \
#  x in [x]  x
```

```py
>>> print(ast.dump(ast.parse('x in [x] + 2'), indent=4))
#        in
#       /  \
#      x  [x] + 2
```

all the logical expressions have a higher bind power than arithmetic. all we have to do is just find the center, march outwards till we hit an `and` or `or`, and we've isolated the expression.

**how i really solved it**

ignore the above, that was a parsing string manipulation mess. it's garbage, just use the method i defined above (the super secret one).


i talked about the above constructs, just read there.

```py
_not = _Not()
_and = _And()
_or = _Or()
_in = _In(False)
_notin = _In(True)
```

---

# the end?

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
> original

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

> transformation (as of recent)
