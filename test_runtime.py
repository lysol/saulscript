from runtime import Runtime
from lexer import *
import sys
import logging

logging.basicConfig(level=logging.DEBUG)

body = open(sys.argv[1], 'r').read()
rt = Runtime()
context = rt.execute(body)
print context