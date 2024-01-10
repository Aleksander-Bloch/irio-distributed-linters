from enum import Enum

from fastapi import FastAPI, UploadFile

from linters.spaces_around_assignment_linter_v0 import lint_spaces_around_assignment_v0

app = FastAPI()


class LinterEnum(Enum):
    NO_SEMICOLONS_LINTER = "no_semicolons_linter"
    SPACES_AROUND_ASSIGNMENT_LINTER = "spaces_linter"


@app.post("/lint/")
async def create_upload_file(linter: str, file: UploadFile):
    if linter in [e.value for e in LinterEnum]:
        code = await file.read()
        code_str = str(code)
        match linter:
            case LinterEnum.NO_SEMICOLONS_LINTER:
                return lint_spaces_around_assignment_v0(code_str)
            case LinterEnum.SPACES_AROUND_ASSIGNMENT_LINTER:
                return ''
    else:
        return f"not linter with name {linter} available"


