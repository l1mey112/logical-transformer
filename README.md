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

- [ ] elif
- [ ] assert
- [ ] return
- [ ] break
- [ ] for (counter)
- [ ] in
- [ ] for (iterator)
- [ ] Combinations of the above