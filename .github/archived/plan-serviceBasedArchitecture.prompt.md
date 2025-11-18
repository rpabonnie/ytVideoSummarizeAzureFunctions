# Plan: Refactor to Service-Based Architecture with Security Enhancements

Restructure `function_app.py` into modular services for Gemini AI, Notion integration, and email notifications, implementing secure URL validation and following Azure Functions best practices.

## Implementation Steps

### 1. Create Service Layer Structure
Following `agent.md` guidelines, establish the recommended project structure:

```
ytVideoSummarizeAzureFunction/
├── function_app.py          # Function definitions only (orchestration)
├── services/
│   ├── __init__.py
│   ├── gemini_service.py    # AI summarization logic
│   ├── notion_service.py    # Notion API interactions
│   └── email_service.py     # Email notification service
├── utils/
│   ├── __init__.py
│   ├── validators.py        # YouTube URL validation
│   └── exceptions.py        # Custom exception classes
└── tests/
    ├── __init__.py
    ├── test_validators.py
    └── test_services.py
```

**Actions:**
- Create `services/` directory with `__init__.py`
- Create `utils/` directory with `__init__.py`
- Create `tests/` directory with `__init__.py`

### 2. Implement Secure YouTube URL Validator
Create `utils/validators.py` with comprehensive URL validation to protect against malicious attacks.

**Security Requirements:**
- **HTTPS only** - Reject HTTP URLs
- **Domain whitelist** - Allow only: `youtube.com`, `www.youtube.com`, `m.youtube.com`, `youtu.be`
- **Video ID validation** - Regex pattern: `[a-zA-Z0-9_-]{11}` (YouTube's standard format)
- **Path traversal prevention** - Block `../`, `./`, encoded variants
- **Injection prevention** - Sanitize special characters, block script tags
- **Query parameter filtering** - Allow only safe params: `v`, `t`, `list`; strip tracking params

**Validation Function:**
```python
def validate_youtube_url(url: str) -> str:
    """
    Validates and sanitizes YouTube URL.
    
    Args:
        url: YouTube URL to validate
        
    Returns:
        Sanitized YouTube URL
        
    Raises:
        InvalidYouTubeUrlError: If URL is invalid or potentially malicious
    """
```

**Validation Steps:**
1. Parse URL using `urllib.parse`
2. Verify scheme is `https`
3. Validate domain against whitelist
4. Extract video ID (from `v` param or path for `youtu.be`)
5. Validate video ID format with regex
6. Reconstruct clean URL with only allowed parameters
7. Return sanitized URL

### 3. Create Custom Exception Classes
Create `utils/exceptions.py` for cleaner error handling.

**Exception Hierarchy:**
```python
class YouTubeSummarizerError(Exception):
    """Base exception for YouTube Summarizer"""
    pass

class InvalidYouTubeUrlError(YouTubeSummarizerError):
    """Raised when YouTube URL is invalid or malicious"""
    pass

class GeminiApiError(YouTubeSummarizerError):
    """Raised when Gemini API call fails"""
    pass

class NotionApiError(YouTubeSummarizerError):
    """Raised when Notion API call fails"""
    pass

class KeyVaultError(YouTubeSummarizerError):
    """Raised when Key Vault access fails"""
    pass
```

### 4. Implement GeminiService Class
Create `services/gemini_service.py` extracting all Gemini-related logic from `function_app.py`.

**Class Structure:**
```python
class GeminiService:
    """Service for YouTube video summarization using Google Gemini AI"""
    
    def __init__(self, key_vault_url: str):
        """Initialize service with Key Vault URL"""
        
    def _get_api_key(self) -> str:
        """Retrieve Gemini API key from Azure Key Vault"""
        
    def _build_prompt(self, youtube_url: str) -> str:
        """Generate structured prompt for Gemini"""
        
    def _parse_response(self, response_text: str) -> dict:
        """Parse and validate Gemini response as JSON"""
        
    def summarize_video(self, youtube_url: str) -> dict:
        """
        Main method: Summarize YouTube video using Gemini.
        
        Args:
            youtube_url: Validated YouTube URL
            
        Returns:
            dict: Structured summary with title, tags, bullets, etc.
            
        Raises:
            GeminiApiError: If API call fails
        """
```

**Implementation Details:**
- Use singleton pattern for Key Vault client (initialized once)
- Use module-level caching for API key (retrieve once per cold start)
- Maintain existing Gemini configuration (model: `gemini-2.5-pro`, LOW media resolution)
- Keep existing prompt structure and JSON parsing logic
- Add comprehensive error handling with custom exceptions

### 5. Refactor function_app.py
Update `function_app.py` to use service layer (orchestration only).

**New Structure:**
```python
from services.gemini_service import GeminiService
from services.notion_service import NotionService
from services.email_service import EmailService
from utils.validators import validate_youtube_url
from utils.exceptions import InvalidYouTubeUrlError, GeminiApiError

# Initialize services at module level (singleton pattern)
gemini_service = None
notion_service = None

@app.route(route="ytSummarizeToNotion", methods=["POST"])
def ytSummarizeToNotion(req: func.HttpRequest) -> func.HttpResponse:
    """Orchestrator function - delegates to services"""
    
    # 1. Parse request
    # 2. Validate YouTube URL using utils.validators
    # 3. Call gemini_service.summarize_video()
    # 4. Call notion_service.create_page() (future)
    # 5. Call email_service.send_notification() (future)
    # 6. Return response
```

**Error Handling:**
- Catch `InvalidYouTubeUrlError` → Return 400 Bad Request
- Catch `GeminiApiError` → Return 500 Internal Server Error
- Catch `KeyVaultError` → Return 500 with auth guidance
- Catch generic `Exception` → Return 500 with minimal details

### 6. Add NotionService Class Skeleton
Create `services/notion_service.py` with placeholder methods.

**Class Structure:**
```python
class NotionService:
    """Service for creating Notion pages from video summaries"""
    
    def __init__(self, key_vault_url: str):
        """Initialize service with Key Vault URL"""
        
    def _get_api_key(self) -> str:
        """Retrieve Notion API key from Azure Key Vault"""
        
    def create_page(self, summary_data: dict) -> str:
        """
        Create Notion page with video summary.
        
        Args:
            summary_data: Summary dict from GeminiService
            
        Returns:
            str: Notion page URL
            
        Raises:
            NotionApiError: If page creation fails
        """
        # TODO: Implement Notion API integration
        raise NotImplementedError("Notion integration pending")
```

### 7. Implement Email Notification Service
Create `services/email_service.py` for Azure Functions SendGrid output binding.

**Class Structure:**
```python
class EmailService:
    """Service for sending email notifications via SendGrid"""
    
    def format_success_email(self, youtube_url: str, notion_url: str, summary: dict) -> dict:
        """
        Format success notification email.
        
        Returns:
            dict: Email data for SendGrid binding
        """
        
    def format_failure_email(self, youtube_url: str, error: str) -> dict:
        """
        Format failure notification email.
        
        Returns:
            dict: Email data for SendGrid binding
        """
```

**SendGrid Binding Configuration:**
- Add to `function_app.py` function signature (future enhancement)
- Configure `host.json` with SendGrid extension
- Add `SENDGRID_API_KEY` to Key Vault
- Format emails with HTML template

## Implementation Status

### ✅ Current State
- Working Azure Function with Gemini integration
- Key Vault authentication using DefaultAzureCredential
- Basic YouTube URL validation (domain check only)
- JSON response parsing with fallback handling

### 🔄 To Be Implemented
1. Service layer structure (directories and files)
2. Secure URL validator with comprehensive checks
3. Custom exception classes
4. GeminiService class extraction
5. function_app.py refactoring
6. NotionService skeleton
7. EmailService implementation
8. Unit tests for validators and services

## Further Considerations

### 1. Service Initialization Strategy
**Question:** Initialize services once at module level or per-request?

**Recommendation:** Module-level singleton pattern
- **Pros:** Reuse Key Vault clients, reduce cold start overhead, cache API keys
- **Cons:** Shared state across requests (not an issue for stateless services)
- **Implementation:** Initialize services outside function handler

### 2. URL Validator Strictness Level
**Question:** How strict should URL validation be?

**Recommendation:** Balanced approach
- Allow standard YouTube parameters: `v` (video ID), `t` (timestamp), `list` (playlist)
- Strip tracking parameters: `utm_*`, `si`, `feature`, etc.
- Block all path traversal attempts and encoded variants
- Reject URLs with fragments (`#`) or authentication (`user:pass@`)

### 3. Error Response Detail Level
**Question:** How much error detail to expose in API responses?

**Recommendation:** Security-first approach
- **Development:** Detailed error messages with stack traces
- **Production:** Generic messages for 500 errors, specific for 400 errors
- **Always:** Log full errors to Application Insights
- **Never:** Expose Key Vault URLs, API keys, or internal paths

### 4. Testing Strategy
**Question:** What level of testing is needed?

**Recommendation:** Prioritize security-critical components
- **Phase 1:** Unit tests for URL validator (critical security component)
- **Phase 2:** Integration tests with mocked Gemini/Notion APIs
- **Phase 3:** End-to-end tests with test Key Vault and test API keys

**Test Coverage Goals:**
- URL validator: 100% (security critical)
- Services: 80%+ (business logic)
- function_app.py: 70%+ (orchestration)

### 5. Obsolete Plan File
**Question:** What to do with `plan-geminiNotionAppleShortcuts.prompt.md`?

**Recommendation:** Archive for historical reference
- Create `context/archive/` directory
- Move old plan file to archive with timestamp
- Keep as documentation of initial implementation decisions
- Update README.md to reference new architecture plan

### 6. Key Vault Client Optimization
**Question:** How to minimize Key Vault calls?

**Recommendation:** Multi-level caching
- **Module-level cache:** Store API keys in memory during function lifetime
- **Refresh strategy:** TTL-based refresh (e.g., 1 hour) or manual invalidation
- **Cold start:** Accept first request latency for Key Vault retrieval
- **Error handling:** Fallback to environment variables if Key Vault unavailable (local dev only)

## Technical Details

### Dependencies
No new dependencies required - all packages already in `requirements.txt`:
- `azure-identity` - DefaultAzureCredential
- `azure-keyvault-secrets` - SecretClient
- `google-genai` - Gemini API
- `notion-client` - Notion API (future)

### Configuration Changes
**No changes required to:**
- `local.settings.json` - Already has KEY_VAULT_URL
- `requirements.txt` - All dependencies present
- `host.json` - Current configuration sufficient

**Future additions:**
- SendGrid extension configuration in `host.json`
- `SENDGRID_API_KEY` in Key Vault (for email notifications)

### Migration Path
**Step-by-step migration to avoid breaking changes:**
1. Create new service files alongside existing `function_app.py`
2. Test services individually with unit tests
3. Update `function_app.py` to use services while keeping old logic commented
4. Test refactored function locally
5. Remove old logic after successful testing
6. Deploy to Azure and monitor

## Success Criteria

### Functional Requirements
- ✅ Function accepts YouTube URLs and returns summaries (no regression)
- ✅ Enhanced URL validation prevents malicious URLs
- ✅ Modular services enable easy addition of Notion and email features
- ✅ Error handling provides clear feedback for different failure scenarios

### Non-Functional Requirements
- ✅ No performance degradation (maintain current latency)
- ✅ Code maintainability improved (separation of concerns)
- ✅ Security hardened (comprehensive URL validation)
- ✅ Testability enhanced (isolated service components)

## Next Actions

1. **Review and approve this plan** - Confirm architecture decisions
2. **Create directory structure** - `services/`, `utils/`, `tests/`
3. **Implement URL validator** - Start with security-critical component
4. **Write validator tests** - Ensure comprehensive coverage
5. **Extract GeminiService** - Refactor existing logic
6. **Update function_app.py** - Wire up services
7. **Test locally** - Verify no regressions
8. **Archive old plan** - Move to `context/archive/`

---

**Created:** November 16, 2025  
**Status:** 📋 Plan ready for review and implementation
