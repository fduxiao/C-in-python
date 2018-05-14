from io import BytesIO
from functools import wraps


def unavailable(err_type, *args, **kwargs):
    raise err_type(*args, **kwargs)


def instruction(func):
    @wraps(func)
    def instruction_constructor(self, *args, **kwargs):
        # here self, *args, **kwargs will be passed to func
        return lambda: func(self, *args, **kwargs)
    return instruction_constructor


class VirtualMachine:

    def __init__(self, memory_size=10000, input_stream=None, output_stream=None):
        self.memory = [
                          lambda: unavailable(TypeError, 'Empty')
                      ] * memory_size  # which will invoke error when called
        self.CS = 0

        self.DS = len(self.memory)
        self.memory += [0] * memory_size  # add data segment

        self.SS = len(self.memory)
        self.memory += [0] * memory_size  # add stack
        # point stack pointer to stack end
        self.SP = len(self.memory)
        self.BP = len(self.memory) - 1

        self.IP = self.CS
        self.AX = 0
        self.BX = 0
        self.CX = 0
        self.DX = 0
        # Flags
        self.ZERO = 0
        self.NEG = 0

        if input_stream is None:
            self.input_stream = BytesIO()
        else:
            self.input_stream = input_stream

        if output_stream is None:
            self.output_stream = BytesIO()
        else:
            self.output_stream = output_stream

    def add_instruction(self, inst):
        self.memory[self.IP] = inst
        self.IP += 1

    def next(self):
        inst: callable = self.memory[self.IP]  # read instruction
        self.IP += 1  # move to next
        return inst()

    def read_address(self, target, address_only=False):
        if target in ['AX', 'BX', 'CX', 'DX', 'SP', 'BP']:  # AX
            if address_only:
                raise TypeError('NO ADDRESS')
            return getattr(self, target)
        elif target.startswith('[') and target.endswith(']'):  # memory
            address = target[1:-1]
            for register in ['AX', 'BX', 'CX', 'DX', 'SP', 'BP']:
                if address.startswith(register):
                    if '+' in address:
                        offset = int(address.split('+')[1])
                    elif '-' in address:
                        offset = -int(address.split('-')[1])
                    else:
                        offset = 0
                    address = getattr(self, register) + offset
                    break
            else:
                address = int(address)
            if address_only:
                return address
            return self.memory[address]
        else:  # immediate number
            if address_only:
                raise TypeError('NO ADDRESS')
            if '.' in target:
                return float(target)
            return int(target)

    def write_address(self, target, value):
        if target in ['AX', 'BX', 'CX', 'DX', 'SP', 'BP']:  # AX
            setattr(self, target, value)
        elif target.startswith('[') and target.endswith(']'):  # memory
            address = target[1:-1]
            for register in ['AX', 'BX', 'CX', 'DX', 'SP', 'BP']:
                if address.startswith(register):
                    if '+' in address:
                        offset = int(address.split('+')[1])
                    elif '-' in address:
                        offset = -int(address.split('-')[1])
                    else:
                        offset = 0
                    address = getattr(self, register) + offset
                    break
            else:
                address = int(address)
            self.memory[address] = value
        else:
            raise TypeError("Unknown type: %s" % target)

    # memory operations
    @instruction
    def move(self, destination, source):
        # parse origin
        source = self.read_address(source)
        self.write_address(destination, source)

    @instruction
    def lea(self, destination, variable):
        variable = self.read_address(variable, address_only=True)
        self.write_address(destination, variable)

    @instruction
    def push(self, target):
        self.SP -= 1
        if self.SP == self.SS:
            raise MemoryError('Insufficient stack space')
        target = self.read_address(target)
        self.memory[self.SP] = target

    @instruction
    def pop(self, writable):
        value = self.memory[self.SP]
        self.SP += 1
        if writable is not None:  # for inner calling
            self.write_address(writable, value)
        return value

    # IO operations
    @instruction
    def input(self, writable):
        value = self.input_stream.read(1)
        value = ord(value)  # write ascii code
        self.write_address(writable, value)

    @instruction
    def output(self, readable):
        value = self.read_address(readable)
        self.output_stream.write(chr(value))

    # arithmetic operations
    def set_flags(self, value):
        if value == 0:
            self.ZERO = 1
        if value < 0:
            self.NEG = 1

    @instruction
    def add(self, x, y):
        value1 = self.read_address(x)
        value2 = self.read_address(y)
        total = value1 + value2
        self.set_flags(total)
        self.write_address(x, total)
        return total

    @instruction
    def cmp(self, x, y):
        value1 = self.read_address(x)
        value2 = self.read_address(y)
        diff = value1 - value2
        self.set_flags(diff)
        return diff

    @instruction
    def sub(self, x, y):
        diff = self.cmp(x, y)
        self.write_address(x, diff)
        return diff

    @instruction
    def mul(self, x, y):
        value1 = self.read_address(x)
        value2 = self.read_address(y)
        prod = value1 * value2
        self.set_flags(prod)
        self.write_address(x, prod)

    @instruction
    def div(self, x, y):
        value1 = self.read_address(x)
        value2 = self.read_address(y)
        quot = value1 // value2
        self.set_flags(quot)
        self.write_address(x, quot)

    @instruction
    def fdiv(self, x, y):
        value1 = self.read_address(x)
        value2 = self.read_address(y)
        quot = value1 / value2
        self.set_flags(quot)
        self.write_address(x, quot)

    # bitwise operations
    @instruction
    def bit_not(self, x):
        value = self.read_address(x)
        result = ~value
        self.set_flags(result)
        self.write_address(x, result)

    @instruction
    def bit_test(self, x, y):
        value1 = self.read_address(x)
        value2 = self.read_address(y)
        result = value1 & value2
        self.set_flags(result)
        return result

    @instruction
    def bit_and(self, x, y):
        result = self.bit_test(x, y)
        self.write_address(x, result)

    @instruction
    def bit_or(self, x, y):
        value1 = self.read_address(x)
        value2 = self.read_address(y)
        result = value1 | value2
        self.set_flags(result)
        self.write_address(x, result)

    @instruction
    def bit_xor(self, x, y):
        value1 = self.read_address(x)
        value2 = self.read_address(y)
        result = value1 ^ value2
        self.set_flags(result)
        self.write_address(x, result)

    # jump operations
    @instruction
    def jmp(self, address):
        address = self.read_address(address)
        self.IP = address

    @instruction
    def je(self, address):
        address = self.read_address(address)
        if self.ZERO:
            self.IP = address

    jz = je

    @instruction
    def jne(self, address):
        address = self.read_address(address)
        if not self.ZERO:
            self.IP = address

    jnz = jne

    @instruction
    def jb(self, address):  # jump if below
        address = self.read_address(address)
        if not self.ZERO and self.NEG:  # result of CMP x, y
            self.IP = address

    @instruction
    def jnb(self, address):
        address = self.read_address(address)
        if self.ZERO or not self.NEG:
            self.IP = address

    @instruction
    def jbe(self, address):
        address = self.read_address(address)
        if self.ZERO or self.NEG:
            self.IP = address

    @instruction
    def ja(self, address):  # jump if above
        address = self.read_address(address)
        if not self.ZERO and not self.NEG:
            self.IP = address

    @instruction
    def jna(self, address):
        address = self.read_address(address)
        if self.ZERO or self.NEG:
            self.IP = address

    @instruction
    def jae(self, address):
        address = self.read_address(address)
        if self.ZERO or not self.NEG:
            self.IP = address

    @instruction
    def ret(self):
        address = self.pop(None)
        self.jmp(str(address))
