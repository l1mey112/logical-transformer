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

easy, solved now.

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
if _if0 and cond():
    _if0 = False
    print('test1')
if _if0 and cond():
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

```py
while cond():
    if expr():
        break
```
> original
```py
_while0 = True
while _while0 and cond(): # short circuit
    if expr():
        _while0 = False
        continue
```
> transformation

# for (counter) + for (iterator)

possible for a for loop to unpack into multiple variables, look out for that.

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

---

# the end?

```py
def fizzbuzz(limit):
	fb_count = 0
	for num in range(1, limit + 1):
		if num % 3 == 0 and num % 5 == 0:
			print("FizzBuzz")
			fb_count += 1
		elif num % 3 == 0:
			print("Fizz")
		elif num % 5 == 0:
			print("Buzz")
		else:
			print(num)
	return fb_count
```
> original

*redo transformation*

> transformation (as of recent)
