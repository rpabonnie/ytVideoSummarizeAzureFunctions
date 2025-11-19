"""
Log capture utility for collecting runtime logs and request context.

This utility provides a mechanism to capture all log entries during
request processing for inclusion in failure email notifications.
"""

import logging
import json
import traceback
from datetime import datetime
from typing import Any
from io import StringIO


class LogCapture:
    """Captures log entries and request context for failure analysis."""
    
    def __init__(self):
        """Initialize log capture with empty buffer."""
        self.log_buffer = []
        self.request_data = {}
        self.error_info = {}
        self.start_time = datetime.utcnow()
    
    def add_log(self, level: str, message: str):
        """
        Add a log entry to the buffer.
        
        Args:
            level: Log level (INFO, WARNING, ERROR, etc.)
            message: Log message
        """
        timestamp = datetime.utcnow().isoformat()
        self.log_buffer.append({
            "timestamp": timestamp,
            "level": level,
            "message": message
        })
    
    def set_request_data(self, request_body: dict | None, headers: dict | None = None):
        """
        Capture request data for failure analysis.
        
        Args:
            request_body: Parsed JSON request body
            headers: Request headers (optional)
        """
        self.request_data = {
            "body": request_body or {},
            "headers": self._sanitize_headers(headers) if headers else {},
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def set_error_info(self, error: Exception, context: dict | None = None):
        """
        Capture error information including stack trace.
        
        Args:
            error: Exception that occurred
            context: Additional context about the error
        """
        self.error_info = {
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
            "context": context or {},
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _sanitize_headers(self, headers: dict) -> dict:
        """
        Remove sensitive headers like API keys and auth tokens.
        
        Args:
            headers: Raw request headers
            
        Returns:
            Sanitized headers dictionary
        """
        sensitive_keys = {
            'x-functions-key', 'authorization', 'x-api-key',
            'cookie', 'x-ms-client-principal'
        }
        
        sanitized = {}
        for key, value in headers.items():
            if key.lower() in sensitive_keys:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value
        
        return sanitized
    
    def generate_markdown_report(self) -> str:
        """
        Generate a comprehensive markdown report of the failure.
        
        Returns:
            Markdown-formatted failure report
        """
        duration = (datetime.utcnow() - self.start_time).total_seconds()
        
        md = StringIO()
        md.write("# Azure Functions Failure Report\n\n")
        md.write(f"**Generated:** {datetime.utcnow().isoformat()}Z\n\n")
        md.write(f"**Duration:** {duration:.2f} seconds\n\n")
        md.write("---\n\n")
        
        # Request Information
        md.write("## Request Information\n\n")
        if self.request_data:
            md.write("### Request Body\n\n")
            md.write("```json\n")
            md.write(json.dumps(self.request_data.get('body', {}), indent=2))
            md.write("\n```\n\n")
            
            if self.request_data.get('headers'):
                md.write("### Request Headers\n\n")
                md.write("```json\n")
                md.write(json.dumps(self.request_data.get('headers', {}), indent=2))
                md.write("\n```\n\n")
        else:
            md.write("*No request data captured*\n\n")
        
        # Error Information
        md.write("## Error Information\n\n")
        if self.error_info:
            md.write(f"**Error Type:** `{self.error_info.get('type', 'Unknown')}`\n\n")
            md.write(f"**Error Message:**\n\n")
            md.write(f"```\n{self.error_info.get('message', 'No message')}\n```\n\n")
            
            if self.error_info.get('context'):
                md.write("**Error Context:**\n\n")
                md.write("```json\n")
                md.write(json.dumps(self.error_info.get('context', {}), indent=2))
                md.write("\n```\n\n")
            
            md.write("**Stack Trace:**\n\n")
            md.write("```python\n")
            md.write(self.error_info.get('traceback', 'No traceback available'))
            md.write("\n```\n\n")
        else:
            md.write("*No error information captured*\n\n")
        
        # Log Entries
        md.write("## Runtime Logs\n\n")
        if self.log_buffer:
            md.write("| Timestamp | Level | Message |\n")
            md.write("|-----------|-------|----------|\n")
            for log_entry in self.log_buffer:
                timestamp = log_entry['timestamp'].split('T')[1][:12]  # HH:MM:SS.mmm
                level = log_entry['level']
                message = log_entry['message'].replace('\n', ' ').replace('|', '\\|')[:100]
                md.write(f"| {timestamp} | {level} | {message} |\n")
            
            md.write("\n### Detailed Logs\n\n")
            for i, log_entry in enumerate(self.log_buffer, 1):
                md.write(f"**[{i}] {log_entry['timestamp']} - {log_entry['level']}**\n\n")
                md.write(f"```\n{log_entry['message']}\n```\n\n")
        else:
            md.write("*No logs captured*\n\n")
        
        # Footer
        md.write("---\n\n")
        md.write("*This report was automatically generated by the Azure Functions failure notification system.*\n")
        
        return md.getvalue()


class LogCaptureHandler(logging.Handler):
    """Custom logging handler that captures logs to a LogCapture instance."""
    
    def __init__(self, log_capture: LogCapture):
        """
        Initialize handler with LogCapture instance.
        
        Args:
            log_capture: LogCapture instance to send logs to
        """
        super().__init__()
        self.log_capture = log_capture
    
    def emit(self, record: logging.LogRecord):
        """
        Emit a log record to the LogCapture buffer.
        
        Args:
            record: Log record to capture
        """
        try:
            msg = self.format(record)
            self.log_capture.add_log(record.levelname, msg)
        except Exception:
            self.handleError(record)
