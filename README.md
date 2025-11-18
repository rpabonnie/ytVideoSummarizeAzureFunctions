# YouTube Video Summarizer to Notion

An **Azure Functions** application built with **Python** that automatically summarizes YouTube videos using AI and saves the summaries to Notion, with email notification upon successful completion.

## Overview

This serverless application processes YouTube videos by:
1. Sending YouTube URLs directly to Google Gemini for native video processing
2. Generating AI-powered summaries using Google Gemini's video analysis capabilities
3. Creating organized Notion pages with the summary
4. Sending email notifications when complete

**Repository:** [rpabonnie/ytVideoSummarizeAzureFunctions](https://github.com/rpabonnie/ytVideoSummarizeAzureFunctions)  
**Runtime:** Python 3.13  
**Framework:** Azure Functions v2 Programming Model

---

## Function Workflow

```mermaid
graph TD
graph TD
    A[HTTP POST Request] -->|YouTube URL| B[ytSummarizeToNotion Function]
    B --> C{Validate Input}
    C -->|Invalid URL| D[Return 400 Error]
    C -->|Valid URL| E[Retrieve Secrets from Azure Key Vault]
    E --> F[Fetch Notion API Key]
    E --> G[Fetch Google Gemini API Key]
    F --> H[Send Video URL to Gemini API]
    G --> H
    H --> I[Gemini Processes Video Natively]
    I --> J[Generate Summary with AI Analysis]
    J --> K[Create Notion Page]
    K --> L[Format Summary Content]
    L --> M[Save to Notion Database]
    M --> |200 OK| N[Send Email Notification]
    
    style A fill:#e1f5ff
    style B fill:#fff4e1
    style E fill:#ffe1f5
    style H fill:#e1ffe1
    style I fill:#e1ffe1
    style K fill:#f5e1ff
    style N fill:#ffe1e1
```

---

## Features

- **🎥 YouTube Integration**: Processes videos directly via URL using Gemini's native video capabilities
- **🤖 AI Summarization**: Uses Google Gemini for intelligent video analysis and summarization
- **📝 Notion Integration**: Creates structured pages in your Notion workspace
- **📧 Email Notifications**: Sends confirmation emails upon successful processing
- **🔐 Secure**: Secrets managed via Azure Key Vault
- **☁️ Serverless**: Scales automatically with Azure Functions
- **🔍 Comprehensive Logging**: Application Insights integration for monitoring

---

## Prerequisites

- **Python 3.13**
- **Azure Subscription**
- **Azure Functions Core Tools**
- **Google Gemini API Key**
- **Notion Account** (with integration created)
- **Azure Key Vault** (for secret management)

---

## Local Development Setup

### 1. Clone the Repository
```powershell
git clone https://github.com/rpabonnie/ytVideoSummarizeAzureFunctions.git
cd ytVideoSummarizeAzureFunctions
```

### 2. Create Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure Local Settings
Create or update `local.settings.json`:
```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "KEY_VAULT_URL": "https://your-keyvault.vault.azure.net/"
  }
}
```

### 5. Configure Azure Key Vault
Store secrets in Azure Key Vault:
```powershell
# Store Gemini API Key
az keyvault secret set --vault-name <keyvault-name> --name "GOOGLE-API-KEY" --value "<your-gemini-key>"

# Store Notion API Key
az keyvault secret set --vault-name <keyvault-name> --name "NOTION-API-KEY" --value "<your-notion-key>"
```

### 6. Configure Notion Integration
Set up Notion database and configuration:
```powershell
# Copy example configuration
Copy-Item notion_config.example.json notion_config.json

# Edit notion_config.json with your database ID
# See NOTION_SETUP.md for detailed instructions
```

📖 **[Complete Notion Setup Guide](./NOTION_SETUP.md)**

### 7. Run Locally
```powershell
func host start
```

---

## API Usage

### Endpoint
```
POST http://localhost:7071/api/ytSummarizeToNotion
```

### Request Body
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

### Example Request (PowerShell)
```powershell
$body = @{ url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:7071/api/ytSummarizeToNotion" `
  -Method Post `
  -Body $body `
  -ContentType "application/json"
```

### Success Response
```json
{
  "status": "success",
  "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "summary": {
    "title": "Video Title",
    "tags": ["tag1", "tag2"],
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "brief_summary": "Overview of the video...",
    "summary_bullets": ["Point 1", "Point 2"],
    "tools_and_technologies": [{"tool": "Tool Name", "purpose": "Usage"}]
  },
  "notion_url": "https://notion.so/workspace/page-id",
  "notion_success": true
}
```

---

## Notion Integration

The function automatically saves video summaries to a Notion database with structured formatting.

📖 **[Complete Setup Guide](./NOTION_SETUP.md)**

### Quick Start

1. Create a Notion integration at [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Store API key in Azure Key Vault as `NOTION-API-KEY`
3. Create a database and grant integration access
4. Copy database ID to `notion_config.json`
5. Test with a video URL

See [NOTION_SETUP.md](./NOTION_SETUP.md) for detailed step-by-step instructions.

---

## Project Structure

```
ytVideoSummarizeAzureFunctions/
├── function_app.py              # Main Azure Function definitions
├── host.json                    # Function host configuration
├── local.settings.json          # Local development settings (not committed)
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── services/
│   ├── gemini_service.py        # AI summarization logic using Google Gemini
│   ├── notion_service.py        # Notion API interactions
│   └── email_service.py         # Email notification service (planned)
├── utils/
│   ├── validators.py            # Input validation functions
│   └── exceptions.py            # Custom exception classes
└── tests/
    └── __init__.py              # Test infrastructure (planned)
```

---

## Deployment

### Deploy to Azure
```powershell
# Login to Azure
az login

# Deploy the function app
func azure functionapp publish <your-function-app-name>
```

### Configure Production Settings
```powershell
# Set Key Vault URL
az functionapp config appsettings set `
  --name <app-name> `
  --resource-group <rg-name> `
  --settings "KEY_VAULT_URL=https://<keyvault-name>.vault.azure.net/"

# Enable Managed Identity
az functionapp identity assign `
  --name <app-name> `
  --resource-group <rg-name>

# Grant Key Vault access
az keyvault set-policy `
  --name <keyvault-name> `
  --object-id <function-app-identity> `
  --secret-permissions get list
```

---

## Security

- ✅ Secrets stored in **Azure Key Vault** (never in code)
- ✅ **Managed Identity** for secure Key Vault access
- ✅ **ADMIN auth level** for function endpoints
- ✅ Input validation and sanitization
- ✅ HTTPS-only communication in production

---

## Monitoring

- **Application Insights** enabled for telemetry
- Function execution tracking
- Error and exception logging
- Performance metrics
- Token usage monitoring for AI services

---

## Dependencies

Key packages (see `requirements.txt` for full list):
- `azure-functions` - Azure Functions runtime
- `google-genai` - Google Gemini AI integration
- `notion-client` - Notion API client (planned)
- `azure-identity` - Azure authentication
- `azure-keyvault-secrets` - Key Vault integration

---

## Error Handling

The function handles various error scenarios:
- **400**: Invalid YouTube URL
- **404**: Video not found or private
- **401**: API authentication issues
- **500**: Internal processing errors
- **429**: Rate limit exceeded

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License.

---

## Resources

- [Azure Functions Python Guide](https://learn.microsoft.com/azure/azure-functions/functions-reference-python)
- [Azure Key Vault Documentation](https://learn.microsoft.com/azure/key-vault/)
- [Notion API Documentation](https://developers.notion.com/)
- [Google Gemini API Documentation](https://ai.google.dev/docs)

---

## Contact

For questions or support, please open an issue in the GitHub repository.

**Last Updated:** November 16, 2025
