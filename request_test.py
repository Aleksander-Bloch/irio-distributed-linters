import requests

test_url = 'http://localhost:8000/uploadfile/'

with open("test_file.txt", "rb") as test_file:
    test_response = requests.post(test_url, files={"file": test_file}, params={"linter": "pylint"})
    print(test_response.request.body)
    print(test_response.status_code)
    print(test_response.content)
