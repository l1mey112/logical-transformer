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

these operators have very low "bind power" - "precedence" - etc, we don't need to account for everything else.

> all logical operators have VERY LOW precedence

so to select an expression that is related to these operators, scan until you reach another one (or a EOL).

```
and ... ... ... ... and
    ^^^^^^^^^^^^^^^   \- not here, this has a low precedence
                  \- this is the expression
```

simple arithmetic can replace these operators, python has C like truthiness.

```py
True - 1 == False       # not operator
True * False == False   # and operator
True + False == True    # or operator
```

you could use bitwise, but that won't work with bitwise not.

```py
~True == -2 == ~1       # not right
```

that's replacing, but exact precedence?

```py
>>> import ast
>>> print(ast.dump(ast.parse('not True and False', mode='eval'), indent=4))
Expression(
    body=BoolOp(
        op=And(),
        values=[
            UnaryOp(
                op=Not(),
                operand=Constant(value=True)),
            Constant(value=False)]))
```

> `not True and False` is parsed as `(not True) and False`

when you hit `not` keep scanning till you hit `and` or `or` or EOL, then you have the expression.

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
while (cond()) and _while0:
    if expr():
        _while0 = False
        continue
```
> transformation

- [ ] for (counter)
- [ ] in
- [ ] for (iterator)
- [ ] Combinations of the above