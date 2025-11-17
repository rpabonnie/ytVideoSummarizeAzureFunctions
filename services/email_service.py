"""
Email notification service for SendGrid integration.

This service encapsulates email notification logic including:
- Formatting success and failure emails
- Integration with Azure Functions SendGrid output binding
- HTML email templates
"""

import logging
from typing import Dict, Any


class EmailService:
    """Service for sending email notifications via SendGrid."""
    
    def __init__(self, from_email: str, to_email: str):
        """
        Initialize Email service with sender and recipient.
        
        Args:
            from_email: Sender email address (verified in SendGrid)
            to_email: Recipient email address
            
        Raises:
            ValueError: If emails are empty or invalid format
        """
        if not from_email or not to_email:
            raise ValueError("from_email and to_email cannot be empty")
        
        self.from_email = from_email
        self.to_email = to_email
        logging.info(f"EmailService initialized: {from_email} -> {to_email}")
    
    def format_success_email(
        self, 
        youtube_url: str, 
        notion_url: str, 
        summary: dict
    ) -> Dict[str, Any]:
        """
        Format success notification email for SendGrid binding.
        
        Args:
            youtube_url: Original YouTube video URL
            notion_url: Created Notion page URL
            summary: Video summary data from GeminiService
            
        Returns:
            dict: Email data for SendGrid output binding with keys:
                - personalizations: Recipient list
                - from: Sender info
                - subject: Email subject
                - content: HTML email body
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
        
        return {
            "personalizations": [
                {
                    "to": [{"email": self.to_email}]
                }
            ],
            "from": {"email": self.from_email},
            "subject": f"✅ Summary Ready: {title}",
            "content": [
                {
                    "type": "text/html",
                    "value": html_content
                }
            ]
        }
    
    def format_failure_email(self, youtube_url: str, error: str) -> Dict[str, Any]:
        """
        Format failure notification email for SendGrid binding.
        
        Args:
            youtube_url: YouTube video URL that failed
            error: Error message
            
        Returns:
            dict: Email data for SendGrid output binding
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
        
        return {
            "personalizations": [
                {
                    "to": [{"email": self.to_email}]
                }
            ],
            "from": {"email": self.from_email},
            "subject": "❌ Video Summary Failed",
            "content": [
                {
                    "type": "text/html",
                    "value": html_content
                }
            ]
        }
