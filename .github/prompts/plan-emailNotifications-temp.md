````prompt
# Plan: Integrate Azure Communication Services Email with Comprehensive Error Reporting

Implement email notification functionality using Azure Communication Services (ACS) Email to notify when Notion pages are successfully created and send detailed alerts for all errors and failures during video processing.

## Overview

This plan adds Azure Communication Services Email integration to the YouTube Video Summarizer Azure Function. The existing `EmailService` class structure is adapted for ACS Email SDK integration with both success and failure email templates. This implementation will ensure notifications for:

- ✅ **Success notifications**: When videos are successfully summarized and Notion pages created
- ❌ **Failure notifications**: For all error scenarios (rate limits, invalid URLs, API failures, etc.)
- 📧 **Professional HTML emails**: With formatted content, links, and error details
- 🔐 **Azure-native security**: Managed Identity support, no API keys in production code

## Why Azure Communication Services Email?

**Azure Communication Services Email is the recommended solution** (verified from official Microsoft documentation):

1. ✅ **Native Azure service** - First-party Microsoft solution, not third-party
2. ✅ **Free Azure-managed domain** - `donotreply@xxxxxxxx.azurecomm.net` (no DNS verification needed)
3. ✅ **Managed Identity support** - No API keys required in production
4. ✅ **Cost-effective** - ~$0.25 per 1,000 emails (25k emails = ~$6.25/month)
5. ✅ **Better integration** - Direct SDK integration with Azure Functions
6. ✅ **Azure Communication Services alternative** - Azure Communication Services no longer sold via Azure Marketplace

**Documentation**: [Azure Communication Services Email](https://learn.microsoft.com/en-us/azure/communication-services/concepts/email/prepare-email-communication-resource)

## Architecture

### Email Flow
```
Azure Function → EmailService (ACS SDK) → Azure Communication Services → Email Delivery
     ↓                                                                        ↓
Error Occurs                                                          User Notification
     ↓
EmailService.send_failure_email()
     ↓
ACS Email API (with HTML template)
```

### Azure Communication Services Benefits
- **Native Azure integration**: Seamless with Azure Functions and Key Vault
- **Managed Identity**: Production deployments use system-assigned identity (no secrets)
- **Connection String**: Development uses connection string from Key Vault
- **Delivery tracking**: Built-in email delivery status and event handling

## Implementation Steps

### Step 1: Provision Azure Communication Services (Completed)

#### 1.1 Create Azure Communication Services Resource (Completed)

**Option A: Azure Portal**
1. Navigate to Azure Portal → Create a resource
2. Search for "Communication Services"
3. Click "Create"
4. Fill in details:
   - **Subscription**: Select your Azure subscription
   - **Resource Group**: Same as Function App (e.g., `ytVideoSummarizer-rg`)
   - **Resource Name**: `ytVideoSummarizer-acs` (must be globally unique)
   - **Data Location**: United States (or your preferred region)
5. Click "Review + Create" → "Create"
6. Wait for deployment (~1-2 minutes)

**Option B: Azure CLI**
```powershell
# Set variables
$resourceGroup = "<your-resource-group>"
$acsName = "ytVideoSummarizer-acs"
$location = "global"
$dataLocation = "United States"

# Create Communication Services resource
az communication create `
  --name $acsName `
  --resource-group $resourceGroup `
  --location $location `
  --data-location $dataLocation
```

#### 1.2 Create Email Communication Services Resource (Completed)

**Option A: Azure Portal**
1. Navigate to Azure Portal → Create a resource
2. Search for "Email Communication Services"
3. Click "Create"
4. Fill in details:
   - **Subscription**: Same as above
   - **Resource Group**: Same as Function App
   - **Resource Name**: `ytVideoSummarizer-email`
   - **Data Location**: United States (must match ACS resource)
5. Click "Review + Create" → "Create"

**Option B: Azure CLI**
```powershell
$emailServiceName = "ytVideoSummarizer-email"

# Create Email Communication Services resource
az communication email create `
  --name $emailServiceName `
  --resource-group $resourceGroup `
  --location $location `
  --data-location $dataLocation
```

#### 1.3 Provision Azure-Managed Email Domain (Free, No Verification) (Completed)

**Azure Portal Steps:**
1. Navigate to your **Email Communication Services** resource (`ytVideoSummarizer-email`)
2. In left menu, select **Provision domains**
3. Click **Add domain** → **Azure domain** (free option)
4. Click **Add**
5. Azure provisions a domain like: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.azurecomm.net`
6. Wait for provisioning (~2-3 minutes)
7. **Copy the domain name** - you'll use this as the sender address

**Result**: Your sender email will be: `DoNotReply@xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.azurecomm.net`

**Note**: For custom domains (e.g., `noreply@yourdomain.com`), see [Custom Domain Setup](https://learn.microsoft.com/en-us/azure/communication-services/quickstarts/email/add-custom-verified-domains) - requires DNS verification.

#### 1.4 Connect Email Domain to Communication Services (Completed)

**Azure Portal Steps:**
1. Navigate to your **Communication Services** resource (`ytVideoSummarizer-acs`)
2. In left menu, select **Email** → **Domains**
3. Click **Connect domain**
4. Select your Email Communication Services resource (`ytVideoSummarizer-email`)
5. Select the Azure-managed domain you provisioned
6. Click **Connect**
7. Wait for connection (~1 minute)

**Verify**: Domain status should show "Connected"

#### 1.5 Get Connection String and Store in Key Vault (Completed)

**Get Connection String:**

**Azure Portal:**
1. Navigate to your **Communication Services** resource (`ytVideoSummarizer-acs`)
2. In left menu, select **Keys**
3. Copy the **Primary connection string**
   - Format: `endpoint=https://<resource-name>.communication.azure.com/;accesskey=<key>`

**Azure CLI:**
```powershell
# Get connection string
$connectionString = az communication show-connection-string `
  --name $acsName `
  --resource-group $resourceGroup `
  --query "primaryConnectionString" `
  --output tsv

Write-Host "Connection String: $connectionString"
```

**Store in Azure Key Vault:**

**Local Development:**
```powershell
# Set variables
$vaultName = "<your-keyvault-name>"

# Store connection string in Key Vault
az keyvault secret set `
  --vault-name $vaultName `
  --name "ACS-CONNECTION-STRING" `
  --value $connectionString

# Verify storage
az keyvault secret show `
  --vault-name $vaultName `
  --name "ACS-CONNECTION-STRING" `
  --query "value" `
  --output tsv
```

**Production (Azure Portal):**
1. Navigate to Azure Key Vault
2. Secrets → "+ Generate/Import"
3. **Name**: `ACS-CONNECTION-STRING`
4. **Value**: Paste ACS connection string
5. Click "Create"

**Security Note**: For production with Managed Identity:
- Function App uses system-assigned identity to access Key Vault
- No connection string needed in production code (retrieved from Key Vault at runtime)
- Alternative: Use endpoint + Managed Identity directly (no connection string)

---

### Step 2: Update Project Dependencies

Add Azure Communication Services Email SDK to `requirements.txt`.

**File**: `requirements.txt`

**Add this line:**
```txt
azure-communication-email>=1.0.0
```

**Complete requirements.txt (for reference):**
```txt
azure-functions
azure-identity
azure-keyvault-secrets
google-genai
notion-client
azure-communication-email>=1.0.0
```

**Actions:**
- Edit `requirements.txt`
- Add `azure-communication-email>=1.0.0` to dependencies
- Install locally: `pip install -r requirements.txt`

---

### Step 3: Configure Function App Settings

Add Azure Communication Services configuration and email addresses to Azure Function App settings.

#### 3.1 Configure ACS Connection String

**Option A: Direct Key Vault Reference (Recommended for Production)**
```powershell
# Set Function App name and resource group
$functionApp = "<your-function-app-name>"
$resourceGroup = "<your-resource-group>"
$keyVaultUrl = "<your-keyvault-url>"  # e.g., https://myvault.vault.azure.net/

# Add ACS connection string as Key Vault reference
az functionapp config appsettings set `
  --name $functionApp `
  --resource-group $resourceGroup `
  --settings "ACS_CONNECTION_STRING=@Microsoft.KeyVault(SecretUri=${keyVaultUrl}/secrets/ACS-CONNECTION-STRING/)"
```

**Option B: Direct Value (For Local Testing)**
```powershell
# Retrieve secret from Key Vault
$acsConnectionString = az keyvault secret show `
  --vault-name $vaultName `
  --name "ACS-CONNECTION-STRING" `
  --query "value" `
  --output tsv

# Set as app setting (local testing only)
az functionapp config appsettings set `
  --name $functionApp `
  --resource-group $resourceGroup `
  --settings "ACS_CONNECTION_STRING=$acsConnectionString"
```

#### 3.2 Configure Email Addresses

```powershell
# Set email configuration
az functionapp config appsettings set `
  --name $functionApp `
  --resource-group $resourceGroup `
  --settings `
    "EMAIL_FROM=<verified-sender-email@domain.com>" `
    "EMAIL_TO=<your-notification-email@domain.com>"
```

**Important:**
- `EMAIL_FROM` **must match** the verified sender email from Step 1.4
- `EMAIL_TO` can be any email address (where you want to receive notifications)

#### 3.3 Local Development Configuration

**File**: `local.settings.json`

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "KEY_VAULT_URL": "https://<your-keyvault>.vault.azure.net/",
    "Azure Communication ServicesApiKey": "<paste-Azure Communication Services-api-key-for-local-testing>",
    "EMAIL_FROM": "<verified-sender-email@domain.com>",
    "EMAIL_TO": "<your-email@domain.com>"
  }
}
```

**⚠️ Security Note**: 
- `local.settings.json` is in `.gitignore` (never commit secrets)
- Use Key Vault references in production
- For local testing, you can paste the Azure Communication Services API key directly

**Actions:**
- Update `local.settings.json` with Azure Communication Services settings
- Configure Function App settings in Azure Portal or via CLI
- Verify settings: `az functionapp config appsettings list --name $functionApp --resource-group $resourceGroup`

---

### Step 4: Integrate EmailService into Function App

Modify `function_app.py` to initialize `EmailService` and send notifications for success/failure scenarios.

#### 4.1 Initialize EmailService (Module Level)

**File**: `function_app.py`

**Add to imports:**
```python
from services.email_service import EmailService
```

**Update global service variables:**
```python
# Initialize services at module level (singleton pattern)
gemini_service: GeminiService | None = None
notion_service: NotionService | None = None
email_service: EmailService | None = None  # Add this line
```

**Update `_initialize_services()` function:**
```python
def _initialize_services():
    """Initialize services with Key Vault URL from environment."""
    global gemini_service, notion_service, email_service
    
    if gemini_service is None:
        key_vault_url = os.environ.get("KEY_VAULT_URL")
        if not key_vault_url:
            raise ValueError("KEY_VAULT_URL environment variable not configured")
        
        logging.info("Initializing services...")
        gemini_service = GeminiService(key_vault_url)
        notion_service = NotionService(key_vault_url)
        
        # Initialize EmailService
        from_email = os.environ.get("EMAIL_FROM")
        to_email = os.environ.get("EMAIL_TO")
        
        if from_email and to_email:
            email_service = EmailService(from_email, to_email)
            logging.info("EmailService initialized successfully")
        else:
            logging.warning("Email configuration missing (EMAIL_FROM/EMAIL_TO). Email notifications disabled.")
        
        logging.info("Services initialized successfully")
```

#### 4.2 Add Azure Communication Services Output Binding Decorator

**Update function signature:**
```python
@app.route(route="ytSummarizeToNotion", methods=["POST"])
@app.send_grid_output(arg_name="Azure Communication ServicesMessage", api_key="Azure Communication ServicesApiKey")
def ytSummarizeToNotion(req: func.HttpRequest, Azure Communication ServicesMessage: func.Out[str]) -> func.HttpResponse:
```

**Decorator Parameters:**
- `arg_name="Azure Communication ServicesMessage"`: Output binding parameter name
- `api_key="Azure Communication ServicesApiKey"`: App setting name containing Azure Communication Services API key

#### 4.3 Send Success Emails

**After successful Notion page creation (around line 180):**

```python
# Step 5: Create Notion page
notion_url = None
notion_success = False
try:
    logging.info("Creating Notion page with summary...")
    if notion_service is None:
        raise ValueError("NotionService not initialized")
    notion_url = notion_service.create_page(summary)
    notion_success = True
    logging.info(f"Notion page created successfully: {notion_url}")
    
    # Send success email notification
    if email_service and notion_url:
        try:
            email_data = email_service.format_success_email(
                youtube_url=sanitized_url,
                notion_url=notion_url,
                summary=summary
            )
            Azure Communication ServicesMessage.set(json.dumps(email_data))
            logging.info("Success email notification queued for delivery")
        except Exception as e:
            logging.warning(f"Failed to send success email (non-fatal): {str(e)}")
    
except NotionApiError as e:
    logging.warning(f"Notion integration failed (non-fatal): {e.message}")
    # Don't fail the entire request - summary is still valid
except KeyVaultError as e:
    logging.warning(f"Notion Key Vault error (non-fatal): {e.message}")
except Exception as e:
    logging.warning(f"Unexpected Notion error (non-fatal): {str(e)}")
```

#### 4.4 Send Failure Emails for All Error Scenarios

**Helper function to send failure emails:**
```python
def _send_failure_email(
    Azure Communication ServicesMessage: func.Out[str],
    youtube_url: str,
    error_message: str
):
    """
    Send failure notification email.
    
    Args:
        Azure Communication ServicesMessage: Azure Communication Services output binding
        youtube_url: YouTube URL that failed processing
        error_message: Error description
    """
    if email_service:
        try:
            email_data = email_service.format_failure_email(
                youtube_url=youtube_url,
                error=error_message
            )
            Azure Communication ServicesMessage.set(json.dumps(email_data))
            logging.info("Failure email notification queued for delivery")
        except Exception as e:
            logging.error(f"Failed to send failure email: {str(e)}")
```

**Add to each error handling block:**

1. **Rate Limit Exceeded (429)**
```python
if not is_allowed:
    logging.warning(f"Rate limit exceeded: {request_count} requests in the last hour")
    
    # Send failure email
    _send_failure_email(
        Azure Communication ServicesMessage,
        req_body.get('url', 'Unknown URL') if req_body else 'Unknown URL',
        f"Rate limit exceeded: {request_count}/{RATE_LIMIT_PER_HOUR} requests in last hour. Please try again later."
    )
    
    return func.HttpResponse(...)
```

2. **Invalid JSON (400)**
```python
except ValueError as e:
    logging.error(f"Invalid JSON in request body: {str(e)}")
    
    # Send failure email (no URL available)
    _send_failure_email(
        Azure Communication ServicesMessage,
        "N/A - Invalid Request",
        f"Invalid JSON format in request: {str(e)}"
    )
    
    return func.HttpResponse(...)
```

3. **Request Validation Failed (400)**
```python
except InvalidYouTubeUrlError as e:
    logging.error(f"Request validation failed: {e.message}")
    
    # Send failure email
    _send_failure_email(
        Azure Communication ServicesMessage,
        req_body.get('url', 'Invalid URL'),
        f"Request validation failed: {e.message}"
    )
    
    return func.HttpResponse(...)
```

4. **YouTube URL Validation Failed (400)**
```python
except InvalidYouTubeUrlError as e:
    logging.error(f"URL validation failed: {e.message}")
    
    # Send failure email
    _send_failure_email(
        Azure Communication ServicesMessage,
        youtube_url,
        f"Invalid YouTube URL: {e.message}"
    )
    
    return func.HttpResponse(...)
```

5. **Gemini API Error (503/500)**
```python
except GeminiApiError as e:
    logging.error(f"Gemini API error: {e.message}")
    
    # Send failure email
    _send_failure_email(
        Azure Communication ServicesMessage,
        sanitized_url,
        f"AI summarization failed: {e.message}"
    )
    
    return func.HttpResponse(...)
```

6. **Key Vault Error (500)**
```python
except KeyVaultError as e:
    logging.error(f"Key Vault error: {e.message}")
    
    # Send failure email
    _send_failure_email(
        Azure Communication ServicesMessage,
        sanitized_url,
        f"Configuration error (Key Vault): {e.message}"
    )
    
    return func.HttpResponse(...)
```

7. **Unexpected Errors (500)**
```python
except Exception as e:
    logging.error(f"Unexpected error: {str(e)}", exc_info=True)
    
    # Send failure email
    _send_failure_email(
        Azure Communication ServicesMessage,
        req_body.get('url', 'Unknown URL') if 'req_body' in locals() else 'Unknown',
        f"Internal server error: {str(e)}"
    )
    
    return func.HttpResponse(...)
```

**Actions:**
- Add `EmailService` import and initialization
- Add `@app.send_grid_output` decorator to function
- Add `Azure Communication ServicesMessage: func.Out[str]` parameter
- Implement `_send_failure_email()` helper function
- Add success email after Notion page creation
- Add failure emails in all error handling blocks

---

### Step 5: Error Email Strategy Decisions

#### 5.1 Rate Limit Email Behavior

**Question**: Should rate limit errors (429) trigger emails on every rejection?

**Options:**
- **A. Email every rate limit rejection** (current plan)
  - Pros: User always notified
  - Cons: Can spam inbox if user retries aggressively
  
- **B. Email only first rejection per hour**
  - Pros: Prevents email spam
  - Cons: More complex tracking logic
  
- **C. Skip rate limit emails entirely**
  - Pros: User gets HTTP 429 response anyway
  - Cons: No email record of rate limit hits

**Recommendation**: **Option A** (email every rejection)
- Rationale: User should be notified of all failures
- Mitigation: Rate limit already prevents excessive requests (30/hour)
- User can configure email filters if needed

**Implementation**: Include rate limit errors in email notifications (already in plan).

#### 5.2 Partial Failure Scenarios

**Question**: If summary succeeds but Notion fails, send success or failure email?

**Current Behavior**: 
- Summary generation succeeds
- Notion integration fails (non-fatal)
- HTTP 200 response with `"notion_success": false`

**Options:**
- **A. Send success email (summary worked)**
  - Include warning note: "Notion page creation failed"
  
- **B. Send failure email (Notion failed)**
  - Include note: "Summary generated but Notion integration failed"
  
- **C. Send both emails**
  - Success email for summary
  - Failure email for Notion error

**Recommendation**: **Option B** (failure email)
- Rationale: User expects end-to-end success (summary + Notion)
- Failure email provides error details for debugging
- User can still access summary in HTTP response
- Consistent with "notify me when it successfully publishes a page in notion"

**Implementation**: Send failure email when `notion_success = False`

```python
# After Notion creation attempt
if not notion_success and email_service:
    try:
        error_msg = "Summary generated successfully, but Notion page creation failed. Check Azure Function logs for details."
        email_data = email_service.format_failure_email(
            youtube_url=sanitized_url,
            error=error_msg
        )
        Azure Communication ServicesMessage.set(json.dumps(email_data))
        logging.info("Partial failure email notification sent")
    except Exception as e:
        logging.warning(f"Failed to send partial failure email: {str(e)}")
```

#### 5.3 Email Send Failure Handling

**Question**: Should email send failures block function execution?

**Recommendation**: **Non-fatal** (log warnings only)
- Rationale: Core functionality (summarization, Notion) more important than notifications
- Email delivery is best-effort
- Azure Communication Services binding has automatic retry logic

**Implementation**: Wrap all `Azure Communication ServicesMessage.set()` calls in try-except (already in plan).

---

### Step 6: Testing Strategy

#### 6.1 Local Testing Setup

**Prerequisites:**
1. ✅ Azure Communication Services account created
2. ✅ API key stored in Key Vault
3. ✅ Sender email verified
4. ✅ `local.settings.json` configured
5. ✅ Dependencies installed: `pip install -r requirements.txt`

**Start Function Locally:**
```powershell
# Clear Python cache (if needed)
Remove-Item -Path "__pycache__" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "services\__pycache__" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "utils\__pycache__" -Recurse -Force -ErrorAction SilentlyContinue

# Start function
func start
```

#### 6.2 Test Success Email

**Scenario**: Valid YouTube URL → Summary + Notion → Success Email

```powershell
$body = @{
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
} | ConvertTo-Json

$response = Invoke-RestMethod `
  -Uri "http://localhost:7071/api/ytSummarizeToNotion" `
  -Method Post `
  -Body $body `
  -ContentType "application/json"

$response | ConvertTo-Json -Depth 10
```

**Expected Outcome:**
- ✅ HTTP 200 response
- ✅ `"notion_success": true`
- ✅ `"notion_url"` populated
- ✅ Email received with:
  - Subject: `✅ Summary Ready: [Video Title]`
  - "View in Notion" button (links to Notion page)
  - Brief summary excerpt
  - Original YouTube URL

**Verification:**
1. Check email inbox (`EMAIL_TO` address)
2. Verify email content and formatting
3. Click "View in Notion" button → Notion page opens
4. Check Azure Function logs for: `"Success email notification queued for delivery"`

#### 6.3 Test Failure Emails

**Test 1: Invalid YouTube URL**
```powershell
$body = @{ url = "https://invalid-url.com" } | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://localhost:7071/api/ytSummarizeToNotion" `
  -Method Post `
  -Body $body `
  -ContentType "application/json"
```

**Expected:**
- ❌ HTTP 400 response
- ✅ Failure email received with error: "Invalid YouTube URL"

---

**Test 2: Invalid JSON**
```powershell
$body = "{ invalid json }"

Invoke-RestMethod `
  -Uri "http://localhost:7071/api/ytSummarizeToNotion" `
  -Method Post `
  -Body $body `
  -ContentType "application/json"
```

**Expected:**
- ❌ HTTP 400 response
- ✅ Failure email with error: "Invalid JSON format"

---

**Test 3: Rate Limit Exceeded**

```powershell
# Send 31 requests in rapid succession (exceeds 30/hour limit)
1..31 | ForEach-Object {
    $body = @{ url = "https://www.youtube.com/watch?v=test$_" } | ConvertTo-Json
    try {
        Invoke-RestMethod -Uri "http://localhost:7071/api/ytSummarizeToNotion" -Method Post -Body $body -ContentType "application/json"
    } catch {
        Write-Host "Request $_ failed (expected after 30)"
    }
}
```

**Expected:**
- ✅ First 30 requests succeed (or fail for other reasons)
- ❌ 31st request returns HTTP 429
- ✅ Failure email for rate limit error

---

**Test 4: Missing Notion Configuration**

```powershell
# Temporarily rename notion_config.json
Rename-Item -Path "notion_config.json" -NewName "notion_config.json.bak"

# Send request
$body = @{ url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:7071/api/ytSummarizeToNotion" -Method Post -Body $body -ContentType "application/json"

# Restore config
Rename-Item -Path "notion_config.json.bak" -NewName "notion_config.json"
```

**Expected:**
- ✅ HTTP 200 response (summary succeeds)
- ✅ `"notion_success": false`
- ✅ Failure email: "Summary generated successfully, but Notion page creation failed"

---

**Test 5: Invalid Gemini API Key**

```powershell
# Temporarily change KEY_VAULT_URL in local.settings.json to invalid value
# Or remove GOOGLE-API-KEY from Key Vault (if safe to do so)

$body = @{ url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:7071/api/ytSummarizeToNotion" -Method Post -Body $body -ContentType "application/json"
```

**Expected:**
- ❌ HTTP 500 or 503 response
- ✅ Failure email: "AI summarization failed: [error details]"

#### 6.4 Email Content Verification Checklist

For each test email, verify:

**Success Email:**
- [ ] Subject line includes video title
- [ ] HTML formatting renders correctly
- [ ] "View in Notion" button present and clickable
- [ ] Notion URL valid (opens correct page)
- [ ] Brief summary excerpt displayed
- [ ] Original YouTube URL included at bottom
- [ ] Professional styling (colors, fonts, spacing)

**Failure Email:**
- [ ] Subject line: "❌ Video Summary Failed"
- [ ] Error message clearly displayed in code block
- [ ] YouTube URL included (if available)
- [ ] Troubleshooting guidance provided
- [ ] Professional styling maintained

#### 6.5 Production Testing

After local testing succeeds:

1. **Deploy to Azure**
```powershell
func azure functionapp publish <function-app-name>
```

2. **Test Production Endpoint**
```powershell
$functionKey = "<your-function-key>"  # From Azure Portal → Function App → App Keys
$body = @{ url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ" } | ConvertTo-Json

Invoke-RestMethod `
  -Uri "https://<function-app-name>.azurewebsites.net/api/ytSummarizeToNotion" `
  -Method Post `
  -Body $body `
  -ContentType "application/json" `
  -Headers @{ "x-functions-key" = $functionKey }
```

3. **Monitor Application Insights**
```powershell
# View recent logs
az monitor app-insights query `
  --app <app-insights-name> `
  --analytics-query "traces | where message contains 'email' | order by timestamp desc | take 20"
```

4. **Verify Azure Communication Services Activity**
   - Azure Communication Services Portal → Activity Feed
   - Check delivery status, opens, clicks

---

### Step 7: Documentation Updates

#### 7.1 Update README.md

**Add to Features section:**
```markdown
## Features

- 🎥 **YouTube Integration**: Processes videos directly via URL
- 🤖 **AI Summarization**: Uses Google Gemini for intelligent analysis
- 📝 **Notion Integration**: Automatically saves summaries to Notion databases
- 📧 **Email Notifications**: Success and failure alerts via Azure Communication Services
- 🔐 **Secure**: Secrets managed via Azure Key Vault
- ☁️ **Serverless**: Scales automatically with Azure Functions
```

**Add Email Setup section:**
```markdown
## Email Notifications Setup

The function sends email notifications via Azure Communication Services for:
- ✅ Successful Notion page creation
- ❌ All error scenarios (rate limits, invalid URLs, API failures)

### Setup Steps

1. **Create Azure Communication Services Account**
   - Azure Portal → Marketplace → Azure Communication Services Email Delivery
   - Select **Free tier** (25,000 emails/month)

2. **Get API Key**
   - Azure Communication Services Portal → Settings → API Keys → Create API Key
   - Permissions: Mail Send (Full Access)

3. **Verify Sender Email**
   - Azure Communication Services Portal → Settings → Sender Authentication
   - Verify Single Sender → Enter your email → Confirm verification email

4. **Store API Key**
   ```powershell
   az keyvault secret set \
     --vault-name <vault> \
     --name "Azure Communication Services-API-KEY" \
     --value "<Azure Communication Services-api-key>"
   ```

5. **Configure Function App**
   ```powershell
   az functionapp config appsettings set \
     --name <app-name> \
     --resource-group <rg> \
     --settings \
       "Azure Communication ServicesApiKey=@Microsoft.KeyVault(...)" \
       "EMAIL_FROM=<verified-sender@domain.com>" \
       "EMAIL_TO=<your-email@domain.com>"
   ```

See [Azure Communication Services Documentation](https://docs.Azure Communication Services.com/) for details.
```

**Update Prerequisites:**
```markdown
## Prerequisites

- **Python 3.13**
- **Azure Subscription**
- **Azure Functions Core Tools**
- **Google Gemini API Key**
- **Notion Account** (with integration created)
- **Azure Communication Services Account** (free tier) ← Add this
- **Azure Key Vault** (for secret management)
```

#### 7.2 Update local.settings.json Template

**Add to local.settings.json documentation:**
```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "KEY_VAULT_URL": "https://<your-keyvault>.vault.azure.net/",
    "Azure Communication ServicesApiKey": "<Azure Communication Services-api-key>",
    "EMAIL_FROM": "<verified-sender@domain.com>",
    "EMAIL_TO": "<your-email@domain.com>"
  }
}
```

#### 7.3 Create Email Setup Documentation (Optional)

**File**: `EMAIL_SETUP.md`

Optional detailed guide similar to `NOTION_SETUP.md`, covering:
- Azure Communication Services account creation
- API key generation
- Sender verification (Single Sender vs Domain Authentication)
- Azure Key Vault integration
- Troubleshooting email delivery issues

---

## Security Considerations

### 1. API Key Management

- ✅ **Azure Communication Services API Key stored in Azure Key Vault**
- ✅ **Key Vault reference in Function App settings** (not direct value)
- ✅ **Managed Identity access** to Key Vault (no credentials in code)
- ✅ **Local development**: API key in `local.settings.json` (gitignored)
- ❌ **Never log Azure Communication Services API keys**

### 2. Sender Email Verification

- ✅ **Sender verification prevents spoofing**
- ✅ **Single Sender Verification** sufficient for personal use
- ✅ **Domain Authentication** recommended for custom domains
- ⚠️ **Free tier limitation**: Only verified senders can be used as "From" address

### 3. Email Content Security

- ✅ **HTML emails sanitized** (no user-generated content)
- ✅ **URLs validated** before including in emails
- ✅ **Error messages sanitized** (no sensitive data leaked)
- ✅ **HTTPS links** to Notion and YouTube

### 4. Rate Limiting

- ✅ **Function rate limit** (30 requests/hour) prevents Azure Communication Services abuse
- ✅ **Azure Communication Services free tier**: 25,000 emails/month
- ⚠️ **Monitor Azure Communication Services usage** to avoid exceeding free tier

---

## Error Handling Summary

### Email Notification Triggers

| Scenario | HTTP Status | Email Type | Error Message |
|----------|-------------|------------|---------------|
| **Success** | 200 | ✅ Success | N/A |
| **Rate Limit** | 429 | ❌ Failure | "Rate limit exceeded: X/30 requests" |
| **Invalid JSON** | 400 | ❌ Failure | "Invalid JSON format in request" |
| **Invalid URL** | 400 | ❌ Failure | "Invalid YouTube URL: [details]" |
| **Gemini API Error** | 503/500 | ❌ Failure | "AI summarization failed: [details]" |
| **Key Vault Error** | 500 | ❌ Failure | "Configuration error (Key Vault)" |
| **Notion Failure** | 200* | ❌ Failure | "Summary generated, Notion failed" |
| **Unexpected Error** | 500 | ❌ Failure | "Internal server error: [details]" |

*Note: Notion failures return HTTP 200 (summary succeeds) but trigger failure email.

### Email Send Failure Handling

All `Azure Communication ServicesMessage.set()` calls wrapped in try-except:
- ✅ **Non-fatal**: Email failures don't break core functionality
- ✅ **Logged as warnings**: `logging.warning("Failed to send email: ...")`
- ✅ **Best-effort delivery**: Azure Communication Services binding has automatic retry

---

## Implementation Checklist

### Azure Communication Services Provisioning
- [ ] Create Azure Communication Services account in Azure Marketplace (free tier)
- [ ] Generate Azure Communication Services API key (Mail Send permissions)
- [ ] Verify sender email address (Single Sender Verification)
- [ ] Store API key in Azure Key Vault (`Azure Communication Services-API-KEY`)

### Code Changes
- [ ] Add `azure-functions-Azure Communication Services` to `requirements.txt`
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Update `function_app.py`:
  - [ ] Import `EmailService`
  - [ ] Add `email_service` global variable
  - [ ] Initialize EmailService in `_initialize_services()`
  - [ ] Add `@app.send_grid_output` decorator
  - [ ] Add `Azure Communication ServicesMessage` parameter
  - [ ] Implement `_send_failure_email()` helper
  - [ ] Add success email after Notion creation
  - [ ] Add failure emails in all error blocks

### Configuration
- [ ] Update `local.settings.json` with Azure Communication Services settings
- [ ] Configure Function App settings (Azure):
  - [ ] `Azure Communication ServicesApiKey` (Key Vault reference)
  - [ ] `EMAIL_FROM` (verified sender)
  - [ ] `EMAIL_TO` (recipient)

### Testing
- [ ] **Local Testing**:
  - [ ] Test success email (valid URL → Notion → email)
  - [ ] Test failure emails (invalid URL, JSON, rate limit, etc.)
  - [ ] Verify email content and formatting
  - [ ] Check all links work (Notion, YouTube)
- [ ] **Production Testing**:
  - [ ] Deploy to Azure: `func azure functionapp publish <app-name>`
  - [ ] Test production endpoint with function key
  - [ ] Monitor Application Insights logs
  - [ ] Verify Azure Communication Services Activity Feed

### Documentation
- [ ] Update `README.md`:
  - [ ] Add email notifications to Features
  - [ ] Add Azure Communication Services to Prerequisites
  - [ ] Add Email Notifications Setup section
- [ ] Update `local.settings.json` template/documentation
- [ ] (Optional) Create `EMAIL_SETUP.md` detailed guide

---

## Success Criteria

Implementation is complete when:

✅ **Functional Requirements**
1. Success emails sent when Notion pages created
2. Failure emails sent for all error scenarios (7+ types)
3. Emails delivered to `EMAIL_TO` address
4. HTML formatting renders correctly in email clients

✅ **Configuration**
5. Azure Communication Services account provisioned (free tier)
6. Sender email verified
7. API key stored in Key Vault
8. Function App settings configured

✅ **Testing**
9. Local testing passes (success + failure scenarios)
10. Production deployment successful
11. Email delivery verified in Azure Communication Services Activity Feed
12. All links in emails functional

✅ **Documentation**
13. README.md updated with setup instructions
14. Configuration templates updated
15. (Optional) EMAIL_SETUP.md created

---

## Design Decisions & Rationale

### 1. Azure Communication Services vs. Azure Communication Services Email

**Decision**: Use Azure Communication Services

**Rationale**:
- ✅ **25,000 free emails/month** (ACS has no free tier)
- ✅ **Output binding** available (declarative, minimal code)
- ✅ **Existing EmailService** already designed for Azure Communication Services
- ✅ **Mature service** with excellent deliverability
- ✅ **Azure Marketplace integration** (easy provisioning)

**Alternative Considered**: Azure Communication Services Email
- No free tier (~$0.25 per 1,000 emails)
- No output binding (SDK only)
- Newer service, less mature

### 2. Non-Fatal Email Send Failures

**Decision**: Email failures don't break core functionality

**Rationale**:
- ✅ **Core value**: Video summarization + Notion integration
- ✅ **Email is notification layer** (not critical path)
- ✅ **Azure Communication Services binding has retry logic** (transient failures auto-retried)
- ✅ **User gets HTTP response** regardless of email status

### 3. Failure Email for Partial Success (Notion Fails)

**Decision**: Send failure email when Notion fails, even if summary succeeds

**Rationale**:
- ✅ **User expectation**: End-to-end success (summary + Notion)
- ✅ **Aligned with request**: "notify me when it successfully publishes a page in notion"
- ✅ **Actionable**: User can debug Notion configuration
- ✅ **Summary still available** in HTTP response

### 4. Rate Limit Errors Trigger Emails

**Decision**: Send email for every rate limit rejection

**Rationale**:
- ✅ **Comprehensive error reporting** (all failures notified)
- ✅ **Rate limit already prevents spam** (max 30/hour)
- ✅ **User awareness**: Know when requests are blocked

**Mitigation**: User can configure email filters if needed.

---

## Future Enhancements

After successful implementation:

1. **Email Templates**
   - Store HTML templates in separate files
   - Support template customization
   - Add rich media (video thumbnails, embedded players)

2. **Email Preferences**
   - Allow users to configure notification types (success only, failures only, all)
   - Support multiple recipient emails
   - Email digest (daily summary instead of per-request)

3. **Azure Communication Services Features**
   - Click tracking (monitor Notion link clicks)
   - Open tracking (verify email receipt)
   - Categories/tags for filtering in Azure Communication Services dashboard

4. **Advanced Error Handling**
   - Retry logic for transient Notion failures
   - Exponential backoff for rate-limited users
   - Batch email notifications (group multiple errors)

5. **Monitoring & Analytics**
   - Application Insights custom events for email sends
   - Azure Communication Services webhook integration (delivery status)
   - Email delivery rate dashboards

---

## Timeline Estimate

| Phase | Task | Estimated Time |
|-------|------|----------------|
| 1 | Azure Communication Services account setup + sender verification | 15 minutes |
| 2 | Store API key in Key Vault | 5 minutes |
| 3 | Update requirements.txt + install | 5 minutes |
| 4 | Configure Function App settings | 10 minutes |
| 5 | Code integration (function_app.py changes) | 1-2 hours |
| 6 | Local testing (success + failure scenarios) | 1 hour |
| 7 | Documentation updates | 30 minutes |
| 8 | Production deployment + testing | 30 minutes |
| **Total** | **End-to-end implementation** | **3.5-4.5 hours** |

---

## References

### Azure Communication Services Documentation
- [Azure Communication Services Getting Started](https://docs.Azure Communication Services.com/for-developers/sending-email/api-getting-started)
- [Sender Verification](https://docs.Azure Communication Services.com/ui/sending-email/sender-verification)
- [Azure Communication Services API Keys](https://docs.Azure Communication Services.com/ui/account-and-settings/api-keys)
- [Email Activity Feed](https://docs.Azure Communication Services.com/ui/analytics-and-reporting/email-activity-feed)

### Azure Functions Documentation
- [Azure Communication Services Output Binding](https://learn.microsoft.com/azure/azure-functions/functions-bindings-Azure Communication Services)
- [Azure Functions Python Guide](https://learn.microsoft.com/azure/azure-functions/functions-reference-python)
- [Output Bindings Concepts](https://learn.microsoft.com/azure/azure-functions/functions-triggers-bindings#binding-direction)

### Azure Key Vault
- [Key Vault Best Practices](https://learn.microsoft.com/azure/key-vault/general/best-practices)
- [Key Vault References in App Settings](https://learn.microsoft.com/azure/app-service/app-service-key-vault-references)

### Project Files
- `services/email_service.py` - EmailService implementation (already complete)
- `function_app.py` - Main function logic (requires integration)
- `utils/exceptions.py` - Custom exceptions
- `.github/prompts/agent.md` - Architecture guidelines

---

## Appendix: EmailService Class Reference

The `EmailService` class (already implemented in `services/email_service.py`) provides:

### Methods

**`__init__(from_email: str, to_email: str)`**
- Initializes service with sender and recipient emails
- Validates emails are not empty
- Logs initialization

**`format_success_email(youtube_url: str, notion_url: str, summary: dict) -> Dict[str, Any]`**
- Creates Azure Communication Services-compatible success email data
- Includes video title, brief summary, Notion link button
- Returns dict with `personalizations`, `from`, `subject`, `content` keys

**`format_failure_email(youtube_url: str, error: str) -> Dict[str, Any]`**
- Creates Azure Communication Services-compatible failure email data
- Includes error message in styled code block
- Returns same structure as success email

### Usage Example

```python
# Initialize
email_service = EmailService(
    from_email="noreply@yourdomain.com",
    to_email="notifications@yourdomain.com"
)

# Success email
email_data = email_service.format_success_email(
    youtube_url="https://youtube.com/watch?v=abc",
    notion_url="https://notion.so/page-id",
    summary={"title": "Video Title", "brief_summary": "..."}
)
Azure Communication ServicesMessage.set(json.dumps(email_data))

# Failure email
email_data = email_service.format_failure_email(
    youtube_url="https://youtube.com/watch?v=xyz",
    error="Invalid video ID"
)
Azure Communication ServicesMessage.set(json.dumps(email_data))
```

---

**End of Plan**
````

