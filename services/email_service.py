"""
Email notification service for Azure Communication Services Email integration.

This service encapsulates email notification logic including:
- Formatting success and failure emails
- Integration with Azure Communication Services Email SDK
- HTML email templates
- Markdown attachment support for failure logs
"""

import logging
import os
import base64
from typing import Dict, Any
from azure.communication.email import EmailClient
from azure.identity import DefaultAzureCredential


class EmailService:
    """Service for sending email notifications via Azure Communication Services Email."""
    
    def __init__(self, from_email: str, to_email: str, connection_string: str | None = None):
        """
        Initialize Email service with sender and recipient.
        
        Args:
            from_email: Sender email address (verified in ACS)
            to_email: Recipient email address
            connection_string: ACS connection string (optional, uses env if not provided)
            
        Raises:
            ValueError: If emails are empty or invalid format
        """
        if not from_email or not to_email:
            raise ValueError("from_email and to_email cannot be empty")
        
        self.from_email = from_email
        self.to_email = to_email
        
        # Initialize EmailClient with connection string
        conn_str = connection_string or os.environ.get("ACS_CONNECTION_STRING")
        if not conn_str:
            raise ValueError("ACS_CONNECTION_STRING not configured")
        
        self.email_client = EmailClient.from_connection_string(conn_str)
        logging.info(f"EmailService initialized: {from_email} -> {to_email}")
    
    def send_success_email(
        self, 
        youtube_url: str, 
        notion_url: str, 
        summary: dict
    ) -> None:
        """
        Send success notification email via Azure Communication Services.
        
        Args:
            youtube_url: Original YouTube video URL
            notion_url: Created Notion page URL
            summary: Video summary data from GeminiService
        """
        title = summary.get('title', 'Unknown Video')
        brief = summary.get('brief_summary', 'No summary available')
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #0066cc;">✅ Video Summary Created</h2>
            
            <h3>{title}</h3>
            
            <p><strong>Summary:</strong><br>{brief}</p>
            
            <p>
                <a href="{notion_url}" 
                   style="background-color: #0066cc; color: white; padding: 10px 20px; 
                          text-decoration: none; border-radius: 5px; display: inline-block;">
                    View in Notion
                </a>
            </p>
            
            <p style="color: #666; font-size: 12px;">
                Original video: <a href="{youtube_url}">{youtube_url}</a>
            </p>
        </body>
        </html>
        """
        
        message = {
            "senderAddress": self.from_email,
            "recipients": {
                "to": [{"address": self.to_email}]
            },
            "content": {
                "subject": f"✅ Summary Ready: {title}",
                "html": html_content
            }
        }
        
        try:
            poller = self.email_client.begin_send(message)
            result = poller.result()
            logging.info(f"Success email sent. Message ID: {result['id']}")
        except Exception as e:
            logging.error(f"Failed to send success email: {str(e)}")
            raise
    
    def send_failure_email(
        self, 
        youtube_url: str, 
        error: str, 
        markdown_report: str | None = None,
        request_body: dict | None = None
    ) -> None:
        """
        Send failure notification email with comprehensive logs via Azure Communication Services.
        
        Args:
            youtube_url: YouTube video URL that failed
            error: Error message
            markdown_report: Optional markdown-formatted failure report to attach
            request_body: Optional request body data to include in email
        """
        # Build HTML content with request details
        request_details = ""
        if request_body:
            request_details = f"""
            <p><strong>Request Body:</strong><br>
               <pre style="background-color: #f4f4f4; padding: 10px; overflow-x: auto; 
                           border-radius: 5px; font-size: 12px;">
{self._format_json_for_html(request_body)}
               </pre>
            </p>
            """
        
        attachment_note = ""
        if markdown_report:
            attachment_note = """
            <p style="background-color: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; 
                      margin: 15px 0;">
                📎 <strong>Complete failure logs attached</strong> as <code>failure-report.md</code>
                <br>Contains: Request data, stack trace, and complete runtime logs
            </p>
            """
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #cc0000;">❌ Video Summary Failed</h2>
            
            {attachment_note}
            
            <p><strong>Video URL:</strong><br>
               <a href="{youtube_url}">{youtube_url}</a>
            </p>
            
            <p><strong>Error:</strong><br>
               <code style="background-color: #f4f4f4; padding: 10px; display: block; 
                            border-left: 3px solid #cc0000; overflow-x: auto;">
                   {self._escape_html(error)}
               </code>
            </p>
            
            {request_details}
            
            <p style="color: #666; font-size: 12px; margin-top: 20px;">
                {f"Complete diagnostic information is attached as a markdown file." if markdown_report else "Please check the Azure Function logs for more details."}
            </p>
        </body>
        </html>
        """
        
        message = {
            "senderAddress": self.from_email,
            "recipients": {
                "to": [{"address": self.to_email}]
            },
            "content": {
                "subject": "❌ Video Summary Failed - Diagnostic Logs Attached",
                "html": html_content
            }
        }
        
        # Add markdown attachment if provided
        if markdown_report:
            attachment_content = base64.b64encode(markdown_report.encode('utf-8')).decode('utf-8')
            message["attachments"] = [
                {
                    "name": "failure-report.md",
                    "contentType": "text/markdown",
                    "contentInBase64": attachment_content
                }
            ]
        
        try:
            poller = self.email_client.begin_send(message)
            result = poller.result()
            logging.info(f"Failure email sent with {'attachment' if markdown_report else 'no attachment'}. Message ID: {result['id']}")
        except Exception as e:
            logging.error(f"Failed to send failure email: {str(e)}")
            raise
    
    def _escape_html(self, text: str) -> str:
        """
        Escape HTML special characters.
        
        Args:
            text: Text to escape
            
        Returns:
            HTML-escaped text
        """
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))
    
    def _format_json_for_html(self, data: dict) -> str:
        """
        Format JSON data for HTML display.
        
        Args:
            data: Dictionary to format
            
        Returns:
            Formatted JSON string
        """
        import json
        try:
            formatted = json.dumps(data, indent=2)
            return self._escape_html(formatted)
        except Exception:
            return self._escape_html(str(data))
