# Plan: Setup Gemini & Notion APIs with Apple Shortcuts Authentication

Configure Azure Function to accept YouTube video URLs from Apple Shortcuts, use Gemini's native video processing (no YouTube library needed), access secrets from your existing Azure Key Vault, and secure the endpoint for mobile access.

## Steps

1. **Add Python dependencies** to [`requirements.txt`](c:\Users\rpabo\source\repos\ytVideoSummarizeAzureFunction\requirements.txt) for Gemini (`google-generativeai`), Notion (`notion-client`), and Azure Key Vault (`azure-identity`, `azure-keyvault-secrets`) - no YouTube library needed since Gemini processes videos directly

2. **Configure local settings** in [`local.settings.json`](c:\Users\rpabo\source\repos\ytVideoSummarizeAzureFunction\local.settings.json) by adding generated GUID for `AzureFunctionsJobHost__functions__ytSummarizeToNotion__authLevel__masterKey`, `KEY_VAULT_URL` set to `https://rpc-personal-secrets.vault.azure.net/`, and placeholder values for `NOTION_API_KEY` and `GEMINI_API_KEY` for local testing
3. **Update function code** in [`ytSummarizeToNotion.py`](c:\Users\rpabo\source\repos\ytVideoSummarizeAzureFunction\ytSummarizeToNotion.py) to accept JSON body with `url` field, load secrets using `DefaultAzureCredential` + `SecretClient`, send YouTube URL directly to Gemini for video summarization, and create Notion page with results
3a. The implementation will be a step-by-step process:
   - Parse incoming JSON for YouTube URL
   - Use `DefaultAzureCredential` to authenticate with Azure Key Vault
   -  `GEMINI-API-KEY` from Key Vault
   - Call Gemini API with the YouTube URL to get the summary.
   - We need to develop a prompt for Gemini to summarize the video content effectively.
   - The prompt needs to format the result in a JSON structure that is compatible with Notion's API for easy page creation. Including title, tags, summay in bullet points and a breif summary of tools used by the author and what they where used for.
   - log the resulting summary in the console for verification and test if the summary is generated correctly.
3b. development will stop there for now.
5. I've already stored the Gemini api key and Notion api key in the Key vault.

6. **Configure Apple Shortcuts** to make POST request to function endpoint with custom header `x-functions-key` containing the admin key (retrieved from Azure Portal after deployment), and JSON body containing YouTube URL

## Further Considerations

1. **Function key retrieval?** Admin key will be auto-generated on first deployment - retrieve via Azure Portal under Function App → App Keys → `_master` key, or use `az functionapp keys list` command

2. **Alternative auth for mobile?** Option A: Use function-level admin key in `x-functions-key` header (simple, works well with Shortcuts) / Option B: Implement custom token validation / Option C: Use Azure API Management in front for OAuth

3. **Local admin key format?** Generate GUID using PowerShell `New-Guid` or use online generator, store as `AzureFunctionsJobHost__functions__ytSummarizeToNotion__authLevel__masterKey` in local settings for testing identical auth flow locally
