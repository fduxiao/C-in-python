"""
monad style parser
"""
from functools import wraps


class TokenError(Exception):
    def __init__(self, desc, pos):
        super().__init__()
        self.desc = desc
        self.pos = pos

    def __repr__(self):
        return "TokenError %s: at %d" % (self.desc, self.pos)

    def __str__(self):
        return self.__repr__()

    @staticmethod
    def from_state(desc, state):
        pos, _ = state
        return TokenError(desc, pos)


def parse_item(state: (int, str)):
    pos, string = state
    if string[pos:] == '':
        raise TokenError("Unexpected EOF", pos)
    return string[pos], (pos+1, string)


def parse_sat(predict):
    @wraps(predict)
    def parser(state):
        item, state = parse_item(state)
        if predict(item):
            return item, state
        raise TokenError.from_state('Unexpected character `%s`' % item, state)
    return parser


def parse_char(char):
    return parse_sat(lambda x: char == x)


def parse_string(string):
    def parser(state: (int, str)):
        result = ''
        for char in string:
            char, state = parse_char(char)
            result += char
        return result, state
    parser.__name__ = "parse <{}>".format(string)
    return parser


def parse_many(parse_func):
    parse_one = parse_many1(parse_func)

    @wraps(parse_func)
    def parser(state: (int, str)):
        try:
            many, state = parse_one(state)
        except TokenError:
            return [], state
        else:
            return many, state
    return parser


def parse_many1(parse_func):
    parse_any = parse_many(parse_func)

    @wraps(parse_func)
    def parser(state: (int, str)):
        one, state = parse_func(state)
        many, state = parse_any(state)
        return [one] + many, state
    return parser


def is_space(char):
    return char in {' ', '\t', '\n', '\r'}


def parse_space():
    return parse_many(parse_sat(is_space))


def parse_token(parse_func):
    @wraps(parse_func)
    def parser(state):
        a, state = parse_func(state)
        parse_space()
        return a, state
    return parser


def parse_symbol(string):
    return parse_token(parse_string(string))
