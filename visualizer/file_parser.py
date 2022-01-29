# This module uses various code parsers to grab data about the code,
# and compress it into a lightweight and standardized tree that is easy to visualize.

# General imports:
import enum
from pprint import pprint

# C++ parsing:
import os.path
import sys

import clang.cindex


class ParseModes(enum.Enum):
    CPP, PYTHON = range(2)


class Node:
    def __init__(self, parent_node=None):
        self.parent_node = parent_node
        self.root_node = None
        if self.parent_node is not None:
            self.root_node = self.parent_node.root_node


class CodeBlock(Node):
    def __init__(self, parent_node=None):
        super().__init__(parent_node)


class Function(Node):
    def __init__(self, cursor: clang.cindex.Cursor, parent_node=None):
        super().__init__(parent_node)
        self.children_nodes = []

        print('Constructing function \'' + cursor.spelling + '\' from cursor:')
        for i in cursor.get_children():
            if i.kind.name == 'COMPOUND_STMT':
                print("Function body:")
                for j in i.get_children():
                    print('\t', j.kind)
            elif i.kind.name == 'PARM_DECL':
                pass
                # FIXME: parse function arguments
            else:
                raise RuntimeError('Unknown cursor child in function', i.kind)
        print()

class CodeTree:
    def __init__(self):
        self.functions = []
        self.classes = []
        self.methods = []
        self.namespaces = []


def is_file_in_standart(file: str) -> bool:
    triggers = [
        'gcc',
        'bits',
        'assert.h',
        'ctype.h',
        'errno.h',
        'locale.h',
        'math.h',
        'stddef.h',
        'stdlib.h',
        'setjmp.h',
        'signal.h',
        'stdarg.h',
        'stdarg.h',
        'stddef.h',
        '__stddef_max_align_t.h',
        '__stddef_max_align_t.h',
        'stdio.h',
        'stdint.h',
        'sched.h',
        'pthread.h',
        'string.h',
        'time.h',
        'time.h',
        'wchar.h',
        'wctype.h',
        'fenv.h',
        'inttypes.h',
        'uchar.h',
        'libintl.h',
    ]
    for i in triggers:
        if i in file:
            return True
    return False


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


# DEBUG FUNCTION
def cursor_dump(cursor):
    printer = info_print
    if is_file_in_standart(str(cursor.location.file)):
        printer = no_print
    # else:
    #     if '.h' in str(cursor.location.file):
    #         ans = ''
    #         for i in str(cursor.location.file)[::-1]:
    #             if i == '/':
    #                 break
    #             ans += i
    #         print('\'' + ans[::-1] + '\',')
    #     printer = no_print
    printer("kind:", cursor.kind)
    printer("\tspelling:", cursor.spelling)
    printer("\ttype:", cursor.type.spelling)
    printer("\taccess_specifier:", cursor.access_specifier)
    printer("\textent:", cursor.extent)
    printer("\tlocation:", cursor.location)
    printer("\tin file:", cursor.location.file)
    printer("\tusr:", cursor.get_usr())


def cursor_dump_rec(cursor, depth=0):
    info_print(depth * "\t",
               "kind:", cursor.kind,
               "\tspelling:", cursor.spelling,
               "\ttype:", cursor.type.spelling,
               "\taccess_specifier:", cursor.access_specifier,
               "\textent:", cursor.extent
               )
    for child in cursor.get_children():
        cursor_dump_rec(child, depth + 1)


class Parser:
    def __init__(self):
        self.target = None
        self.code_tree = CodeTree()

    def parse(self, target: str, mode: ParseModes) -> None:
        self.target = os.path.abspath(target)

        if mode == ParseModes.PYTHON:
            print('Python code parsing is not implemented yet')
            sys.exit(1)
        elif mode == ParseModes.CPP:
            self.parse_cpp()
        else:
            raise RuntimeError('Invalid mode given')

    def parse_cpp(self) -> None:
        if not os.path.isdir(self.target):
            print('Given target is not a directory')
            sys.exit(1)

        print("Processing DIR:\t", self.target)

        for root, subdirs, files in os.walk(self.target):
            for file_name in files:
                if file_name.endswith('.cpp'):
                    print("Found C++:\t\t", root + '/' + file_name)
                    self.parse_cpp_file(root + '/' + file_name)
                else:
                    print("Found Not C++:\t", root + '/' + file_name)

    def parse_cpp_file(self, file_path: str) -> None:
        index = clang.cindex.Index.create()
        translation_unit = index.parse(file_path, args=[])

        # FIXME: stop and print this if any diags:
        def get_diag_info(diag):
            return {'severity': diag.severity,
                    'location': diag.location,
                    'spelling': diag.spelling,
                    'ranges': diag.ranges,
                    'fixits': diag.fixits}

        pprint(('diags', [get_diag_info(d) for d in translation_unit.diagnostics]))

        for cursor in translation_unit.cursor.get_children():
            if not is_file_in_standart(str(cursor.location.file)):
                if cursor.kind.name == 'FUNCTION_DECL':
                    self.code_tree.functions.append(Function(cursor))
                elif cursor.kind.name == 'USING_DIRECTIVE':
                    print('LMAO, using!!')
                else:
                    cursor_dump(cursor)
                    raise NotImplementedError('Unknown cursor kind', cursor.kind)

            # cursor_dump(cursor)
