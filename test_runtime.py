from saulscript import Context
import sys
import logging

if len(sys.argv) > 2:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.ERROR)

body = open(sys.argv[1], 'r').read()
ctx = Context()
result = ctx.execute(body)
print ctx
