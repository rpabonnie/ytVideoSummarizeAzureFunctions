"""
Notion service for creating pages from video summaries.

This service encapsulates Notion API interactions including:
- Azure Key Vault integration for API key retrieval
- Page creation with structured content
- Error handling and validation
"""

import logging
from typing import Optional
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

from utils.exceptions import NotionApiError, KeyVaultError


class NotionService:
    """Service for creating Notion pages from video summaries."""
    
    # Module-level cache for API credentials (singleton pattern)
    _credential: Optional[DefaultAzureCredential] = None
    _secret_client: Optional[SecretClient] = None
    _notion_api_key: Optional[str] = None
    _client = None
    
    def __init__(self, key_vault_url: str):
        """
        Initialize Notion service with Key Vault URL.
        
        Args:
            key_vault_url: Azure Key Vault URL (e.g., https://your-vault.vault.azure.net/)
            
        Raises:
            ValueError: If key_vault_url is empty or invalid
        """
        if not key_vault_url:
            raise ValueError("key_vault_url cannot be empty")
        
        self.key_vault_url = key_vault_url
        logging.info(f"NotionService initialized with Key Vault: {key_vault_url}")
    
    def _get_api_key(self) -> str:
        """
        Retrieve Notion API key from Azure Key Vault (with caching).
        
        Returns:
            str: Notion API key
            
        Raises:
            KeyVaultError: If Key Vault access fails
        """
        # Return cached key if available
        if NotionService._notion_api_key:
            return NotionService._notion_api_key
        
        try:
            # Initialize credential if not cached
            if not NotionService._credential:
                logging.info("Initializing DefaultAzureCredential for Key Vault access")
                NotionService._credential = DefaultAzureCredential()
            
            # Initialize secret client if not cached
            if not NotionService._secret_client:
                logging.info(f"Connecting to Key Vault: {self.key_vault_url}")
                NotionService._secret_client = SecretClient(
                    vault_url=self.key_vault_url,
                    credential=NotionService._credential
                )
            
            # Retrieve and cache API key
            logging.info("Retrieving NOTION-API-KEY from Key Vault")
            secret = NotionService._secret_client.get_secret("NOTION-API-KEY")
            NotionService._notion_api_key = secret.value
            
            if not NotionService._notion_api_key:
                raise KeyVaultError("Retrieved API key is empty or None")
            
            logging.info("Successfully retrieved Notion API key from Key Vault")
            return NotionService._notion_api_key
            
        except Exception as e:
            error_msg = (
                "Failed to retrieve Notion API key from Key Vault. "
                "Ensure you're authenticated with 'az login' for local development, "
                "or that Managed Identity is configured in Azure."
            )
            logging.error(f"{error_msg} Details: {str(e)}")
            raise KeyVaultError(error_msg, original_error=e)
    
    def _initialize_client(self):
        """
        Initialize Notion client with cached API key.
        
        Returns:
            Client: Notion API client
        """
        if NotionService._client is None:
            api_key = self._get_api_key()
            from notion_client import Client
            logging.info("Initializing Notion API client")
            NotionService._client = Client(auth=api_key)
        return NotionService._client
    
    def _load_config(self) -> dict:
        """
        Load Notion configuration from notion_config.json.
        
        Returns:
            dict: Configuration containing database_id and property_mapping
            
        Raises:
            NotionApiError: If config file not found or database_id missing
        """
        import json
        from pathlib import Path
        
        config_path = Path(__file__).parent.parent / "notion_config.json"
        
        if not config_path.exists():
            raise NotionApiError(
                "notion_config.json not found. See NOTION_SETUP.md for setup instructions."
            )
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            raise NotionApiError(f"Invalid JSON in notion_config.json: {str(e)}")
        except Exception as e:
            raise NotionApiError(f"Failed to load notion_config.json: {str(e)}")
        
        if not config.get('database_id') or config['database_id'] == "PASTE_YOUR_DATABASE_ID_HERE":
            raise NotionApiError(
                "database_id not configured in notion_config.json. "
                "Please add your Notion database ID (see NOTION_SETUP.md)."
            )
        
        logging.info(f"Loaded Notion config for database: {config.get('database_name', 'Unknown')}")
        return config
    
    def _truncate_tag(self, tag: str, max_length: int = 100) -> str:
        """
        Safely truncate a tag to the specified maximum length.
        
        This method ensures:
        - Tags are truncated at word boundaries when possible
        - Unicode characters are not broken
        - Empty or whitespace-only results are avoided
        
        Args:
            tag: The tag string to truncate
            max_length: Maximum allowed length (default: 100 for Notion)
        
        Returns:
            str: Truncated tag string
        """
        tag_str = str(tag).strip()
        
        # If tag is within limit, return as-is
        if len(tag_str) <= max_length:
            return tag_str
        
        # Truncate to max_length, ensuring we don't break unicode characters
        # Python 3 handles this correctly when slicing strings
        truncated = tag_str[:max_length]
        
        # Try to truncate at last word boundary to avoid mid-word cuts
        last_space = truncated.rfind(' ')
        if last_space > 0:  # Only use word boundary if it's not at the start
            truncated = truncated[:last_space]
        
        # Ensure we don't return empty string or just whitespace
        truncated = truncated.strip()
        if not truncated:
            # If word boundary truncation resulted in empty string,
            # fall back to simple truncation
            truncated = tag_str[:max_length].strip()
        
        return truncated
    
    def _build_properties(self, summary_data: dict, property_mapping: dict, static_properties: dict = None) -> dict:
        """
        Build Notion page properties from Gemini summary data.
        
        Args:
            summary_data: Dict from Gemini (title, tags, url, brief_summary, etc.)
            property_mapping: Config mapping Gemini fields to Notion properties (supports string or list of strings)
            static_properties: Dict of static property values to always set (e.g., content_type)
        
        Returns:
            dict: Notion API properties object
        """
        properties = {}
        
        # Title (required, special "title" type)
        # Supports mapping to multiple properties (first as title, rest as rich_text)
        if 'title' in summary_data:
            title_value = summary_data['title'] or "Untitled Video"
            title_properties = property_mapping.get('title', 'Title')
            
            # Normalize to list for uniform processing
            if isinstance(title_properties, str):
                title_properties = [title_properties]
            
            # First property is the actual Notion title type
            if title_properties:
                properties[title_properties[0]] = {
                    "title": [
                        {
                            "type": "text",
                            "text": {"content": title_value}
                        }
                    ]
                }
                
                # Additional properties are rich_text type
                for prop_name in title_properties[1:]:
                    properties[prop_name] = {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": title_value}
                            }
                        ]
                    }
        
        # Tags (multi_select type)
        if 'tags' in summary_data and isinstance(summary_data['tags'], list):
            tags_properties = property_mapping.get('tags', 'Tags')
            
            # Normalize to list for uniform processing
            if isinstance(tags_properties, str):
                tags_properties = [tags_properties]
            
            # Apply to all mapped properties
            for prop_name in tags_properties:
                properties[prop_name] = {
                    "multi_select": [
                        {"name": self._truncate_tag(tag)} for tag in summary_data['tags'] if tag
                    ]
                }
        
        # URL (url type)
        if 'url' in summary_data and summary_data['url']:
            url_properties = property_mapping.get('url', 'URL')
            
            # Normalize to list for uniform processing
            if isinstance(url_properties, str):
                url_properties = [url_properties]
            
            # Apply to all mapped properties
            for prop_name in url_properties:
                properties[prop_name] = {
                    "url": summary_data['url']
                }
        
        # Static properties (e.g., content_type with fixed value)
        if static_properties:
            for prop_key, prop_config in static_properties.items():
                property_name = prop_config.get('property_name')
                property_value = prop_config.get('value')
                
                if property_name and property_value:
                    # Assume select type for static properties (can be extended for other types)
                    properties[property_name] = {
                        "select": {"name": str(property_value)}
                    }
        
        return properties
    
    def _build_content_blocks(self, summary_data: dict, content_sections: dict) -> list:
        """
        Build Notion page content blocks from summary data.
        
        Creates rich text blocks for page body using content_sections config.
        
        Args:
            summary_data: Summary dict from GeminiService
            content_sections: Config mapping for page body content sections
            
        Returns:
            list: Notion block objects for page children
        """
        children = []
        
        # Process each content section from config
        for section_key, section_config in content_sections.items():
            field_name = section_config.get('field')
            heading_text = section_config.get('heading', section_key.replace('_', ' ').title())
            
            # Skip if field not in summary data
            if field_name not in summary_data or not summary_data[field_name]:
                continue
            
            # Add heading
            children.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": heading_text}}]
                }
            })
            
            field_data = summary_data[field_name]
            
            # Handle brief_summary (paragraph text)
            if field_name == 'brief_summary' and isinstance(field_data, str):
                children.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": field_data[:2000]}}]
                    }
                })
            
            # Handle summary_bullets (list of strings)
            elif field_name == 'summary_bullets' and isinstance(field_data, list):
                for bullet in field_data:
                    if bullet:  # Skip empty bullets
                        children.append({
                            "object": "block",
                            "type": "bulleted_list_item",
                            "bulleted_list_item": {
                                "rich_text": [{"type": "text", "text": {"content": str(bullet)[:2000]}}]
                            }
                        })
            
            # Handle tools_and_technologies (list of dicts or strings)
            elif field_name == 'tools_and_technologies' and isinstance(field_data, list):
                for item in field_data:
                    if isinstance(item, dict):
                        tool = item.get('tool', '')
                        purpose = item.get('purpose', '')
                        content = f"{tool}: {purpose}" if purpose else tool
                    else:
                        content = str(item)
                    
                    if content:  # Skip empty items
                        children.append({
                            "object": "block",
                            "type": "bulleted_list_item",
                            "bulleted_list_item": {
                                "rich_text": [{"type": "text", "text": {"content": content[:2000]}}]
                            }
                        })
        
        return children
    
    def create_page(self, summary_data: dict) -> str:
        """
        Create Notion page with video summary.
        
        This method will:
        1. Retrieve Notion API key from Key Vault
        2. Format summary data into Notion blocks
        3. Create a new page in the configured database
        4. Return the page URL
        
        Args:
            summary_data: Summary dict from GeminiService containing:
                - title: Video title
                - tags: List of tags
                - url: YouTube URL
                - brief_summary: Overview paragraph
                - summary_bullets: Key points list
                - tools_and_technologies: Tools mentioned
                
        Returns:
            str: Notion page URL
            
        Raises:
            NotionApiError: If page creation fails
            KeyVaultError: If Key Vault access fails
        """
        try:
            # Initialize client and load config
            client = self._initialize_client()
            config = self._load_config()
            
            database_id = config['database_id']
            property_mapping = config.get('property_mapping', {})
            static_properties = config.get('static_properties', {})
            content_sections = config.get('content_sections', {})
            
            logging.info(f"Creating Notion page for video: {summary_data.get('title', 'Unknown')}")
            
            # Build Notion API request
            properties = self._build_properties(summary_data, property_mapping, static_properties)
            children = self._build_content_blocks(summary_data, content_sections)
            
            # Create page (synchronous call)
            response = client.pages.create(
                parent={"database_id": database_id},
                properties=properties,
                children=children
            )
            
            # Extract and return page URL
            page_url = response.get('url', '')
            if not page_url:
                raise NotionApiError("No URL returned from Notion API")
            
            logging.info(f"Successfully created Notion page: {page_url}")
            return page_url
            
        except NotionApiError:
            # Re-raise our custom errors
            raise
        except KeyVaultError:
            # Re-raise Key Vault errors
            raise
        except Exception as e:
            # Wrap any other exceptions
            logging.error(f"Notion page creation failed: {str(e)}")
            raise NotionApiError(
                f"Failed to create Notion page: {str(e)}",
                original_error=e
            )
