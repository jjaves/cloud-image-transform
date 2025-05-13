from flask import Flask, request
from image_processor_func.main import process_image_for_transformation

app = Flask(__name__)


@app.route('/process_image', methods=['GET'])
def process_image():
    return process_image_for_transformation(request)


if __name__ == '__main__':
    app.run(debug=True, port=8080)
