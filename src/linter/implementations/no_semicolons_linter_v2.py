from linter_base import LinterBase, CODE_SUCCESS, CODE_FAILURE
from typing import Tuple

class LinterImpl(LinterBase):

    def get_name(self) -> str:
        return "no_semicolons"
    
    def get_version(self) -> str:
        return "v2"
    
    def lint_code(self, code) -> Tuple[int, str]:
        lines = code.splitlines()

        inside_docstring = False
        for line_num, line in enumerate(lines):
            inside_comment = False
            for char_num, char in enumerate(line):

                if inside_comment: #comments trump docstrings
                    continue

                if char == "#":
                    inside_comment=True

                if line[char_num-2:char_num+1]==r'"""':
                    inside_docstring = not inside_docstring
        
                if char == ';' and not inside_comment and not inside_docstring:
                    return CODE_FAILURE, f"ERROR: found semicolon in line {line_num} at position {char_num}"
                  
        return CODE_SUCCESS, "CORRECT: no redundant semicolons in code"
