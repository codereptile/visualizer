# This module uses various code parsers to grab data about the code,
# and compress it into a lightweight and standardized tree that is easy to visualize.
import random
from pprint import pprint

import arcade
import enum
import os.path
import sys
from .tree_objects import *
from .cpp_specific_functions import *


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
        # FIXME: make cross-file scan for function decl/def and similar

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


class NodeGraphicsInfo:
    def __init__(self, target):
        self.target = target

        self.pos_x = 0
        self.pos_y = 0

        self.size_x = 50
        self.size_y = 50


class Visualizer(arcade.Window):
    def __init__(self):
        super().__init__(int(arcade.get_screens()[0].width), int(arcade.get_screens()[0].height),
                         title="Codereptile visualizer", resizable=True, center_window=True, vsync=True)
        arcade.set_background_color((255, 255, 255))
        arcade.start_render()
        arcade.draw_text("LOADING", self.width // 2, self.height // 2, (0, 0, 0), self.width / 20, anchor_x="center",
                         anchor_y="center")
        arcade.finish_render()

        self.parser = Parser()
        self.graphics_info = {}

        self.scaler = Scaler(0.9)

        self.should_redraw = False
        self.a = False
        # FIXME: make this 'a' a proper thing
        # TODO: add side-by-side code comparison

    def set_graphics_info(self, node):
        self.graphics_info[node] = NodeGraphicsInfo(node)
        if type(node) != CodeLine:
            for i in node.body_nodes:
                self.set_graphics_info(i)
            # FIXME: probably this if type(node) == If thing should have a more elegant solution
            if type(node) == If:
                for i in node.else_nodes:
                    self.set_graphics_info(i)

    def parse(self, target: str, mode: ParseModes) -> None:
        self.parser.parse(target, mode)
        for i in self.parser.code_tree.functions:
            self.set_graphics_info(i)
        for i in self.parser.code_tree.classes:
            self.set_graphics_info(i)
        self.should_redraw = True

    def on_resize(self, width: float, height: float):
        for i in self.parser.code_tree.classes:
            self.compute_node_size(i, self.scaler)

        for i in self.parser.code_tree.functions:
            self.compute_node_size(i, self.scaler)

        offset_x = 100

        for i in self.parser.code_tree.classes:
            self.compute_node_position(i, self.scaler, offset_x, (self.height - self.graphics_info[i].size_y) // 2)
            offset_x += self.scaler.OBJECTS_BUFFER

        for i in self.parser.code_tree.functions:
            self.compute_node_position(i, self.scaler, offset_x, (self.height - self.graphics_info[i].size_y) // 2)
            offset_x += self.scaler.OBJECTS_BUFFER

        self.should_redraw = True

    def compute_node_size(self, node, scaler: Scaler) -> None:
        if type(node) == CodeLine or (self.a and type(node) == CodeBlock):
            self.graphics_info[node].size_x = scaler.MIN_SIZE
            self.graphics_info[node].size_y = scaler.MIN_SIZE
        else:
            self.graphics_info[node].size_x = 0
            self.graphics_info[node].size_y = 0 + scaler.BUFFER_SIZE_VERTICAL * (len(node.body_nodes) + 1)
            # calculate new size:
            for i in node.body_nodes:
                self.compute_node_size(i, scaler)
                self.graphics_info[node].size_y += self.graphics_info[i].size_y
                self.graphics_info[node].size_x = max(self.graphics_info[node].size_x,
                                                      self.graphics_info[i].size_x + scaler.BUFFER_SIZE_HORIZONTAL * 2)
            if type(node) == If:
                for i in node.else_nodes:
                    self.compute_node_size(i, scaler)
                    self.graphics_info[node].size_y += self.graphics_info[i].size_y
                    self.graphics_info[node].size_x = max(self.graphics_info[node].size_x, self.graphics_info[
                        i].size_x + scaler.BUFFER_SIZE_HORIZONTAL * 2)
            if type(node) == Function:
                self.graphics_info[node].size_y += scaler.FUNCTIONS_ACCESS_SPECIFIER_BUFFER

    def compute_node_position(self, node, scaler: Scaler, offset_x: int, offset_y: int) -> None:
        self.graphics_info[node].pos_x = offset_x
        self.graphics_info[node].pos_y = offset_y
        if type(node) != CodeLine:
            offset_y += self.graphics_info[node].size_y

            if type(node) == Function:
                offset_y -= scaler.FUNCTIONS_ACCESS_SPECIFIER_BUFFER

            offset_x += scaler.BUFFER_SIZE_HORIZONTAL
            for i in node.body_nodes:
                offset_y -= scaler.BUFFER_SIZE_VERTICAL
                offset_y -= self.graphics_info[i].size_y
                self.compute_node_position(i, scaler, offset_x, offset_y)
            if type(node) == If:
                for i in node.else_nodes:
                    offset_y -= scaler.BUFFER_SIZE_VERTICAL
                    offset_y -= self.graphics_info[i].size_y
                    self.compute_node_position(i, scaler, offset_x, offset_y)

    def on_draw(self):
        if self.should_redraw:
            arcade.start_render()

            for i in self.parser.code_tree.classes:
                self.recursive_node_draw(i)
            for i in self.parser.code_tree.functions:
                self.recursive_node_draw(i)

            arcade.finish_render()
            self.should_redraw = False

    def recursive_node_draw(self, node):
        color = (0, 50, 255)
        if type(node) == CodeLine:
            color = (0, 50, 255)
            if self.a:
                return
        elif type(node) == ForLoop or type(node) == ForRangeLoop or type(node) == WhileLoop:
            color = (255, 0, 0)
        elif type(node) == If:
            color = (0, 255, 0)
        elif type(node) == Function:
            color = (125, 125, 125)
        elif type(node) == CodeBlock:
            if not self.a:
                color = (0, 0, 0, 0)
        arcade.draw_rectangle_filled(self.graphics_info[node].pos_x + self.graphics_info[node].size_x / 2,
                                     self.graphics_info[node].pos_y + self.graphics_info[node].size_y / 2,
                                     self.graphics_info[node].size_x, self.graphics_info[node].size_y, color)
        if type(node) != CodeBlock:
            arcade.draw_rectangle_outline(self.graphics_info[node].pos_x + self.graphics_info[node].size_x / 2,
                                          self.graphics_info[node].pos_y + self.graphics_info[node].size_y / 2,
                                          self.graphics_info[node].size_x, self.graphics_info[node].size_y, (0, 0, 0))
        if type(node) != CodeLine:
            for i in node.body_nodes:
                self.recursive_node_draw(i)
            if type(node) == If:
                for i in node.else_nodes:
                    self.recursive_node_draw(i)

    def update(self, delta_time):
        pass
