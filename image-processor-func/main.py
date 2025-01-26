from flask import request, send_file
import functions_framework
from PIL import Image, ImageOps
import requests
import io

@functions_framework.http
def process_image_for_kindle(flask_request):
   """HTTP Cloud Function to fetch, convert, and return an image."""
   try:
      original_image_url = flask_request.args.get('url')
      target_width = int(flask_request.args.get('w', 600))
      target_height = int(flask_request.args.get('h', 800))

      if not original_image_url:
         return "Error: 'url' parameter is required.", 400

      image_response = requests.get(original_image_url, stream=True, timeout=30)
      image_response.raise_for_status()

      img = Image.open(image_response.raw)

      img = ImageOps.grayscale(img)

      img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

      if img.mode != 'L':
         img = img.convert('L')

      byte_arr = io.BytesIO()
      img.save(byte_arr, format='PNG')
      byte_arr.seek(0)

      return send_file(byte_arr, mimetype='image/png')

   except requests.exceptions.RequestException as e:
      print(f"Error fetching image: {e}")
      return f"Error fetching original image: {e}", 500
   except ValueError as e:
      print(f"Error with parameters: {e}")
      return f"Error processing parameters: {e}", 400
   except Exception as e:
      print(f"An unexpected error occurred: {e}")
      return f"An unexpected error occurred: {e}", 500