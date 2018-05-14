from vmachine import VirtualMachine
import sys


def main():
    vm = VirtualMachine()
    vm.input_stream = sys.stdin.buffer
    vm.output_stream = sys.stdout
    vm.add_instruction(vm.input('AX'))
    vm.add_instruction(vm.output('AX'))

    vm.IP = 0
    vm.next()
    print('--------------AX: %d----------------' % vm.AX)
    vm.next()


if __name__ == '__main__':
    main()
