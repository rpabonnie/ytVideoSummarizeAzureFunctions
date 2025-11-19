"""
Configuration service for loading settings from Azure App Configuration.

This service provides centralized configuration management with:
- Azure App Configuration integration for remote settings
- Fallback to local JSON files for development
- Caching for performance
- Support for Notion configuration
"""

import logging
import json
import os
from pathlib import Path
from typing import Optional

from azure.identity import DefaultAzureCredential
from azure.appconfiguration import AzureAppConfigurationClient
from utils.exceptions import KeyVaultError


class ConfigService:
    """Service for loading configuration from Azure App Configuration or local files."""
    
    # Module-level cache for configuration (singleton pattern)
    _credential: Optional[DefaultAzureCredential] = None
    _app_config_client: Optional[AzureAppConfigurationClient] = None
    _notion_config_cache: Optional[dict] = None
    
    def __init__(self, app_config_connection_string: str | None = None):
        """
        Initialize Configuration service.
        
        Args:
            app_config_connection_string: Azure App Configuration connection string
                If None, will try to load from APP_CONFIG_CONNECTION_STRING env var
        """
        self.app_config_connection_string = (
            app_config_connection_string or 
            os.environ.get("APP_CONFIG_CONNECTION_STRING")
        )
        
        if self.app_config_connection_string:
            logging.info("ConfigService initialized with Azure App Configuration")
        else:
            logging.info("ConfigService initialized in local-only mode (no App Configuration)")
    
    def _get_app_config_client(self) -> AzureAppConfigurationClient | None:
        """
        Get Azure App Configuration client (with caching).
        
        Returns:
            AzureAppConfigurationClient or None if not configured
        """
        # Return None if no connection string configured
        if not self.app_config_connection_string:
            return None
        
        # Return cached client if available
        if ConfigService._app_config_client:
            return ConfigService._app_config_client
        
        try:
            logging.info("Initializing Azure App Configuration client")
            ConfigService._app_config_client = AzureAppConfigurationClient.from_connection_string(
                self.app_config_connection_string
            )
            logging.info("Successfully connected to Azure App Configuration")
            return ConfigService._app_config_client
            
        except Exception as e:
            logging.warning(
                f"Failed to initialize App Configuration client: {str(e)}. "
                f"Falling back to local configuration files."
            )
            return None
    
    def _load_from_app_config(self, key: str) -> dict | None:
        """
        Load configuration from Azure App Configuration.
        
        Args:
            key: Configuration key (e.g., "notion_config")
            
        Returns:
            dict: Parsed JSON configuration or None if not found/available
        """
        client = self._get_app_config_client()
        if not client:
            return None
        
        try:
            logging.info(f"Loading configuration '{key}' from Azure App Configuration")
            config_setting = client.get_configuration_setting(key=key)
            
            if not config_setting or not config_setting.value:
                logging.warning(f"Configuration key '{key}' not found in App Configuration")
                return None
            
            # Parse JSON value
            config_data = json.loads(config_setting.value)
            logging.info(f"Successfully loaded '{key}' from App Configuration")
            return config_data
            
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in App Configuration key '{key}': {str(e)}")
            return None
        except Exception as e:
            logging.warning(
                f"Failed to load '{key}' from App Configuration: {str(e)}. "
                f"Falling back to local file."
            )
            return None
    
    def _load_from_local_file(self, file_path: Path) -> dict | None:
        """
        Load configuration from local JSON file.
        
        Args:
            file_path: Path to JSON configuration file
            
        Returns:
            dict: Parsed JSON configuration or None if not found
        """
        if not file_path.exists():
            logging.warning(f"Local config file not found: {file_path}")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            logging.info(f"Loaded configuration from local file: {file_path}")
            return config_data
            
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in {file_path}: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Failed to load {file_path}: {str(e)}")
            return None
    
    def get_notion_config(self) -> dict:
        """
        Get Notion configuration from Azure App Configuration or local file.
        
        Loading priority:
        1. Cached configuration (if available)
        2. Azure App Configuration (if configured)
        3. Local notion_config.json file
        
        Returns:
            dict: Notion configuration containing database_id, property_mapping, etc.
            
        Raises:
            ValueError: If configuration not found or database_id not configured
        """
        # Return cached config if available
        if ConfigService._notion_config_cache:
            logging.debug("Using cached Notion configuration")
            return ConfigService._notion_config_cache
        
        config_data = None
        
        # Try Azure App Configuration first
        config_data = self._load_from_app_config("notion_config")
        
        # Fall back to local file if App Configuration unavailable
        if not config_data:
            local_path = Path(__file__).parent.parent / "notion_config.json"
            config_data = self._load_from_local_file(local_path)
        
        # Validate configuration
        if not config_data:
            raise ValueError(
                "Notion configuration not found. Please configure either:\n"
                "1. Azure App Configuration with key 'notion_config', OR\n"
                "2. Local file 'notion_config.json'\n"
                "See NOTION_SETUP.md for setup instructions."
            )
        
        if not config_data.get('database_id') or config_data['database_id'] == "PASTE_YOUR_DATABASE_ID_HERE":
            raise ValueError(
                "database_id not configured in Notion configuration. "
                "Please add your Notion database ID (see NOTION_SETUP.md)."
            )
        
        # Cache the configuration
        ConfigService._notion_config_cache = config_data
        logging.info(f"Notion config loaded for database: {config_data.get('database_name', 'Unknown')}")
        
        return config_data
    
    def clear_cache(self):
        """Clear cached configuration (useful for testing or forcing reload)."""
        ConfigService._notion_config_cache = None
        logging.info("Configuration cache cleared")
