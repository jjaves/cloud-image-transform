gcloud functions deploy image-transform \
  --gen2 \
  --runtime python312 \
  --region us-west1 \
  --source ./image_processor_func \
  --entry-point process_image_for_transformation \
  --trigger-http \
  --allow-unauthenticated