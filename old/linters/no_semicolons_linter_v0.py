import sys


def no_semicolons(lint_input: str):
    curr_line = 1
    curr_char_in_line = 0

    for char in lint_input:
        curr_char_in_line += 1
        if char == "\n":
            curr_line += 1
            curr_char_in_line = 0
        elif char == ';':
            return False, f"ERROR: found semicolon in line {curr_line} at position {curr_char_in_line}"

    return True, "CORRECT: no redundant semicolons in code"


if __name__ == "__main__":
    code_file_name = sys.argv[1]

    with open(code_file_name, "r") as code_file:
        code_file_str = code_file.read()

    lint_status, lint_message = no_semicolons(code_file_str)

    print(lint_status, lint_message, end="")
