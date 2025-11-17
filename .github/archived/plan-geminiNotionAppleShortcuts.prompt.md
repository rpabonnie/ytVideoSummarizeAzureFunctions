# Plan: Setup Gemini & Notion APIs with Apple Shortcuts Authentication

Configure Azure Function to accept YouTube video URLs from Apple Shortcuts, use Gemini's native video processing (no YouTube library needed), access secrets from your existing Azure Key Vault, and secure the endpoint for mobile access.

## Implementation Status

### ✅ Completed Steps

1. **✅ Add Python dependencies** - All required packages are in [`requirements.txt`](c:\Users\rpabo\source\repos\ytVideoSummarizeAzureFunction\requirements.txt):
   - `google-generativeai` for Gemini API
   - `notion-client` for Notion integration
   - `azure-identity` and `azure-keyvault-secrets` for secure Key Vault access
   - No YouTube library needed (Gemini processes videos directly)

2. **✅ Configure local settings** in [`local.settings.json`](c:\Users\rpabo\source\repos\ytVideoSummarizeAzureFunction\local.settings.json):
   - Generated secure GUID for admin key: `021dd70d-eeb5-42c8-911a-b72b96984f6e`
   - Set `KEY_VAULT_URL` to `https://rpc-personal-secrets.vault.azure.net/`
   - Configured AzureFunctionsJobHost with admin authentication
   - Added CORS and LocalHttpPort settings

3. **✅ Update function code** in [`function_app.py`](c:\Users\rpabo\source\repos\ytVideoSummarizeAzureFunction\function_app.py):
   - ✅ Accepts JSON POST requests with `url` field
   - ✅ Validates YouTube URL format (youtube.com or youtu.be)
   - ✅ Uses `DefaultAzureCredential` + `SecretClient` for secure Key Vault access
   - ✅ Retrieves `GEMINI-API-KEY` from Azure Key Vault
   - ✅ Sends YouTube URL directly to Gemini for video summarization
   - ✅ Comprehensive error handling and logging
   - ✅ Returns JSON-formatted summary with proper structure
   - ⏳ Notion integration pending (as per step 3b)

4. **✅ Security Implementation:**
   - Function requires ADMIN authentication via `x-functions-key` header
   - All API keys stored in Azure Key Vault (not in code)
   - Input validation prevents malicious URLs
   - Detailed error logging for troubleshooting
   - Azure CLI authentication required for local development

5. **✅ Testing Setup:**
   - Function running at: `http://localhost:7071/api/ytSummarizeToNotion`
   - Created [`TESTING.md`](c:\Users\rpabo\source\repos\ytVideoSummarizeAzureFunction\TESTING.md) with Postman instructions
   - Ready for testing with admin key authentication

### 🔄 Current Development Phase

**Step 3b - Testing and Verification:**
- The implementation is complete up to the outlined stopping point
- Function accepts YouTube URLs and generates summaries using Gemini
- Summaries are logged to console for verification
- Gemini prompt formatted to return JSON structure compatible with Notion API
- Development paused before Notion integration (as specified)

### ⏳ Pending Steps

6. **⏳ Configure Apple Shortcuts** to make POST request to function endpoint with custom header `x-functions-key` containing the admin key (retrieved from Azure Portal after deployment), and JSON body containing YouTube URL

7. **⏳ Implement Notion Integration:**
   - Retrieve `NOTION-API-KEY` from Key Vault
   - Create Notion page with summarized content
   - Return Notion page URL in response

8. **⏳ Deploy to Azure:**
   - Set up managed identity for Key Vault access
   - Deploy function app
   - Configure production admin key
   - Test with Apple Shortcuts from mobile device

## Technical Details

### Security Architecture
- **Authentication:** Admin-level function key required (HTTP header: `x-functions-key`)
- **Secrets Management:** Azure Key Vault with DefaultAzureCredential
- **Local Development:** Azure CLI authentication (`az login`)
- **Production:** Managed Identity for Key Vault access

### API Request Format
```json
POST http://localhost:7071/api/ytSummarizeToNotion
Headers:
  x-functions-key: 021dd70d-eeb5-42c8-911a-b72b96984f6e
  Content-Type: application/json

Body:
{
  "url": "https://www.youtube.com/watch?v=videoid"
}
```

### API Response Format
```json
{
  "status": "success",
  "youtube_url": "https://www.youtube.com/watch?v=...",
  "summary": {
    "title": "Video Title",
    "tags": ["tag1", "tag2"],
    "summary_bullets": ["point1", "point2"],
    "brief_summary": "Overview text",
    "tools_and_technologies": [
      {"tool": "name", "purpose": "description"}
    ]
  },
  "note": "Video summarized successfully. Notion integration pending."
}
```

### Gemini Prompt Strategy
The implementation uses a structured prompt that:
- Instructs Gemini to analyze the YouTube video
- Requests JSON output in Notion-compatible format
- Focuses on key takeaways, concepts, and practical applications
- Extracts title, tags, bullet points, and tools/technologies

## Further Considerations

1. **✅ Function key retrieval** - Admin key auto-generated for local testing; production key will be generated on Azure deployment

2. **✅ Alternative auth for mobile** - Using function-level admin key in `x-functions-key` header (simple, works well with Apple Shortcuts)

3. **✅ Local admin key format** - Generated GUID `021dd70d-eeb5-42c8-911a-b72b96984f6e` using PowerShell `New-Guid`

4. **New: Testing Checklist**
   - ✅ Function starts without errors
   - ✅ Admin authentication configured
   - ✅ Key Vault connection ready
   - ⏳ Test with real YouTube URL in Postman
   - ⏳ Verify Gemini summary quality
   - ⏳ Validate JSON structure matches Notion requirements

## Next Actions

1. **Test the function** using Postman or PowerShell (see [`TESTING.md`](c:\Users\rpabo\source\repos\ytVideoSummarizeAzureFunction\TESTING.md))
2. **Verify Gemini output** - Check if summaries are well-formatted and useful
3. **Iterate on prompt** if needed to improve summary quality
4. **Proceed to Notion integration** once Gemini output is validated

---

**Last Updated:** November 16, 2025  
**Status:** ✅ Ready for testing - Function running locally with secure Key Vault integration
