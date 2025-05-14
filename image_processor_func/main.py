import functions_framework
from flask import send_file, make_response
from PIL import Image
import requests
import io
import re
from enum import Enum
from dataclasses import dataclass
from os import environ


class ImgFmt(Enum):
    JPEG = "JPEG"
    JPEG2000 = "JPEG2000"
    WEBP = "WEBP"
    PNG = "PNG"
    AVIF = "AVIF"
    BMP = "BMP"
    ICO = "ICO"
    GIF = "GIF"
    TIFF = "TIFF"


@dataclass(frozen=True)
class FmtTrts:
    lossless: bool
    alpha: bool
    mmtype: str
    output: bool


FMT_TRAITS_MAP = {
    ImgFmt.JPEG: FmtTrts(lossless=False, alpha=False, mmtype="image/jpeg", output=True),
    ImgFmt.WEBP: FmtTrts(lossless=True, alpha=True, mmtype="image/webp", output=True),
    ImgFmt.PNG: FmtTrts(lossless=True, alpha=True, mmtype="image/png", output=True),
    ImgFmt.AVIF: FmtTrts(lossless=True, alpha=True, mmtype="image/avif", output=False),
    ImgFmt.BMP: FmtTrts(lossless=True, alpha=False, mmtype="image/bmp", output=False),
    ImgFmt.JPEG2000: FmtTrts(
        lossless=False, alpha=True, mmtype="image/jpeg2000", output=False
    ),
    ImgFmt.ICO: FmtTrts(
        lossless=True, alpha=True, mmtype="image/vnd.microsoft.icon", output=False
    ),
    ImgFmt.GIF: FmtTrts(lossless=False, alpha=True, mmtype="image/gif", output=False),
    ImgFmt.TIFF: FmtTrts(lossless=True, alpha=True, mmtype="image/tiff", output=False),
}


def _parse_bg_color_string(bg_color_str: str | None) -> tuple[int, int, int] | None:
    """
    Parse background color string.
    Return (r,g,b) tuple in 0-255 range, or None if parsing fails.
    """
    if not bg_color_str:
        return None
    bg_color_str = bg_color_str.lower().strip()

    # check if rgb(r,g,b)
    match = re.fullmatch(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", bg_color_str)
    if match:
        try:
            r, g, b = [int(x) for x in match.groups()]
            if all(0 <= val <= 255 for val in (r, g, b)):
                return r, g, b
        except ValueError:
            pass
    return None


def _fetch_image(url: str) -> tuple[Image.Image, str | None]:
    """Fetches an image from a URL."""
    image_response = requests.get(url, stream=True, timeout=30)
    image_response.raise_for_status()
    img = Image.open(image_response.raw)
    original_format = img.format
    return img, original_format


def _rotate_image(img: Image.Image, degrees: int) -> tuple[Image.Image, int, int]:
    """Rotates an image and returns the new image and dimensions."""
    original_width, original_height = img.size
    if degrees in [90, 180, 270]:
        img = img.rotate(
            degrees, resample=Image.Resampling.BICUBIC, expand=True, fillcolor="white"
        )
        if degrees in [90, 270]:
            return img, original_height, original_width

    return img, original_width, original_height


def _calculate_target_dimensions(
    original_width: int,
    original_height: int,
    target_width_str: str | None,
    target_height_str: str | None,
) -> tuple[int, int]:
    """Calculates target dimensions, maintaining aspect ratio if one dimension is missing."""

    def parse_positive_int(s: str | None) -> int | None:
        if s is None:
            return None
        try:
            val = int(s)
            return val if val > 0 else None
        except ValueError:
            return None

    target_w = parse_positive_int(target_width_str)
    target_h = parse_positive_int(target_height_str)

    if target_w is not None and target_h is not None:
        return target_w, target_h

    if target_w is not None:
        if original_width > 0:
            calculated_th = int(target_w * (float(original_height) / original_width))
        else:
            calculated_th = 0
        return target_w, calculated_th

    if target_h is not None:
        if original_height > 0:
            calculated_tw = int(target_h * (float(original_width) / original_height))
        else:
            calculated_tw = 0
        return calculated_tw, target_h

    return original_width, original_height


def _apply_grayscale(img: Image.Image) -> Image.Image:
    """Converts an image to grayscale if it's not already."""
    if img.mode not in ("L", "1"):
        return img.convert("L")
    if img.mode == "1":
        img = img.convert("L")
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
        api_key = environ.get("CLOUD_IMAGE_API_KEY")
        provided_api_key = flask_request.args.get("apikey")
        if not provided_api_key or provided_api_key != api_key:
            return "Unauthorized: Access is denied due to an invalid API key.", 401
    except Exception as e:
        print(f"Error checking API key: {e}")
        return "Authorization Failed: Access is denied.", 401

    try:
        original_image_url = flask_request.args.get("url")
        if not original_image_url:
            return "Error: 'url' parameter is required.", 400

        target_width_str = flask_request.args.get("w")
        target_height_str = flask_request.args.get("h")
        rotate_degrees = int(flask_request.args.get("rotate", 0))
        bg_color_str = flask_request.args.get("bg")
        parsed_bg_color = _parse_bg_color_string(bg_color_str)
        set_grayscale = bool(int(flask_request.args.get("gs", 0)))
        requested_format_str = flask_request.args.get("fmt")
        set_quality = int(flask_request.args.get("qlt", 90))
        img, original_format_str = _fetch_image(original_image_url)

        try:
            if original_format_str:
                original_format_enum = ImgFmt[original_format_str.upper()]
            else:
                return (
                    "Error: Could not determine the format of the original image.",
                    400,
                )
        except KeyError:
            return (
                f"Error: Original image format '{original_format_str}' is not supported.",
                400,
            )

        output_format_enum = None
        if requested_format_str:
            try:
                requested_format_enum = ImgFmt[requested_format_str.upper()]
                if (
                    requested_format_enum in FMT_TRAITS_MAP
                    and FMT_TRAITS_MAP[requested_format_enum].output
                ):
                    output_format_enum = requested_format_enum
                else:
                    return (
                        f"Error: Requested format '{requested_format_str}' is not supported for output.",
                        400,
                    )
            except KeyError:
                return (
                    f"Error: Requested format '{requested_format_str}' is invalid.",
                    400,
                )
        else:
            if (
                original_format_enum in FMT_TRAITS_MAP
                and FMT_TRAITS_MAP[original_format_enum].output
            ):
                output_format_enum = original_format_enum
            else:
                output_format_enum = ImgFmt.PNG

        img, original_width, original_height = _rotate_image(img, rotate_degrees)

        target_width, target_height = _calculate_target_dimensions(
            original_width, original_height, target_width_str, target_height_str
        )

        if target_width <= 0 or target_height <= 0:
            return "Error: Target width and height must be positive values.", 400
        img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

        if parsed_bg_color:
            img = _apply_background_color(img, *parsed_bg_color)

        if set_grayscale:
            img = _apply_grayscale(img)

        output_format_traits = FMT_TRAITS_MAP[output_format_enum]

        if not output_format_traits.alpha and img.mode in ("RGBA", "LA", "P"):
            if img.mode == "P" and "transparency" in img.info:
                img = img.convert("RGBA")
            img = img.convert("RGB")
        elif output_format_traits.alpha and img.mode not in ("RGBA", "LA"):
            if "transparency" in img.info or img.mode == "P":
                img = img.convert("RGBA")

        byte_arr = io.BytesIO()

        pillow_output_format_str = output_format_enum.value

        img.save(
            byte_arr,
            format=pillow_output_format_str,
            optimize=True,
            quality=set_quality,
        )
        byte_arr.seek(0)

        mime_type = output_format_traits.mmtype
        response = make_response(send_file(byte_arr, mimetype=mime_type))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
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
