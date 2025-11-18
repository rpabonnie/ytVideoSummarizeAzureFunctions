# Notion Integration Setup Guide

This guide walks you through configuring the Notion integration for the YouTube Video Summarizer Azure Function.

## Prerequisites

- A Notion account ([sign up here](https://www.notion.so/signup))
- Workspace Owner permissions (or ability to create integrations)
- Azure Key Vault access (for storing API key)

---

## Step 1: Create a Notion Integration

1. **Navigate to Notion Integrations Dashboard**
   - Go to [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
   - Click **"+ New integration"**

2. **Configure Integration Settings**
   - **Name**: `YouTube Video Summarizer` (or your preferred name)
   - **Associated workspace**: Select your target workspace
   - **Type**: Internal integration
   - **Capabilities**: 
     - ✅ Read content
     - ✅ Update content
     - ✅ Insert content

3. **Save and Get API Key**
   - Click **"Submit"** to create the integration
   - Go to the **"Secrets"** tab
   - Copy the **"Internal Integration Secret"** (this is your API key)
   - ⚠️ **Keep this secret safe!** Never commit it to version control

---

## Step 2: Store API Key in Azure Key Vault

### Local Development

```powershell
# Set your Key Vault name
$vaultName = "your-keyvault-name"

# Store the Notion API key
az keyvault secret set `
  --vault-name $vaultName `
  --name "NOTION-API-KEY" `
  --value "secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### Production (Azure Portal)

1. Navigate to your Azure Key Vault
2. Go to **Secrets** → **+ Generate/Import**
3. **Name**: `NOTION-API-KEY`
4. **Value**: Paste your Notion integration secret
5. Click **"Create"**

---

## Step 3: Create or Select Target Database

### Option A: Create New Database

1. In Notion, create a new page or open an existing one
2. Type `/database` and select **"Database - Inline"**
3. Name it **"YouTube Summaries"** (or your preferred name)
4. Add the following properties (columns):

| Property Name       | Type          | Description                          |
|---------------------|---------------|--------------------------------------|
| Title               | Title         | Video title (auto-created)           |
| Tags                | Multi-select  | Video topic tags                     |
| URL                 | URL           | YouTube video link                   |
| Brief Summary       | Text          | Short summary paragraph              |
| Summary Points      | Text          | Bullet point summary                 |
| Tools & Tech        | Text          | Technologies mentioned in video      |

### Option B: Use Existing Database

Ensure your database has compatible properties. The integration will map fields based on `notion_config.json`.

---

## Step 4: Grant Integration Access to Database

⚠️ **Critical Step**: Integrations can only access pages/databases explicitly shared with them.

1. **Open your database as a full page**
   - Click the database title to open it in full page view

2. **Share with Integration**
   - Click the **`•••`** menu (top-right corner)
   - Scroll down to **"Connections"**
   - Click **"+ Add connection"**
   - Search for your integration name (e.g., "YouTube Video Summarizer")
   - Click to add the connection
   - Confirm the integration can access this page and all child pages

---

## Step 5: Get Database ID

1. **Open database as full page** (if not already)
2. **Copy page link**
   - Click **Share** → **Copy link**
   - Or copy URL from browser address bar

3. **Extract Database ID**
   - URL format: `https://www.notion.so/{workspace}/{database_id}?v={view_id}`
   - Example: `https://www.notion.so/myworkspace/a1b2c3d4e5f6?v=123456`
   - Database ID: `a1b2c3d4e5f6` (32 characters, may include hyphens)

4. **Copy the Database ID** (you'll need it for the next step)

> 💡 **Tip**: The database ID is the 32-character string between the workspace name and `?v=` in the URL.

---

## Step 6: Configure `notion_config.json`

1. **Copy example config**
   ```powershell
   Copy-Item notion_config.example.json notion_config.json
   ```

2. **Edit `notion_config.json`**
   ```json
   {
     "database_id": "PASTE_YOUR_DATABASE_ID_HERE",
     "database_name": "YouTube Summaries",
     "property_mapping": {
       "title": "Title",
       "tags": "Tags",
       "url": "URL",
       "brief_summary": "Brief Summary",
       "summary_bullets": "Summary Points",
       "tools_and_technologies": "Tools & Tech"
     }
   }
   ```

3. **Paste your Database ID**
   - Replace `PASTE_YOUR_DATABASE_ID_HERE` with the ID from Step 5

4. **Customize property mapping** (optional)
   - If your database uses different property names, update the mappings
   - Example: Change `"Tags"` to `"Categories"` if that's your column name

---

## Step 7: Configure Azure Function App (Production)

### Grant Managed Identity Access to Key Vault

```powershell
# Get Function App's Managed Identity
$functionApp = "your-function-app-name"
$resourceGroup = "your-resource-group"

# Enable system-assigned managed identity
az functionapp identity assign `
  --name $functionApp `
  --resource-group $resourceGroup

# Get the identity's object ID
$identityId = az functionapp identity show `
  --name $functionApp `
  --resource-group $resourceGroup `
  --query principalId `
  --output tsv

# Grant Key Vault access
az keyvault set-policy `
  --name $vaultName `
  --object-id $identityId `
  --secret-permissions get list
```

---

## Step 8: Test the Integration

### Local Testing

```powershell
# Start the function locally
func start

# Test with curl or PowerShell
$body = @{
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://localhost:7071/api/ytSummarizeToNotion" `
  -Method Post `
  -Body $body `
  -ContentType "application/json"
```

### Expected Response

```json
{
  "status": "success",
  "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "summary": {
    "title": "Video Title",
    "tags": ["tag1", "tag2"],
    ...
  },
  "notion_url": "https://notion.so/workspace/page-id",
  "notion_success": true
}
```

### Verify in Notion

1. Open your Notion database
2. Verify a new page was created
3. Check that properties are populated correctly
4. Open the page to see the formatted summary content

---

## Troubleshooting

### "Notion integration failed" Error

**Possible Causes:**

1. ❌ **Integration not connected to database page**
   - **Solution**: Repeat Step 4 (Grant Integration Access)

2. ❌ **Invalid Database ID in `notion_config.json`**
   - **Solution**: Verify Database ID matches URL (Step 5)

3. ❌ **API key not in Key Vault**
   - **Solution**: Verify `NOTION-API-KEY` secret exists (Step 2)

4. ❌ **Key Vault permissions missing**
   - **Solution**: Check Managed Identity has `get` and `list` permissions (Step 7)

5. ❌ **Property name mismatch**
   - **Solution**: Ensure `property_mapping` in config matches your database columns

### Check Logs

**Local:**
```powershell
# Function logs will show detailed errors
func start --verbose
```

**Production:**
```powershell
# View Application Insights logs
az monitor app-insights query `
  --app your-app-insights-name `
  --analytics-query "traces | where message contains 'Notion' | order by timestamp desc | take 20"
```

### Common Error Messages

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `notion_config.json not found` | Config file missing | Create config from example file |
| `database_id not configured` | Database ID placeholder not replaced | Add your actual database ID |
| `Failed to retrieve Notion API key` | Key Vault authentication failed | Run `az login` or check Managed Identity |
| `No URL returned from Notion API` | API call succeeded but response unexpected | Check Notion API version |

---

## iOS Shortcuts Configuration

When calling this function from iOS Shortcuts:

1. **Endpoint URL**: `https://your-function-app.azurewebsites.net/api/ytSummarizeToNotion`

2. **Headers**:
   - `Content-Type`: `application/json`
   - `x-functions-key`: `<your-function-key>` (get from Azure Portal → Function App → App Keys)

3. **Body** (JSON):
   ```json
   {
     "url": "<youtube-url-from-share-sheet>"
   }
   ```

4. **Security Note**: 
   - The function key grants access to the Azure Function endpoint only
   - Notion API key remains secure in Azure Key Vault
   - No OAuth flow required (internal integration)

### Sample iOS Shortcut Setup

1. **Get Contents of URL** action:
   - URL: `https://your-function-app.azurewebsites.net/api/ytSummarizeToNotion`
   - Method: `POST`
   - Headers: Add `x-functions-key` and `Content-Type`
   - Request Body: `JSON` with `url` field

2. **Show Result** action:
   - Display the `notion_url` from the response

---

## Next Steps

After successful testing:
- ✅ Add more videos to test edge cases
- ✅ Customize database properties as needed
- ✅ Set up Application Insights monitoring
- ✅ Configure email notifications (future phase)
- ✅ Create iOS Shortcut for quick video saves

---

## Property Customization Guide

You can customize the database properties to match your workflow:

### Example: Different Property Names

If your database uses Spanish column names:

```json
{
  "database_id": "your-database-id",
  "property_mapping": {
    "title": "Título",
    "tags": "Etiquetas",
    "url": "Enlace",
    "brief_summary": "Resumen Breve",
    "summary_bullets": "Puntos Clave",
    "tools_and_technologies": "Herramientas"
  }
}
```

### Example: Simplified Properties

For a minimal database with just title and URL:

```json
{
  "database_id": "your-database-id",
  "property_mapping": {
    "title": "Name",
    "url": "Video Link"
  }
}
```

> ⚠️ **Note**: The `title` property is required. Other properties are optional.

---

## Resources

- [Notion API Documentation](https://developers.notion.com/docs)
- [Create a Notion Integration](https://developers.notion.com/docs/create-a-notion-integration)
- [Working with Databases](https://developers.notion.com/docs/working-with-databases)
- [Azure Key Vault Best Practices](https://learn.microsoft.com/azure/key-vault/general/best-practices)
- [Azure Functions Python Guide](https://learn.microsoft.com/azure/azure-functions/functions-reference-python)

---

## Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section above
2. Review function logs for detailed error messages
3. Open an issue on the [GitHub repository](https://github.com/rpabonnie/ytVideoSummarizeAzureFunctions)

---

**Last Updated:** November 17, 2025
