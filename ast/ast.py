import nodes
import lexer
import lexer.tokens
import logging


class ParseError(Exception):
    pass


class OutOfTokens(Exception):

    def __init__(self, message):
        self.message = message


class AST(object):

    def execute(self, context):
        for expression in self.tree:
            expression.reduce(context)
        return context

    @property
    def next_token(self):
        try:
            return self.tokens[0]
        except IndexError:
            raise OutOfTokens('at next token')

    def shift_token(self):
        return self.tokens.pop(0)

    def unshift_token(self, item):
        return self.tokens.insert(0, item)

    def __init__(self, tokens):
        self.tokens = tokens
        self.tree = nodes.Branch([])

    def is_identifier(self, token, body):
        return isinstance(token, lexer.tokens.IdentifierToken) and \
            token.body == body

    def run(self):
        while True:
            try:
                # look ahead and if there is a binaryoperator in our future,
                # handle it
                self.tree.append(self.handle_expression())
            except OutOfTokens as e:
                logging.debug('out of tokens: %s', e.message)
                break

    def dump(self):
        for line_num, branch in enumerate(self.tree):
            logging.debug("Operation %d:\n%s", line_num, branch)

    def handle_dictionary_expression(self):
        self.shift_token() # get rid of {
        data = nodes.DictionaryNode()
        while True:
            name = self.shift_token()
            if isinstance(name, lexer.tokens.LineTerminatorToken):
                # So, we can have whitespace after a {
                continue
            if isinstance(name, lexer.tokens.RightCurlyBraceToken):
                # done with this dictionary since we got a }
                break
            if not isinstance(name, lexer.tokens.IdentifierToken) and \
                not isinstance(name, lexer.tokens.NumberLiteralToken) and \
                not isinstance(name, lexer.tokens.StringLiteralToken):
                raise ParseError("Expected a name, got %s (%s)" % (name, name.__class__))
            colon = self.shift_token()
            if not isinstance(colon, lexer.tokens.ColonToken):
                raise ParseError("Expected a colon")
            expression = self.handle_operator_expression() # Goes until the end of a line. No comma needed!
            data.set_item(name.body, expression)
        return data

    def handle_operator_expression(self):
        output = []
        op_stack = []
        prev_token = None

        while True:
            logging.debug("Output stack: %s", output)
            logging.debug("Operator stack: %s", op_stack)
            try:
                if isinstance(self.next_token, lexer.tokens.LeftCurlyBraceToken):
                    output.append(self.handle_dictionary_expression())
                token = self.shift_token()
            except IndexError:
                break
            if isinstance(token, lexer.tokens.LineTerminatorToken):
                logging.debug('break it out')
                break
            if (prev_token is None or
                isinstance(prev_token, lexer.tokens.OperatorToken)) and \
                    isinstance(token, lexer.tokens.SubtractionOperatorToken):
                # unary -
                token = lexer.tokens.NegationOperatorToken()
            if not isinstance(token, lexer.tokens.OperatorToken) and not \
                    isinstance(token, lexer.tokens.LiteralToken) and not \
                    isinstance(token, lexer.tokens.IdentifierToken):
                msg = "Expected an operator, literal, or identifier. (Got %s: %s)" % \
                    (token.__class__, token.body)
                logging.error(msg)
                raise ParseError(msg)
            if isinstance(token, nodes.Node) or not isinstance(token, lexer.tokens.OperatorToken):
                # If anything is a node, append it
                output.append(token)
            else:
                while len(op_stack) > 0:
                    token2 = op_stack[-1]

                    is_left_associative = \
                        token.associativity == lexer.tokens.OperatorToken.LEFT
                    is_right_associative = \
                        token.associativity == lexer.tokens.OperatorToken.RIGHT
                    logging.debug("Is Left Associative: %s\t"
                                  "Is Right Associative: %s",
                                  is_left_associative, is_right_associative)
                    if (is_left_associative and token.precedence >= token2.precedence) or \
                            (is_right_associative and
                                token.precedence > token2.precedence):
                        if not isinstance(token, lexer.tokens.RightParenToken):
                            if not isinstance(token2,
                                              lexer.tokens.LeftParenToken):
                                op_token = op_stack.pop()
                                logging.debug(
                                    "Popping %s off stack", op_token.body)
                                output.append(op_token)
                            else:
                                # break because we hit a left paren
                                break
                        else:
                            if not isinstance(token2,
                                              lexer.tokens.LeftParenToken):
                                op_token = op_stack.pop()
                                output.append(op_token)
                            else:
                                # discard left paren and break
                                op_stack.pop()
                                break
                    else:
                        # left operator is equal or larger than right. breakin
                        break
                if not isinstance(token, lexer.tokens.RightParenToken):
                    # push current operator to stack
                    op_stack.append(token)
                # ignore right paren
            # hold onto this for the next run in case we need to
            # check for unary operators
            prev_token = token
        # drain the operator stack
        while len(op_stack) > 0:
            operator = op_stack.pop()
            output.append(operator)

        logging.debug('Output: ')
        logging.debug(output)

        tree_stack = []
        # turn the list of output tokens into a tree branch
        logging.debug('Turn list of output tokens into a tree branch')
        while True:
            try:
                token = output.pop(0)
            except IndexError:
                break
            if not isinstance(token, lexer.tokens.OperatorToken):
                tree_stack.append(self.handle_token(token))
            else:
                logging.debug("%s", tree_stack)
                logging.debug("Determining if %s is unary or binary", token)
                if isinstance(token, lexer.tokens.BinaryOperatorToken):
                    logging.debug("%s is binary", token)
                    right, left = tree_stack.pop(), tree_stack.pop()
                    tree_stack.append(token.get_node(left, right))
                elif isinstance(token, lexer.tokens.UnaryOperatorToken):
                    logging.debug("%s is unary", token)
                    target = tree_stack.pop()
                    tree_stack.append(token.get_node(target))
        logging.debug("%s" % tree_stack)
        assert len(tree_stack) == 1

        logging.debug('The final tree leaf: %s', tree_stack[0])
        return tree_stack.pop()  # -----------===============#################*

    def handle_token(self, token):
        if isinstance(token, nodes.Node):
            # already resolved down the chain
            return token
        if isinstance(token, lexer.tokens.IdentifierToken):
            # variable?
            # in the future, a function
            return nodes.VariableNode(token.body)
        elif isinstance(token, lexer.tokens.NumberLiteralToken):
            return nodes.NumberNode(token.body)
        elif isinstance(token, lexer.tokens.StringLiteralToken):
            return nodes.StringNode(token.body)
        assert False

    def handle_expression(self):
        while True:
            try:
                logging.debug('Handling expression')
                token = self.next_token
                logging.debug("Consider %s", token.__class__)
            except IndexError:
                raise OutOfTokens('During handle expression')
            if isinstance(token, lexer.tokens.IdentifierToken):
                if self.handler_exists(token):
                    return self.handle_identifier()
                else:
                    return self.handle_operator_expression()
            elif isinstance(token, lexer.tokens.LineTerminatorToken):
                logging.debug("Delete this infernal line terminator")
                self.shift_token()
                return nodes.NopNode()

    def handler_exists(self, token):
        method_name = 'handle_identifier_' + token.body
        return hasattr(self, method_name)

    def handle_identifier(self):
        token = self.shift_token()
        method_name = 'handle_identifier_' + token.body
        method = getattr(self, method_name)
        return method(token)

    def handle_identifier_if(self, token):
        logging.debug("Handling IF")
        condition = self.handle_operator_expression()
        then_branch = nodes.Branch([])
        else_branch = nodes.Branch([])
        while not isinstance(self.next_token, lexer.tokens.IdentifierToken) or \
                self.next_token.body not in ['else', 'end']:
            logging.debug("Checking next expression as part of THEN clause")
            then_branch.append(self.handle_expression())

        if isinstance(self.next_token, lexer.tokens.IdentifierToken) and \
                self.next_token.body == 'else':
            self.shift_token()
            while not isinstance(self.next_token, lexer.tokens.IdentifierToken) or \
                    self.tokens[0:2] != ['end', 'if']:
                logging.debug(
                    "Checking next expression as part of ELSE clause")
                else_branch.append(self.handle_expression())
        end_token = self.shift_token()
        if_token = self.shift_token()
        logging.debug("Then: %s, Else: %s, End If: %s %s",
                      then_branch, else_branch, end_token.body, if_token.body)
        assert isinstance(end_token, lexer.tokens.IdentifierToken) and \
            end_token.body == 'end'
        assert isinstance(if_token, lexer.tokens.IdentifierToken) and \
            if_token.body == 'if'

        return nodes.IfNode(condition, then_branch, else_branch)

    def handle_identifier_true(self, token):
        assert token.value.lower() == 'true'
        return nodes.BooleanNode(True)

    def handle_identifier_false(self, token):
        assert token.value.lower() == 'false'
        return nodes.BooleanNode(False)
