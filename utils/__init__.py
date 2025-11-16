"""
Utilities package for YouTube Summarizer Azure Function.

This package contains utility functions and custom exceptions:
- validators: Input validation functions (YouTube URLs, etc.)
- exceptions: Custom exception classes for error handling
"""

__all__ = ['validate_youtube_url', 'YouTubeSummarizerError', 'InvalidYouTubeUrlError', 
           'GeminiApiError', 'NotionApiError', 'KeyVaultError']
