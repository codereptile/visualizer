# This module uses various code parsers to grab data about the code,
# and compress it into a lightweight and standardized tree that is easy to visualize.

import enum
import os.path
import sys
from .tree_objects import *


class ParseModes(enum.Enum):
    CPP, PYTHON = range(2)


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
            # FIXME: you kinda forgot that this code should have THE SAME TREE!!!
            #  (make parsing outside of class constructors)
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

        diagnostics = list(translation_unit.diagnostics)
        if len(diagnostics):
            error_print('FOUND ERRORS:')
            for diag in diagnostics:
                error_print('Error:')
                error_print('\tseverity:', diag.severity)
                error_print('\tlocation:', diag.location)
                error_print('\tspelling:', diag.spelling)
                error_print('\tranges:', diag.ranges)
                error_print('\tfixits:', diag.fixits)
            sys.exit(2)

        for cursor in translation_unit.cursor.get_children():
            if not is_file_in_standart(str(cursor.location.file)):
                if cursor.kind.name == 'FUNCTION_DECL':
                    self.code_tree.functions.append(Function(None, cursor))
                elif cursor.kind.name == 'USING_DIRECTIVE':
                    print('LMAO, using!!')
                    # FIXME: this should 100% be different =)
                else:
                    cursor_dump(cursor)
                    raise NotImplementedError('Unknown cursor kind', cursor.kind)

            # cursor_dump(cursor)
