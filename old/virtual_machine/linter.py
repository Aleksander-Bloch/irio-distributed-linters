import subprocess


class Linter:

    def __init__(self, name, version, file_name):
        self.name = name
        self.version = version
        self.file_name = file_name

    @classmethod
    def parse_linting_result(cls, result_str):
        # format stringa zwracanego przez linter: "True komunikat o rezultacie"
        two_elem_list = result_str.split(" ", 1)
        if two_elem_list[0] == "True":
            res1 = True
        else:
            res1 = False

        return res1, two_elem_list[1]

    def lint(self, temp_code_file_name: str):
        result = subprocess.run(["python", self.file_name, temp_code_file_name], capture_output=True)
        return self.parse_linting_result(str(result.stdout, encoding='utf-8'))
