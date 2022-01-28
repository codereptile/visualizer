import time
import clang.cindex
import arcade
from pprint import pprint


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


MIN_SIZE = 0
FUNCTIONS_ACCESS_SPECIFIER_BUFFER = 0
BUFFER_SIZE_VERTICAL = 0
BUFFER_SIZE_HORIZONTAL = 0
OBJECTS_BUFFER = 0
LINE_WIDTH = 0


def set_scale(x: float) -> None:
    global MIN_SIZE, FUNCTIONS_ACCESS_SPECIFIER_BUFFER, BUFFER_SIZE_VERTICAL, BUFFER_SIZE_HORIZONTAL, \
        OBJECTS_BUFFER, LINE_WIDTH
    MIN_SIZE = int(50 * x)
    FUNCTIONS_ACCESS_SPECIFIER_BUFFER = int(10 * x)
    BUFFER_SIZE_VERTICAL = int(20 * x)
    BUFFER_SIZE_HORIZONTAL = int(20 * x)
    OBJECTS_BUFFER = int(500 * x)
    LINE_WIDTH = int(10 * x)


def cursor_dump(cursor, depth=0):
    output_object = BaseObject()

    info_print(depth * "\t",
               "kind:", cursor.kind,
               "\tspelling:", cursor.spelling,
               "\ttype:", cursor.type.spelling,
               "\taccess_specifier:", cursor.access_specifier,
               "\textent:", cursor.extent
               )
    for child in cursor.get_children():
        output_object.objects.append(cursor_dump(child, depth + 1))


class Line:
    def __init__(self, source, target):
        self.source = source
        self.target = target

    def draw(self):
        arcade.draw_line(self.source.pos_x + self.source.size_x / 2,
                         self.source.pos_y + self.source.size_y / 2,
                         self.target.pos_x + self.target.size_x / 2,
                         self.target.pos_y + self.target.size_y,
                         (0, 0, 0), LINE_WIDTH)


class BaseObject:
    def __init__(self):
        self.pos_x = 500
        self.pos_y = 500

        self.size_x = MIN_SIZE
        self.size_y = MIN_SIZE

        self.objects = []

    def print(self, depth: int = 0):
        print(depth * "\t", "GENERAL OBJECT")

    def compute_size(self):
        if len(self.objects) == 0:
            self.size_x = MIN_SIZE
            self.size_y = MIN_SIZE
        else:
            # reset:
            self.size_x = 0
            self.size_y = 0 + BUFFER_SIZE_VERTICAL * (len(self.objects) + 1)
            # calculate new size:
            for i in self.objects:
                i.compute_size()
                self.size_y += i.size_y
                self.size_x = max(self.size_x, i.size_x + BUFFER_SIZE_HORIZONTAL * 2)

    def compute_pos(self, offset_x, offset_y):
        self.pos_x = offset_x
        self.pos_y = offset_y

        offset_y += self.size_y

        if type(self) == Function:
            offset_y -= FUNCTIONS_ACCESS_SPECIFIER_BUFFER

        offset_x += BUFFER_SIZE_HORIZONTAL
        for i in self.objects:
            offset_y -= BUFFER_SIZE_VERTICAL
            offset_y -= i.size_y
            i.compute_pos(offset_x, offset_y)

    def compute_lines(self, objects, lines: list):
        for i in self.objects:
            i.compute_lines(objects, lines)

    def draw(self):
        arcade.draw_rectangle_filled(self.pos_x + self.size_x / 2, self.pos_y + self.size_y / 2, self.size_x,
                                     self.size_y, (0, 125, 125))
        for j in self.objects:
            j.draw()


class CodeBlock(BaseObject):
    def __init__(self):
        super().__init__()

    def print(self, depth: int = 0):
        print(depth * "\t", "Code Block:")
        for i in self.objects:
            i.print(depth + 1)

    def draw(self):
        arcade.draw_rectangle_filled(self.pos_x + self.size_x / 2, self.pos_y + self.size_y / 2,
                                     self.size_x, self.size_y, (200, 200, 200))
        for j in self.objects:
            j.draw()


class Function(BaseObject):
    def __init__(self):
        super().__init__()
        self.parameters = []
        self.name = "No name set!"

        self.access_specifier = "INVALID"

    def print(self, depth: int = 0):
        print(depth * "\t", "Function:", self.name)
        print((depth + 1) * "\t", "Parameters:", self.parameters)
        print((depth + 1) * "\t", "Access Specifier:", self.access_specifier)
        print((depth + 1) * "\t", "Body:")
        for i in self.objects:
            i.print(depth + 2)

    def compute_size(self):
        super().compute_size()
        self.size_y += FUNCTIONS_ACCESS_SPECIFIER_BUFFER

    def draw(self):
        arcade.draw_rectangle_filled(self.pos_x + self.size_x / 2, self.pos_y + self.size_y / 2,
                                     self.size_x, self.size_y, (150, 150, 150))
        if self.access_specifier == "PUBLIC":
            arcade.draw_rectangle_filled(self.pos_x + self.size_x / 2,
                                         self.pos_y + self.size_y - FUNCTIONS_ACCESS_SPECIFIER_BUFFER / 2,
                                         self.size_x, FUNCTIONS_ACCESS_SPECIFIER_BUFFER,
                                         (0, 255, 0))
        elif self.access_specifier == "PROTECTED":
            arcade.draw_rectangle_filled(self.pos_x + self.size_x / 2,
                                         self.pos_y + self.size_y - FUNCTIONS_ACCESS_SPECIFIER_BUFFER / 2,
                                         self.size_x, FUNCTIONS_ACCESS_SPECIFIER_BUFFER,
                                         (255, 255, 0))
        elif self.access_specifier == "PRIVATE":
            arcade.draw_rectangle_filled(self.pos_x + self.size_x / 2,
                                         self.pos_y + self.size_y - FUNCTIONS_ACCESS_SPECIFIER_BUFFER / 2,
                                         self.size_x, FUNCTIONS_ACCESS_SPECIFIER_BUFFER,
                                         (255, 0, 0))
        elif self.access_specifier == "CONSTRUCTOR":
            arcade.draw_rectangle_filled(self.pos_x + self.size_x / 2,
                                         self.pos_y + self.size_y - FUNCTIONS_ACCESS_SPECIFIER_BUFFER / 2,
                                         self.size_x, FUNCTIONS_ACCESS_SPECIFIER_BUFFER,
                                         (255, 0, 255))
        else:
            arcade.draw_rectangle_filled(self.pos_x + self.size_x / 2,
                                         self.pos_y + self.size_y - FUNCTIONS_ACCESS_SPECIFIER_BUFFER / 2,
                                         self.size_x, FUNCTIONS_ACCESS_SPECIFIER_BUFFER,
                                         (150, 150, 150))
        for j in self.objects:
            j.draw()


class Class(BaseObject):
    def __init__(self):
        super().__init__()
        self.name = "No name set!"

    def print(self, depth: int = 0):
        print(depth * "\t", "Class:", self.name)
        print((depth + 1) * "\t", "Body:")
        for i in self.objects:
            i.print(depth + 2)

    def draw(self):
        arcade.draw_rectangle_filled(self.pos_x + self.size_x / 2, self.pos_y + self.size_y / 2, self.size_x,
                                     self.size_y, (50, 50, 50))
        for j in self.objects:
            j.draw()


class CodeLine(BaseObject):
    def __init__(self):
        super().__init__()
        self.kind = "NO KIND"
        self.cursor = None

    def draw(self):
        arcade.draw_rectangle_filled(self.pos_x + self.size_x / 2, self.pos_y + self.size_y / 2, self.size_x,
                                     self.size_y, (0, 0, 200))
        for j in self.objects:
            j.draw()

    def print(self, depth: int = 0):
        print(depth * "\t", "Code line: " + self.kind)

    def get_all_call_expressions(self, ans: list, cursor):
        if cursor.kind.name == "CALL_EXPR":
            ans.append(cursor.spelling)
        for i in cursor.get_children():
            self.get_all_call_expressions(ans, i)

    def compute_lines(self, objects, lines: list):
        call_expressions = []
        self.get_all_call_expressions(call_expressions, self.cursor)
        # FIXME: this is SUPER slow!!!
        for i in call_expressions:
            for j in objects:
                target = self.find_target_function(j, i)
                if target is not None:
                    lines.append(Line(self, target))

    def find_target_function(self, node, call_expression):
        if type(node) == Function:
            if node.name == call_expression:
                return node
            else:
                return None
        else:
            for i in node.objects:
                possible_target = self.find_target_function(i, call_expression)
                if possible_target is not None:
                    return possible_target
            return None


class ForLoop(BaseObject):
    def __init__(self):
        super().__init__()

    def draw(self):
        arcade.draw_rectangle_filled(self.pos_x + self.size_x / 2, self.pos_y + self.size_y / 2, self.size_x,
                                     self.size_y, (200, 0, 0))
        for j in self.objects:
            j.draw()


class FunctionHandler:
    def __init__(self, function):
        self.function = function


def print_diagnostics(translation_unit):
    def get_diag_info(diag):
        return {'severity': diag.severity,
                'location': diag.location,
                'spelling': diag.spelling,
                'ranges': diag.ranges,
                'fixits': diag.fixits}

    pprint(('diags', [get_diag_info(d) for d in translation_unit.diagnostics]))


class ParsedCode:
    def __init__(self, path_to_file: str):
        self.path_to_file = path_to_file
        self.objects = []

        self.function_handlers = []

        self.lines = []
        self.total_size_x = 0

    def detect_functions(self, current_object: BaseObject):
        if type(current_object) == Function:
            self.function_handlers.append(FunctionHandler(current_object))
        for i in current_object.objects:
            self.detect_functions(i)

    def parse(self):
        index = clang.cindex.Index.create()
        translation_unit = index.parse(self.path_to_file, args=[])

        for function in translation_unit.cursor.get_children():
            object_candidate = self.parse_object(function)
            if object_candidate is not None:
                self.objects.append(object_candidate)

        print_diagnostics(translation_unit)

        for i in self.objects:
            self.detect_functions(i)

        for i in self.objects:
            i.compute_lines(self.objects, self.lines)

    def print(self):
        for i in self.objects:
            i.print()

    def draw(self):
        for i in self.objects:
            i.draw()
        for i in self.lines:
            i.draw()

    def compute_layout(self, center_x: int, center_y: int):
        self.total_size_x = (len(self.objects) - 1) * OBJECTS_BUFFER

        for i in self.objects:
            i.compute_size()
            self.total_size_x += i.size_x

        current_offset_x = center_x - self.total_size_x / 2

        for i in self.objects:
            i.compute_pos(current_offset_x, center_y - i.size_y // 2)
            current_offset_x += i.size_x + OBJECTS_BUFFER

        for i in self.function_handlers:
            print(i.function.name, i.function.pos_x, i.function.pos_y)

    def parse_object(self, cursor: clang.cindex.Cursor, depth: int = 0):
        if cursor.kind.name == "FUNCTION_DECL" or cursor.kind.name == "CXX_METHOD" or cursor.kind.name == "CONSTRUCTOR":
            function_object = Function()

            if cursor.kind.name == "CXX_METHOD":
                function_object.access_specifier = cursor.access_specifier.name
            elif cursor.kind.name == "CONSTRUCTOR":
                function_object.access_specifier = "CONSTRUCTOR"

            function_object.name = cursor.spelling

            # FIXME: This is the 'anti-visualizing-the-whole-std-library-set' defence.
            #  Probably this could be done better
            if function_object.name[0] == '_':
                return None
            # ------------------------------------------------

            for function_detail_cursor in cursor.get_children():
                if function_detail_cursor.kind.name == "PARM_DECL":
                    function_object.parameters.append(
                        [function_detail_cursor.spelling, function_detail_cursor.type.spelling])
                elif function_detail_cursor.kind.name == "COMPOUND_STMT":
                    for line_cursor in function_detail_cursor.get_children():
                        object_candidate = self.parse_object(line_cursor, depth + 1)
                        if object_candidate is None:
                            raise NotImplementedError("Unsupported body block: " + line_cursor.kind.name)
                        function_object.objects.append(object_candidate)
                else:
                    raise NotImplementedError("Unsupported function detail: " + function_detail_cursor.kind.name)
            return function_object
        elif cursor.kind.name == "CLASS_DECL":
            class_object = Class()

            class_object.name = cursor.spelling

            for class_detail_cursor in cursor.get_children():
                if class_detail_cursor.kind.name == "CXX_ACCESS_SPEC_DECL":
                    pass
                elif class_detail_cursor.kind.name == "CXX_METHOD":
                    class_object.objects.append(self.parse_object(class_detail_cursor, depth + 1))
                elif class_detail_cursor.kind.name == "FIELD_DECL":
                    pass
                elif class_detail_cursor.kind.name == "CONSTRUCTOR":
                    class_object.objects.append(self.parse_object(class_detail_cursor, depth + 1))
                else:
                    raise NotImplementedError("Unsupported class detail:", class_detail_cursor.kind.name)
            return class_object
        elif cursor.kind.name == "FOR_STMT" or cursor.kind.name == "WHILE_STMT":
            # FIXME: make while an independent class
            for_loop_object = ForLoop()

            for for_loop_detail_cursor in cursor.get_children():
                if for_loop_detail_cursor.kind.name == "COMPOUND_STMT":
                    for line_cursor in for_loop_detail_cursor.get_children():
                        object_candidate = self.parse_object(line_cursor, depth + 1)
                        if object_candidate is None:
                            print(line_cursor.location)
                            raise NotImplementedError("Unsupported body block: " + line_cursor.kind.name)
                        for_loop_object.objects.append(object_candidate)
                else:
                    # FIXME: actually save this data
                    pass
            if len(for_loop_object.objects) == 0:
                raise NotImplementedError("One-liner loops are not supported")

            return for_loop_object
        elif cursor.kind.name == "COMPOUND_STMT":
            # FIXME: make this a proper class
            code_block_object = CodeBlock()

            for line_cursor in cursor.get_children():
                object_candidate = self.parse_object(line_cursor, depth + 1)
                if object_candidate is None:
                    print(line_cursor.location)
                    raise NotImplementedError("Unsupported body block: " + line_cursor.kind.name)
                code_block_object.objects.append(object_candidate)
            return code_block_object
        elif cursor.kind.name in ["DECL_STMT", "CALL_EXPR", "UNEXPOSED_EXPR", "RETURN_STMT", "IF_STMT",
                                  "BINARY_OPERATOR", "COMPOUND_ASSIGNMENT_OPERATOR"]:
            code_line = CodeLine()
            code_line.cursor = cursor
            code_line.kind = cursor.kind.name
            return code_line
        else:
            return None


class Visualizer(arcade.Window):
    def __init__(self):
        super().__init__(int(arcade.get_screens()[0].width), int(arcade.get_screens()[0].height),
                         title="Codereptile visualizer", resizable=True, center_window=True, vsync=True)

        arcade.set_background_color((255, 255, 255))
        arcade.start_render()
        arcade.draw_text("LOADING", self.width // 2, self.height // 2, (0, 0, 0), self.width / 20, anchor_x="center",
                         anchor_y="center")
        arcade.finish_render()

        self.drawn = False
        self.scale = 0.9

        # self.parsed_files = [ParsedCode("../scanner/main.cpp")]
        self.parsed_files = [ParsedCode("some_code.cpp")]
        for parsed_file in self.parsed_files:
            parsed_file.parse()

        print("\n-------------------------------------------------------------\n")
        for parsed_file in self.parsed_files:
            parsed_file.print()
        print("\n-------------------------------------------------------------\n")

    def on_draw(self):
        if not self.drawn:
            arcade.start_render()

            for parsed_file in self.parsed_files:
                parsed_file.draw()

            arcade.finish_render()
            self.drawn = True

    def on_resize(self, width: float, height: float):
        set_scale(self.scale)
        i = 1
        for parsed_file in self.parsed_files:
            parsed_file.compute_layout(i * self.width // (2 * len(self.parsed_files)), self.height // 2)
            i += 2
        self.drawn = False

    def update(self, delta_time):
        pass


game = Visualizer()
arcade.run()
