from lexer import *
from ast import *
import sys

body = open(sys.argv[1], 'r').read()
result = Lexer(body).run()
# for line in result:
#     for token in line:
#         print token.show(),
#     print
print result
iast = AST(result)
try:
    iast.run()
    iast.dump()
except ParseError as e:
    print e.message
    raise
except AssertionError as e:
    iast.dump()
    raise
