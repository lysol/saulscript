import nodes
import lexer
import lexer.tokens
import logging


class ParseError(Exception):
    pass


class EndContextExecution(Exception):
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
            except EndContextExecution:
                logging.error('Unexpected }')
                raise ParseError("Unexpected }")

    def dump(self):
        for line_num, branch in enumerate(self.tree):
            logging.debug("Operation %d:\n%s", line_num, branch)

    def handle_function_definition(self):
        logging.debug("Handling a function definition")
        self.shift_token() # get rid of (
        sig_names = []
        while True:
            token = self.shift_token()
            if isinstance(token, lexer.tokens.RightParenToken):
                break # get rid of it
            if isinstance(token, lexer.tokens.CommaToken):
                continue # eat it
            if not isinstance(token, lexer.tokens.IdentifierToken):
                raise ParseError("Expected an argument name, got %s" % token)
            sig_names.append(token.body)
        if not isinstance(self.next_token, lexer.tokens.LeftCurlyBraceToken):
            raise ParseError("Expected {, got %s" % self.next_token)
        self.shift_token() # get rid of {

        new_branch = nodes.Branch()
        while True:
            try:
                new_branch.append(self.handle_expression())
            except EndContextExecution:
                # end of function declaration
                break
        func_node = nodes.FunctionNode(sig_names, new_branch)
        return func_node

    def handle_function_invocation(self, name_token):
        logging.debug("Handling a function invocation")
        self.shift_token() # get rid of (
        arg_tokens = []
        logging.debug("Examining arguments")
        while True:
            token = self.next_token
            logging.debug("Function Invocation: Consider %s" % token)
            if isinstance(token, lexer.tokens.RightParenToken):
                self.shift_token()
                break
            arg_tokens.append(self.handle_operator_expression())
            if isinstance(self.next_token, lexer.tokens.CommaToken):
                # eat the comma and keep going
                self.shift_token()
                continue
        logging.debug("Done reading arguments")
        return nodes.InvocationNode(name_token.body, arg_tokens)          

    def handle_list_expression(self):
        logging.debug("Handling a list expression")
        self.shift_token() # get rid of [
        data = nodes.ListNode()
        while isinstance(self.next_token, lexer.tokens.LineTerminatorToken):
            # ignore line breaks here until we see data
            self.shift_token()
        while True:
            logging.debug("List looks like this now: %s", data)
            if isinstance(self.next_token, lexer.tokens.RightSquareBraceToken):
                logging.debug("Encountered a ], shift it off and return the list node.")
                self.shift_token()
                break
            expression = self.handle_operator_expression()
            if isinstance(self.next_token, lexer.tokens.CommaToken):
                # eat the comma and keep going
                self.shift_token()
            if expression is not None:
                data.append(expression)
        return data

    def handle_dictionary_expression(self):
        logging.debug("Handling a dictionary expression")
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
            if expression is not None:
                data.set_item(name.body, expression)
        return data

    def handle_operator_expression(self):
        output = []
        op_stack = []
        prev_token = None
        # keep track of the parens opened. If we deplete all the (s, stop parsing the operator expression
        paren_count = 0

        while True:
            logging.debug("Output stack: %s", output)
            logging.debug("Operator stack: %s", op_stack)
            try:
                if isinstance(self.next_token, lexer.tokens.LeftCurlyBraceToken):
                    output.append(self.handle_dictionary_expression())
                elif isinstance(self.next_token, lexer.tokens.LeftSquareBraceToken):
                    output.append(self.handle_list_expression())
                elif isinstance(self.next_token, lexer.tokens.RightCurlyBraceToken):
                    logging.debug("} encountered, stop processing operator expression")
                    break
                elif isinstance(self.next_token, lexer.tokens.LeftParenToken):
                    paren_count += 1
                elif isinstance(self.next_token, lexer.tokens.RightParenToken):
                    paren_count -= 1
                    if paren_count < 0:
                        # too many )s found. This is the end of the operator expression
                        break
                token = self.shift_token()
                logging.debug("Operator context: Consider %s", token)
            except IndexError:
                logging.debug("Encountered IndexError, break")
                break
            if isinstance(token, lexer.tokens.LineTerminatorToken) or \
                isinstance(token, lexer.tokens.RightCurlyBraceToken) or \
                isinstance(token, lexer.tokens.CommaToken):
                logging.debug('encountered a line terminator, comma, or }, break it out')
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
                if isinstance(self.next_token, lexer.tokens.LeftParenToken):
                    # function invocation or definition
                    if token.body == 'function':
                        output.append(self.handle_function_definition())
                    else:
                        output.append(self.handle_function_invocation(token))
                else:
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

        if len(output) == 0:
            # nothing. probably a \n after a ,
            return None

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
                    try:
                        right, left = tree_stack.pop(), tree_stack.pop()
                    except IndexError:
                        logging.error("Encountered IndexError. Tree stack: %s", tree_stack)
                        raise ParseError()
                    tree_stack.append(token.get_node(left, right))
                elif isinstance(token, lexer.tokens.UnaryOperatorToken):
                    logging.debug("%s is unary", token)
                    target = tree_stack.pop()
                    tree_stack.append(token.get_node(target))
        logging.debug("%s" % tree_stack)
        if len(tree_stack) != 1:
            logging.error("Tree stack length is not 1. Contents: %s", tree_stack)
        assert len(tree_stack) == 1

        logging.debug('The final tree leaf: %s', tree_stack[0])
        return tree_stack.pop()  # -----------===============#################*

    def handle_token(self, token):
        if isinstance(token, nodes.Node) or isinstance(token, nodes.ListNode):
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
        assert "Unexpected token: %s (%s)" % (token, token.__class__)

    def handle_expression(self):
        while True:
            try:
                logging.debug('Handling expression')
                token = self.next_token
                logging.debug("Consider %s", token.__class__)
            except IndexError:
                raise OutOfTokens('During handle expression')
            if isinstance(token, lexer.tokens.IdentifierToken) or \
                isinstance(token, lexer.tokens.LiteralToken):
                if self.handler_exists(token):
                    return self.handle_identifier()
                else:
                    return self.handle_operator_expression()
            elif isinstance(token, lexer.tokens.LineTerminatorToken):
                logging.debug("Delete this infernal line terminator")
                self.shift_token()
                return nodes.NopNode()
            elif isinstance(token, lexer.tokens.RightCurlyBraceToken):
                logging.debug("Found }, beat it")
                self.shift_token()
                raise EndContextExecution()

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
            try:
                then_branch.append(self.handle_expression())
            except EndContextExecution:
                logging.error("There shouldn't be a } here because we're in an if statement")
                raise ParseError("Unexpected }")

        if isinstance(self.next_token, lexer.tokens.IdentifierToken) and \
                self.next_token.body == 'else':
            self.shift_token()
            while not isinstance(self.next_token, lexer.tokens.IdentifierToken) or \
                    self.tokens[0:2] != ['end', 'if']:
                logging.debug(
                    "Checking next expression as part of ELSE clause")
                try:
                    else_branch.append(self.handle_expression())
                except EndContextExecution:
                    logging.error("There shouldn't be a } here because we're in an if statement")
                    raise ParseError("Unexpected }")
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

    def handle_identifier_return(self, token):
        logging.debug("Handling return statement")
        return_node = self.handle_operator_expression()
        return nodes.ReturnNode(return_node)
