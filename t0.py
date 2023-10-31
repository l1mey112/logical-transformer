from typing import *

# still want a skip forward function....

#def transform_skip_over_undesirables(src: str, start: int) -> int:
#    # may contain comments, may contain strings. parse them out
#
#    start = 0
#    index = 0
#    strch = None
#    inside_string = False
#    while index < len(src):
#        ch = src[index]
#        
#        if ch.isspace():
#            index += 1
#            continue
#
#        if strch is None and (ch == "'" or ch == '"'):
#            strch = ch
#
#        nindex = index + 1
#
#        # test "  
#        #     <^
#
#        if ch == "#":
#            if start != index:
#                yield (True, src[start:index])
#            yield (False, src[index:])
#            break
#        elif ch == strch or nindex >= len(src):
#            inside_string = not inside_string
#
#            if inside_string:
#                # string starting, handle text before
#                yield (True, src[start:index])
#            else:
#                # string over
#                strch = None
#                yield (False, src[start:index])
#
#            start = nindex
#
#        if inside_string:
#            if ch == "\\":
#                index += 1 # skip \n
#        index += 1

def skip(src: str, start: int) -> int:
	i = start
	strch = None

	while i < len(src):
		ch = src[i]
		i += 1

# assert skip('   "hello"   test s') == 'test s'
# assert skip('   # comment') == ''