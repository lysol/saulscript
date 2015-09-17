from lexer import *
import sys


body = open(sys.argv[1], 'r').read()
result = Lexer(body).run()
for token in result:
    print token.show(),
print
