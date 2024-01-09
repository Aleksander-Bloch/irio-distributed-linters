from virtual_machine.linter import Linter


class LintersManager:

    def __init__(self):
        self.linters_dict = {}

    def add_linter(self, linter: Linter):
        self.linters_dict[(linter.name, linter.version)] = linter

    def get_linter(self, linter_name, version) -> Linter:
        return self.linters_dict.get((linter_name, version))
