from fastapi import FastAPI, UploadFile

app = FastAPI()


@app.post("/uploadfile/")
async def create_upload_file(linter: str, file: UploadFile):
    print(linter)
    print(await file.read())
    return linter, file


