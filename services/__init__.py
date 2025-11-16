"""
Services package for YouTube Summarizer Azure Function.

This package contains service classes that encapsulate business logic:
- GeminiService: AI-powered video summarization using Google Gemini
- NotionService: Notion API integration for saving summaries
- EmailService: Email notifications via SendGrid
"""

__all__ = ['GeminiService', 'NotionService', 'EmailService']
