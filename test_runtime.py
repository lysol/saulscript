from runtime import Runtime
from lexer import *
import sys
import logging

if len(sys.argv) > 2:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.ERROR)

body = open(sys.argv[1], 'r').read()
rt = Runtime()
context = rt.execute(body)
print context
