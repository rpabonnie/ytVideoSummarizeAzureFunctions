"""
Email notification service for Azure Communication Services Email integration.

This service encapsulates email notification logic including:
- Formatting success and failure emails
- Integration with Azure Communication Services Email SDK
- HTML email templates
"""

import logging
import os
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
    
    def send_failure_email(self, youtube_url: str, error: str) -> None:
        """
        Send failure notification email via Azure Communication Services.
        
        Args:
            youtube_url: YouTube video URL that failed
            error: Error message
        """
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #cc0000;">❌ Video Summary Failed</h2>
            
            <p><strong>Video URL:</strong><br>
               <a href="{youtube_url}">{youtube_url}</a>
            </p>
            
            <p><strong>Error:</strong><br>
               <code style="background-color: #f4f4f4; padding: 10px; display: block; 
                            border-left: 3px solid #cc0000;">
                   {error}
               </code>
            </p>
            
            <p style="color: #666; font-size: 12px;">
                Please check the Azure Function logs for more details.
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
                "subject": "❌ Video Summary Failed",
                "html": html_content
            }
        }
        
        try:
            poller = self.email_client.begin_send(message)
            result = poller.result()
            logging.info(f"Failure email sent. Message ID: {result['id']}")
        except Exception as e:
            logging.error(f"Failed to send failure email: {str(e)}")
            raise
