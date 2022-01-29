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
