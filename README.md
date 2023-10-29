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
_else = True
if cond1():
    _else = False
    # cond1
if not _else and cond2():
    _else = False
    # cond2
if _else:
    # cond3
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

- [ ] for (counter)
- [ ] in
- [ ] for (iterator)
- [ ] Combinations of the above