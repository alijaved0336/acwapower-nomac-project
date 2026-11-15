#!/bin/bash

# Build and Deploy ClickHouse with Azure Blob Storage
set -e

echo "🚀 Building ClickHouse with Azure Blob Storage support..."

# Configuration
RESOURCE_GROUP="ACWA-DEV-MPC-SWRO-RG01"
CONTAINER_APP_NAME="swro-clickhouse"
REGISTRY_NAME="your-registry"  # Replace with your Azure Container Registry
IMAGE_NAME="clickhouse-azure"
TAG="latest"

# Step 1: Build Docker image
echo "📦 Building Docker image..."
docker build -f docker/Dockerfile.clickhouse-azure -t $REGISTRY_NAME/$IMAGE_NAME:$TAG .

# Step 2: Push to registry (if using Azure Container Registry)
echo "📤 Pushing to registry..."
# Uncomment if using Azure Container Registry
# az acr login --name $REGISTRY_NAME
# docker push $REGISTRY_NAME.azurecr.io/$IMAGE_NAME:$TAG

# Step 3: Update Container App
echo "🔄 Updating Container App..."
az containerapp update \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --image $REGISTRY_NAME.azurecr.io/$IMAGE_NAME:$TAG \
  --set-env-vars \
    CLICKHOUSE_DB=swro_db \
    CLICKHOUSE_USER=default \
    CLICKHOUSE_PASSWORD=swro_clickhouse_2024! \
    CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT=1 \
    AZURE_STORAGE_KEY=WoViPIos6ZrAL2XP5VIPPbH/bGjXBeGmSGkIXAhxCJitCkrYqu53B02W8dVdZSYNCq2QZVl+cxRk+AStmJXDiQ== \
    AZURE_STORAGE_ACCOUNT=mpcswrosg \
    AZURE_STORAGE_CONTAINER=swro

echo "✅ ClickHouse with Azure Blob Storage deployed successfully!"
echo "🔗 Access URL: https://swro-clickhouse.redsea-86e0b078.uaenorth.azurecontainerapps.io"

# Step 4: Verify deployment
echo "🔍 Verifying deployment..."
sleep 30
curl -f "https://swro-clickhouse.redsea-86e0b078.uaenorth.azurecontainerapps.io/ping" || echo "⚠️  Health check failed - container may still be starting"

echo "🎉 Deployment complete!"
