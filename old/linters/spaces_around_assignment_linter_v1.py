# handles a == 4 case correctly
def lint_spaces_around_assignment_v1(code: str):
    allowed_chars_before_assignment = ["<", ">", "+", "-", "*", "/", "%", "="]
    allowed_char_after_assignment = ["="]
    store = {-2: "", -1: "", 0: ""}

    for line_no, line in enumerate(code.splitlines()):
        for char_no, char in enumerate(list(line)):
            store[-2] = store[-1]
            store[-1] = store[0]
            store[0] = char

            if store[-1] != "=":
                continue

            good_char_before = False
            for allowed_char in allowed_chars_before_assignment:
                if store[-2] == allowed_char:
                    good_char_before = True
                    break

            good_char_after = False
            for allowed_char in allowed_char_after_assignment:
                if store[0] == allowed_char:
                    good_char_after = True
                    break

            if not good_char_before and not good_char_after and (store[-2] != " " or store[0] != " "):
                return False, f"ERROR: no spaces around assignment in ine {line_no + 1} at position {char_no}"
    return True, "CORRECT: all assignments have spaces around them"
