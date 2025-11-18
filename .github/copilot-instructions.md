# GitHub Copilot Instructions - YouTube Video Summarizer to Notion

## Project Overview

This is an **Azure Functions** application built with **Python 3.13** that:
- Accepts YouTube video URLs via HTTP POST requests
- Processes videos using **Google Gemini's native video analysis**
- Generates AI-powered summaries
- Creates structured Notion pages (in progress)
- Sends email notifications upon completion (planned)

**Tech Stack:**
- Runtime: Python 3.13
- Framework: Azure Functions v2 Programming Model
- AI: Google Gemini API
- Integration: Notion API
- Security: Azure Key Vault for secret management

---

## Code Style and Standards

### Python Style
- Follow PEP 8 conventions
- Use type hints for function parameters and return values (e.g., `def func(param: str) -> dict:`)
- Use `|` for union types (Python 3.10+ syntax): `str | None` instead of `Optional[str]`
- Prefer descriptive variable names over abbreviations
- Use docstrings for all public functions and classes

### Import Organization
- Group imports: standard library → third-party → local modules
- Use absolute imports from project root
- Example order:
  ```python
  import logging
  import json
  
  import azure.functions as func
  from azure.identity import DefaultAzureCredential
  
  from services.gemini_service import GeminiService
  from utils.validators import validate_youtube_url
  ```

### Error Handling
- Use custom exceptions from `utils/exceptions.py`
- Always log errors with context: `logging.error(f"Error message: {str(e)}")`
- Return appropriate HTTP status codes:
  - `400`: Invalid input (bad YouTube URL, missing fields)
  - `401`: Authentication issues
  - `404`: Resource not found
  - `500`: Internal server errors
  - `503`: External service unavailable

---

## Security Requirements

### Critical Security Rules
- **NEVER commit secrets, API keys, or credentials to code**
- **ALWAYS use Azure Key Vault for secret management**
- Store secrets in Key Vault with names: `NOTION-API-KEY`, `GOOGLE-API-KEY`
- Use `DefaultAzureCredential()` for Key Vault authentication
- Keep `AuthLevel.ADMIN` for HTTP functions requiring authentication
- Validate and sanitize ALL external inputs, especially URLs

### Input Validation
- Always use validators from `utils/validators.py`
- Validate YouTube URLs using `validate_youtube_url()` before processing
- Validate request body structure using `validate_request_body()`
- Sanitize URLs to prevent injection attacks

### Example Secure Pattern
```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
secret_client = SecretClient(vault_url=key_vault_url, credential=credential)
api_key = secret_client.get_secret("GOOGLE-API-KEY").value
```

---

## Azure Functions Development

### Function Definition Pattern
- Use the v2 programming model with decorators
- Set appropriate auth levels: `@app.route(route="name", methods=["POST"])`
- Use `func.AuthLevel.ADMIN` for production endpoints
- Return JSON responses with proper MIME type

### HTTP Function Template
```python
@app.route(route="functionName", methods=["POST"])
def function_name(req: func.HttpRequest) -> func.HttpResponse:
    """
    Brief description of function purpose.
    
    Args:
        req: HTTP request with JSON body
        
    Returns:
        HTTP response with JSON data or error
    """
    try:
        req_body = req.get_json()
        # Process request
        return func.HttpResponse(
            json.dumps({"status": "success"}),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
```

### Service Initialization
- Initialize services at module level (singleton pattern) for reuse across requests
- Use lazy initialization to defer Key Vault access until first request
- Cache credentials to minimize Key Vault calls

---

## Project Structure and Organization

### File Organization
```
ytVideoSummarizeAzureFunctions/
├── function_app.py              # Function definitions only
├── services/
│   ├── gemini_service.py        # AI summarization logic
│   ├── notion_service.py        # Notion API interactions
│   └── email_service.py         # Email notifications
├── utils/
│   ├── validators.py            # Input validation functions
│   └── exceptions.py            # Custom exception classes
└── tests/
    └── __init__.py              # Test infrastructure
```

### Code Organization Best Practices
- Keep `function_app.py` focused on HTTP handling and orchestration
- Move business logic to service classes in `services/`
- Place validation logic in `utils/validators.py`
- Define custom exceptions in `utils/exceptions.py`
- Separate concerns: one service per external API integration

---

## Dependencies and Libraries

### Core Libraries (see requirements.txt)
- `azure-functions`: Azure Functions runtime
- `google-genai`: Google Gemini AI integration
- `notion-client`: Notion API client
- `azure-identity`: Azure authentication
- `azure-keyvault-secrets`: Key Vault secret retrieval

### Adding New Dependencies
1. Add package to `requirements.txt`
2. Install locally: `pip install -r requirements.txt`
3. Test locally before deploying
4. Document any new required secrets in Key Vault

---

## Testing Guidelines

### Test Requirements
- Write tests in `tests/` directory
- Test all validation functions
- Mock external APIs (Gemini, Notion, Key Vault)
- Test error scenarios (invalid URLs, API failures, missing secrets)

### Running Tests
- Use pytest for testing framework
- Run tests before deploying: `pytest tests/`
- Ensure all tests pass before creating PR

---

## Development Workflow

### Local Setup
1. Create virtual environment: `python -m venv venv`
2. Activate: `.\venv\Scripts\Activate.ps1` (Windows) or `source venv/bin/activate` (Unix)
3. Install dependencies: `pip install -r requirements.txt`
4. Configure `local.settings.json` with Key Vault URL
5. Run function: `func host start`

### Required Environment Variables (local.settings.json)
```json
{
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "KEY_VAULT_URL": "https://your-keyvault.vault.azure.net/"
  }
}
```

### Testing Endpoints Locally
```powershell
$body = @{ url = "https://www.youtube.com/watch?v=VIDEO_ID" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:7071/api/ytSummarizeToNotion" `
  -Method Post `
  -Body $body `
  -ContentType "application/json"
```

### Clearing Python Cache
After major code changes, clear cache to avoid import errors:
```powershell
Remove-Item -Path "__pycache__" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "services\__pycache__" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "utils\__pycache__" -Recurse -Force -ErrorAction SilentlyContinue
```

---

## API Integration Guidelines

### Google Gemini Integration
- Use `GeminiService` class for all Gemini API calls
- Process YouTube videos using Gemini's native video capabilities
- Send video URLs directly to Gemini API (no transcript extraction needed)
- Handle rate limits and API errors gracefully

### Notion Integration
- Use `NotionService` class for all Notion API operations
- Create structured pages with proper formatting
- Handle Notion API rate limits
- Return Notion page URLs in responses

### Azure Key Vault Integration
- Use `DefaultAzureCredential()` for authentication
- Cache secret values to reduce API calls
- Handle Key Vault errors with custom `KeyVaultError` exception
- Never log secret values

---

## Logging Best Practices

### Logging Standards
- Use Python's `logging` module (already configured by Azure Functions)
- Log levels:
  - `logging.info()`: Normal flow, important milestones
  - `logging.warning()`: Potential issues, fallback scenarios
  - `logging.error()`: Errors that need attention
- Include context in log messages: video URLs, operation types, error details
- Never log secrets or sensitive data

### Example Logging
```python
logging.info(f"Processing YouTube URL: {sanitized_url}")
logging.warning(f"Retrying API call, attempt {retry_count}")
logging.error(f"Gemini API error: {e.message}", exc_info=True)
```

---

## Deployment Checklist

### Before Deploying
- [ ] All tests pass locally
- [ ] Secrets configured in Azure Key Vault
- [ ] Function App has Managed Identity enabled
- [ ] Key Vault access policies grant Function App secret read permissions
- [ ] `KEY_VAULT_URL` environment variable set in Function App settings
- [ ] Python cache cleared

### Deployment Command
```powershell
func azure functionapp publish <function-app-name>
```

---

## Common Patterns

### Singleton Service Pattern
```python
# At module level
service: ServiceClass | None = None

def _initialize_service():
    global service
    if service is None:
        service = ServiceClass(config)
```

### Safe JSON Parsing
```python
try:
    req_body = req.get_json()
except ValueError as e:
    return func.HttpResponse(
        json.dumps({"error": "Invalid JSON format"}),
        status_code=400,
        mimetype="application/json"
    )
```

### URL Validation and Sanitization
```python
try:
    youtube_url = req_body.get('url', '')
    sanitized_url = validate_youtube_url(youtube_url)
except InvalidYouTubeUrlError as e:
    return func.HttpResponse(
        json.dumps({"error": e.message}),
        status_code=e.status_code,
        mimetype="application/json"
    )
```

---

## Additional Notes

- This is a serverless application - optimize for cold start performance
- Keep dependencies minimal to reduce deployment size
- Use Application Insights for production monitoring
- Follow Azure Functions best practices for scalability
- Document all breaking changes in commit messages
