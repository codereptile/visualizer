def error_print(*args):
    print("\x1B[31;40m", end="")
    for i in args:
        print(i, end=" ")
    print("\x1B[0m")


def info_print(*args):
    print("\x1B[32;40m", end="")
    for i in args:
        print(i, end=" ")
    print("\x1B[0m")


def no_print(*args):
    pass


class Scaler:
    def __init__(self, initial_scale: float = 1):
        self.MIN_SIZE = 0
        self.FUNCTIONS_ACCESS_SPECIFIER_BUFFER = 0
        self.BUFFER_SIZE_VERTICAL = 0
        self.BUFFER_SIZE_HORIZONTAL = 0
        self.OBJECTS_BUFFER = 0
        self.LINE_WIDTH = 0
        self.rescale(initial_scale)

    def rescale(self, scale: float = 1):
        self.MIN_SIZE = int(50 * scale)
        self.FUNCTIONS_ACCESS_SPECIFIER_BUFFER = int(10 * scale)
        self.BUFFER_SIZE_VERTICAL = int(20 * scale)
        self.BUFFER_SIZE_HORIZONTAL = int(20 * scale)
        self.OBJECTS_BUFFER = int(300 * scale)
        self.LINE_WIDTH = int(10 * scale)
