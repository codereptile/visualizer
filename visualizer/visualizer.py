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

        for i in self.code_tree.roots:
            self.detect_all_objects(i)

        for i in self.code_tree.nodes:
            self.detect_if_function(i)

        for i in self.code_tree.nodes:
            self.detect_if_function_call(i)

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
                    self.code_tree.roots.append(Function(None, cursor))
                else:
                    cursor_dump(cursor)
                    print("Warning,", cursor.kind.name, "not supported!!")

            # cursor_dump(cursor)

    def detect_all_objects(self, node):
        self.code_tree.nodes.append(node)
        if type(node) != CodeLine:
            for i in node.body_nodes:
                self.detect_all_objects(i)
            if type(node) == If:
                for i in node.else_nodes:
                    self.detect_all_objects(i)

    # Detects if a node is a function, and if so, adds it to the function dict
    def detect_if_function(self, node):
        if type(node) == Function:
            self.code_tree.functions[node.name] = node

    def detect_if_function_call(self, node):
        # FIXME: make more detailed, recursive check (done, but need to check If statements)
        # TODO: somehow show how many times a function is called in a line
        if type(node) == CodeLine:
            self.check_cursor_for_function_calls(node, node.cursor)

    def check_cursor_for_function_calls(self, node, cursor):
        if cursor.kind.name == 'CALL_EXPR':
            self.code_tree.function_calls.append(
                FunctionCall(node, self.code_tree.functions.get(cursor.spelling)))
        for child in cursor.get_children():
            self.check_cursor_for_function_calls(node, child)


class NodeGraphicsInfo:
    def __init__(self, target):
        self.target = target

        # left lower corner
        self.pos_x = 0
        self.pos_y = 0

        self.size_x = 50
        self.size_y = 50


class FunctionCallGraphicsInfo:
    def __init__(self, function_call):
        self.function_call = function_call

        self.start_pos_x = -1
        self.start_pos_y = -1
        self.end_pos_x = -1
        self.end_pos_y = -1


class Visualizer(arcade.Window):
    def __init__(self, scale: float):
        super().__init__(int(arcade.get_screens()[0].width), int(arcade.get_screens()[0].height),
                         title="Codereptile visualizer", resizable=True, center_window=True, vsync=True)
        arcade.set_background_color((255, 255, 255))
        arcade.start_render()
        arcade.draw_text("LOADING", self.width // 2, self.height // 2, (0, 0, 0), self.width / 20, anchor_x="center",
                         anchor_y="center")
        arcade.finish_render()

        self.parser = Parser()
        self.graphics_info = {}

        self.scaler = Scaler(scale)

        self.should_redraw = False
        self.a = False
        # FIXME: make this 'a' a proper thing (it's used for showing blocks)
        # TODO: add side-by-side code comparison

    def set_graphics_info(self, node):
        if type(node) == FunctionCall:
            self.graphics_info[node] = FunctionCallGraphicsInfo(node)
            return
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
        # FIXME: make one loop instead of two to reduce code duplicates
        for i in self.parser.code_tree.roots:
            self.set_graphics_info(i)
        for i in self.parser.code_tree.function_calls:
            self.set_graphics_info(i)
        self.should_redraw = True

    def on_resize(self, width: float, height: float):
        for i in self.parser.code_tree.roots:
            self.compute_node_size(i, self.scaler)

        offset_x = 100

        for i in self.parser.code_tree.roots:
            self.compute_node_position(i, self.scaler, offset_x, (self.height - self.graphics_info[i].size_y) // 2)
            offset_x += self.scaler.OBJECTS_BUFFER

        for i in self.parser.code_tree.function_calls:
            self.compute_function_call_graphics_info(i)

        self.should_redraw = True

    def compute_function_call_graphics_info(self, node):
        if node.target is not None:
            self.graphics_info[node].start_pos_x = self.graphics_info[node.source].pos_x + self.graphics_info[
                node.source].size_x / 2
            self.graphics_info[node].start_pos_y = self.graphics_info[node.source].pos_y + self.graphics_info[
                node.source].size_y / 2
            self.graphics_info[node].end_pos_x = self.graphics_info[node.target].pos_x + self.graphics_info[
                node.target].size_x / 2
            self.graphics_info[node].end_pos_y = self.graphics_info[node.target].pos_y + self.graphics_info[
                node.target].size_y

    def compute_node_size(self, node, scaler: Scaler) -> None:
        if type(node) == CodeLine:
            self.graphics_info[node].size_x = scaler.MIN_SIZE
            self.graphics_info[node].size_y = scaler.MIN_SIZE
        elif type(node) == CodeBlock:
            self.graphics_info[node].size_x = 0
            self.graphics_info[node].size_y = 0 + scaler.BUFFER_SIZE_VERTICAL * (len(node.body_nodes) + 1)
            # calculate new size:
            for i in node.body_nodes:
                self.compute_node_size(i, scaler)
                self.graphics_info[node].size_y += self.graphics_info[i].size_y
                self.graphics_info[node].size_x = max(self.graphics_info[node].size_x,
                                                      self.graphics_info[i].size_x + scaler.BUFFER_SIZE_HORIZONTAL * 2)
        elif type(node) == ForLoop or type(node) == ForRangeLoop or type(node) == WhileLoop:
            self.graphics_info[node].size_x = 0
            self.graphics_info[node].size_y = 0 + scaler.BUFFER_SIZE_VERTICAL * (len(node.body_nodes) + 1)
            # calculate new size:
            for i in node.body_nodes:
                self.compute_node_size(i, scaler)
                self.graphics_info[node].size_y += self.graphics_info[i].size_y
                self.graphics_info[node].size_x = max(self.graphics_info[node].size_x,
                                                      self.graphics_info[i].size_x + scaler.BUFFER_SIZE_HORIZONTAL * 2)
        elif type(node) == If:
            self.graphics_info[node].size_x = 0
            self.graphics_info[node].size_y = 0 + scaler.BUFFER_SIZE_VERTICAL * (
                    len(node.body_nodes) + len(node.else_nodes) + 1)
            # calculate new size:
            for i in node.body_nodes:
                self.compute_node_size(i, scaler)
                self.graphics_info[node].size_y += self.graphics_info[i].size_y
                self.graphics_info[node].size_x = max(self.graphics_info[node].size_x,
                                                      self.graphics_info[i].size_x + scaler.BUFFER_SIZE_HORIZONTAL * 2)
            for i in node.else_nodes:
                self.compute_node_size(i, scaler)
                self.graphics_info[node].size_y += self.graphics_info[i].size_y
                self.graphics_info[node].size_x = max(self.graphics_info[node].size_x,
                                                      self.graphics_info[i].size_x + scaler.BUFFER_SIZE_HORIZONTAL * 2)
        elif type(node) == Function:
            self.graphics_info[node].size_x = 0
            self.graphics_info[node].size_y = 0 + scaler.BUFFER_SIZE_VERTICAL * (len(node.body_nodes) + 1)
            # calculate new size:
            for i in node.body_nodes:
                self.compute_node_size(i, scaler)
                self.graphics_info[node].size_y += self.graphics_info[i].size_y
                self.graphics_info[node].size_x = max(self.graphics_info[node].size_x,
                                                      self.graphics_info[i].size_x + scaler.BUFFER_SIZE_HORIZONTAL * 2)
            if type(node) == Function:
                self.graphics_info[node].size_y += scaler.FUNCTIONS_ACCESS_SPECIFIER_BUFFER
        else:
            raise RuntimeError("unknown type")

    def compute_node_position(self, node, scaler: Scaler, offset_x: int, offset_y: int) -> None:
        self.graphics_info[node].pos_x = offset_x
        self.graphics_info[node].pos_y = offset_y

        if type(node) == CodeLine:
            pass
        elif type(node) == CodeBlock:
            offset_y += self.graphics_info[node].size_y
            offset_x += scaler.BUFFER_SIZE_HORIZONTAL
            for i in node.body_nodes:
                offset_y -= scaler.BUFFER_SIZE_VERTICAL
                offset_y -= self.graphics_info[i].size_y
                self.compute_node_position(i, scaler, offset_x, offset_y)
        elif type(node) == ForLoop or type(node) == ForRangeLoop or type(node) == WhileLoop:
            offset_y += self.graphics_info[node].size_y
            offset_x += scaler.BUFFER_SIZE_HORIZONTAL
            for i in node.body_nodes:
                offset_y -= scaler.BUFFER_SIZE_VERTICAL
                offset_y -= self.graphics_info[i].size_y
                self.compute_node_position(i, scaler, offset_x, offset_y)
        elif type(node) == If:
            offset_y += self.graphics_info[node].size_y
            offset_x += scaler.BUFFER_SIZE_HORIZONTAL
            for i in node.body_nodes:
                offset_y -= scaler.BUFFER_SIZE_VERTICAL
                offset_y -= self.graphics_info[i].size_y
                self.compute_node_position(i, scaler, offset_x, offset_y)
            for i in node.else_nodes:
                offset_y -= scaler.BUFFER_SIZE_VERTICAL
                offset_y -= self.graphics_info[i].size_y
                self.compute_node_position(i, scaler, offset_x, offset_y)
        elif type(node) == Function:
            offset_y += self.graphics_info[node].size_y
            offset_y -= scaler.FUNCTIONS_ACCESS_SPECIFIER_BUFFER
            offset_x += scaler.BUFFER_SIZE_HORIZONTAL
            for i in node.body_nodes:
                offset_y -= scaler.BUFFER_SIZE_VERTICAL
                offset_y -= self.graphics_info[i].size_y
                self.compute_node_position(i, scaler, offset_x, offset_y)
        else:
            raise RuntimeError("unknown type")

    def on_draw(self):
        if self.should_redraw:
            arcade.start_render()

            for i in self.parser.code_tree.roots:
                self.recursive_node_draw(i)
            for i in self.parser.code_tree.function_calls:
                self.function_call_draw(i)

            arcade.finish_render()
            self.should_redraw = False

    def function_call_draw(self, node):
        if node.target != None:
            def quadBezier(t, p0, p1, p2):
                return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2

            t = 0
            num_segments = 100
            block = 1 / num_segments

            prev_point_x = self.graphics_info[node].start_pos_x
            prev_point_y = self.graphics_info[node].start_pos_y

            while t < 1.001:
                v = [self.graphics_info[node].end_pos_x - self.graphics_info[node].start_pos_x,
                     self.graphics_info[node].end_pos_y - self.graphics_info[node].start_pos_y]
                perp_v = [v[1], -v[0]]
                x = quadBezier(t, self.graphics_info[node].start_pos_x,
                               (self.graphics_info[node].start_pos_x + self.graphics_info[node].end_pos_x) // 2 +
                               perp_v[0] * self.scaler.LINE_CURVATURE,
                               self.graphics_info[node].end_pos_x)
                y = quadBezier(t, self.graphics_info[node].start_pos_y,
                               (self.graphics_info[node].start_pos_y + self.graphics_info[node].end_pos_y) // 2 +
                               perp_v[0] * self.scaler.LINE_CURVATURE,
                               self.graphics_info[node].end_pos_y)
                arcade.draw_line(prev_point_x, prev_point_y,
                                 x, y,
                                 (0, 0, 0), self.scaler.LINE_WIDTH)
                prev_point_x = x
                prev_point_y = y
                t += block

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
        # FIXME: use draw_xywh_rectangle_filled
        arcade.draw_rectangle_filled(self.graphics_info[node].pos_x + self.graphics_info[node].size_x / 2,
                                     self.graphics_info[node].pos_y + self.graphics_info[node].size_y / 2,
                                     self.graphics_info[node].size_x, self.graphics_info[node].size_y, color)
        if type(node) != CodeBlock:
            arcade.draw_rectangle_outline(self.graphics_info[node].pos_x + self.graphics_info[node].size_x / 2,
                                          self.graphics_info[node].pos_y + self.graphics_info[node].size_y / 2,
                                          self.graphics_info[node].size_x, self.graphics_info[node].size_y, (0, 0, 0))
        if type(node) != CodeLine:
            offset_y = 0
            for i in node.body_nodes:
                self.recursive_node_draw(i)
                offset_y += self.graphics_info[i].size_y + self.scaler.BUFFER_SIZE_VERTICAL
            if type(node) == If and node.else_nodes:
                arcade.draw_line(self.graphics_info[node].pos_x,
                                 self.graphics_info[node].pos_y + self.graphics_info[node].size_y - offset_y,
                                 self.graphics_info[node].pos_x + self.graphics_info[node].size_x,
                                 self.graphics_info[node].pos_y + self.graphics_info[node].size_y - offset_y,
                                 (0, 0, 0), self.scaler.LINE_WIDTH)
                for i in node.else_nodes:
                    self.recursive_node_draw(i)

    def update(self, delta_time):
        pass
