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

yeah, precedence issues. let's just hope that they don't give us something like this.

```py
not x == y      # not (x == y)
False == x == y # (False == x) == y
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

```py
def func():
    if test:
        return 10

a = func()
```
> original
```py
def func():
    if test:
        yield 10
    yield None

a = next(func())
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

the `in` expression is functionally equivalent to the code above. no really, unless you're overloading `__contains__` that code is basically it. `filter` isn't bad! it would follows the same looping logic with no list comprehension, or `for` keyword. wrap the whole thing in another lambda, because we can't use `return`, and also to avoid invoking side effects multiple times inside the original labmda.

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
#       /   \
#      x  [x] + 2
```

all the logical expressions have a higher bind power than arithmetic. all we have to do is just find the center, march outwards till we hit an `and` or `or`, and we've isolated the expression.