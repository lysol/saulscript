import logging
import nodes
from .. import exceptions
from ..lexer import tokens
import traceback
import sys

class SyntaxTree(object):

    def _debug(self, text, *args):
        if type(text) != str:
            text = repr(text)
        logging.debug(("<Line %d, Token %d> " % (self.line_num, self.token_counter)) + text, *args)

    def _inc_line(self):
        self.line_num += 1
        self.token_counter = 0

    def execute(self, context, time_limit=-1, op_limit=-1):
        context.set_op_limit(op_limit)
        context.set_time_limit(time_limit)

        for expression in self.tree:
            expression.reduce(context)
        return context

    @property
    def next_token(self):
        try:
            return self.tokens[0]
        except IndexError:
            raise exceptions.OutOfTokens(self.line_num, 'at next token')

    def shift_token(self):
        self._debug('Shifting token %s', self.next_token)
        self.token_counter += 1
        try:
            token = self.tokens.pop(0)
            self.line_num = token.line_num
            return token
        except IndexError:
            raise exceptions.ParseError(self.line_num, "Unexpected end of input")

    def unshift_token(self, item):
        return self.tokens.insert(0, item)

    def __init__(self, context_class, tokens):
        self.tokens = tokens
        self.tree = nodes.Branch([])
        self.line_num = 0
        self.context_class = context_class
        self.token_counter = 0

    def is_identifier(self, token, body):
        return isinstance(token, tokens.IdentifierToken) and \
            token.body == body

    def run(self):
        while True:
            try:
                # look ahead and if there is a binaryoperator in our future,
                # handle it
                self.tree.append(self.handle_expression())
            except exceptions.OutOfTokens as e:
                self._debug('*** Out of tokens: %s', e.message)
                for line in self.tree:
                    self._debug("FINAL AST: %s", line)
                break
            except exceptions.EndContextExecution:
                logging.error('Unexpected }')
                raise exceptions.ParseError(self.line_num, "Unexpected }")

    def dump(self):
        for line_num, branch in enumerate(self.tree):
            self._debug("Operation %d:\n%s", line_num, branch)

    def handle_function_definition(self):
        self._debug("Handling a function definition")
        self.shift_token()  # get rid of (
        sig_names = []
        while True:
            token = self.shift_token()
            if isinstance(token, tokens.RightParenToken):
                self._debug("Found right paren, continue with rest of function definition")
                break  # get rid of it
            if isinstance(token, tokens.CommaToken):
                self._debug("Found comma, continue to next argument")
                continue  # eat it
            if not isinstance(token, tokens.IdentifierToken):
                raise exceptions.ParseError(self.line_num,
                    "Expected an argument name, got %s" % token)
            sig_names.append(token.body)
        if not isinstance(self.next_token, tokens.LeftCurlyBraceToken):
            raise exceptions.ParseError(self.line_num, "Expected {, got %s" % self.next_token)
        self.shift_token()  # get rid of {

        new_branch = nodes.Branch()
        while True:
            try:
                new_branch.append(self.handle_expression())
            except exceptions.EndContextExecution:
                # end of function declaration
                break
        func_node = nodes.FunctionNode(self.line_num, self.context_class, sig_names, new_branch)
        return func_node

    def handle_subscript_notation(self, variable_token):
        self._debug("Handling a subscript notation")
        self.shift_token()  # get rid of [
        index_node = self.handle_operator_expression()  # ends before ]
        sub_node = nodes.SubscriptNotationNode(self.line_num, 
            nodes.VariableNode(self.line_num, variable_token.body), index_node)
        if not isinstance(self.next_token, tokens.RightSquareBraceToken):
            raise exceptions.ParseError(self.line_num,
                "Unexpected %s during subscript notation parse" %
                self.next_token)
        self.shift_token()
        return sub_node

    def handle_function_invocation(self, name_token):
        self._debug("Handling a function invocation")
        self.shift_token()  # get rid of (
        arg_tokens = []
        self._debug("Examining arguments")
        while True:
            token = self.next_token
            self._debug("Current argument set: %s", repr(arg_tokens))
            self._debug("Function Invocation: Consider %s" % token)
            if isinstance(token, tokens.RightParenToken):
                self.shift_token()
                break
            arg = self.handle_operator_expression()
            if arg is None:
                raise exceptions.ParseError(self.line_num,
                    "Unexpected character")
            arg_tokens.append(arg)
            if isinstance(self.next_token, tokens.CommaToken):
                self._debug("Found comma, continue to next argument")
                # eat the comma and keep going
                self.shift_token()
                continue
        self._debug("Done reading arguments in function invocation")
        return nodes.InvocationNode(self.line_num, name_token.body, arg_tokens)

    def handle_list_expression(self):
        self._debug("Handling a list expression")
        self.shift_token()  # get rid of [
        data = nodes.ListNode()
        while isinstance(self.next_token, tokens.LineTerminatorToken):
            # ignore line breaks here until we see data
            self.shift_token()
        while True:
            self._debug("List looks like this now: %s", data)
            if isinstance(self.next_token, tokens.RightSquareBraceToken):
                self._debug(
                    "Encountered a ], shift it off and return the list node.")
                self.shift_token()
                break
            expression = self.handle_operator_expression()
            if isinstance(self.next_token, tokens.CommaToken):
                # eat the comma and keep going
                self.shift_token()
            if expression is not None:
                data.append(expression)
        return data

    def handle_dictionary_expression(self):
        self._debug("Handling a dictionary expression")
        self.shift_token()  # get rid of {
        data = nodes.DictionaryNode(self.line_num)
        while True:
            name = self.shift_token()
            if isinstance(name, tokens.LineTerminatorToken):
                # So, we can have whitespace after a {
                self._inc_line()
                continue
            if isinstance(name, tokens.RightCurlyBraceToken):
                # done with this dictionary since we got a }
                break
            if not isinstance(name, tokens.IdentifierToken) and \
                not isinstance(name, tokens.NumberLiteralToken) and \
                    not isinstance(name, tokens.StringLiteralToken):
                raise exceptions.ParseError(self.line_num,
                                            "Expected a name, got %s (%s)" %
                                            (name, name.__class__))
            colon = self.shift_token()
            if not isinstance(colon, tokens.ColonToken):
                raise exceptions.ParseError(self.line_num, "Expected a colon")
            # Goes until the end of a line. No comma needed!
            expression = self.handle_operator_expression()
            if expression is not None:
                data[name.body] = expression
        return data

    def handle_operator_expression(self):
        self._debug("Handling operator expression.")
        output = []
        op_stack = []
        prev_token = None
        # keep track of the parens opened.
        # If we deplete all the (s, stop parsing the operator expression
        paren_count = 0

        while True:
            self._debug("Output stack: %s", output)
            self._debug("Operator stack: %s", op_stack)
            try:
                self._debug('The next token is %s', self.next_token)
                if isinstance(self.next_token,
                              tokens.LeftCurlyBraceToken):
                    self._debug(">> Calling handle_dictionary_expression from operator_expression")
                    output.append(self.handle_dictionary_expression())
                elif isinstance(self.next_token,
                                tokens.LeftSquareBraceToken):
                    self._debug(">> Calling handle_list_expression from operator_expression")
                    output.append(self.handle_list_expression())
                elif isinstance(self.next_token,
                                tokens.RightCurlyBraceToken):
                    self._debug(
                        ">> } encountered, stop processing operator expression")
                    self._debug(
                        str(paren_count))
                    if paren_count > 0:
                        self._debug("Paren count is over 1 while a } has been encountered.")
                        raise exceptions.ParseError("Unexpected }")
                    break
                elif isinstance(self.next_token,
                                tokens.RightSquareBraceToken):
                    self._debug(
                        ">> ] encountered, stop processing operator expression")
                    if paren_count > 0:
                        self._debug("Paren count is over 1 while a } has been encountered.")
                        raise exceptions.ParseError("Unexpected }")                    
                    break
                if isinstance(self.next_token, tokens.LeftParenToken):
                    self._debug('Incrementing number of parens.')
                    paren_count += 1
                if isinstance(self.next_token, tokens.RightParenToken):
                    paren_count -= 1
                    self._debug(">> Decrementing number of parens.")
                    if paren_count < 1:
                        self._debug(">> Found an unmatched ), which means this is the end of the operator expression")
                        # too many )s found. This is the end of
                        # the operator expression
                        break
                if isinstance(self.next_token, tokens.RightParenToken):
                    self._debug("THE RIGHT PAREN IS HERE")
                self._debug('Parent Count: %d', paren_count)
                token = self.shift_token()
                self._debug("Operator context: Consider %s", token)
            except IndexError:
                self._debug("Encountered IndexError, break")
                break
            if isinstance(token, tokens.LineTerminatorToken) or \
                isinstance(token, tokens.RightCurlyBraceToken) or \
                    isinstance(token, tokens.CommaToken):
                self._debug(
                    'encountered a line terminator, comma, or }, break it out')
                if isinstance(token, tokens.LineTerminatorToken):
                    self._inc_line()
                break
            if (prev_token is None or
                isinstance(prev_token, tokens.OperatorToken)) and \
                    isinstance(token, tokens.SubtractionOperatorToken):
                # unary -
                token = tokens.NegationOperatorToken()
            if not isinstance(token, tokens.OperatorToken) and not \
                    isinstance(token, tokens.LiteralToken) and not \
                    isinstance(token, tokens.IdentifierToken):
                msg = "Expected an operator, literal, or identifier. (Got %s: %s)" % \
                    (token.__class__, token.body)
                logging.error(msg)
                raise exceptions.ParseError(self.line_num, msg)
            if isinstance(token, nodes.Node) or not \
                    isinstance(token, tokens.OperatorToken):
                # If anything is a node, append it
                if isinstance(self.next_token, tokens.LeftParenToken):
                    # function invocation or definition
                    if token.body == 'function':
                        output.append(self.handle_function_definition())
                    else:
                        output.append(self.handle_function_invocation(token))
                elif isinstance(self.next_token,
                                tokens.LeftSquareBraceToken):
                    # subscript syntax
                    output.append(self.handle_subscript_notation(token))
                else:
                    output.append(token)
            else:
                while len(op_stack) > 0:
                    token2 = op_stack[-1]

                    is_left_associative = \
                        token.associativity == tokens.OperatorToken.LEFT
                    is_right_associative = \
                        token.associativity == tokens.OperatorToken.RIGHT
                    self._debug("Is Left Associative: %s\t"
                                  "Is Right Associative: %s",
                                  is_left_associative, is_right_associative)
                    if (is_left_associative and token.precedence >= token2.precedence) or \
                            (is_right_associative and
                                token.precedence > token2.precedence):
                        if not isinstance(token, tokens.RightParenToken):
                            if not isinstance(token2,
                                              tokens.LeftParenToken):
                                op_token = op_stack.pop()
                                self._debug(
                                    "Popping %s off stack", op_token.body)
                                output.append(op_token)
                            else:
                                # break because we hit a left paren
                                break
                        else:
                            if not isinstance(token2,
                                              tokens.LeftParenToken):
                                op_token = op_stack.pop()
                                output.append(op_token)
                            else:
                                # discard left paren and break
                                op_stack.pop()
                                break
                    else:
                        # left operator is equal or larger than right. breakin
                        break
                if not isinstance(token, tokens.RightParenToken):
                    # push current operator to stack
                    op_stack.append(token)
                # ignore right paren
            # hold onto this for the next run in case we need to
            # check for unary operators
            prev_token = token

        self._debug('Done feeding in tokens, now drain the operator stack')

        # drain the operator stack
        while len(op_stack) > 0:
            operator = op_stack.pop()
            output.append(operator)

        self._debug('Output: ')
        self._debug(output)

        if len(output) == 0:
            # nothing. probably a \n after a ,
            return None

        tree_stack = []
        # turn the list of output tokens into a tree branch
        self._debug('Turn list of output tokens into a tree branch')
        while True:
            try:
                token = output.pop(0)
                self._debug("Consider %s from output" % token)
            except IndexError:
                break
            if not isinstance(token, tokens.OperatorToken):
                tree_stack.append(self.handle_token(token))
            else:
                self._debug("Tree stack: %s", tree_stack)
                self._debug("Determining if %s is unary or binary", token)
                if isinstance(token, tokens.BinaryOperatorToken):
                    self._debug("%s is binary", token)
                    try:
                        right, left = tree_stack.pop(), tree_stack.pop()
                    except IndexError:
                        logging.error("Encountered IndexError. Tree stack: %s",
                                      tree_stack)
                        raise exceptions.ParseError(self.line_num)
                    tree_stack.append(token.get_node(self.line_num, left, right))
                elif isinstance(token, tokens.UnaryOperatorToken):
                    self._debug("%s is unary", token)
                    target = tree_stack.pop()
                    tree_stack.append(token.get_node(self.line_num, target))
        self._debug("%s" % tree_stack)
        if len(tree_stack) != 1:
            logging.error("Tree stack length is not 1. Contents: %s",
                          tree_stack)
        if len(tree_stack) != 1:
            raise exceptions.ParseError(self.line_num)

        self._debug('The final tree leaf: %s', tree_stack[0])
        return tree_stack.pop()  # -----------===============#################*

    def handle_token(self, token):
        self._debug("handle token")
        if isinstance(token, nodes.Node) or isinstance(token, nodes.ListNode) or \
                isinstance(token, nodes.DictionaryNode):
            # already resolved down the chain
            self._debug("This token is actually a node, so return it")
            return token
        elif isinstance(token, tokens.IdentifierToken):
            # variable?
            if token.body == 'true':
                return nodes.BooleanNode(self.line_num, True)
            elif token.body == 'false':
                return nodes.BooleanNode(self.line_num, False)
            self._debug("Deciding that %s is a variable" % token)
            return nodes.VariableNode(self.line_num, token.body)
        elif isinstance(token, tokens.NumberLiteralToken):
            return nodes.NumberNode(self.line_num, token.body)
        elif isinstance(token, tokens.StringLiteralToken):
            return nodes.StringNode(self.line_num, token.body)
        assert "Unexpected token: %s (%s)" % (token, token.__class__)

    def handle_expression(self):
        while True:
            try:
                self._debug('Handling expression')
                token = self.next_token
                self._debug("Consider %s", token.__class__)
            except IndexError:
                # didn't shift the token off yet so make sure the line num is accurate
                raise exceptions.OutOfTokens(self.line_num + 1, 'During handle expression')
            if isinstance(token, tokens.IdentifierToken) or \
                    isinstance(token, tokens.LiteralToken):
                if self.handler_exists(token):
                    return self.handle_identifier()
                else:
                    return self.handle_operator_expression()
            elif isinstance(token, tokens.LineTerminatorToken):
                self._debug("Delete this infernal line terminator")
                self._inc_line()
                self.shift_token()
                return nodes.NopNode(self.line_num)
            elif isinstance(token, tokens.RightCurlyBraceToken):
                self._debug("Found }, beat it")
                self.shift_token()
                raise exceptions.EndContextExecution(self.line_num)
            else:
                raise exceptions.ParseError(self.line_num)

    def handler_exists(self, token):
        self._debug("* Checking if there is a handler for %s" % token)
        method_name = 'handle_identifier_' + token.body
        return hasattr(self, method_name)

    def handle_identifier(self):
        token = self.shift_token()
        method_name = 'handle_identifier_' + token.body
        method = getattr(self, method_name)
        return method(token)

    def handle_identifier_if(self, token):
        self._debug("Handling IF")
        condition = self.handle_operator_expression()
        then_branch = nodes.Branch([])
        else_branch = nodes.Branch([])
        while not isinstance(self.next_token, tokens.IdentifierToken) or \
                self.next_token.body not in ['else', 'end']:
            self._debug("Checking next expression as part of THEN clause")
            try:
                then_branch.append(self.handle_expression())
            except exceptions.EndContextExecution:
                logging.error("There shouldn't be a } here "
                              "because we're in an if statement")
                raise exceptions.ParseError(self.line_num, "Unexpected }")
            except exceptions.OutOfTokens:
                raise exceptions.SaulRuntimeError(self.line_num,
                    "Unexpected end of file during if statement")

        if isinstance(self.next_token, tokens.IdentifierToken) and \
                self.next_token.body == 'else':
            self.shift_token()
            while not isinstance(self.next_token, tokens.IdentifierToken) or \
                    self.tokens[0:2] != ['end', 'if']:
                self._debug(
                    "Checking next expression as part of ELSE clause")
                try:
                    else_branch.append(self.handle_expression())
                except exceptions.EndContextExecution:
                    logging.error("There shouldn't be a } here "
                                  "because we're in an if statement")
                    raise exceptions.ParseError(self.line_num, "Unexpected }")
                except exceptions.OutOfTokens:
                    raise exceptions.SaulRuntimeError(self.line_num,
                        "Unexpected end of file during if statement")
        end_token = self.shift_token()
        if_token = self.shift_token()
        self._debug("Then: %s, Else: %s, End If: %s %s",
                      then_branch, else_branch, end_token.body, if_token.body)
        assert isinstance(end_token, tokens.IdentifierToken) and \
            end_token.body == 'end'
        assert isinstance(if_token, tokens.IdentifierToken) and \
            if_token.body == 'if'

        return nodes.IfNode(self.line_num, condition, then_branch, else_branch)

    def handle_identifier_true(self, token):
        self._debug("Encountered 'true'")
        assert token.value.lower() == 'true'
        return nodes.BooleanNode(self.line_num, True)

    def handle_identifier_false(self, token):
        self._debug("Encountered 'false'")
        assert token.value.lower() == 'false'
        return nodes.BooleanNode(self.line_num, False)

    def handle_identifier_return(self, token):
        self._debug("Handling return statement")
        return_node = self.handle_operator_expression()
        return nodes.ReturnNode(self.line_num, return_node)

    def handle_identifier_while(self, token):
        self._debug("Handling while loop")
        condition = self.handle_operator_expression()
        branch = nodes.Branch()
        try:
            while not isinstance(self.next_token, tokens.IdentifierToken) or \
                    self.next_token.body not in ['end']:
                try:
                    branch.append(self.handle_expression())
                except exceptions.EndContextExecution:
                    logging.error("There shouldn't be a } here "
                                  "because we're in a while statement")
                    raise exceptions.ParseError(self.line_num, "Unexpected }")
        except exceptions.OutOfTokens:
            raise exceptions.SaulRuntimeError(self.line_num, "end while expected")
        end_token = self.shift_token()
        while_token = self.shift_token()
        assert isinstance(end_token, tokens.IdentifierToken) and \
            end_token.body == 'end'
        assert isinstance(while_token, tokens.IdentifierToken) and \
            while_token.body == 'while'

        return nodes.WhileNode(self.line_num, condition, branch)

    def handle_identifier_for(self, token):
        self._debug("Handling for loop")

        token = self.shift_token()
        if not isinstance(token, tokens.IdentifierToken):
            raise exceptions.ParseError(self.line_num, "Expected a name, got %s" % token)
        var_name = token.body

        token = self.shift_token()
        if not isinstance(token, tokens.IdentifierToken) or \
                token.body != 'in':
            raise exceptions.ParseError(self.line_num, "Expected 'in', got %s" % token)

        iterable = self.handle_operator_expression()
        self._debug("The iterable is %s" % iterable)
        branch = nodes.Branch()
        try:
            while not isinstance(self.next_token, tokens.IdentifierToken) or \
                    self.next_token.body not in ['end']:
                self._debug("For Loop: Consider %s" % self.next_token)
                try:
                    branch.append(self.handle_expression())
                    self._debug(
                        "Just handled an expression."
                        "Branch looks like %s now" % branch)
                except exceptions.EndContextExecution:
                    logging.error("There shouldn't be a } here"
                                  "because we're in a for loop")
                    raise exceptions.ParseError(self.line_num, "Unexpected }")
        except exceptions.OutOfTokens:
            raise exceptions.SaulRuntimeError(self.line_num, "end for expected")
        end_token = self.shift_token()
        for_token = self.shift_token()
        self._debug("End token: %s, For token: %s" % (end_token, for_token))
        assert isinstance(end_token, tokens.IdentifierToken) and \
            end_token.body == 'end'
        assert isinstance(for_token, tokens.IdentifierToken) and \
            for_token.body == 'for'

        self._debug("Returning for loop node")
        return nodes.ForNode(self.line_num, var_name, iterable, branch)
