# This module uses various code parsers to grab data about the code,
# and compress it into a lightweight and standardized tree that is easy to visualize.
import random
from pprint import pprint
import sys

import arcade
import enum
import os.path
import time

import clang.cindex

from .tree_objects import *
from .cpp_specific_functions import *


class ParseModes(enum.Enum):
    CPP, PYTHON = range(2)


class Parser:
    def __init__(self):
        self.target = None
        self.code_tree = CodeTree()
        # If True, attempts to ignore all errors and visualize as much as possible
        self.bruteforce = False
        self.verbose = False

    def parse(self, target: str, mode: ParseModes, bruteforce: bool, verbose: bool) -> None:
        self.bruteforce = bruteforce
        self.verbose = verbose

        self.target = os.path.abspath(target)

        if mode == ParseModes.PYTHON:
            red_on_black_print('Python code parsing is not implemented yet')
            sys.exit(1)
        elif mode == ParseModes.CPP:
            self.parse_cpp()
        else:
            # FIXME: you kinda forgot that this code should have THE SAME TREE!!!
            #  (make parsing outside of class constructors)
            raise RuntimeError('Invalid mode given')

        output_verbose(self.verbose, "-------------------------------")
        for i in self.code_tree.functions:
            if len(self.code_tree.functions[i].body_nodes) > 0:
                output_verbose(self.verbose, "Found function", i, self.code_tree.functions[i])
                self.code_tree.roots.append(self.code_tree.functions[i])
                self.detect_all_objects(self.code_tree.functions[i])
        for i in self.code_tree.methods:
            if len(self.code_tree.methods[i].body_nodes) > 0:
                output_verbose(self.verbose, "Found method", i, self.code_tree.methods[i])
                self.detect_all_objects(self.code_tree.methods[i])
        for i in self.code_tree.classes:
            if len(self.code_tree.classes[i].body_nodes) > 0:
                output_verbose(self.verbose, "Found class", i, self.code_tree.classes[i])
                self.code_tree.roots.append(self.code_tree.classes[i])
                self.detect_all_objects(self.code_tree.classes[i])
        for i in self.code_tree.structures:
            if len(self.code_tree.structures[i].body_nodes) > 0:
                output_verbose(self.verbose, "Found structure", i, self.code_tree.structures[i])
                self.code_tree.roots.append(self.code_tree.structures[i])
                self.detect_all_objects(self.code_tree.structures[i])
        output_verbose(self.verbose, "-------------------------------")

        for i in self.code_tree.nodes:
            self.detect_if_function_call(i)

    def parse_cpp(self) -> None:
        if not os.path.isdir(self.target):
            red_on_black_print('Given target is not a directory')
            sys.exit(1)

        output_verbose(self.verbose, "Processing DIR:\t", self.target)

        for root, subdirs, files in os.walk(self.target):
            for file_name in files:
                if file_name.endswith('.cpp'):
                    output_verbose(self.verbose, "Found C++:\t\t", root + '/' + file_name)
                    self.parse_cpp_file(root + '/' + file_name)
                else:
                    output_verbose(self.verbose, "Found Not C++:\t", root + '/' + file_name)

    def parse_cpp_file(self, file_path: str) -> None:
        index = clang.cindex.Index.create()
        translation_unit = index.parse(file_path, args=['-std=c++2a'])

        diagnostics = list(translation_unit.diagnostics)
        if len(diagnostics):
            message = 'FOUND ERRORS:\n'
            for diag in diagnostics:
                message += 'Error:\n'
                message += '\tseverity:' + str(diag.severity) + '\n'
                message += '\tlocation:' + str(diag.location) + '\n'
                message += '\tspelling:' + str(diag.spelling) + '\n'
                message += '\tranges:' + str(diag.ranges) + '\n'
                message += '\tfixits:' + str(diag.fixits) + '\n'
            output_error(self.bruteforce, message)

        for cursor in translation_unit.cursor.get_children():
            if not is_file_in_standart(str(cursor.location.file)):
                if cursor.kind.name == 'FUNCTION_DECL':
                    if self.code_tree.functions.get(cursor.get_usr()) is None:
                        self.code_tree.functions[cursor.get_usr()] = Function(None)
                    self.code_tree.functions[cursor.get_usr()].parse_cpp(cursor, self.bruteforce, self.verbose)
                elif cursor.kind.name == 'CXX_METHOD':
                    cursor_children = list(cursor.get_children())
                    for i in cursor_children:
                        if i.kind.name == 'TYPE_REF':
                            class_parent_usr = i.referenced.get_usr()
                            if self.code_tree.methods.get(cursor.get_usr()) is None and \
                                    self.code_tree.classes.get(class_parent_usr) is not None:
                                self.code_tree.methods[cursor.get_usr()] = Function(
                                    self.code_tree.classes.get(class_parent_usr))
                                self.code_tree.classes.get(class_parent_usr).body_nodes.append(
                                    self.code_tree.methods[cursor.get_usr()])
                    if self.code_tree.methods.get(cursor.get_usr()) is None:
                        output_error(self.bruteforce, "Error: Could not create a method!!")
                    else:
                        self.code_tree.methods[cursor.get_usr()].parse_cpp(cursor, self.bruteforce, self.verbose)
                elif cursor.kind.name == 'CLASS_DECL':
                    if self.code_tree.classes.get(cursor.get_usr()) is None:
                        self.code_tree.classes[cursor.get_usr()] = Class(None)
                    self.code_tree.classes[cursor.get_usr()].parse_cpp(cursor, self.code_tree, self.bruteforce,
                                                                       self.verbose)
                elif cursor.kind.name == 'STRUCT_DECL':
                    if self.code_tree.structures.get(cursor.get_usr()) is None:
                        self.code_tree.structures[cursor.get_usr()] = Struct(None)
                    self.code_tree.structures[cursor.get_usr()].parse_cpp(cursor, self.code_tree, self.bruteforce,
                                                                          self.verbose)
                else:
                    output_error(self.bruteforce, "Error: ", cursor.kind.name, " not supported!!")

    def detect_all_objects(self, node):
        self.code_tree.nodes.append(node)
        if type(node) != CodeLine:
            for i in node.body_nodes:
                if type(i) == str:
                    # this is a dictionary
                    self.detect_all_objects(node.body_nodes[i])
                else:
                    self.detect_all_objects(i)
            if type(node) == If:
                for i in node.else_nodes:
                    self.detect_all_objects(i)

    def detect_if_function_call(self, node):
        # FIXME: make more detailed, recursive check (done, but need to check If statements)
        # TODO: somehow show how many times a function is called in a line
        if type(node) == CodeLine:
            self.check_cursor_for_function_calls(node, node.cursor)

    def check_cursor_for_function_calls(self, node, cursor):
        if cursor.kind.name == 'CALL_EXPR':
            cursor_children = list(cursor.get_children())
            if len(cursor_children) and (cursor_children[0].kind.name == 'MEMBER_REF_EXPR' or
                                         cursor_children[0].kind.name == 'UNEXPOSED_EXPR') \
                    and cursor_children[0].referenced is not None:
                if self.code_tree.functions.get(cursor_children[0].referenced.get_usr()) is not None:
                    self.code_tree.function_calls.append(
                        FunctionCall(node, self.code_tree.functions.get(cursor_children[0].referenced.get_usr())))
                elif self.code_tree.methods.get(cursor_children[0].referenced.get_usr()) is not None:
                    self.code_tree.function_calls.append(
                        FunctionCall(node, self.code_tree.methods.get(cursor_children[0].referenced.get_usr())))
                else:
                    output_verbose(self.verbose, "Couldn't find called function: ",
                                   cursor_children[0].referenced.get_usr())
            else:
                # FIXME: do smth here
                # FIXME: add support for class constructor calls detection
                # raise RuntimeError("Cannot see call expr target")
                pass

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

        self.bruteforce = False
        self.verbose = False

        self.global_offset_x = 100
        self.global_offset_y = 0

        self.current_selected_node = None

        # TODO: add side-by-side code comparison

    def set_graphics_info(self, node):
        if type(node) == FunctionCall:
            self.graphics_info[node] = FunctionCallGraphicsInfo(node)
            return
        self.graphics_info[node] = NodeGraphicsInfo(node)
        if type(node) != CodeLine:
            for i in node.body_nodes:
                if type(i) == str:
                    # this is a dictionary
                    self.set_graphics_info(node.body_nodes[i])
                else:
                    self.set_graphics_info(i)

            # FIXME: probably this if type(node) == If thing should have a more elegant solution
            if type(node) == If:
                for i in node.else_nodes:
                    self.set_graphics_info(i)

    def parse(self, target: str, mode: ParseModes, bruteforce: bool, verbose: bool) -> None:
        self.bruteforce = bruteforce
        self.verbose = verbose

        self.parser.parse(target, mode, self.bruteforce, self.verbose)
        # FIXME: make one loop instead of two to reduce code duplicates
        for i in self.parser.code_tree.roots:
            self.set_graphics_info(i)
        for i in self.parser.code_tree.function_calls:
            self.set_graphics_info(i)
        self.should_redraw = True

    def on_resize(self, width: float, height: float):
        for i in self.parser.code_tree.roots:
            self.compute_node_size(i, self.scaler)

        tmp_offset_x = 0

        for i in self.parser.code_tree.roots:
            self.compute_node_position(i, self.scaler, self.global_offset_x + tmp_offset_x,
                                       self.global_offset_y + (self.height - self.graphics_info[i].size_y) // 2)
            tmp_offset_x += self.scaler.OBJECTS_BUFFER
            tmp_offset_x += self.graphics_info[i].size_x

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

            self.graphics_info[node].size_y += scaler.FUNCTIONS_ACCESS_SPECIFIER_BUFFER
        elif type(node) == Class:
            self.graphics_info[node].size_x = 0
            self.graphics_info[node].size_y = 0 + scaler.BUFFER_SIZE_CLASS_VERTICAL * (len(node.body_nodes) + 1)
            # calculate new size:
            for i in node.body_nodes:
                self.compute_node_size(node.body_nodes[i], scaler)
                self.graphics_info[node].size_y += self.graphics_info[node.body_nodes[i]].size_y
                self.graphics_info[node].size_x = max(self.graphics_info[node].size_x,
                                                      self.graphics_info[node.body_nodes[i]].size_x +
                                                      scaler.BUFFER_SIZE_HORIZONTAL * 2)

        elif type(node) == Struct:
            self.graphics_info[node].size_x = 0
            self.graphics_info[node].size_y = 0 + scaler.BUFFER_SIZE_CLASS_VERTICAL * (len(node.body_nodes) + 1)
            # calculate new size:
            for i in node.body_nodes:
                self.compute_node_size(node.body_nodes[i], scaler)
                self.graphics_info[node].size_y += self.graphics_info[node.body_nodes[i]].size_y
                self.graphics_info[node].size_x = max(self.graphics_info[node].size_x,
                                                      self.graphics_info[node.body_nodes[i]].size_x +
                                                      scaler.BUFFER_SIZE_HORIZONTAL * 2)
        else:
            raise RuntimeError("unknown type:", type(node))

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
        elif type(node) == Class:
            offset_y += self.graphics_info[node].size_y
            offset_x += scaler.BUFFER_SIZE_HORIZONTAL
            for i in node.body_nodes:
                offset_y -= scaler.BUFFER_SIZE_CLASS_VERTICAL
                offset_y -= self.graphics_info[node.body_nodes[i]].size_y
                self.compute_node_position(node.body_nodes[i], scaler, offset_x, offset_y)
        elif type(node) == Struct:
            offset_y += self.graphics_info[node].size_y
            offset_x += scaler.BUFFER_SIZE_HORIZONTAL
            for i in node.body_nodes:
                offset_y -= scaler.BUFFER_SIZE_CLASS_VERTICAL
                offset_y -= self.graphics_info[node.body_nodes[i]].size_y
                self.compute_node_position(node.body_nodes[i], scaler, offset_x, offset_y)
        else:
            raise RuntimeError("unknown type:", type(node))

    def move_root(self, node, scaler: Scaler, d_x: int, d_y: int) -> None:
        offset_x = self.graphics_info[node].pos_x + d_x
        offset_y = self.graphics_info[node].pos_y + d_y

        self.compute_node_position(node, scaler, offset_x, offset_y)

    def on_draw(self):
        if self.should_redraw:
            start_time = time.time()
            arcade.start_render()

            for i in self.parser.code_tree.roots:
                self.recursive_node_draw(i)
            for i in self.parser.code_tree.function_calls:
                self.function_call_draw(i)

            arcade.finish_render()
            self.should_redraw = False

            end_time = time.time()
            output_verbose(self.verbose, "Code redraw took:", end_time - start_time,
                           "seconds (" + str(1 / (end_time - start_time)), "FPS)")

    def function_call_draw(self, node):
        if node.target is not None:
            # FIXME: do this properly
            self.compute_function_call_graphics_info(node)
            def quad_bezier(t, p0, p1, p2):
                return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2

            t = 0
            num_segments = 20
            block = 1 / num_segments

            prev_point_x = self.graphics_info[node].start_pos_x
            prev_point_y = self.graphics_info[node].start_pos_y

            curvature_sign = 1
            if self.graphics_info[node].end_pos_x - self.graphics_info[node].start_pos_x > 0:
                curvature_sign = -1

            v = [self.graphics_info[node].end_pos_x - self.graphics_info[node].start_pos_x,
                 self.graphics_info[node].end_pos_y - self.graphics_info[node].start_pos_y]
            perp_v_scaled = [v[1] * self.scaler.LINE_CURVATURE * curvature_sign,
                             -v[0] * self.scaler.LINE_CURVATURE * curvature_sign]

            while t < 1.001:
                x = quad_bezier(t, self.graphics_info[node].start_pos_x,
                                (self.graphics_info[node].start_pos_x + self.graphics_info[node].end_pos_x) // 2 +
                                perp_v_scaled[0],
                                self.graphics_info[node].end_pos_x)
                y = quad_bezier(t, self.graphics_info[node].start_pos_y,
                                (self.graphics_info[node].start_pos_y + self.graphics_info[node].end_pos_y) // 2 +
                                perp_v_scaled[1],
                                self.graphics_info[node].end_pos_y)
                arcade.draw_line(prev_point_x, prev_point_y,
                                 x, y,
                                 (0, 0, 0), self.scaler.LINE_WIDTH)
                prev_point_x = x
                prev_point_y = y
                t += block

    def recursive_node_draw(self, node):
        color = (0, 0, 0)
        if type(node) == CodeLine:
            color = (0, 50, 255)
        elif type(node) == ForLoop or type(node) == ForRangeLoop or type(node) == WhileLoop:
            color = (255, 0, 0)
        elif type(node) == If:
            color = (0, 255, 0)
        elif type(node) == Function:
            color = (125, 125, 125)
        elif type(node) == CodeBlock:
            color = (0, 0, 0, 0)
        elif type(node) == Class:
            color = (50, 50, 50)
        elif type(node) == Struct:
            color = (75, 75, 75)
        arcade.draw_xywh_rectangle_filled(
            self.graphics_info[node].pos_x,
            self.graphics_info[node].pos_y,
            self.graphics_info[node].size_x,
            self.graphics_info[node].size_y,
            color
        )
        if type(node) != CodeBlock:
            arcade.draw_xywh_rectangle_outline(
                self.graphics_info[node].pos_x,
                self.graphics_info[node].pos_y,
                self.graphics_info[node].size_x,
                self.graphics_info[node].size_y,
                (0, 0, 0)
            )
            if node == self.current_selected_node:
                arcade.draw_xywh_rectangle_outline(
                    self.graphics_info[node].pos_x,
                    self.graphics_info[node].pos_y,
                    self.graphics_info[node].size_x,
                    self.graphics_info[node].size_y,
                    (255, 255, 0), 5
                )

        if type(node) != CodeLine:
            offset_y = 0
            for i in node.body_nodes:
                if type(i) == str:
                    # this is a dictionary
                    self.recursive_node_draw(node.body_nodes[i])
                    offset_y += self.graphics_info[node.body_nodes[i]].size_y + self.scaler.BUFFER_SIZE_VERTICAL
                else:
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

    def on_key_press(self, symbol, modifier):
        if symbol == arcade.key.UP:
            if self.current_selected_node is None:
                for i in self.parser.code_tree.roots:
                    self.move_root(i, self.scaler, 0, -50)
            elif self.current_selected_node in self.parser.code_tree.roots:
                self.move_root(self.current_selected_node, self.scaler, 0, 50)
            self.should_redraw = True
        elif symbol == arcade.key.DOWN:
            if self.current_selected_node is None:
                for i in self.parser.code_tree.roots:
                    self.move_root(i, self.scaler, 0, 50)
            elif self.current_selected_node in self.parser.code_tree.roots:
                self.move_root(self.current_selected_node, self.scaler, 0, -50)
            self.should_redraw = True
        elif symbol == arcade.key.RIGHT:
            if self.current_selected_node is None:
                for i in self.parser.code_tree.roots:
                    self.move_root(i, self.scaler, -50, 0)
            elif self.current_selected_node in self.parser.code_tree.roots:
                self.move_root(self.current_selected_node, self.scaler, 50, 0)
            self.should_redraw = True
        elif symbol == arcade.key.LEFT:
            if self.current_selected_node is None:
                for i in self.parser.code_tree.roots:
                    self.move_root(i, self.scaler, 50, 0)
            elif self.current_selected_node in self.parser.code_tree.roots:
                self.move_root(self.current_selected_node, self.scaler, -50, 0)
            self.should_redraw = True
        elif symbol == arcade.key.KEY_0:
            self.scaler.rescale(self.scaler.current_scale * 1.05)
        elif symbol == arcade.key.KEY_9:
            self.scaler.rescale(self.scaler.current_scale * 0.95)

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        if button == 1:
            self.should_redraw = True
            self.current_selected_node = None
            min_size_x = 1e9
            # Find the smallest object selected:
            for i in self.parser.code_tree.nodes:
                if type(i) == CodeBlock:
                    continue
                offset_x = x - self.graphics_info[i].pos_x
                offset_y = y - self.graphics_info[i].pos_y
                if self.graphics_info[i].size_x < min_size_x and \
                        (0 <= offset_x <= self.graphics_info[i].size_x) and \
                        (0 <= offset_y <= self.graphics_info[i].size_y):
                    self.current_selected_node = i
                    min_size_x = self.graphics_info[i].size_x

    def on_mouse_release(self, x: float, y: float, button: int, modifiers: int):
        pass
