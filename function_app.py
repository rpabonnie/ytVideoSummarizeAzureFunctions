import azure.functions as func
import logging
import json
import os

from services.gemini_service import GeminiService
from services.notion_service import NotionService
from utils.validators import validate_youtube_url, validate_request_body
from utils.exceptions import (
    InvalidYouTubeUrlError,
    GeminiApiError,
    NotionApiError,
    KeyVaultError
)

app = func.FunctionApp(http_auth_level=func.AuthLevel.ADMIN)

# Initialize services at module level (singleton pattern)
# This allows reuse across requests and caches Key Vault credentials
gemini_service: GeminiService | None = None
notion_service: NotionService | None = None


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
    
    Args:
        req: HTTP request with JSON body containing 'url' field
        
    Returns:
        HTTP response with JSON summary or error message
    """
    logging.info('YouTube Summarize to Notion function triggered.')
    
    try:
        # Initialize services (lazy initialization on first request)
        _initialize_services()
        
        # Step 1: Parse request body
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
