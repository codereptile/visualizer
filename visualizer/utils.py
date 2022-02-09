# TODO: make debug prints proper
def red_on_black_print(*args):
    print("\x1B[31;40m", end="")
    for i in args:
        print(i, end=" ")
    print("\x1B[0m")


def info_print(*args):
    print("\x1B[34;1m", end="")
    for i in args:
        print(i, end=" ")
    print("\x1B[0m")


def green_on_black_print(*args):
    print("\x1B[32;40m", end="")
    for i in args:
        print(i, end=" ")
    print("\x1B[0m")


def extra_print(*args):
    print("\x1B[34;40m", end="")
    for i in args:
        print(i, end=" ")
    print("\x1B[0m")


def no_print(*args):
    pass


def output_error(brute_force: bool, *args):
    if brute_force:
        red_on_black_print(*args)
    else:
        s = ''
        for i in args:
            s += str(i)
        raise RuntimeError(s)


def output_verbose(verbose: bool, *args):
    if verbose:
        info_print(*args)


class Scaler:
    def __init__(self, initial_scale: float = 1):
        self.current_scale = initial_scale
        self.MIN_SIZE = 0
        self.FUNCTIONS_ACCESS_SPECIFIER_BUFFER = 0
        self.BUFFER_SIZE_VERTICAL = 0
        self.BUFFER_SIZE_CLASS_VERTICAL = 0
        self.BUFFER_SIZE_HORIZONTAL = 0
        self.OBJECTS_BUFFER = 0
        self.LINE_WIDTH = 0
        # Higher would result in a more curved line:
        self.LINE_CURVATURE = 1 / 4
        self.rescale(initial_scale)

    def rescale(self, scale: float = 1):
        self.current_scale = scale
        # TODO: add profiles
        self.MIN_SIZE = max(int(50 * scale), 1)
        self.FUNCTIONS_ACCESS_SPECIFIER_BUFFER = int(10 * scale)
        self.BUFFER_SIZE_VERTICAL = int(20 * scale)
        self.BUFFER_SIZE_CLASS_VERTICAL = int(100 * scale)
        self.BUFFER_SIZE_HORIZONTAL = int(20 * scale)
        self.OBJECTS_BUFFER = int(400 * scale)
        self.LINE_WIDTH = max(int(10 * scale), 1)

        # kek_profile:
        # self.MIN_SIZE = max(int(100 * scale), 1)
        # self.FUNCTIONS_ACCESS_SPECIFIER_BUFFER = int(10 * scale)
        # self.BUFFER_SIZE_VERTICAL = 0
        # self.BUFFER_SIZE_HORIZONTAL = 0
        # self.OBJECTS_BUFFER = int(1000 * scale)
        # self.LINE_WIDTH = 1
