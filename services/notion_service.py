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
        # TODO: Implement Notion API integration
        # Steps:
        # 1. Get API key: api_key = self._get_api_key()
        # 2. Initialize Notion client: from notion_client import Client
        # 3. Format summary_data into Notion blocks (rich text, headings, bullets)
        # 4. Create page: client.pages.create(parent={...}, properties={...}, children=[...])
        # 5. Extract and return page URL from response
        
        logging.warning("Notion integration not yet implemented")
        raise NotImplementedError(
            "Notion integration is pending. "
            "The create_page method will be implemented in the next phase."
        )
