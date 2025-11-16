# Agent Instructions for ytVideoSummarizeAzureFunction

## Project Overview
This is an **Azure Functions** project built with **Python** using the Azure Functions v2 programming model. The project is designed to summarize YouTube videos and integrate with Notion (based on the function name `ytSummarizeToNotion`).

**Repository:** rpabonnie/ytVideoSummarizeAzureFunctions  
**Branch:** main  
**Runtime:** Python  
**Azure Functions Version:** v2 (programming model)

---

## Project Structure

```
ytVideoSummarizeAzureFunction/
├── function_app.py          # Main application entry point with function definitions
├── host.json                # Function app host configuration
├── local.settings.json      # Local development settings (not deployed)
├── requirements.txt         # Python dependencies
└── context/
    └── agent.md            # This file - Agent instructions
```

---

## Current Implementation Status

### Function: `ytSummarizeToNotion`
- **Trigger Type:** HTTP
- **Auth Level:** ADMIN (requires function key)
- **Route:** `ytSummarizeToNotion`
- **Current State:** Template/placeholder implementation
- **Expected Functionality:** Should summarize YouTube videos and save to Notion (not yet implemented)

---

## Development Guidelines

### 1. Python Environment Setup
- **Python Version:** Python 3.13 (hard requirement)
- **Virtual Environment:** Use `.venv` or Python virtual environment
- **Activation Command:** `.venv\Scripts\Activate.ps1` (PowerShell on Windows)

### 2. Installing Dependencies
```powershell
# Install all requirements
python -m pip install -r requirements.txt

# Install additional packages (add to requirements.txt)
python -m pip install <package-name>
```

### 3. Local Development & Testing

#### Running the Function Locally
Use the available VS Code task or terminal command:

**Option 1: VS Code Task**
- Task ID: `func: func: host start`
- This task automatically installs dependencies and starts the function host

**Option 2: Terminal Command**
```powershell
func host start
```

#### Testing the Function
```powershell
# Test with query parameter
Invoke-RestMethod -Uri "http://localhost:7071/api/ytSummarizeToNotion?name=Test" -Method Get

# Test with JSON body
$body = @{ name = "Test" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:7071/api/ytSummarizeToNotion" -Method Post -Body $body -ContentType "application/json"
```

### 4. Configuration Management

#### Local Settings (`local.settings.json`)
- **Purpose:** Stores local development configuration, environment variables, and secrets
- **Not deployed:** This file stays local (excluded from Git)
- **Required Settings:**
  - `AzureWebJobsStorage`: Connection string for Azure Storage (use `UseDevelopmentStorage=true` for local emulator)
  - `FUNCTIONS_WORKER_RUNTIME`: Set to `python`

#### Adding Environment Variables
Add to `local.settings.json` under `Values`:
```json
{
  "Values": {
    "NOTION_API_KEY": "your-notion-api-key",
    "GOOGLE_API_KEY": "your-google-gemini-api-key",
    "KEY_VAULT_URL": "https://your-keyvault.vault.azure.net/"
  }
}
```

### 5. Implementing the YouTube Summarization Feature

#### Required Dependencies (add to `requirements.txt`)
```
azure-functions
youtube-transcript-api  # For fetching YouTube transcripts
google-generativeai     # For AI summarization using Gemini
notion-client          # For Notion integration
azure-identity         # For Azure Key Vault authentication
azure-keyvault-secrets # For retrieving secrets from Azure Key Vault
python-dotenv          # For environment management
```

#### Implementation Steps

1. **Retrieve Secrets** from Azure Key Vault (Notion API key, Gemini API key)
4. **Send Video url and receive Summary of  Content** using Google Gemini
5. **Create Notion Page** with summary
6. **Return Success Response** with Notion page URL

#### Example Function Structure
```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

@app.route(route="ytSummarizeToNotion", methods=["POST"])
def ytSummarizeToNotion(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # 1. Get secrets from Azure Key Vault
        credential = DefaultAzureCredential()
        key_vault_url = os.environ.get("KEY_VAULT_URL")
        secret_client = SecretClient(vault_url=key_vault_url, credential=credential)
        
        notion_key = secret_client.get_secret("NOTION-API-KEY").value
        gemini_key = secret_client.get_secret("GOOGLE-API-KEY").value
        
        # 2. Parse request body to get YouTube URL
        req_body = req.get_json()
        video_url = req_body.get('url')  # Expected field: 'url'
        
        # 3. Validate input
        if not video_url:
            return func.HttpResponse("Missing url in request body", status_code=400)
        
        # 4. Extract video ID and fetch transcript
        # 5. Generate summary using Gemini
        # 6. Create Notion page
        # 7. Return response
        
        return func.HttpResponse(
            json.dumps({"status": "success", "notion_url": notion_url}),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return func.HttpResponse(str(e), status_code=500)
```

### 6. Code Organization Best Practices

#### Recommended Project Structure
```
ytVideoSummarizeAzureFunction/
├── function_app.py          # Function definitions only
├── services/
│   ├── __init__.py
│   ├── youtube_service.py   # YouTube API interactions
│   ├── summarizer.py        # AI summarization logic
│   └── notion_service.py    # Notion API interactions
├── models/
│   └── __init__.py
│   └── schemas.py           # Request/response models
├── utils/
│   └── __init__.py
│   └── validators.py        # Input validation
└── tests/
    └── test_function.py
```

### 7. Error Handling

Implement comprehensive error handling:
- **Invalid YouTube URL** → 400 Bad Request
- **Video not found or private** → 404 Not Found
- **Transcript unavailable** → 422 Unprocessable Entity
- **API key issues** → 401 Unauthorized
- **Notion integration failures** → 500 Internal Server Error
- **Rate limiting** → 429 Too Many Requests

### 8. Logging

Use Azure Functions built-in logging:
```python
import logging

logging.info("Processing video: {video_id}")
logging.warning("Transcript not available, using fallback")
logging.error("Failed to create Notion page: {error}")
```

### 9. Security Considerations

- **Never commit secrets** to Git
- **Use Azure Key Vault** for all secrets (Notion API key, Gemini API key)
- Configure **Managed Identity** for the Function App to access Key Vault
- Keep `AuthLevel.ADMIN` for sensitive operations
- Validate and sanitize all inputs (especially YouTube URLs)
- Implement rate limiting if needed
- Use HTTPS only in production

#### Setting up Azure Key Vault

1. **Create Key Vault:**
```powershell
az keyvault create --name <keyvault-name> --resource-group <rg-name> --location <location>
```

2. **Add Secrets:**
```powershell
az keyvault secret set --vault-name <keyvault-name> --name "NOTION-API-KEY" --value "<your-notion-key>"
az keyvault secret set --vault-name <keyvault-name> --name "GOOGLE-API-KEY" --value "<your-gemini-key>"
```

3. **Grant Function App Access:**
```powershell
# Enable managed identity for function app
az functionapp identity assign --name <app-name> --resource-group <rg-name>

# Grant access to Key Vault
az keyvault set-policy --name <keyvault-name> --object-id <function-app-identity> --secret-permissions get list
```

### 10. Deployment

#### Deploy to Azure
```powershell
# Login to Azure
az login

# Deploy function app
func azure functionapp publish <your-function-app-name>
```

#### Configure Application Settings in Azure
```powershell
# Set Key Vault URL
az functionapp config appsettings set --name <app-name> --resource-group <rg-name> --settings "KEY_VAULT_URL=https://<keyvault-name>.vault.azure.net/"

# Secrets are retrieved from Key Vault at runtime, not stored in app settings
```

### 11. Testing Strategy

- **Unit Tests:** Test individual services (YouTube, Summarizer, Notion)
- **Integration Tests:** Test complete workflow
- **Local Testing:** Use `func host start` and test endpoints
- **Mock External APIs:** Use mocks for YouTube/OpenAI/Notion in tests

### 12. Monitoring & Observability

- Enable **Application Insights** (already configured in `host.json`)
- Monitor function executions, failures, and performance
- Set up alerts for errors and performance degradation
- Track token usage for AI services

---

## Common Tasks Reference

### Adding a New HTTP Function
```python
@app.route(route="newFunction", methods=["GET", "POST"])
def newFunction(req: func.HttpRequest) -> func.HttpResponse:
    # Implementation
    pass
```

### Adding a Timer Trigger
```python
@app.schedule(schedule="0 */5 * * * *", arg_name="myTimer")
def timer_function(myTimer: func.TimerRequest) -> None:
    # Runs every 5 minutes
    pass
```

### Adding a Queue Trigger
```python
@app.queue_trigger(arg_name="msg", queue_name="myqueue", connection="AzureWebJobsStorage")
def queue_function(msg: func.QueueMessage) -> None:
    # Process queue message
    pass
```

---

## Environment Variables Checklist

Ensure these are configured:
- [ ] `AzureWebJobsStorage` - Azure Storage connection string
- [ ] `FUNCTIONS_WORKER_RUNTIME` - Set to `python`
- [ ] `KEY_VAULT_URL` - Azure Key Vault URL (e.g., https://your-vault.vault.azure.net/)
- [ ] `APPLICATIONINSIGHTS_CONNECTION_STRING` - For production monitoring

**Secrets stored in Azure Key Vault:**
- [ ] `NOTION-API-KEY` - Notion integration token (stored in Key Vault)
- [ ] `GOOGLE-API-KEY` - Google Gemini API key (stored in Key Vault)

---

## Troubleshooting

### Function not starting locally
- Ensure Python 3.13 is installed and activated
- Verify all dependencies are installed
- Check `local.settings.json` is properly configured
- Ensure Azure Functions Core Tools are installed
- For local development, authenticate with Azure CLI: `az login`
- **After major code changes:** Clear Python cache to avoid import errors:
  ```powershell
  Remove-Item -Path "__pycache__" -Recurse -Force -ErrorAction SilentlyContinue
  Remove-Item -Path "services\__pycache__" -Recurse -Force -ErrorAction SilentlyContinue
  Remove-Item -Path "utils\__pycache__" -Recurse -Force -ErrorAction SilentlyContinue
  ```

### Import errors
- Activate virtual environment
- Reinstall requirements: `pip install -r requirements.txt`
- Clear `__pycache__` directories after code refactoring

### Deployment failures
- Check Azure CLI authentication: `az account show`
- Verify function app exists and is running
- Check deployment logs

---

## Next Steps for Full Implementation

1. **Set up Azure Key Vault** and store Notion and Gemini API keys
2. **Install required packages** (youtube-transcript-api, google-generativeai, notion-client, azure-identity, azure-keyvault-secrets)
3. **Configure environment** with Python 3.13 and Key Vault URL in `local.settings.json`
4. **Implement Key Vault client** for secret retrieval
5. **Implement YouTube service** to fetch video transcripts from URL
6. **Implement summarization service** using Google Gemini
7. **Implement Notion service** to create pages
8. **Update main function** to orchestrate the workflow
9. **Add comprehensive error handling**
10. **Write unit and integration tests**
11. **Test locally** with real YouTube URLs in request body
12. **Deploy to Azure** with managed identity and Key Vault access

---

## Resources

- [Azure Functions Python Developer Guide](https://learn.microsoft.com/azure/azure-functions/functions-reference-python)
- [Azure Functions v2 Programming Model](https://learn.microsoft.com/azure/azure-functions/functions-reference-python?tabs=asgi%2Capplication-level)
- [Azure Key Vault Documentation](https://learn.microsoft.com/azure/key-vault/)
- [Azure Key Vault Python Quickstart](https://learn.microsoft.com/azure/key-vault/secrets/quick-create-python)
- [YouTube Transcript API](https://pypi.org/project/youtube-transcript-api/)
- [Notion API Documentation](https://developers.notion.com/)
- [Google Gemini API Documentation](https://ai.google.dev/docs)

---

**Last Updated:** November 16, 2025
