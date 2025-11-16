"""
Input validation utilities for YouTube Summarizer Azure Function.

This module provides secure validation for user inputs, particularly
YouTube URLs, to prevent malicious attacks and ensure data integrity.
"""

import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from utils.exceptions import InvalidYouTubeUrlError


# YouTube domain whitelist
ALLOWED_YOUTUBE_DOMAINS = {
    'youtube.com',
    'www.youtube.com',
    'm.youtube.com',
    'youtu.be'
}

# YouTube video ID regex pattern (11 characters: alphanumeric, underscore, hyphen)
VIDEO_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{11}$')

# Allowed query parameters (security: only allow known safe parameters)
ALLOWED_QUERY_PARAMS = {'v', 't', 'list', 'index', 'start'}


def validate_youtube_url(url: str) -> str:
    """
    Validates and sanitizes YouTube URL for security.
    
    Security checks:
    - Enforces HTTPS scheme only
    - Validates domain against whitelist
    - Extracts and validates video ID format
    - Prevents path traversal attacks (../, ./, encoded variants)
    - Prevents injection attacks (special characters, script tags)
    - Strips tracking and potentially malicious query parameters
    
    Args:
        url: YouTube URL to validate
        
    Returns:
        Sanitized YouTube URL in standard format
        
    Raises:
        InvalidYouTubeUrlError: If URL is invalid, malicious, or not from YouTube
        
    Examples:
        >>> validate_youtube_url('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
        'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        
        >>> validate_youtube_url('https://youtu.be/dQw4w9WgXcQ')
        'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        
        >>> validate_youtube_url('http://youtube.com/watch?v=test')
        InvalidYouTubeUrlError: Only HTTPS URLs are allowed
    """
    
    # Basic input validation
    if not url or not isinstance(url, str):
        raise InvalidYouTubeUrlError("URL must be a non-empty string")
    
    # Remove leading/trailing whitespace
    url = url.strip()
    
    # Check for obviously malicious patterns before parsing
    malicious_patterns = [
        '../',           # Path traversal
        './',            # Path traversal
        '%2e%2e',       # Encoded path traversal
        '%2e%2f',       # Encoded path traversal
        '<script',       # Script injection (case-insensitive check below)
        'javascript:',   # JavaScript protocol
        'data:',         # Data protocol
        'file:',         # File protocol
        'ftp:',          # FTP protocol
    ]
    
    url_lower = url.lower()
    for pattern in malicious_patterns:
        if pattern in url_lower:
            raise InvalidYouTubeUrlError(f"URL contains potentially malicious pattern: {pattern}")
    
    # Check for authentication in URL (user:pass@domain)
    if '@' in url.split('://')[0] if '://' in url else url:
        raise InvalidYouTubeUrlError("URL must not contain authentication credentials")
    
    # Parse URL
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise InvalidYouTubeUrlError(f"Failed to parse URL: {str(e)}")
    
    # Validate scheme (HTTPS only for security)
    if parsed.scheme != 'https':
        raise InvalidYouTubeUrlError("Only HTTPS URLs are allowed. YouTube uses HTTPS.")
    
    # Validate domain (must be in whitelist)
    domain = parsed.netloc.lower()
    if domain not in ALLOWED_YOUTUBE_DOMAINS:
        raise InvalidYouTubeUrlError(
            f"Invalid domain '{domain}'. Must be one of: {', '.join(ALLOWED_YOUTUBE_DOMAINS)}"
        )
    
    # Extract video ID based on URL format
    video_id = None
    
    if domain == 'youtu.be':
        # Format: https://youtu.be/VIDEO_ID
        # Path should be /VIDEO_ID (no subdirectories)
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) == 1 and path_parts[0]:
            video_id = path_parts[0]
        else:
            raise InvalidYouTubeUrlError("Invalid youtu.be URL format. Expected: https://youtu.be/VIDEO_ID")
    
    else:
        # Format: https://youtube.com/watch?v=VIDEO_ID or https://youtube.com/embed/VIDEO_ID
        
        # Check for /watch format
        if parsed.path.startswith('/watch'):
            query_params = parse_qs(parsed.query)
            if 'v' in query_params and query_params['v']:
                video_id = query_params['v'][0]
            else:
                raise InvalidYouTubeUrlError("Missing 'v' parameter in YouTube watch URL")
        
        # Check for /embed format
        elif parsed.path.startswith('/embed/'):
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) == 2 and path_parts[0] == 'embed' and path_parts[1]:
                video_id = path_parts[1]
            else:
                raise InvalidYouTubeUrlError("Invalid YouTube embed URL format")
        
        else:
            raise InvalidYouTubeUrlError(
                "Invalid YouTube URL format. Expected /watch?v=... or /embed/... path"
            )
    
    # Validate video ID format
    if not video_id:
        raise InvalidYouTubeUrlError("Could not extract video ID from URL")
    
    if not VIDEO_ID_PATTERN.match(video_id):
        raise InvalidYouTubeUrlError(
            f"Invalid video ID format: '{video_id}'. Must be 11 alphanumeric characters, "
            f"underscores, or hyphens."
        )
    
    # Extract and filter query parameters (only allow safe ones)
    safe_params = {}
    if parsed.query:
        query_params = parse_qs(parsed.query)
        for param, values in query_params.items():
            if param in ALLOWED_QUERY_PARAMS and values:
                # Only keep first value and validate it's safe
                value = values[0]
                # Basic validation: alphanumeric, underscore, hyphen only
                if re.match(r'^[a-zA-Z0-9_-]+$', value):
                    safe_params[param] = value
    
    # Always include video ID in v parameter
    safe_params['v'] = video_id
    
    # Reconstruct clean URL in standard format
    clean_query = urlencode(sorted(safe_params.items()))
    clean_url = urlunparse((
        'https',
        'www.youtube.com',
        '/watch',
        '',
        clean_query,
        ''  # No fragment
    ))
    
    return clean_url


def validate_request_body(body: dict) -> None:
    """
    Validates the request body structure.
    
    Args:
        body: Parsed JSON request body
        
    Raises:
        InvalidYouTubeUrlError: If request body is invalid
    """
    if not isinstance(body, dict):
        raise InvalidYouTubeUrlError("Request body must be a JSON object")
    
    if 'url' not in body:
        raise InvalidYouTubeUrlError("Missing 'url' field in request body")
    
    if not body['url']:
        raise InvalidYouTubeUrlError("'url' field cannot be empty")
