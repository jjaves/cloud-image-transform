from dotenv import load_dotenv
from os import path

script_dir = path.abspath(path.dirname(__file__))
dotenv_file_path = path.join(script_dir, '.env')

if path.exists(dotenv_file_path):
    load_dotenv(dotenv_path=dotenv_file_path)
    print(f"local_dev.py: Loaded .env file from {dotenv_file_path}")
else:
    print(f"local_dev.py: .env file not found at {dotenv_file_path}. ")

from image_processor_func.main import process_image_for_transformation
from flask import Flask, request

app = Flask(__name__)


@app.route('/process_image', methods=['GET'])
def process_image():
    return process_image_for_transformation(request)


if __name__ == '__main__':
    app.run(debug=True, port=8080)
