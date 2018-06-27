"""
C reference from https://www.gnu.org/software/gnu-c-manual/gnu-c-manual.html
"""
import enum
import re
from parser import *
import math


class Fraction:
    """
    Actually I use this to handle `int`
    """
    def __init__(self, numerator: int, denominator: int=1):
        if denominator == 0:
            raise ZeroDivisionError()
        if denominator < 0:
            numerator *= -1
            denominator *= -1
        gcd = math.gcd(numerator, denominator)
        self.numerator = numerator // gcd
        self.denominator = denominator // gcd

    @staticmethod
    def from_int(integer: int):
        return Fraction(integer, 1)

    def __eq__(self, other) -> bool:
        if isinstance(other, int):
            other = Fraction.from_int(other)
        elif not isinstance(other, Fraction):
            raise TypeError("Cannot compare type Fraction with type {}".format(type(other)))
        return other.denominator * self.numerator == other.numerator * self.denominator

    def __lt__(self, other):
        if isinstance(other, int):
            other = Fraction.from_int(other)
        elif not isinstance(other, Fraction):
            raise TypeError("Cannot compare type Fraction with type {}".format(type(other)))
        return other.denominator * self.numerator < other.numerator * self.denominator

    def __le__(self, other):
        if isinstance(other, int):
            other = Fraction.from_int(other)
        elif not isinstance(other, Fraction):
            raise TypeError("Cannot compare type Fraction with type {}".format(type(other)))
        return other.denominator * self.numerator <= other.numerator * self.denominator

    def __add__(self, other):
        if isinstance(other, int):
            other = Fraction.from_int(other)
        elif not isinstance(other, Fraction):
            raise TypeError("Cannot add type {} to type Fraction".format(type(other)))
        gcd = math.gcd(self.denominator, other.denominator)
        numerator = self.denominator // gcd * other.numerator + other.denominator // gcd * self.numerator
        denominator = self.denominator * other.denominator // gcd
        return Fraction(numerator, denominator)

    def __sub__(self, other):
        if isinstance(other, int):
            other = Fraction.from_int(other)
        elif not isinstance(other, Fraction):
            raise TypeError("Cannot sub {} from type Fraction".format(type(other)))
        gcd = math.gcd(self.denominator, other.denominator)
        numerator = other.denominator // gcd * self.numerator - self.denominator // gcd * other.numerator
        denominator = self.denominator * other.denominator // gcd
        return Fraction(numerator, denominator)

    def __mul__(self, other):
        if isinstance(other, int):
            other = Fraction.from_int(other)
        elif not isinstance(other, Fraction):
            raise TypeError("Cannot mul type Fraction with type {}".format(type(other)))
        numerator = other.numerator * self.numerator
        denominator = self.denominator * other.denominator
        return Fraction(numerator, denominator)

    def __truediv__(self, other):
        if isinstance(other, int):
            other = Fraction.from_int(other)
        elif not isinstance(other, Fraction):
            raise TypeError("Cannot div type Fraction by type {}".format(type(other)))
        numerator = other.denominator * self.numerator
        denominator = self.denominator * other.numerator
        return Fraction(numerator, denominator)

    def __repr__(self):
        return "Fraction(%d, %d)" % (self.numerator, self.denominator)

    def __str__(self):
        if self.denominator == 1:
            return str(self.numerator)
        return "(%s/%s)" % (self.numerator, self.denominator)

    def __float__(self):
        return self.numerator / self.denominator


IDENTIFIER_PATTERN = re.compile(r"^([a-zA-z_]([a-zA-z_0-9]*))")


class Identifier:
    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return self.name == other.name

    @staticmethod
    def parse_identifier(state):
        pos, string = state
        result = IDENTIFIER_PATTERN.match(string)
        if result is None:
            raise TokenError("Invalid identifier name", pos)
        name = result.group(0)  # matched part
        return Identifier(name), (pos+len(name), string[result.end():])


class Keywords(enum.Enum):
    AUTO = 0
    BREAK = 1
    CASE = 2
    CHAR = 3
    CONST = 4
    CONTINUE = 5
    DEFAULT = 6
    DO = 7
    DOUBLE = 8
    ELSE = 9
    ENUM = 10
    EXTERN = 11
    FLOAT = 12
    FOR = 13
    GOTO = 14
    IF = 15
    INT = 16
    LONG = 17
    REGISTER = 18
    RETURN = 19
    SHORT = 20
    SIGNED = 21
    SIZEOF = 22
    STATIC = 23
    STRUCT = 24
    SWITCH = 25
    TYPEDEF = 26
    UNION = 27
    UNSIGNED = 28
    VOID = 29
    VOLATILE = 30
    WHILE = 31
    RESTRICT = 32

    @staticmethod
    def parse_keyword(state: (int, str)):
        pos, string = state
        rest = string[pos:]
        for one in Keywords:
            name = one.name.lower()
            if rest.startswith(name):  # matched
                return one, (pos + len(name), string)
        raise TokenError("Expected keyword here", pos)


class Constant:
    def __init__(self, value):
        self.value = value

    @staticmethod
    def parse(state: (int, str)):
        return None, state

    def __repr__(self):
        return "{}({})".format(type(self).__name__, self.value)

    def __str__(self):
        return self.__repr__()


class IntegerConstant(Constant):

    def __init__(self, value):
        super().__init__(Fraction(value))

    @staticmethod
    def parse(state: (int, str)):
        pos, string = state
        rest = string[pos:]
        if rest.startswith('0x'):  # hex number
            pos += 2
            rest = rest[2:]
            result = re.match('^([0-9a-fA-F]+)', rest)
            if result is None:
                raise TokenError("Expect hex literal here", pos)
            literal = result.group(0)
            return IntegerConstant(int(literal, 0x10)), (pos+len(literal), string)
        elif rest.startswith('0'):  # octal number
            pos += 1
            rest = rest[1:]
            result = re.match('^([0-7]+)', rest)
            if result is None:
                raise TokenError("Expect octal literal here", pos)
            literal = result.group(0)
            return IntegerConstant(int(literal, 0o10)), (pos + len(literal), string)
        else:  # decimal
            # result = re.match('^([1-9][0-9]*)', string)
            # they should be the same
            result = re.match('^([0-9]+)', string)
            if result is None:
                raise TokenError("Expect decimal literal here", pos)
            literal = result.group(0)
            return IntegerConstant(int(literal, 10)), (pos + len(literal), string)


class CharConstant(Constant):
    @staticmethod
    def parse(state: (int, str)):
        _, state = parse_char("'")(state)
        pos, string = state
        if string[pos] == '\\':  # transferred character
            pos += 1  # backslash
            char = {
                '\\': b'\\',
                '?': b'?',
                '\'': b'\'',
                '"': b'"',
                'a': b'\a',
                'b': b'\b',
                'f': b'\f',
                'n': b'\n',
                'r': b'\r',
                't': b'\t',
                'v': b'\v',
            }.get(string[pos], None)
            if char is not None:  # exactly one character
                pos += 1
            else:  # hex or octal
                if string[pos] == 'x':  # hex number
                    pos += 1  # x
                    char = bytes.fromhex(string[pos:pos+2])
                    pos += 2  # hh
                else:  # octal number
                    result = re.match('^([0-7]{1,3})', string[pos:pos+3])
                    if result is None:
                        raise TokenError("Expect octal literal", pos)
                    literal = result.group(0)
                    value = int(literal, 0o10)
                    char = chr(value).encode('ascii')
                    pos += len(literal)
        else:
            char = string[pos].encode('ascii')
            pos += 1

        _, state = parse_char("'")((pos, string))
        return CharConstant(char), state


class StringConstant(Constant):
    @staticmethod
    def parse(state: (int, str)):
        _, state = parse_char('"')(state)
        pos, string = state
        target = ""
        # I'm missing pointer here.
        while pos < len(string):
            ch = string[pos]
            # end flag
            if ch == '"':
                break

            if ch == '\\':  # transfer
                pos += 1  # backslash
                char = {
                    '\\': '\\',
                    '?': '?',
                    '\'': '\'',
                    '"': '"',
                    'a': '\a',
                    'b': '\b',
                    'f': '\f',
                    'n': '\n',
                    'r': '\r',
                    't': '\t',
                    'v': '\v',
                }.get(string[pos], None)
                if char is not None:  # exactly one character
                    pos += 1
                else:  # hex or octal
                    if string[pos] == 'x':  # hex number
                        pos += 1  # x
                        target += chr(int(string[pos:pos+2], 16))
                        pos += 2  # hh
                    else:  # octal number
                        result = re.match('^([0-7]{1,3})', string[pos:pos+3])
                        if result is None:
                            raise TokenError("Expect octal literal", pos)
                        literal = result.group(0)
                        value = int(literal, 0o10)
                        target += chr(value)
                        pos += len(literal)
            else:  # normal character
                target += ch
                pos += 1  # move to next character

        _, state = parse_char('"')((pos, string))
        return StringConstant(target), state
