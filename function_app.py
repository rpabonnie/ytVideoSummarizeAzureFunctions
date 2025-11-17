import azure.functions as func
import logging
import json
import os
from datetime import datetime, timedelta
from collections import deque

from services.gemini_service import GeminiService
from services.notion_service import NotionService
from utils.validators import validate_youtube_url, validate_request_body
from utils.exceptions import (
    InvalidYouTubeUrlError,
    GeminiApiError,
    KeyVaultError
)

app = func.FunctionApp(http_auth_level=func.AuthLevel.ADMIN)

# Initialize services at module level (singleton pattern)
# This allows reuse across requests and caches Key Vault credentials
gemini_service: GeminiService | None = None
notion_service: NotionService | None = None

# Rate limiting configuration (dev/testing phase)
RATE_LIMIT_PER_HOUR = 30
request_timestamps = deque()  # Stores timestamps of requests in the last hour


def _initialize_services():
    """Initialize services with Key Vault URL from environment."""
    global gemini_service, notion_service
    
    if gemini_service is None:
        key_vault_url = os.environ.get("KEY_VAULT_URL")
        if not key_vault_url:
            raise ValueError("KEY_VAULT_URL environment variable not configured")
        
        logging.info("Initializing services...")
        gemini_service = GeminiService(key_vault_url)
        notion_service = NotionService(key_vault_url)
        logging.info("Services initialized successfully")


def _check_rate_limit() -> tuple[bool, int]:
    """
    Check if request is within rate limit (30 requests per hour).
    
    Returns:
        Tuple of (is_allowed, requests_in_last_hour)
    """
    now = datetime.utcnow()
    one_hour_ago = now - timedelta(hours=1)
    
    # Remove timestamps older than 1 hour
    while request_timestamps and request_timestamps[0] < one_hour_ago:
        request_timestamps.popleft()
    
    current_count = len(request_timestamps)
    
    if current_count >= RATE_LIMIT_PER_HOUR:
        return False, current_count
    
    # Add current request timestamp
    request_timestamps.append(now)
    return True, current_count + 1

@app.route(route="ytSummarizeToNotion", methods=["POST"])
def ytSummarizeToNotion(req: func.HttpRequest) -> func.HttpResponse:
    """
    Secure Azure Function that accepts YouTube URLs and generates summaries using Gemini.
    
    This function orchestrates the video summarization workflow:
    1. Validates request and YouTube URL
    2. Summarizes video using GeminiService
    3. (Future) Creates Notion page with NotionService
    4. (Future) Sends email notification
    
    Requires ADMIN authentication (x-functions-key header).
    Rate limited to 30 requests per hour (dev/testing phase).
    
    Args:
        req: HTTP request with JSON body containing 'url' field
        
    Returns:
        HTTP response with JSON summary or error message
    """
    logging.info('YouTube Summarize to Notion function triggered.')
    
    try:
        # Initialize services (lazy initialization on first request)
        _initialize_services()
        
        # Step 1: Check rate limit (30 requests per hour)
        is_allowed, request_count = _check_rate_limit()
        if not is_allowed:
            logging.warning(f"Rate limit exceeded: {request_count} requests in the last hour")
            return func.HttpResponse(
                json.dumps({
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {RATE_LIMIT_PER_HOUR} requests per hour allowed. Please try again later.",
                    "requests_in_last_hour": request_count
                }),
                status_code=429,
                mimetype="application/json"
            )
        
        logging.info(f"Rate limit check passed: {request_count}/{RATE_LIMIT_PER_HOUR} requests in last hour")
        
        # Step 2: Parse request body
        try:
            req_body = req.get_json()
        except ValueError as e:
            logging.error(f"Invalid JSON in request body: {str(e)}")
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON format"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Step 2: Validate request body structure
        try:
            validate_request_body(req_body)
        except InvalidYouTubeUrlError as e:
            logging.error(f"Request validation failed: {e.message}")
            return func.HttpResponse(
                json.dumps({"error": e.message}),
                status_code=e.status_code,
                mimetype="application/json"
            )
        
        # Step 3: Validate and sanitize YouTube URL
        try:
            youtube_url = req_body.get('url', '')
            sanitized_url = validate_youtube_url(youtube_url)
            logging.info(f"Processing YouTube URL: {sanitized_url}")
        except InvalidYouTubeUrlError as e:
            logging.error(f"URL validation failed: {e.message}")
            return func.HttpResponse(
                json.dumps({"error": e.message}),
                status_code=e.status_code,
                mimetype="application/json"
            )
        
        # Step 4: Summarize video using GeminiService
        try:
            if gemini_service is None:
                raise ValueError("GeminiService not initialized")
            
            summary = gemini_service.summarize_video(sanitized_url)
            logging.info("Video summarized successfully")
            
        except KeyVaultError as e:
            logging.error(f"Key Vault error: {e.message}")
            return func.HttpResponse(
                json.dumps({"error": e.message}),
                status_code=e.status_code,
                mimetype="application/json"
            )
        except GeminiApiError as e:
            logging.error(f"Gemini API error: {e.message}")
            return func.HttpResponse(
                json.dumps({"error": e.message}),
                status_code=e.status_code,
                mimetype="application/json"
            )
        
        # Step 5: Return success response
        # (Notion integration will be added in future phase)
        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "youtube_url": sanitized_url,
                "summary": summary,
                "note": "Video summarized successfully. Notion integration pending."
            }, indent=2),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        # Catch-all for unexpected errors
        logging.error(f"Unexpected error: {str(e)}", exc_info=True)
        return func.HttpResponse(
            json.dumps({"error": "Internal server error. Check function logs for details."}),
            status_code=500,
            mimetype="application/json"
        )
