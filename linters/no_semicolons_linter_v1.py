def no_semicolons(lint_input):

    curr_line = 1
    curr_char_in_line = 0

    inside_comment = False

    for char in lint_input:
        curr_char_in_line += 1
        if char == "#":
            inside_comment = True
        elif char == "\n":
            curr_line += 1
            curr_char_in_line = 0
            inside_comment = False
        elif char == ';':
            if not inside_comment:
                return False, f"ERROR: found semicolon in line {curr_line} at position {curr_char_in_line}"

    return True, "CORRECT: no redundant semicolons in code"


with open("test_no_semicolons.txt", "r") as test_file:
    print(no_semicolons(test_file.read()))

