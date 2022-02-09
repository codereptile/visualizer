import sys

import clang.cindex
from .cpp_specific_functions import *
from .utils import *


class CodeTree:
    def __init__(self):
        # list of all independent objects
        self.roots = []

        # list of all objects
        self.nodes = []

        self.function_calls = []

        self.functions = {}
        self.classes = {}
        self.structures = {}
        self.methods = {}
        self.namespaces = {}


def parse_cursor(children_nodes, cursor: clang.cindex.Cursor, parent_node, bruteforce: bool, verbose: bool):
    if cursor.kind.name == 'COMPOUND_STMT':
        for i in cursor.get_children():
            parse_cursor(children_nodes, i, parent_node, bruteforce, verbose)
    elif cursor.kind.name == 'FOR_STMT':
        children_nodes.append(ForLoop(parent_node, cursor, bruteforce, verbose))
    elif cursor.kind.name == 'CXX_FOR_RANGE_STMT':
        children_nodes.append(ForRangeLoop(parent_node, cursor, bruteforce, verbose))
    elif cursor.kind.name == 'WHILE_STMT':
        children_nodes.append(WhileLoop(parent_node, cursor, bruteforce, verbose))
    elif cursor.kind.name == 'IF_STMT':
        children_nodes.append(If(parent_node, cursor, bruteforce, verbose))
    elif cursor.kind.name in ['BINARY_OPERATOR',
                              'CALL_EXPR',
                              'RETURN_STMT',
                              'DECL_STMT',
                              'UNARY_OPERATOR',
                              'UNEXPOSED_EXPR',
                              'CXX_DELETE_EXPR',
                              'BREAK_STMT',
                              'CXX_TRY_STMT',
                              'COMPOUND_ASSIGNMENT_OPERATOR',
                              'CXX_UNARY_EXPR',
                              'DECL_REF_EXPR',
                              'SWITCH_STMT',  # FIXME: parse switch statement
                              ]:
        if len(children_nodes) == 0 or type(children_nodes[-1]) != CodeBlock:
            children_nodes.append(CodeBlock(parent_node, bruteforce, verbose))
        children_nodes[-1].add_line(cursor, bruteforce, verbose)
    else:
        output_error(bruteforce, "Unknown object: ", cursor.kind.name, " located: ", cursor.location)


class Node:
    # FIXME: move construction away from constructor
    def __init__(self, parent_node):
        self.parent_node = parent_node
        self.root_node = self
        if self.parent_node is not None:
            self.root_node = self.parent_node.root_node


class CodeLine(Node):
    # FIXME: move construction away from constructor
    def __init__(self, parent_node, cursor: clang.cindex.Cursor, bruteforce: bool, verbose: bool):
        super().__init__(parent_node)
        self.cursor = cursor

    def print(self, depth):
        print('\t' * depth, self.cursor.kind)


class CodeBlock(Node):
    # FIXME: move construction away from constructor
    def __init__(self, parent_node, bruteforce: bool, verbose: bool):
        super().__init__(parent_node)
        self.body_nodes = []

    def add_line(self, cursor: clang.cindex.Cursor, bruteforce: bool, verbose: bool):
        self.body_nodes.append(CodeLine(self, cursor, bruteforce, verbose))

    def print(self, depth):
        print('\t' * depth, 'Block of code:')
        for i in self.body_nodes:
            i.print(depth + 1)


class Loop(Node):
    # FIXME: move construction away from constructor
    def __init__(self, parent_node, cursor: clang.cindex.Cursor, bruteforce: bool, verbose: bool):
        super().__init__(parent_node)
        self.body_nodes = []

    def print(self, depth):
        for i in self.body_nodes:
            i.print(depth + 1)


class ForLoop(Loop):
    # FIXME: move construction away from constructor
    def __init__(self, parent_node, cursor: clang.cindex.Cursor, bruteforce: bool, verbose: bool):
        super().__init__(parent_node, cursor, bruteforce, verbose)

        cursor_children = list(cursor.get_children())
        parse_cursor(self.body_nodes, cursor_children[-1], self, bruteforce, verbose)
        # FIXME: make a proper loop arguments parse

    def print(self, depth):
        print('\t' * depth, 'For loop:')
        super().print(depth)


class ForRangeLoop(Loop):
    # FIXME: move construction away from constructor
    def __init__(self, parent_node, cursor: clang.cindex.Cursor, bruteforce: bool, verbose: bool):
        super().__init__(parent_node, cursor, bruteforce, verbose)

        cursor_children = list(cursor.get_children())
        parse_cursor(self.body_nodes, cursor_children[-1], self, bruteforce, verbose)
        # FIXME: make a proper loop arguments parse

    def print(self, depth):
        print('\t' * depth, 'For range loop:')
        super().print(depth)


class WhileLoop(Loop):
    # FIXME: move construction away from constructor
    def __init__(self, parent_node, cursor: clang.cindex.Cursor, bruteforce: bool, verbose: bool):
        super().__init__(parent_node, cursor, bruteforce, verbose)

        cursor_children = list(cursor.get_children())
        parse_cursor(self.body_nodes, cursor_children[-1], self, bruteforce, verbose)
        # FIXME: make a proper loop arguments parse

    def print(self, depth):
        print('\t' * depth, 'While loop:')
        super().print(depth)


class If(Node):
    # FIXME: move construction away from constructor
    def __init__(self, parent_node, cursor: clang.cindex.Cursor, bruteforce: bool, verbose: bool):
        super().__init__(parent_node)

        self.body_nodes = []
        self.else_nodes = []

        cursor_children = list(cursor.get_children())

        # FIXME: parse condition

        for i in cursor_children[1].get_children():
            parse_cursor(self.body_nodes, i, self, bruteforce, verbose)
        if len(cursor_children) == 3:
            parse_cursor(self.else_nodes, cursor_children[2], self, bruteforce, verbose)

    def print(self, depth):
        print('\t' * depth, 'If:')
        for i in self.body_nodes:
            i.print(depth + 1)
        if len(self.else_nodes):
            print('\t' * depth, 'Else:')
            for i in self.else_nodes:
                i.print(depth + 1)


class Function(Node):
    # FIXME: move construction away from constructor
    def __init__(self, parent_node):
        super().__init__(parent_node)
        self.body_nodes = []
        self.name = ""

    def parse_cpp(self, cursor: clang.cindex.Cursor, bruteforce: bool, verbose: bool):
        self.name = cursor.spelling

        cursor_children = list(cursor.get_children())

        if len(cursor_children) and cursor_children[-1].kind.name == 'COMPOUND_STMT':
            parse_cursor(self.body_nodes, cursor_children[-1], self, bruteforce, verbose)
        # FIXME: parse function arguments
        # FIXME: parse function return
        # TODO: add print method


class Class(Node):
    def __init__(self, parent_node):
        super().__init__(parent_node)
        self.body_nodes = {}
        self.name = ""

    def parse_cpp(self, cursor: clang.cindex.Cursor, code_tree: CodeTree, bruteforce: bool, verbose: bool):
        self.name = cursor.spelling

        for i in cursor.get_children():
            if i.kind.name == 'FIELD_DECL':
                pass
                # TODO: parse field declarations
            elif i.kind.name == 'CONSTRUCTOR':
                pass
                # TODO: parse struct constructor
            elif i.kind.name == 'DESTRUCTOR':
                pass
                # TODO: parse struct destructor
            elif i.kind.name == 'CXX_METHOD':
                code_tree.methods[i.get_usr()] = Function(self)
                self.body_nodes[i.get_usr()] = code_tree.methods[i.get_usr()]
                code_tree.methods[i.get_usr()].parse_cpp(i, bruteforce, verbose)
            elif i.kind.name == 'CXX_ACCESS_SPEC_DECL':
                pass
                # nothing should be here, access specifiers are taken from methods themselves
            else:
                output_error(bruteforce, "Unknown class field: ", i.kind.name, " location: ", i.location)
        # TODO: add print method


class Struct(Node):
    def __init__(self, parent_node):
        super().__init__(parent_node)
        self.body_nodes = {}
        self.name = ""

    def parse_cpp(self, cursor: clang.cindex.Cursor, code_tree: CodeTree, bruteforce: bool, verbose: bool):
        self.name = cursor.spelling

        # cursor_dump_rec(cursor, 0, 2)

        for i in cursor.get_children():
            if i.kind.name == 'FIELD_DECL':
                pass
                # TODO: parse field declarations
            elif i.kind.name == 'CONSTRUCTOR':
                pass
                # TODO: parse struct constructor
            elif i.kind.name == 'CXX_METHOD':
                code_tree.methods[i.get_usr()] = Function(self)
                self.body_nodes[i.get_usr()] = code_tree.methods[i.get_usr()]
                code_tree.methods[i.get_usr()].parse_cpp(i, bruteforce, verbose)
            elif i.kind.name == 'CXX_BASE_SPECIFIER':
                pass
                # TODO: parse base specifier
            elif i.kind.name == 'USING_DECLARATION':
                pass
                # TODO: parse using declarations
            else:
                output_error(bruteforce, "Unknown structure field: ", i.kind.name, " location: ", i.location)

        # TODO: add print method


class FunctionCall:
    def __init__(self, source, target=None):
        self.source = source
        self.target = target
