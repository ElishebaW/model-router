#!/usr/bin/env bash
# ─── Google Cloud Run Deployment Script ───
set -e

PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "your-gcp-project-id")
REGION="us-central1"

echo "=========================================="
echo " Deploying GenAI Model Router to Cloud Run"
echo " Project ID: $PROJECT_ID"
echo " Region: $REGION"
echo "=========================================="

# 1. Build and Deploy Backend Service
echo "Step 1: Building & Deploying FastAPI Backend..."
gcloud run deploy model-router-backend \
  --source ./backend \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_MODEL="google/gemini-2.5-flash",HUGGINGFACE_MODEL="Qwen/Qwen2.5-7B-Instruct"

BACKEND_URL=$(gcloud run services describe model-router-backend --region $REGION --format='value(status.url)')
echo "Backend deployed successfully at: $BACKEND_URL"

# 2. Build and Deploy Frontend Service
echo "Step 2: Building & Deploying Next.js Frontend..."
gcloud run deploy model-router-frontend \
  --source ./frontend \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars NEXT_PUBLIC_BACKEND_URL="$BACKEND_URL"

FRONTEND_URL=$(gcloud run services describe model-router-frontend --region $REGION --format='value(status.url)')

echo "=========================================="
echo " Deployment Complete!"
echo " Frontend URL: $FRONTEND_URL"
echo " Backend URL:  $BACKEND_URL"
echo "=========================================="
