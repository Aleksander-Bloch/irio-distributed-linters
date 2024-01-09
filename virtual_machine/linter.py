class Linter:

    def __init__(self, name, version, file_name):
        self.name = name
        self.version = version
        self.fileName = file_name

    def lint(self, code: str):
        pass
