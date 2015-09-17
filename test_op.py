import string


"""

Expression as Infix
3 + 10 * 12 / ( 3 - 2 )
Postfix
3 10 12 * 3 2 - / +
"""


class Operator(object):

    ops = {
        '(': 1,
        '.': 1,
        '*': 3,
        '/': 3,
        '+': 4,
        '-': 4,
        '>': 6,
        '>=': 6,
        '<': 6,
        '<=': 6,
        '==': 7,
        ')': 9,
        '=': 14
    }

    def __init__(self, operator):
        self.prec = self.ops[operator]
        self.op = operator

    def __str__(self):
        return self.__repr__

    def __repr__(self):
        return self.op

expression = '1 + 20 / ( 10 + 5 ) * 10 + 3'.split()

op_stack = []
output = []


def show_info():
    print "operator stack ", op_stack
    print "output ", repr(output)

while True:
    try:
        token = expression.pop(0)
    except IndexError:
        break
    if token[0] in string.digits:
        # number
        print 'adding %d to output' % float(token)
        output.append(float(token))
        show_info()
    elif token in Operator.ops:
        token1, val1 = token, Operator.ops[token]
        print 'Considering operator %s' % token1
        while len(op_stack) > 0:
            print 'Pop ops from stack to output'
            token2, val2 = op_stack[-1], Operator.ops[op_stack[-1]]
            if val1 >= val2:
                if token1 != ')':
                    if token2 != '(':
                        operator = Operator(op_stack.pop())
                        print "Popping %s off stack" % operator.op
                        output.append(operator)
                        show_info()
                    else:
                        print 'Breaking because we\'re at a ('
                        break
                else:
                    if token2 != '(':
                        operator = Operator(op_stack.pop())
                        print "Popping %s off stack" % operator.op
                        output.append(operator)
                        show_info()
                    else:
                        print 'Pop ( off and discard. Breakin op loop'
                        op_stack.pop()
                        show_info()
                        break
            else:
                print "Left operator is equal or larger than right. Break from poppin"
                break
        if token1 != ')':
            print "Pushing current token to operator stack"
            op_stack.append(token)
            show_info()
        else:
            print 'Ignoring )'
print "Draining operator stack"
while len(op_stack) > 0:
    operator = Operator(op_stack.pop())
    output.append(operator)
    print "Added %s" % operator.op
    show_info()
print "calculating it"

calc_stack = []

while True:
    try:
        item = output.pop(0)
    except IndexError:
        break
    if not isinstance(item, Operator):
        # number
        calc_stack.append(item)
    else:
        right, left = calc_stack.pop(), calc_stack.pop()
        expr = '%.5f %s %.5f' % (left, item.op, right)
        print 'Evaluating %s' % expr
        calc_stack.append(eval(expr))
    print "Calc Stack: ", calc_stack
