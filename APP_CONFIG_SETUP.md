# Azure App Configuration Setup Guide

This guide explains how to set up **Azure App Configuration** for centralized configuration management of your YouTube Video Summarizer function.

## Why Use Azure App Configuration?

**Benefits:**
- ✅ **No Redeployment Required**: Update Notion settings without redeploying the function
- ✅ **Centralized Management**: Manage all configuration in one place
- ✅ **Version Control**: Track configuration changes over time
- ✅ **Environment Management**: Different configs for dev, staging, production
- ✅ **Dynamic Updates**: Changes take effect on next function execution
- ✅ **Fallback Support**: Automatically falls back to local `notion_config.json` if App Configuration is unavailable

---

## Prerequisites

- Azure Subscription
- Azure CLI installed (`az --version`)
- Existing Azure Function App deployed
- Notion configuration ready (see [NOTION_SETUP.md](./NOTION_SETUP.md))

---

## Setup Steps

### 1. Create Azure App Configuration Store

```powershell
# Set variables
$resourceGroup = "your-resource-group"
$location = "eastus"
$appConfigName = "yt-summarizer-config"  # Must be globally unique

# Create App Configuration store
az appconfig create `
  --name $appConfigName `
  --resource-group $resourceGroup `
  --location $location `
  --sku Free
```

**Note:** The Free tier provides:
- 1,000 requests per day
- 10 MB storage
- Perfect for this use case

---

### 2. Add Notion Configuration to App Configuration

You can add configuration via Azure Portal or CLI.

#### Option A: Using Azure Portal

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to your App Configuration store
3. Click **Configuration explorer** → **+ Create** → **Key-value**
4. Set the following:
   - **Key**: `notion_config`
   - **Value**: Copy the entire contents of your `notion_config.json`
   - **Content type**: `application/json` (optional)
5. Click **Apply**

#### Option B: Using Azure CLI

```powershell
# Set your App Configuration name
$appConfigName = "yt-summarizer-config"

# Create JSON configuration (all on one line, properly escaped)
$notionConfig = '{\"database_id\":\"YOUR_DATABASE_ID\",\"database_name\":\"YouTube Summaries\",\"property_mapping\":{\"title\":[\"Title\",\"Source\"],\"tags\":\"Tags\",\"url\":\"URL\"},\"static_properties\":{\"content_type\":{\"property_name\":\"Content Type\",\"value\":\"Video\"}},\"content_sections\":{\"brief_summary\":{\"heading\":\"Overview\",\"field\":\"brief_summary\"},\"summary_bullets\":{\"heading\":\"Summary\",\"field\":\"summary_bullets\"},\"tools_and_technologies\":{\"heading\":\"Tools & Technologies\",\"field\":\"tools_and_technologies\"}}}'

# Add to App Configuration
az appconfig kv set `
  --name $appConfigName `
  --key "notion_config" `
  --value $notionConfig `
  --content-type "application/json" `
  --yes
```

**Important:** Replace `YOUR_DATABASE_ID` with your actual Notion database ID.

---

### 3. Get Connection String

```powershell
# Get connection string
az appconfig credential list `
  --name $appConfigName `
  --resource-group $resourceGroup `
  --query "[?name=='Primary'].connectionString" `
  --output tsv
```

Copy the connection string - you'll need it in the next step.

---

### 4. Configure Azure Function App

Add the App Configuration connection string to your Function App settings:

```powershell
# Set your Function App name
$functionAppName = "your-function-app-name"

# Add App Configuration connection string
az functionapp config appsettings set `
  --name $functionAppName `
  --resource-group $resourceGroup `
  --settings "APP_CONFIG_CONNECTION_STRING=<paste-connection-string-here>"
```

---

### 5. Local Development Setup

For local testing, update your `local.settings.json`:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "KEY_VAULT_URL": "https://your-keyvault.vault.azure.net/",
    "APP_CONFIG_CONNECTION_STRING": "Endpoint=https://yt-summarizer-config.azconfig.io;Id=xxx;Secret=xxx"
  }
}
```

---

## How It Works

### Configuration Loading Priority

The `ConfigService` loads Notion configuration in this order:

1. **Memory Cache** (if configuration already loaded)
2. **Azure App Configuration** (if `APP_CONFIG_CONNECTION_STRING` is set)
3. **Local File** (`notion_config.json` - fallback for development)

### Example Flow

```
Request → ConfigService.get_notion_config()
          ↓
          Check cache? Yes → Return cached config
          ↓
          No → Try Azure App Configuration
          ↓
          Success? Yes → Cache and return
          ↓
          No → Try local notion_config.json
          ↓
          Success? Yes → Cache and return
          ↓
          No → Raise ValueError
```

---

## Updating Configuration

### Update Notion Settings Without Redeployment

```powershell
# Update a specific setting (e.g., change database_id)
az appconfig kv set `
  --name $appConfigName `
  --key "notion_config" `
  --value '<updated-json-config>' `
  --content-type "application/json" `
  --yes
```

**Changes take effect:**
- Immediately on next function execution
- No redeployment required
- Cache is per-function-instance, so cold starts get new config

---

## Testing

### 1. Verify Configuration in Azure

```powershell
# List all keys
az appconfig kv list --name $appConfigName

# Get specific configuration
az appconfig kv show `
  --name $appConfigName `
  --key "notion_config"
```

### 2. Test Function Locally

```powershell
# Ensure APP_CONFIG_CONNECTION_STRING is in local.settings.json
func host start

# Test with a YouTube URL
$body = @{ url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:7071/api/ytSummarizeToNotion" `
  -Method Post `
  -Body $body `
  -ContentType "application/json"
```

Check the logs for:
```
ConfigService initialized with Azure App Configuration
Loading configuration 'notion_config' from Azure App Configuration
Successfully loaded 'notion_config' from App Configuration
```

### 3. Test Fallback to Local File

```powershell
# Remove APP_CONFIG_CONNECTION_STRING temporarily
# In local.settings.json, comment out or remove the line

func host start

# Same test as above
```

Check the logs for:
```
ConfigService initialized in local-only mode
Loaded configuration from local file: .../notion_config.json
```

---

## Production Checklist

- [ ] App Configuration store created
- [ ] Connection string added to Function App settings
- [ ] Notion configuration uploaded to App Configuration
- [ ] Test in production environment
- [ ] Verify configuration updates work without redeployment
- [ ] Keep `notion_config.json` as backup in repository

---

## Troubleshooting

### Error: "Failed to initialize App Configuration client"

**Cause:** Invalid connection string or App Configuration not accessible

**Solution:**
1. Verify connection string is correct
2. Check network connectivity
3. Ensure App Configuration resource exists
4. Function will automatically fall back to local `notion_config.json`

### Error: "Configuration key 'notion_config' not found"

**Cause:** Key not added to App Configuration

**Solution:**
```powershell
# Add the missing key
az appconfig kv set `
  --name $appConfigName `
  --key "notion_config" `
  --value '<your-notion-config-json>' `
  --yes
```

### Configuration Not Updating

**Cause:** Configuration is cached per function instance

**Solution:**
- Wait for function to cold start (automatic after ~20 minutes of inactivity)
- Or restart the Function App:
```powershell
az functionapp restart --name $functionAppName --resource-group $resourceGroup
```

---

## Cost Considerations

**Free Tier Limits:**
- 1,000 requests/day
- 10 MB storage

**For this application:**
- Each function execution = 1 request (cached afterward)
- Configuration size = ~1 KB
- **Cost:** $0 (within free tier for typical usage)

---

## Security Best Practices

✅ **DO:**
- Use connection strings with read-only access
- Store connection string in Azure Function App settings (encrypted)
- Keep `notion_config.json` as fallback
- Use App Configuration for non-sensitive configuration only

❌ **DON'T:**
- Don't store API keys or secrets in App Configuration (use Key Vault instead)
- Don't commit connection strings to source control
- Don't share connection strings publicly

---

## Next Steps

- ✅ Configuration is now centralized and easily updatable
- 📖 See [LOGIC_APPS_SETUP.md](./LOGIC_APPS_SETUP.md) for webhook integration
- 📖 See [NOTION_SETUP.md](./NOTION_SETUP.md) for Notion configuration details

---

## Additional Resources

- [Azure App Configuration Documentation](https://learn.microsoft.com/azure/azure-app-configuration/)
- [Python SDK Documentation](https://learn.microsoft.com/python/api/overview/azure/appconfiguration-readme)
- [Best Practices](https://learn.microsoft.com/azure/azure-app-configuration/howto-best-practices)
