from runtime import Runtime
from lexer import *
import sys

body = open(sys.argv[1], 'r').read()
rt = Runtime()
context = rt.execute(body)
print context