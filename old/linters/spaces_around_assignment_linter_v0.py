def lint_spaces_around_assignment_v0(code: str):
    store = ["", "", ""]
    for line_no, line in enumerate(code.splitlines()):
        for char_no, char in enumerate(list(line)):
            store[2] = store[1]
            store[1] = store[0]
            store[0] = char
            if store[1] == "=" and (store[0] != " " or store[2] != " "):
                return False, f"ERROR: no spaces around assignment in ine {line_no + 1} at position {char_no}"
    return True, "CORRECT: all assignments have spaces around them"
