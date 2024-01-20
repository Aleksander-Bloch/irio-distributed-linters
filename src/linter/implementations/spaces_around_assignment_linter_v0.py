from linter_base import LinterBase, CODE_SUCCESS, CODE_FAILURE
from typing import Tuple

class LinterImpl(LinterBase):

    def get_name(self) -> str:
        return "spaces_around_equals"
    
    def get_version(self) -> str:
        return "v0"
    
    def lint_code(self, code) -> Tuple[int, str]:
        lines = code.splitlines()
        for line_num, line in enumerate(lines):
            for char_num, char in enumerate(line):
                if char == '=' and line[char_num-1:char_num+2] != " = ":
                    return CODE_FAILURE, f"ERROR: no spaces around assignment in ine {line_num} at position {char_num}"
        return CODE_SUCCESS, "CORRECT: all assignments have spaces around them"

