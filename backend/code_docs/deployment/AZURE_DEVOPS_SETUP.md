# Azure DevOps Environment Variables Setup Guide

## Overview
This guide explains how to set up environment variables for the SWRO Backend project in Azure DevOps pipelines to fix the "Failed to save user data" error.

## Method 1: Variable Groups (Recommended)

### Step 1: Create Variable Group in Azure DevOps

1. **Navigate to Azure DevOps**
   - Go to your Azure DevOps project
   - Click on **Pipelines** in the left sidebar
   - Click on **Library**

2. **Create New Variable Group**
   - Click **+ Variable group**
   - Name: `SWRO-Backend-Variables`
   - Description: `Environment variables for SWRO Backend application`

3. **Add Variables**
   Add the following variables to your variable group:

   | Variable Name | Value | Secret |
   |---------------|-------|--------|
   | `SECRET_KEY` | `your-production-secret-key-here-make-it-long-and-random` | ✅ Yes |
   | `AZURE_CLIENT_ID` | `53db1bb7-a463-4375-886c-6c0365bd5597` | ❌ No |
   | `AZURE_CLIENT_SECRET` | `your-azure-client-secret-from-app-registration` | ✅ Yes |
   | `AZURE_TENANT_ID` | `aede0578-b8b7-471d-aae3-3e17057bc657` | ❌ No |
   | `JWT_SECRET` | `your-jwt-secret-key-different-from-django-secret` | ✅ Yes |
   | `DELTALAKE_USERS_TABLE_PATH` | `/home/site/wwwroot/data/users` | ❌ No |
   | `DEBUG` | `False` | ❌ No |
   | `ALLOWED_HOSTS` | `mpc-swro-be.azurewebsites.net,localhost,127.0.0.1` | ❌ No |
   | `SERVER_HOSTNAME` | `adb-2063907838277345.5.azuredatabricks.net` | ❌ No |
   | `HTTP_PATH` | `/sql/1.0/warehouses/c94a7333a50caec4` | ❌ No |
   | `ACCESS_TOKEN` | `dapiea1e29cc7b558e48cf98b91c3f12ff38` | ✅ Yes |

   **Important Notes:**
   - Mark `SECRET_KEY`, `AZURE_CLIENT_SECRET`, and `JWT_SECRET` as **secret variables**
   - Use the lock icon to mark variables as secret
   - Secret variables will be masked in logs

### Step 2: Generate Secure Keys

Use these commands to generate secure keys:

```bash
# For Django SECRET_KEY (50 characters)
python -c "import secrets; print(secrets.token_urlsafe(50))"

# For JWT_SECRET (32 characters)
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 3: Set Permissions

1. In your variable group, click **Security**
2. Add your pipeline service principal with **User** permissions
3. Add your development team with appropriate permissions

## Method 2: Pipeline Variables (Alternative)

If you prefer to set variables directly in the pipeline:

1. Go to your pipeline
2. Click **Edit**
3. Click **Variables** (top right)
4. Add each variable individually
5. Mark sensitive variables as **secret**

## Method 3: Azure Key Vault Integration (Most Secure)

For production environments, consider using Azure Key Vault:

1. **Create Azure Key Vault**
   ```bash
   az keyvault create --name swro-backend-kv --resource-group your-rg --location eastus
   ```

2. **Add Secrets to Key Vault**
   ```bash
   az keyvault secret set --vault-name swro-backend-kv --name SECRET-KEY --value "your-secret-key"
   az keyvault secret set --vault-name swro-backend-kv --name AZURE-CLIENT-SECRET --value "your-client-secret"
   az keyvault secret set --vault-name swro-backend-kv --name JWT-SECRET --value "your-jwt-secret"
   ```

3. **Update Variable Group**
   - Link your variable group to Azure Key Vault
   - Map Key Vault secrets to pipeline variables

## Verification Steps

### Step 1: Check Pipeline Logs

After setting up variables, run your pipeline and check the logs:

1. Look for environment variable values in the Django system check step
2. Ensure no variables show as `$(VARIABLE_NAME)` (unresolved)
3. Secret variables should show as `***` in logs

### Step 2: Test the Auth Endpoint

Once deployed, test the `/auth/verify/` endpoint:

```bash
curl -X POST https://mpc-swro-be.azurewebsites.net/auth/verify/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@acwapower.com",
    "sub": "test@acwapower.com",
    "picture": null
  }'
```

Expected response:
```json
{
  "message": "Authentication successful",
  "user": { ... },
  "token": "...",
  "refresh_token": "..."
}
```

### Step 3: Check Application Logs

In Azure App Service:
1. Go to **App Service** → **Log stream**
2. Or check **Monitoring** → **App Service logs**
3. Look for successful user save messages

## Troubleshooting

### Common Issues:

1. **Variable Group Not Found**
   - Ensure variable group name matches exactly in `azure-pipelines.yml`
   - Check permissions on the variable group

2. **Variables Not Resolved**
   - Variables show as `$(VARIABLE_NAME)` in logs
   - Check variable group linking in pipeline

3. **Permission Errors**
   - `DELTALAKE_USERS_TABLE_PATH` directory not writable
   - Update path to `/home/site/wwwroot/data/users` for Azure App Service

4. **Missing Dependencies**
   - Ensure `deltalake` and `pandas` are in `requirements.txt`
   - Check if packages install correctly during deployment

### Debug Commands:

Add this temporary step to your pipeline for debugging:

```yaml
- script: |
    echo "Environment variables check:"
    echo "SECRET_KEY length: ${#SECRET_KEY}"
    echo "AZURE_TENANT_ID: $AZURE_TENANT_ID"
    echo "DELTALAKE_USERS_TABLE_PATH: $DELTALAKE_USERS_TABLE_PATH"
    echo "DEBUG: $DEBUG"
    echo "SERVER_HOSTNAME: $SERVER_HOSTNAME"
    echo "HTTP_PATH: $HTTP_PATH"
    echo "ACCESS_TOKEN length: ${#ACCESS_TOKEN}"
  displayName: 'Debug Environment Variables'
  env:
    SECRET_KEY: $(SECRET_KEY)
    AZURE_TENANT_ID: $(AZURE_TENANT_ID)
    DELTALAKE_USERS_TABLE_PATH: $(DELTALAKE_USERS_TABLE_PATH)
    DEBUG: $(DEBUG)
    SERVER_HOSTNAME: $(SERVER_HOSTNAME)
    HTTP_PATH: $(HTTP_PATH)
    ACCESS_TOKEN: $(ACCESS_TOKEN)
```

## Security Best Practices

1. **Never commit secrets to code**
   - Use `.env.example` for templates only
   - Add `.env` to `.gitignore`

2. **Rotate secrets regularly**
   - Update Azure AD client secrets before expiry
   - Generate new JWT secrets periodically

3. **Use least privilege access**
   - Limit variable group permissions
   - Use managed identities where possible

4. **Monitor secret usage**
   - Enable Azure Key Vault logging
   - Monitor pipeline variable access

## Next Steps

After setting up environment variables:

1. **Test locally** with production-like settings
2. **Deploy to staging** environment first
3. **Monitor logs** for any remaining issues
4. **Set up monitoring** and alerts for the application

## Support

If you encounter issues:

1. Check the enhanced error messages in the updated controller
2. Review Azure App Service logs
3. Verify all environment variables are set correctly
4. Test the endpoint with the provided curl command
