#!/bin/bash

[ -f .env ] && source .env

PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo "Error: GCP Project ID not found. Set using 'gcloud config set project YOUR_PROJECT_ID'"
    exit 1
fi

if [ -z "$GCF_FUNCTION_NAME_ENV_VAR" ]; then
    echo "Error: Environment variable GCF_FUNCTION_NAME_ENV_VAR is not set."
    # ...
    exit 1
fi

if [ -z "$GCF_REGION_ENV_VAR" ]; then
    echo "Error: Environment variable GCF_REGION_ENV_VAR is not set."
    # ...
    exit 1
fi

ENTRY_POINT="process_image_for_transformation"
RUNTIME="python312"
SOURCE_DIR="./image_processor_func"
SECRET_NAME_IN_SM="CLOUD_IMAGE_API_KEY" 
ENV_VAR_NAME_IN_FUNCTION="CLOUD_IMAGE_API_KEY"
REGION=${GCF_REGION_ENV_VAR}
FUNCTION_NAME=${GCF_FUNCTION_NAME_ENV_VAR}



gcloud functions deploy ${FUNCTION_NAME} \
  --gen2 \
  --runtime ${RUNTIME} \
  --region ${REGION} \
  --source ${SOURCE_DIR} \
  --entry-point ${ENTRY_POINT} \
  --trigger-http \
  --allow-unauthenticated \
  --set-secrets="${ENV_VAR_NAME_IN_FUNCTION}=projects/${PROJECT_ID}/secrets/${SECRET_NAME_IN_SM}/versions/latest"


EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
  echo "Function deployed successfully."
  # echo "Function URL: $(gcloud functions describe ${FUNCTION_NAME} --gen2 --project=${PROJECT_ID} --region=${REGION} --format='value(serviceConfig.uri)')"
else
  echo "Function deployment failed with exit code $EXIT_CODE."
fi
