````prompt
# Plan: Integrate Azure Communication Services Email with Comprehensive Error Reporting

Implement email notification functionality using Azure Communication Services (ACS) Email to notify when Notion pages are successfully created and send detailed alerts for all errors and failures during video processing.

## Overview

This plan adds Azure Communication Services Email integration to the YouTube Video Summarizer Azure Function. The existing `EmailService` class will be adapted to use the ACS Email SDK with both success and failure email templates. This implementation will ensure notifications for:

- ✅ **Success notifications**: When videos are successfully summarized and Notion pages created
- ❌ **Failure notifications**: For all error scenarios (rate limits, invalid URLs, API failures, etc.)
- 📧 **Professional HTML emails**: With formatted content, links, and error details

## Architecture

### Email Flow
```
Azure Function → EmailService → ACS Email SDK → ACS Email API → Email Delivery
     ↓                                                              ↓
Error Occurs                                                User Notification
     ↓
EmailService.send_failure_email()
     ↓
ACS Email HTML Content
```

### Azure Communication Services Email Benefits
- **Azure-native integration**: First-party Microsoft service with seamless Azure integration
- **Managed Identity support**: Optional passwordless authentication for production
- **Free Azure-managed domains**: No DNS verification required
- **Reliable delivery**: Enterprise-grade email infrastructure

## Implementation Steps

### Step 1: Provision Azure Communication Services Email

#### 1.1 Create Email Communication Services Resource via Azure Marketplace

**Option A: Azure Portal (Recommended)**
1. Navigate to Azure Portal → **Create a resource** or search in Marketplace
2. Search for **"Email Communication Services"** (also listed as "Email Communication Service")
3. Click **"Create"**
4. Fill in the **Basics** tab:
   - **Subscription**: Select your Azure subscription
   - **Resource Group**: Same as Function App (e.g., `rpabonnie-personal`)
   - **Name**: Globally unique name (e.g., `rpc-email-alerts`)
   - **Region**: Automatic (**Global**)
   - **Data Location**: **United States** (required for email services)
5. Click **"Review + Create"** → **"Create"**
6. Wait for deployment (~1-2 minutes)
7. Once deployed, click **"Go to resource"**

**Option B: Azure CLI**
```powershell
# Note: Requires 'communication' extension
az extension add --name communication

# Create Email Communication Services resource
# Note: The resource type is 'communication' not 'communication email'
az communication create `
  --name rpc-email-alerts `
  --location "Global" `
  --data-location "United States" `
  --resource-group rpabonnie-personal

# Verify creation
az communication show `
  --name rpc-email-alerts `
  --resource-group rpabonnie-personal
```

**⚠️ Important Notes**:
- The resource name must be globally unique across all Azure subscriptions
- Data location is fixed to "United States" for email services
- The Azure Portal may show this as "Email Communication Service" (singular) in some places

#### 1.2 Provision Azure-Managed Domain (Free Sender Address)

**Azure Portal (Recommended):**
1. Navigate to your Email Communication Services resource (`rpc-email-alerts`)
2. In the left sidebar, click **"Provision domains"** under Settings
3. Click **"+ Add domain"** button at the top
4. Select **"Azure Managed Domain"**
5. Click **"Add"**
6. Wait for provisioning (~2-5 minutes)
7. Once provisioned, you'll see the domain listed with:
   - **Domain name**: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.azurecomm.net` (format may show as `bdba1f9f-569d-42e9-b923-2e84691...`)
   - **Domain type**: "Azure subdomain"
   - **Domain status**: "Verified" (with green checkmark)
   - **SPF status**: "Verified"
   - **DKIM status**: "Verified"
   - **DKIM2 status**: "Verified"
8. Click on the domain name to view details
9. In the domain details, under **"MailFrom addresses"**, you'll find your sender address: `DoNotReply@xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.azurecomm.net`

**⚠️ Note**: 
- Azure-managed domains require **no DNS configuration** and are immediately ready for sending emails
- The domain is automatically verified with SPF, DKIM, and DKIM2 authentication
- For custom domains (like yourcompany.com), additional DNS verification is required
- You can add multiple sender usernames to this domain later (e.g., `alerts@`, `notifications@`)

#### 1.3 Get Connection String

**Azure Portal (Primary Method):**
1. Navigate to your Email Communication Services resource (`rpc-email-alerts`)
2. In the left sidebar, click **"Keys"** under Settings
3. You'll see two connection strings:
   - **Primary connection string**
   - **Secondary connection string**
4. Copy the **Primary connection string**
   - Format: `endpoint=https://rpc-email-alerts.unitedstates.communication.azure.com/;accesskey=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

**Azure CLI (Alternative Method):**
```powershell
# First, install the Azure Communication Services CLI extension if not already installed
az extension add --name communication

# List keys for the Communication Services resource
az communication list-key `
  --name rpc-email-alerts `
  --resource-group rpabonnie-personal

# This returns both primaryKey and secondaryKey
# You'll need to construct the connection string manually:
# endpoint=https://<resource-name>.unitedstates.communication.azure.com/;accesskey=<primaryKey>
```

**⚠️ Important**: 
- The Azure Portal method is recommended as it provides the complete connection string ready to use
- The CLI method requires manual construction of the connection string from the endpoint and key
- Keep these credentials secure - they provide full access to send emails from your domain

#### 1.4 Store Connection String in Azure Key Vault

**Local Development:**
```powershell
# Set variables
$vaultName = "<your-keyvault-name>"
$acsConnectionString = "<paste-connection-string>"

# Store secret
az keyvault secret set `
  --vault-name $vaultName `
  --name "ACS-CONNECTION-STRING" `
  --value $acsConnectionString

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
4. **Value**: Paste connection string
5. Click "Create"

#### 1.5 Configure Sender Address Environment Variable

**Get Your Sender Address:**
1. In Azure Portal, navigate to your Email Communication Services resource
2. Go to **"Provision domains"**
3. Click on your Azure-managed domain (e.g., `bdba1f9f-569d-42e9-b923-2e84691...`)
4. Under **"MailFrom addresses"**, copy the default sender address
   - Format: `DoNotReply@xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.azurecomm.net`

**Add to Function App Application Settings:**
```powershell
# Replace with your actual sender address from step above
az functionapp config appsettings set `
  --name <your-function-app-name> `
  --resource-group <your-rg> `
  --settings "ACS_SENDER_EMAIL=DoNotReply@xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.azurecomm.net"
```

**For local testing, add to `local.settings.json`:**
```json
{
  "Values": {
    "ACS_SENDER_EMAIL": "DoNotReply@xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.azurecomm.net"
  }
}
```

**⚠️ Note**: 
- The sender address must exactly match one of the MailFrom addresses in your provisioned domain
- You can add custom sender usernames later (e.g., `alerts@`, `notifications@`) using the Azure Portal or Management SDK


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

Add Azure Communication Services configuration to Azure Function App settings.

#### 3.1 Configure ACS Connection String

**Option A: Direct Key Vault Reference (Recommended)**
```powershell
# Set Function App name and resource group
$functionApp = "<your-function-app-name>"
$resourceGroup = "<your-resource-group>"
$keyVaultUrl = "<your-keyvault-url>"  # e.g., https://myvault.vault.azure.net/

# Add ACS Connection String as Key Vault reference
az functionapp config appsettings set `
  --name $functionApp `
  --resource-group $resourceGroup `
  --settings "ACS_CONNECTION_STRING=@Microsoft.KeyVault(SecretUri=${keyVaultUrl}/secrets/ACS-CONNECTION-STRING/)"
```

**Option B: Direct Value (Less Secure - Not Recommended)**
```powershell
# Retrieve secret from Key Vault
$acsConnectionString = az keyvault secret show `
  --vault-name $vaultName `
  --name "ACS-CONNECTION-STRING" `
  --query "value" `
  --output tsv

# Set as app setting
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
    "ACS_SENDER_EMAIL=DoNotReply@xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.azurecomm.net" `
    "EMAIL_TO=<your-notification-email@domain.com>"
```

**Important:**
- `ACS_SENDER_EMAIL` should be the Azure-managed domain address from Step 1.2
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
    "ACS_CONNECTION_STRING": "<paste-connection-string-for-local-testing>",
    "ACS_SENDER_EMAIL": "DoNotReply@xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.azurecomm.net",
    "EMAIL_TO": "<your-email@domain.com>"
  }
}
```

**⚠️ Security Note**: 
- `local.settings.json` is in `.gitignore` (never commit secrets)
- Use Key Vault references in production
- For local testing, you can paste the ACS connection string directly

**Actions:**
- Update `local.settings.json` with ACS settings
- Configure Function App settings in Azure Portal or via CLI
- Verify settings: `az functionapp config appsettings list --name $functionApp --resource-group $resourceGroup`

---

### Step 4: Integrate EmailService into Function App

Modify `function_app.py` to initialize `EmailService` and send notifications for success/failure scenarios using the Azure Communication Services SDK.

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
        
        # Initialize EmailService with ACS
        acs_connection_string = os.environ.get("ACS_CONNECTION_STRING")
        acs_sender_email = os.environ.get("ACS_SENDER_EMAIL")
        to_email = os.environ.get("EMAIL_TO")
        
        if acs_connection_string and acs_sender_email and to_email:
            email_service = EmailService(
                connection_string=acs_connection_string,
                sender_email=acs_sender_email,
                recipient_email=to_email
            )
            logging.info("EmailService initialized successfully with ACS")
        else:
            logging.warning("Email configuration missing (ACS_CONNECTION_STRING/ACS_SENDER_EMAIL/EMAIL_TO). Email notifications disabled.")
        
        logging.info("Services initialized successfully")
```

#### 4.2 Send Success Emails

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
            email_service.send_success_email(
                youtube_url=sanitized_url,
                notion_url=notion_url,
                summary=summary
            )
            logging.info("Success email notification sent via ACS")
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
    sendGridMessage: func.Out[str],
    youtube_url: str,
    error_message: str
):
    """
    Send failure notification email using ACS Email SDK.
    
    Args:
        youtube_url: YouTube URL that failed processing
        error_message: Error description
    """
    if email_service:
        try:
            email_service.send_failure_email(
                youtube_url=youtube_url,
                error=error_message
            )
            logging.info("Failure email notification sent via ACS")
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
        req_body.get('url', 'Unknown URL') if 'req_body' in locals() else 'Unknown',
        f"Internal server error: {str(e)}"
    )
    
    return func.HttpResponse(...)
```

**Actions:**
- Add `EmailService` import and initialization
- Implement `_send_failure_email()` helper function (no output binding needed)
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
        email_service.send_failure_email(
            youtube_url=sanitized_url,
            error=error_msg
        )
        logging.info("Partial failure email notification sent")
    except Exception as e:
        logging.warning(f"Failed to send partial failure email: {str(e)}")
```

#### 5.3 Email Send Failure Handling

**Question**: Should email send failures block function execution?

**Recommendation**: **Non-fatal** (log warnings only)
- Rationale: Core functionality (summarization, Notion) more important than notifications
- Email delivery is best-effort
- ACS SDK has retry mechanisms built in

**Implementation**: Wrap all email send calls in try-except (already in plan).

---

### Step 6: Testing Strategy

#### 6.1 Local Testing Setup

**Prerequisites:**
1. ✅ SendGrid account created
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

4. **Verify SendGrid Activity**
   - SendGrid Portal → Activity Feed
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
- 📧 **Email Notifications**: Success and failure alerts via SendGrid
- 🔐 **Secure**: Secrets managed via Azure Key Vault
- ☁️ **Serverless**: Scales automatically with Azure Functions
```

**Add Email Setup section:**
```markdown
## Email Notifications Setup

The function sends email notifications via SendGrid for:
- ✅ Successful Notion page creation
- ❌ All error scenarios (rate limits, invalid URLs, API failures)

### Setup Steps

1. **Create SendGrid Account**
   - Azure Portal → Marketplace → SendGrid Email Delivery
   - Select **Free tier** (25,000 emails/month)

2. **Get API Key**
   - SendGrid Portal → Settings → API Keys → Create API Key
   - Permissions: Mail Send (Full Access)

3. **Verify Sender Email**
   - SendGrid Portal → Settings → Sender Authentication
   - Verify Single Sender → Enter your email → Confirm verification email

4. **Store API Key**
   ```powershell
   az keyvault secret set \
     --vault-name <vault> \
     --name "SENDGRID-API-KEY" \
     --value "<sendgrid-api-key>"
   ```

5. **Configure Function App**
   ```powershell
   az functionapp config appsettings set \
     --name <app-name> \
     --resource-group <rg> \
     --settings \
       "SendGridApiKey=@Microsoft.KeyVault(...)" \
       "EMAIL_FROM=<verified-sender@domain.com>" \
       "EMAIL_TO=<your-email@domain.com>"
   ```

See [SendGrid Documentation](https://docs.sendgrid.com/) for details.
```

**Update Prerequisites:**
```markdown
## Prerequisites

- **Python 3.13**
- **Azure Subscription**
- **Azure Functions Core Tools**
- **Google Gemini API Key**
- **Notion Account** (with integration created)
- **SendGrid Account** (free tier) ← Add this
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
    "SendGridApiKey": "<sendgrid-api-key>",
    "EMAIL_FROM": "<verified-sender@domain.com>",
    "EMAIL_TO": "<your-email@domain.com>"
  }
}
```

#### 7.3 Create Email Setup Documentation (Optional)

**File**: `EMAIL_SETUP.md`

Optional detailed guide similar to `NOTION_SETUP.md`, covering:
- SendGrid account creation
- API key generation
- Sender verification (Single Sender vs Domain Authentication)
- Azure Key Vault integration
- Troubleshooting email delivery issues

---

## Security Considerations

### 1. API Key Management

- ✅ **SendGrid API Key stored in Azure Key Vault**
- ✅ **Key Vault reference in Function App settings** (not direct value)
- ✅ **Managed Identity access** to Key Vault (no credentials in code)
- ✅ **Local development**: API key in `local.settings.json` (gitignored)
- ❌ **Never log SendGrid API keys**

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

- ✅ **Function rate limit** (30 requests/hour) prevents SendGrid abuse
- ✅ **SendGrid free tier**: 25,000 emails/month
- ⚠️ **Monitor SendGrid usage** to avoid exceeding free tier

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

All `sendGridMessage.set()` calls wrapped in try-except:
- ✅ **Non-fatal**: Email failures don't break core functionality
- ✅ **Logged as warnings**: `logging.warning("Failed to send email: ...")`
- ✅ **Best-effort delivery**: SendGrid binding has automatic retry

---

## Implementation Checklist

### SendGrid Provisioning
- [ ] Create SendGrid account in Azure Marketplace (free tier)
- [ ] Generate SendGrid API key (Mail Send permissions)
- [ ] Verify sender email address (Single Sender Verification)
- [ ] Store API key in Azure Key Vault (`SENDGRID-API-KEY`)

### Code Changes
- [ ] Add `azure-functions-sendgrid` to `requirements.txt`
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Update `function_app.py`:
  - [ ] Import `EmailService`
  - [ ] Add `email_service` global variable
  - [ ] Initialize EmailService in `_initialize_services()`
  - [ ] Add `@app.send_grid_output` decorator
  - [ ] Add `sendGridMessage` parameter
  - [ ] Implement `_send_failure_email()` helper
  - [ ] Add success email after Notion creation
  - [ ] Add failure emails in all error blocks

### Configuration
- [ ] Update `local.settings.json` with SendGrid settings
- [ ] Configure Function App settings (Azure):
  - [ ] `SendGridApiKey` (Key Vault reference)
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
  - [ ] Verify SendGrid Activity Feed

### Documentation
- [ ] Update `README.md`:
  - [ ] Add email notifications to Features
  - [ ] Add SendGrid to Prerequisites
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
5. SendGrid account provisioned (free tier)
6. Sender email verified
7. API key stored in Key Vault
8. Function App settings configured

✅ **Testing**
9. Local testing passes (success + failure scenarios)
10. Production deployment successful
11. Email delivery verified in SendGrid Activity Feed
12. All links in emails functional

✅ **Documentation**
13. README.md updated with setup instructions
14. Configuration templates updated
15. (Optional) EMAIL_SETUP.md created

---

## Design Decisions & Rationale

### 1. SendGrid vs. Azure Communication Services Email

**Decision**: Use SendGrid

**Rationale**:
- ✅ **25,000 free emails/month** (ACS has no free tier)
- ✅ **Output binding** available (declarative, minimal code)
- ✅ **Existing EmailService** already designed for SendGrid
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
- ✅ **SendGrid binding has retry logic** (transient failures auto-retried)
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

3. **SendGrid Features**
   - Click tracking (monitor Notion link clicks)
   - Open tracking (verify email receipt)
   - Categories/tags for filtering in SendGrid dashboard

4. **Advanced Error Handling**
   - Retry logic for transient Notion failures
   - Exponential backoff for rate-limited users
   - Batch email notifications (group multiple errors)

5. **Monitoring & Analytics**
   - Application Insights custom events for email sends
   - SendGrid webhook integration (delivery status)
   - Email delivery rate dashboards

---

## Timeline Estimate

| Phase | Task | Estimated Time |
|-------|------|----------------|
| 1 | SendGrid account setup + sender verification | 15 minutes |
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

### SendGrid Documentation
- [SendGrid Getting Started](https://docs.sendgrid.com/for-developers/sending-email/api-getting-started)
- [Sender Verification](https://docs.sendgrid.com/ui/sending-email/sender-verification)
- [SendGrid API Keys](https://docs.sendgrid.com/ui/account-and-settings/api-keys)
- [Email Activity Feed](https://docs.sendgrid.com/ui/analytics-and-reporting/email-activity-feed)

### Azure Functions Documentation
- [SendGrid Output Binding](https://learn.microsoft.com/azure/azure-functions/functions-bindings-sendgrid)
- [Azure Functions Python Guide](https://learn.microsoft.com/azure/azure-functions/functions-reference-python)
- [Output Bindings Concepts](https://learn.microsoft.com/azure/azure-functions/functions-triggers-bindings#binding-direction)

### Azure Key Vault
- [Key Vault Best Practices](https://learn.microsoft.com/azure/key-vault/general/best-practices)
- [Key Vault References in App Settings](https://learn.microsoft.com/azure/app-service/app-service-key-vault-references)

### Azure Communication Services
- [Azure Communication Services Email Overview](https://learn.microsoft.com/azure/communication-services/concepts/email/email-overview)
- [Email Quickstart](https://learn.microsoft.com/azure/communication-services/quickstarts/email/send-email)
- [Azure Communication Services Python SDK](https://learn.microsoft.com/python/api/overview/azure/communication-email-readme)

### Project Files
- `services/email_service.py` - EmailService implementation (requires ACS SDK adaptation)
- `function_app.py` - Main function logic (requires integration)
- `utils/exceptions.py` - Custom exceptions
- `.github/prompts/agent.md` - Architecture guidelines

---

## Appendix: Updated EmailService Class Reference

The `EmailService` class in `services/email_service.py` should be updated to use the Azure Communication Services Email SDK:

### Required Changes

**Original SendGrid Output Binding Approach:**
- Methods returned dictionaries for SendGrid output binding
- `format_success_email()` and `format_failure_email()` returned dict structures

**New ACS SDK Approach:**
- Methods should send emails directly using `EmailClient`
- Rename methods to `send_success_email()` and `send_failure_email()`
- Return boolean indicating success/failure instead of dict

### Updated Class Structure

**`__init__(connection_string: str, sender_email: str, recipient_email: str)`**
- Initializes `EmailClient` with connection string
- Stores sender and recipient email addresses
- Validates all parameters are provided
- Logs initialization

**`send_success_email(youtube_url: str, notion_url: str, summary: dict) -> bool`**
- Sends success notification email via ACS Email SDK
- Constructs HTML email content with video title, summary, Notion link
- Uses `EmailClient.begin_send()` method
- Returns `True` on success, `False` on failure
- Logs email send operations

**`send_failure_email(youtube_url: str, error: str) -> bool`**
- Sends failure notification email via ACS Email SDK
- Constructs HTML email content with error details
- Returns `True` on success, `False` on failure
- Logs email send operations

### Usage Example (Updated for ACS)

```python
from azure.communication.email import EmailClient

# Initialize
email_service = EmailService(
    connection_string="endpoint=https://...;accesskey=...",
    sender_email="DoNotReply@xxxxxxxx.azurecomm.net",
    recipient_email="notifications@yourdomain.com"
)

# Success email - returns boolean
success = email_service.send_success_email(
    youtube_url="https://youtube.com/watch?v=abc",
    notion_url="https://notion.so/page-id",
    summary={"title": "Video Title", "brief_summary": "..."}
)

# Failure email - returns boolean
success = email_service.send_failure_email(
    youtube_url="https://youtube.com/watch?v=xyz",
    error="Invalid video ID"
)
```

### ACS Email Message Structure

```python
# Example message structure for ACS SDK
message = {
    "content": {
        "subject": "Email Subject",
        "html": "<html><body>Email content</body></html>"
    },
    "recipients": {
        "to": [{"address": "recipient@domain.com"}]
    },
    "senderAddress": "DoNotReply@xxxxxxxx.azurecomm.net"
}

# Send email
poller = email_client.begin_send(message)
result = poller.result()
```

---

**End of Plan**
````
