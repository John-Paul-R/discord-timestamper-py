import re

import parsedatetime


def sanitize(string):
    # the parsedatetime parser seems to choke on things like `8:30cst`,
    # but does fine with `8:30 cst`
    string = re.sub(r"([0-9])([a-zA-Z])", r"\1 \2", string)
    string = re.sub(r"([a-zA-Z])([0-9])", r"\1 \2", string)
    return string


def try_parsedatetime(string):
    string = sanitize(string)
    cal = parsedatetime.Calendar(version=parsedatetime.VERSION_CONTEXT_STYLE)
    # time_struct, parse_status = cal.parse(string)
    return cal.parse(string)


def try_parsedatetime_raw_print(string):
    cal = parsedatetime.Calendar(version=parsedatetime.VERSION_CONTEXT_STYLE)
    time_struct, parse_status = cal.parse(string)

    print(string)
    print(time_struct)
    print(parse_status)
    print()


if __name__ == '__main__':
    try_parsedatetime_raw_print('May 5th 2:30 in the afternoon')
    try_parsedatetime_raw_print('8:30cst 12/5')
    try_parsedatetime_raw_print('8:30 12/5')
    try_parsedatetime_raw_print('Tentative next session 8:30cst 12/5 (may have to change up)')
    try_parsedatetime_raw_print('Tentative next session 8:30 12/5 (may have to change up)')
    try_parsedatetime_raw_print('Tentative next session 8:30 cst 12/5 (may have to change up)')
    try_parsedatetime_raw_print('next tues 8:30cst')
    try_parsedatetime_raw_print('tues 8:30cst')
    try_parsedatetime_raw_print(sanitize('tues 8:30cst'))
