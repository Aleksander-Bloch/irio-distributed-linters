import os
from threading import Lock

from fastapi import FastAPI, UploadFile

from virtual_machine.linter import Linter
from virtual_machine.linters_manager import LintersManager
import os

app = FastAPI()

code_file_id = 0
code_file_id_lock = Lock()

linters_manager = LintersManager()


async def save_file(upload_file: UploadFile, save_path: str):
    file_bytes = await upload_file.read()
    with open(save_path, "wb") as file_to_save:
        file_to_save.write(file_bytes)


@app.post("/lint/")
async def lint_code_file(linter_name: str, linter_version: int, code_file: UploadFile):

    # get file id for saving user's code to lint
    code_file_id_lock.acquire()
    global code_file_id
    file_id = code_file_id
    code_file_id += 1
    code_file_id_lock.release()

    temp_code_file_name = f"code_{file_id}.txt"
    await save_file(code_file, temp_code_file_name)

    target_linter = linters_manager.get_linter(linter_name, linter_version)

    if target_linter is None:
        server_response = {"error": f"{linter_name}, version: {linter_version} does not exist"}
    else:
        is_code_correct, message = target_linter.lint(temp_code_file_name)
        server_response = {"is_code_correct": is_code_correct, "message": message}

    os.remove(temp_code_file_name)
    return server_response


# If we receive (linter_name, version) that already exists, the old record will be overriden
@app.post("/add_linter/")
async def add_linter(linter_name: str, linter_version: int, linter_file: UploadFile):

    linter_file_name = f"{linter_name}_{linter_version}.py"
    await save_file(linter_file, linter_file_name)

    linters_manager.add_linter(Linter(linter_name, linter_version, linter_file_name))








