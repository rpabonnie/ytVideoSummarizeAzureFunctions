"""
Utilities package for YouTube Summarizer Azure Function.

This package contains utility functions and custom exceptions:
- validators: Input validation functions (YouTube URLs, etc.)
- exceptions: Custom exception classes for error handling
"""

from .validators import validate_youtube_url, validate_request_body
from .exceptions import (
    YouTubeSummarizerError, 
    InvalidYouTubeUrlError, 
    GeminiApiError, 
    NotionApiError, 
    KeyVaultError
)

__all__ = [
    'validate_youtube_url', 
    'validate_request_body',
    'YouTubeSummarizerError', 
    'InvalidYouTubeUrlError', 
    'GeminiApiError', 
    'NotionApiError', 
    'KeyVaultError'
]
