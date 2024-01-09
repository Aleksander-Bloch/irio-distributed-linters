import subprocess


class Linter:

    def __init__(self, name, version, file_name):
        self.name = name
        self.version = version
        self.file_name = file_name

    def parse_linting_result(self, result_str):
        # format stringa zwracanego przez linter: "True komunikat o rezultacie"
        two_elem_list = result_str.split(" ", 1)

        return bool(two_elem_list[0]), two_elem_list[1]

    def lint(self, temp_code_file_name: str):
        result = subprocess.run(["python", self.file_name, temp_code_file_name])

        return self.parse_linting_result(result.stdout)
