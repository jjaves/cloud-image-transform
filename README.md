# Cloud Image Transform

This tool will fetch, re-process, and display images from the web. It uses Google Cloud Function for image manipulation.

### Example usage
`<your-GCP-func-url.com>/<your-endpoint>?url=<external-image-url>&w=300&gs=1`

Parameters:
 - `w`: width in pixels. eg. `&w=300`
 - `h`: height in pixels. eg. `&h=150`
 - `gs`: boolean for grayscale. eg. `gs=1`
 - `bg`: to set transparency background color. eg. `bg=rgb(255,0,0)`
 - `rotate`: Pick from 90, 180, and 270. eg. `rotate=180`
 
## Components

1.  **Image Processing Google Cloud Function (`image_processor_func/main.py`)**:
    *   Fetches an image from a given URL.
    *   Optionally resizes the image to specified dimensions.
    *   Optionally rotates the image.
    *   Optionally converts the image to grayscale.
    *   Optionally applies a background color, RGB.
    *   Returns a PNG.
    *   The entry point for the function is [`process_image_for_transformation`](image_processor_func/main.py).


1.  **Local Development Server (`local_dev.py`)**:
    *   A Flask application that allows local testing of the image processing logic found in [`image_processor_func.main.process_image_for_transformation`](image_processor_func/main.py).

## Setup and Usage

### Python Environment

The project uses Conda for environment management. You can create and activate the environment using the [environment.yml](environment.yml) file:
  ```bash
    conda env create -f environment.yml
    conda activate cloud-image-transform
  ```

### Google Cloud Function
- Deployment: The Google Cloud Function can be deployed using the deploy script:
  ```bash
  chmod +x deploy.sh
  ./deploy.sh 
  ```

- Dependencies: Python dependencies for the cloud function are listed in `requirements.txt`

### Local Development
To test the image processing function locally, run the Flask development server:
```bash
python local_dev.py
```