import azure.functions as func
import logging
import json
import os
from datetime import datetime, timedelta
from collections import deque

from services.gemini_service import GeminiService
from services.notion_service import NotionService
from services.email_service import EmailService
from utils.validators import validate_youtube_url, validate_request_body
from utils.log_capture import LogCapture, LogCaptureHandler
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
email_service: EmailService | None = None

# Rate limiting configuration (dev/testing phase)
RATE_LIMIT_PER_HOUR = 30
request_timestamps = deque()  # Stores timestamps of requests in the last hour


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
            try:
                email_service = EmailService(key_vault_url, from_email, to_email)
                logging.info("EmailService initialized successfully")
            except Exception as e:
                logging.error(f"Failed to initialize EmailService: {str(e)}. Email notifications disabled.", exc_info=True)
        else:
            missing_configs = []
            if not from_email:
                missing_configs.append("EMAIL_FROM")
            if not to_email:
                missing_configs.append("EMAIL_TO")
            logging.warning(f"Email configuration missing: {', '.join(missing_configs)}. Email notifications disabled.")
        
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


def _send_failure_email(
    youtube_url: str, 
    error_message: str, 
    log_capture: LogCapture | None = None,
    request_body: dict | None = None
):
    """
    Send failure notification email with comprehensive logs.
    
    Args:
        youtube_url: YouTube URL that failed processing
        error_message: Error description
        log_capture: LogCapture instance with complete failure logs
        request_body: Original request body for context
    """
    if email_service:
        try:
            markdown_report = None
            if log_capture:
                markdown_report = log_capture.generate_markdown_report()
            
            email_service.send_failure_email(
                youtube_url=youtube_url,
                error=error_message,
                markdown_report=markdown_report,
                request_body=request_body
            )
            logging.info("Failure email notification sent with comprehensive logs")
        except Exception as e:
            logging.warning(f"Failed to send failure email (non-fatal): {str(e)}")

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
    # Initialize log capture for this request
    log_capture = LogCapture()
    
    # Set up logging handler to capture all logs
    logger = logging.getLogger()
    log_handler = LogCaptureHandler(log_capture)
    log_handler.setLevel(logging.INFO)
    logger.addHandler(log_handler)
    
    try:
        logging.info('YouTube Summarize to Notion function triggered.')
        
        # Initialize services (lazy initialization on first request)
        _initialize_services()
        
        # Capture request headers (sanitized)
        headers_dict = dict(req.headers)
        
        # Step 1: Check rate limit (30 requests per hour)
        is_allowed, request_count = _check_rate_limit()
        if not is_allowed:
            logging.warning(f"Rate limit exceeded: {request_count} requests in the last hour")
            
            error_msg = f"Rate limit exceeded: {request_count}/{RATE_LIMIT_PER_HOUR} requests in last hour. Please try again later."
            log_capture.set_error_info(
                Exception("RateLimitExceeded"),
                {"requests_in_last_hour": request_count, "limit": RATE_LIMIT_PER_HOUR}
            )
            
            # Send failure email
            _send_failure_email(
                "Unknown URL",
                error_msg,
                log_capture=log_capture,
                request_body=None
            )
            
            return func.HttpResponse(
                json.dumps({
                    "error": "Rate limit exceeded",
                    "message": error_msg,
                    "requests_in_last_hour": request_count
                }),
                status_code=429,
                mimetype="application/json"
            )
        
        logging.info(f"Rate limit check passed: {request_count}/{RATE_LIMIT_PER_HOUR} requests in last hour")
        
        # Step 2: Parse request body
        req_body = None
        try:
            req_body = req.get_json()
            log_capture.set_request_data(req_body, headers_dict)
        except ValueError as e:
            logging.error(f"Invalid JSON in request body: {str(e)}")
            log_capture.set_error_info(e, {"error_type": "InvalidJSON"})
            
            # Send failure email
            _send_failure_email(
                "N/A - Invalid Request",
                f"Invalid JSON format in request: {str(e)}",
                log_capture=log_capture,
                request_body=None
            )
            
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
            log_capture.set_error_info(e, {"error_type": "ValidationError"})
            
            # Send failure email
            _send_failure_email(
                req_body.get('url', 'Invalid URL') if req_body else 'Invalid URL',
                f"Request validation failed: {e.message}",
                log_capture=log_capture,
                request_body=req_body
            )
            
            return func.HttpResponse(
                json.dumps({"error": e.message}),
                status_code=e.status_code,
                mimetype="application/json"
            )
        
        # Step 3: Validate and sanitize YouTube URL
        youtube_url = ""
        sanitized_url = ""
        try:
            youtube_url = req_body.get('url', '')
            sanitized_url = validate_youtube_url(youtube_url)
            logging.info(f"Processing YouTube URL: {sanitized_url}")
        except InvalidYouTubeUrlError as e:
            logging.error(f"URL validation failed: {e.message}")
            log_capture.set_error_info(e, {
                "error_type": "InvalidURL",
                "provided_url": youtube_url
            })
            
            # Send failure email
            _send_failure_email(
                youtube_url,
                f"Invalid YouTube URL: {e.message}",
                log_capture=log_capture,
                request_body=req_body
            )
            
            return func.HttpResponse(
                json.dumps({"error": e.message}),
                status_code=e.status_code,
                mimetype="application/json"
            )
        
        # Step 4: Summarize video using GeminiService
        summary = None
        try:
            if gemini_service is None:
                raise ValueError("GeminiService not initialized")
            
            summary = gemini_service.summarize_video(sanitized_url)
            logging.info("Video summarized successfully")
            
        except KeyVaultError as e:
            logging.error(f"Key Vault error: {e.message}")
            log_capture.set_error_info(e, {
                "error_type": "KeyVaultError",
                "video_url": sanitized_url
            })
            
            # Send failure email
            _send_failure_email(
                sanitized_url,
                f"Configuration error (Key Vault): {e.message}",
                log_capture=log_capture,
                request_body=req_body
            )
            
            return func.HttpResponse(
                json.dumps({"error": e.message}),
                status_code=e.status_code,
                mimetype="application/json"
            )
        except GeminiApiError as e:
            logging.error(f"Gemini API error: {e.message}")
            log_capture.set_error_info(e, {
                "error_type": "GeminiApiError",
                "video_url": sanitized_url
            })
            
            # Send failure email
            _send_failure_email(
                sanitized_url,
                f"AI summarization failed: {e.message}",
                log_capture=log_capture,
                request_body=req_body
            )
            
            return func.HttpResponse(
                json.dumps({"error": e.message}),
                status_code=e.status_code,
                mimetype="application/json"
            )
        
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
                    logging.info("Success email notification sent")
                except Exception as e:
                    logging.warning(f"Failed to send success email (non-fatal): {str(e)}")
            
        except NotionApiError as e:
            logging.warning(f"Notion integration failed (non-fatal): {e.message}")
            log_capture.set_error_info(e, {
                "error_type": "NotionApiError",
                "video_url": sanitized_url,
                "partial_success": True
            })
            # Don't fail the entire request - summary is still valid
        except KeyVaultError as e:
            logging.warning(f"Notion Key Vault error (non-fatal): {e.message}")
            log_capture.set_error_info(e, {
                "error_type": "NotionKeyVaultError",
                "partial_success": True
            })
        except Exception as e:
            logging.warning(f"Unexpected Notion error (non-fatal): {str(e)}")
            log_capture.set_error_info(e, {
                "error_type": "UnexpectedNotionError",
                "partial_success": True
            })
        
        # Step 6: Return success response
        # Return simple success/failure message - Notion page contains the full summary
        if notion_success and notion_url:
            response_data = {
                "status": "success",
                "message": "Video summarized successfully",
                "youtube_url": sanitized_url
            }
        else:
            # Partial success - summary generated but Notion failed
            response_data = {
                "status": "partial_success",
                "message": "Summary generated but Notion page creation failed",
                "youtube_url": sanitized_url,
                "note": "Check function logs for details"
            }
            
            # Send failure email for partial success
            _send_failure_email(
                sanitized_url,
                "Summary generated successfully, but Notion page creation failed. Check Azure Function logs for details.",
                log_capture=log_capture,
                request_body=req_body
            )
        
        return func.HttpResponse(
            json.dumps(response_data, indent=2),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        # Catch-all for unexpected errors
        logging.error(f"Unexpected error: {str(e)}", exc_info=True)
        log_capture.set_error_info(e, {
            "error_type": "UnexpectedException",
            "critical": True
        })
        
        # Send failure email
        youtube_url = sanitized_url if 'sanitized_url' in locals() and sanitized_url else (
            req_body.get('url', 'Unknown') if 'req_body' in locals() and req_body else 'Unknown'
        )
        _send_failure_email(
            youtube_url,
            f"Internal server error: {str(e)}",
            log_capture=log_capture,
            request_body=req_body if 'req_body' in locals() else None
        )
        
        return func.HttpResponse(
            json.dumps({"error": "Internal server error. Check function logs for details."}),
            status_code=500,
            mimetype="application/json"
        )
    finally:
        # Clean up log handler
        logger.removeHandler(log_handler)
