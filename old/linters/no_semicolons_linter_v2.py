

def no_semicolons(lint_input):

    curr_line = 1
    curr_char_in_line = 0

    inside_comment = False
    inside_string = False
    inside_doc_string = False


    prev_chars = {-1: " ", -2: " "}

    for char in lint_input:
        curr_char_in_line += 1
        if char == "\n":
            curr_line += 1
            curr_char_in_line = 0
            inside_comment = False
        elif inside_comment:
            # ignore chars other than new line if inside comment
            pass
        elif char == "#":
            inside_comment = True
        elif char == "\"":
            if prev_chars[-1] == "\"" and prev_chars[-2] == "\"":
                inside_doc_string = not inside_doc_string
            else:
                inside_string = not inside_string
        elif char == ';':
            if not inside_comment and not inside_string and not inside_doc_string:
                return False, f"ERROR: found semicolon in line {curr_line} at position {curr_char_in_line}"
        # shift prev chars
        prev_chars[-2] = prev_chars[-1]
        prev_chars[-1] = char


    return True, "CORRECT: no redundant semicolons in code"


with open("test_no_semicolons.txt", "r") as test_file:
    print(no_semicolons(test_file.read()))


