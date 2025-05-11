import functions_framework
from flask import request, send_file, make_response
from PIL import Image, ImageOps
import requests
import io
import re


def _parse_bg_color_string(bg_color_str: str | None) -> tuple[int, int, int] | None:
   """
   Parse background color string.
   Return (r,g,b) tuple in 0-255 range, or None if parsing fails.
   """
   if not bg_color_str:
      return None
   bg_color_str = bg_color_str.lower().strip()

   # check if rgb(r,g,b)
   match = re.fullmatch(r"rgb\((\d+),(\d+),(\d+)\)", bg_color_str)
   if match:
      try:
         r, g, b = [int(x) for x in match.groups()]
         if all(0 <= val <= 255 for val in (r, g, b)):
            return r, g, b
      except ValueError:
         pass
   return None


def _fetch_image(url: str) -> Image.Image:
   """Fetches an image from a URL."""
   image_response = requests.get(url, stream=True, timeout=30)
   image_response.raise_for_status()

   return Image.open(image_response.raw)


def _rotate_image(img: Image.Image, degrees: int) -> tuple[Image.Image, int, int]:
   """Rotates an image and returns the new image and dimensions."""
   original_width, original_height = img.size
   if degrees in [90, 180, 270]:
      img = img.rotate(degrees, resample=Image.Resampling.BICUBIC, expand=True, fillcolor="white")
      if degrees in [90, 270]:
         return img, original_height, original_width

   return img, original_width, original_height


def _calculate_target_dimensions(
   original_width: int,
   original_height: int,
   target_width_str: str | None,
   target_height_str: str | None
) -> tuple[int, int]:
   """Calculates target dimensions, maintaining aspect ratio if one dimension is missing."""
   target_width = int(target_width_str) if target_width_str else None
   target_height = int(target_height_str) if target_height_str else None

   if target_width and not target_height:
      aspect_ratio = original_height / original_width
      target_height = int(target_width * aspect_ratio)
   elif not target_width and target_height:
      aspect_ratio = original_width / original_height
      target_width = int(target_height * aspect_ratio)
   elif not target_width and not target_height:
      target_width = original_width
      target_height = original_height
   
   if target_width is None: target_width = original_width
   if target_height is None: target_height = original_height

   return target_width, target_height

def _apply_grayscale(img: Image.Image) -> Image.Image:
   """Converts an image to grayscale if it's not already."""
   if img.mode not in ('L', '1'):
      img = ImageOps.grayscale(img)
   if img.mode != 'L':
      img = img.convert('L')
   return img

def _apply_background_color(img: Image.Image, r: int, g: int, b: int) -> Image.Image:
   """Applies a background color to an image. Assumes img might have transparency."""
   if img.mode != "RGBA":
      img_rgba = img.convert("RGBA")
   else:
      img_rgba = img
   
   background = Image.new("RGBA", img_rgba.size, (r, g, b, 255))
   img_composite = Image.alpha_composite(background, img_rgba)

   return img_composite.convert("RGB")

@functions_framework.http
def process_image_for_transformation(flask_request):
   """HTTP Cloud Function to fetch, convert, and return an image."""
   try:
      original_image_url = flask_request.args.get('url')
      if not original_image_url:
         return "Error: 'url' parameter is required.", 400

      target_width_str = flask_request.args.get('w')
      target_height_str = flask_request.args.get('h')
      rotate_degrees = int(flask_request.args.get('rotate', 0))
      
      bg_color_str = flask_request.args.get('bg')
      print(bg_color_str)
      parsed_bg_color = _parse_bg_color_string(bg_color_str)

      set_grayscale = bool(int(flask_request.args.get('gs', 0)))

      img = _fetch_image(original_image_url)

      img, original_width, original_height = _rotate_image(img, rotate_degrees)

      target_width, target_height = _calculate_target_dimensions(
         original_width, original_height, target_width_str, target_height_str
      )

      if target_width <= 0 or target_height <= 0:
         return "Error: Target width and height must be positive values.", 400
      img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
      print(f"Mode after resize: {img.mode}")

      if parsed_bg_color:
         img = _apply_background_color(img, *parsed_bg_color)
         print(f"Mode after background color: {img.mode}")

      if set_grayscale:
         img = _apply_grayscale(img)
         print(f"Mode after grayscale: {img.mode}")
      
      byte_arr = io.BytesIO()

      if img.mode == 'P' and 'transparency' in img.info:
         img = _apply_grayscale(img)
      
      byte_arr = io.BytesIO()
      output_format = 'PNG'

      if img.mode == 'P' and 'transparency' in img.info:
         img = img.convert('RGBA')
      elif img.mode == 'LA' or img.mode == 'RGBA':
         pass

      img.save(byte_arr, format=output_format)
      byte_arr.seek(0)

      response = make_response(send_file(byte_arr, mimetype=f'image/{output_format.lower()}'))
      # response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
      # response.headers['Pragma'] = 'no-cache'
      # response.headers['Expires'] = '0'
      return response

   except requests.exceptions.RequestException as e:
      print(f"Error fetching image: {e}")
      return f"Error fetching original image: {e}", 500
   except ValueError as e:
      print(f"Error with parameters: {e}")
      return f"Error processing parameters: {e}", 400
   except Exception as e:
      print(f"An unexpected error occurred: {e}")
      import traceback
      print(traceback.format_exc())
      return "An unexpected error occurred processing the image.", 500
