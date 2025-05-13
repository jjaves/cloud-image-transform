# Cloud Image Transform

This tool will fetch, re-process, and display images from the web. It uses Google Cloud Function for image manipulation.

### Quick Example usage
`<your-GCP-func-url.com>/<your-endpoint>?url=<external-image-url>&w=300&gs=1&fmt=png`

Example using `?url=https://storage.googleapis.com/misc-shared-images-public/rita-pup.png&w=300&bg=rgb(9,189,201)&fmt=jpeg`

  <img title="a title" alt="Alt text" src="https://us-west1-trmnl-byos-01.cloudfunctions.net/image-transform?url=https://storage.googleapis.com/misc-shared-images-public/rita-pup.png&w=300&bg=rgb(9,189,201)&fmt=jpeg">

Parameters:
 - `url`:  url of image to ingest. eg. `?url=https://site.io/image.png`
 - `w`: width in pixels. Applying just width will auto scale height. eg. `&w=300`
 - `h`: height in pixels. Applying just height will auto scale width. eg. `&h=150`
 - `fmt`: outputs image format in jpeg, png, or webp only. Default is png. eg. `&fmt=jpeg`
 - `qlt`: for jpeg and webp, decreases the image quality and file size. Default is 90. eg. `&qlt=10`
 - `gs`: boolean for grayscale. eg. `&gs=1`
 - `bg`: to set transparency background color. eg. `&bg=rgb(9,189,201)`
 - `rotate`: Pick from 90, 180, and 270. eg. `&rotate=180`
 
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

### Additional Examples

#### Resize Image

  <details>
  <summary> Original Image </summary>
    <img title="Original" alt="a pup" src="https://storage.googleapis.com/misc-shared-images-public/rita-pup.png">
  </details>

  <details>
  <summary> Resized Image </summary>
    <img title="Original" alt="a pup" src="https://us-west1-trmnl-byos-01.cloudfunctions.net/image-transform?url=https://storage.googleapis.com/misc-shared-images-public/rita-pup.png&w=300">
  </details>

  <details>
  <summary> Add Background and reduce quality/image size </summary>
    <img title="Original" alt="a pup" src="https://us-west1-trmnl-byos-01.cloudfunctions.net/image-transform?url=https://storage.googleapis.com/misc-shared-images-public/rita-pup.png&w=300&bg=rgb(99,200,140)&fmt=jpeg&qlt=1">
  </details>

  <details>
  <summary> Make grayscale </summary>
    <img title="Original" alt="a pup" src="https://us-west1-trmnl-byos-01.cloudfunctions.net/image-transform?url=https://storage.googleapis.com/misc-shared-images-public/rita-pup.png&w=300&bg=rgb(99,200,140)&fmt=jpeg&qlt=1&gs=1">
  </details>

  <details>
  <summary> Rotate!  </summary>
    <img title="90 rotate" alt="a pup" src="https://us-west1-trmnl-byos-01.cloudfunctions.net/image-transform?url=https://storage.googleapis.com/misc-shared-images-public/rita-pup.png&w=300&bg=rgb(99,200,140)&fmt=jpeg&qlt=1&rotate=90"><img title="180 rotate" alt="a pup" src="https://us-west1-trmnl-byos-01.cloudfunctions.net/image-transform?url=https://storage.googleapis.com/misc-shared-images-public/rita-pup.png&w=300&bg=rgb(99,200,140)&fmt=jpeg&qlt=1&rotate=180"><img title="270 rotate" alt="a pup" src="https://us-west1-trmnl-byos-01.cloudfunctions.net/image-transform?url=https://storage.googleapis.com/misc-shared-images-public/rita-pup.png&w=300&bg=rgb(99,200,140)&fmt=jpeg&qlt=1&rotate=270">
  </details>