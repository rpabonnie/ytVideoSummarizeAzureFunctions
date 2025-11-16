"""
Custom exception classes for YouTube Summarizer Azure Function.

This module defines a hierarchy of exceptions for clear error handling
and appropriate HTTP status codes in the function app.
"""


class YouTubeSummarizerError(Exception):
    """Base exception for YouTube Summarizer application."""
    
    def __init__(self, message: str, status_code: int = 500):
        """
        Initialize exception with message and HTTP status code.
        
        Args:
            message: Error description
            status_code: HTTP status code for API response (default: 500)
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class InvalidYouTubeUrlError(YouTubeSummarizerError):
    """
    Raised when YouTube URL is invalid, malicious, or potentially harmful.
    
    This includes:
    - Invalid URL format or scheme (non-HTTPS)
    - Unauthorized domains (not YouTube)
    - Invalid video ID format
    - Path traversal attempts
    - Injection attempts
    """
    
    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class GeminiApiError(YouTubeSummarizerError):
    """
    Raised when Gemini API call fails.
    
    This includes:
    - API authentication failures
    - Rate limiting
    - Invalid API responses
    - Video processing errors
    - Timeout errors
    """
    
    def __init__(self, message: str, original_error: Exception | None = None):
        super().__init__(message, status_code=500)
        self.original_error = original_error


class NotionApiError(YouTubeSummarizerError):
    """
    Raised when Notion API call fails.
    
    This includes:
    - API authentication failures
    - Page creation errors
    - Invalid data format
    - Rate limiting
    """
    
    def __init__(self, message: str, original_error: Exception | None = None):
        super().__init__(message, status_code=500)
        self.original_error = original_error


class KeyVaultError(YouTubeSummarizerError):
    """
    Raised when Azure Key Vault access fails.
    
    This includes:
    - Authentication failures (missing az login)
    - Missing secrets
    - Permission errors
    - Key Vault unavailable
    """
    
    def __init__(self, message: str, original_error: Exception | None = None):
        super().__init__(message, status_code=500)
        self.original_error = original_error
