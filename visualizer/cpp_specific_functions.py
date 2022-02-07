from .utils import *


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


def cursor_dump(cursor):
    if cursor is None:
        return
    printer = extra_print
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


def cursor_dump_short(cursor):
    if cursor is None:
        return
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
    printer("kind:", cursor.kind,
            "\tspelling:", cursor.spelling,
            "\ttype:", cursor.type.spelling,
            "\tusr:", cursor.get_usr())


def cursor_dump_rec(cursor, depth=0, cap=1e9):
    if cursor is None:
        return
    if depth >= cap:
        return
    # info_print(depth * "\t",
    #            "id:", cursor,
    #            "kind:", cursor.kind,
    #            "\tspelling:", cursor.spelling,
    #            "\ttype:", cursor.type.spelling,
    #            # "\taccess_specifier:", cursor.access_specifier,
    #            # "\textent:", cursor.extent,
    #            # "\tin file:", cursor.location.file,
    #            "\tusr:", cursor.get_usr(),
    #            )
    info_print(depth * "\t",
               "kind:", cursor.kind,
               "\tspelling:", cursor.spelling,
               "\tusr:", cursor.get_usr(),
               )
    if cursor.kind.name == 'TYPE_REF' or cursor.kind.name == 'MEMBER_REF_EXPR' or cursor.kind.name == 'UNEXPOSED_EXPR':
        cursor_dump(cursor.referenced)

    # cursor_dump(cursor.get_definition())
    for child in cursor.get_children():
        cursor_dump_rec(child, depth + 1, cap)
