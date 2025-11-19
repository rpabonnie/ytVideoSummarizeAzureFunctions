"""
Unit tests for ConfigService.

Tests configuration loading from Azure App Configuration and local files.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from pathlib import Path

from services.config_service import ConfigService


class TestConfigService(unittest.TestCase):
    """Test cases for ConfigService."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Clear cached configuration before each test
        ConfigService._notion_config_cache = None
        ConfigService._app_config_client = None
    
    def tearDown(self):
        """Clean up after tests."""
        # Clear cached configuration
        ConfigService._notion_config_cache = None
        ConfigService._app_config_client = None
    
    @patch('services.config_service.AzureAppConfigurationClient')
    def test_init_with_connection_string(self, mock_client_class):
        """Test initialization with App Configuration connection string."""
        connection_string = "Endpoint=https://test.azconfig.io;Id=test;Secret=test"
        service = ConfigService(connection_string)
        
        self.assertEqual(service.app_config_connection_string, connection_string)
    
    @patch.dict('os.environ', {'APP_CONFIG_CONNECTION_STRING': 'test-connection'})
    def test_init_from_environment(self):
        """Test initialization from environment variable."""
        service = ConfigService()
        
        self.assertEqual(service.app_config_connection_string, 'test-connection')
    
    def test_init_without_connection_string(self):
        """Test initialization without connection string (local-only mode)."""
        with patch.dict('os.environ', {}, clear=True):
            service = ConfigService()
            
            self.assertIsNone(service.app_config_connection_string)
    
    @patch('services.config_service.AzureAppConfigurationClient')
    def test_get_app_config_client_success(self, mock_client_class):
        """Test successful App Configuration client initialization."""
        connection_string = "Endpoint=https://test.azconfig.io;Id=test;Secret=test"
        service = ConfigService(connection_string)
        
        client = service._get_app_config_client()
        
        mock_client_class.from_connection_string.assert_called_once_with(connection_string)
        self.assertIsNotNone(client)
    
    def test_get_app_config_client_no_connection_string(self):
        """Test App Configuration client returns None when not configured."""
        service = ConfigService()
        
        client = service._get_app_config_client()
        
        self.assertIsNone(client)
    
    @patch('services.config_service.AzureAppConfigurationClient')
    def test_load_from_app_config_success(self, mock_client_class):
        """Test loading configuration from App Configuration."""
        # Mock App Configuration response
        mock_client = Mock()
        mock_setting = Mock()
        mock_setting.value = json.dumps({
            "database_id": "test-db-id",
            "database_name": "Test DB",
            "property_mapping": {"title": "Title"}
        })
        mock_client.get_configuration_setting.return_value = mock_setting
        mock_client_class.from_connection_string.return_value = mock_client
        
        connection_string = "Endpoint=https://test.azconfig.io;Id=test;Secret=test"
        service = ConfigService(connection_string)
        
        config = service._load_from_app_config("notion_config")
        
        self.assertIsNotNone(config)
        self.assertEqual(config['database_id'], 'test-db-id')
        self.assertEqual(config['database_name'], 'Test DB')
    
    @patch('services.config_service.AzureAppConfigurationClient')
    def test_load_from_app_config_not_found(self, mock_client_class):
        """Test loading non-existent configuration from App Configuration."""
        # Mock App Configuration response (not found)
        mock_client = Mock()
        mock_client.get_configuration_setting.return_value = None
        mock_client_class.from_connection_string.return_value = mock_client
        
        connection_string = "Endpoint=https://test.azconfig.io;Id=test;Secret=test"
        service = ConfigService(connection_string)
        
        config = service._load_from_app_config("notion_config")
        
        self.assertIsNone(config)
    
    def test_load_from_local_file_success(self):
        """Test loading configuration from local JSON file."""
        # Create temporary config file
        test_config = {
            "database_id": "local-db-id",
            "database_name": "Local DB",
            "property_mapping": {"title": "Title"}
        }
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', unittest.mock.mock_open(read_data=json.dumps(test_config))):
                service = ConfigService()
                config = service._load_from_local_file(Path("test_config.json"))
                
                self.assertIsNotNone(config)
                self.assertEqual(config['database_id'], 'local-db-id')
    
    def test_load_from_local_file_not_found(self):
        """Test loading from non-existent local file."""
        service = ConfigService()
        
        with patch('pathlib.Path.exists', return_value=False):
            config = service._load_from_local_file(Path("nonexistent.json"))
            
            self.assertIsNone(config)
    
    @patch('services.config_service.AzureAppConfigurationClient')
    def test_get_notion_config_from_app_config(self, mock_client_class):
        """Test getting Notion config from App Configuration."""
        # Mock App Configuration response
        mock_client = Mock()
        mock_setting = Mock()
        mock_setting.value = json.dumps({
            "database_id": "app-config-db-id",
            "database_name": "App Config DB",
            "property_mapping": {"title": "Title"}
        })
        mock_client.get_configuration_setting.return_value = mock_setting
        mock_client_class.from_connection_string.return_value = mock_client
        
        connection_string = "Endpoint=https://test.azconfig.io;Id=test;Secret=test"
        service = ConfigService(connection_string)
        
        config = service.get_notion_config()
        
        self.assertEqual(config['database_id'], 'app-config-db-id')
        self.assertEqual(config['database_name'], 'App Config DB')
    
    @patch('services.config_service.AzureAppConfigurationClient')
    def test_get_notion_config_fallback_to_local(self, mock_client_class):
        """Test fallback to local file when App Configuration fails."""
        # Mock App Configuration failure
        mock_client = Mock()
        mock_client.get_configuration_setting.side_effect = Exception("Connection failed")
        mock_client_class.from_connection_string.return_value = mock_client
        
        # Mock local file
        test_config = {
            "database_id": "local-fallback-id",
            "database_name": "Local Fallback DB",
            "property_mapping": {"title": "Title"}
        }
        
        connection_string = "Endpoint=https://test.azconfig.io;Id=test;Secret=test"
        service = ConfigService(connection_string)
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', unittest.mock.mock_open(read_data=json.dumps(test_config))):
                config = service.get_notion_config()
                
                self.assertEqual(config['database_id'], 'local-fallback-id')
    
    def test_get_notion_config_no_database_id(self):
        """Test error when database_id not configured."""
        test_config = {
            "database_id": "PASTE_YOUR_DATABASE_ID_HERE",
            "database_name": "Test DB"
        }
        
        service = ConfigService()
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', unittest.mock.mock_open(read_data=json.dumps(test_config))):
                with self.assertRaises(ValueError) as context:
                    service.get_notion_config()
                
                self.assertIn("database_id not configured", str(context.exception))
    
    def test_get_notion_config_not_found(self):
        """Test error when configuration not found."""
        service = ConfigService()
        
        # Mock both App Configuration and local file not found
        with patch('pathlib.Path.exists', return_value=False):
            with self.assertRaises(ValueError) as context:
                service.get_notion_config()
            
            self.assertIn("Notion configuration not found", str(context.exception))
    
    def test_config_caching(self):
        """Test that configuration is cached after first load."""
        test_config = {
            "database_id": "cached-db-id",
            "database_name": "Cached DB",
            "property_mapping": {"title": "Title"}
        }
        
        service = ConfigService()
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', unittest.mock.mock_open(read_data=json.dumps(test_config))) as mock_file:
                # First call - should read from file
                config1 = service.get_notion_config()
                
                # Second call - should use cache (file not opened again)
                config2 = service.get_notion_config()
                
                # Verify same object returned
                self.assertEqual(config1, config2)
                self.assertEqual(config1['database_id'], 'cached-db-id')
                
                # Verify file was only opened once (for first call)
                self.assertEqual(mock_file.call_count, 1)
    
    def test_clear_cache(self):
        """Test clearing configuration cache."""
        test_config = {
            "database_id": "test-db-id",
            "database_name": "Test DB",
            "property_mapping": {"title": "Title"}
        }
        
        service = ConfigService()
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', unittest.mock.mock_open(read_data=json.dumps(test_config))):
                # Load config (caches it)
                config = service.get_notion_config()
                self.assertIsNotNone(ConfigService._notion_config_cache)
                
                # Clear cache
                service.clear_cache()
                self.assertIsNone(ConfigService._notion_config_cache)


if __name__ == '__main__':
    unittest.main()
