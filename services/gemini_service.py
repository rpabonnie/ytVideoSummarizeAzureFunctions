"""
Gemini AI service for YouTube video summarization.

This service encapsulates all Google Gemini API interactions including:
- Azure Key Vault integration for API key retrieval
- Video summarization with structured prompts
- JSON response parsing and validation
"""

import logging
import json
from typing import Optional
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from google import genai
from google.genai import types

from utils.exceptions import GeminiApiError, KeyVaultError


class GeminiService:
    """Service for YouTube video summarization using Google Gemini AI."""
    
    # Module-level cache for API credentials (singleton pattern)
    _credential: Optional[DefaultAzureCredential] = None
    _secret_client: Optional[SecretClient] = None
    _gemini_api_key: Optional[str] = None
    _gemini_client: Optional[genai.Client] = None
    
    def __init__(self, key_vault_url: str):
        """
        Initialize Gemini service with Key Vault URL.
        
        Args:
            key_vault_url: Azure Key Vault URL (e.g., https://your-vault.vault.azure.net/)
            
        Raises:
            ValueError: If key_vault_url is empty or invalid
        """
        if not key_vault_url:
            raise ValueError("key_vault_url cannot be empty")
        
        self.key_vault_url = key_vault_url
        logging.info(f"GeminiService initialized with Key Vault: {key_vault_url}")
    
    def _get_api_key(self) -> str:
        """
        Retrieve Gemini API key from Azure Key Vault (with caching).
        
        Returns:
            str: Gemini API key
            
        Raises:
            KeyVaultError: If Key Vault access fails
        """
        # Return cached key if available
        if GeminiService._gemini_api_key:
            return GeminiService._gemini_api_key
        
        try:
            # Initialize credential if not cached
            if not GeminiService._credential:
                logging.info("Initializing DefaultAzureCredential for Key Vault access")
                GeminiService._credential = DefaultAzureCredential()
            
            # Initialize secret client if not cached
            if not GeminiService._secret_client:
                logging.info(f"Connecting to Key Vault: {self.key_vault_url}")
                GeminiService._secret_client = SecretClient(
                    vault_url=self.key_vault_url,
                    credential=GeminiService._credential
                )
            
            # Retrieve and cache API key
            logging.info("Retrieving GOOGLE-API-KEY from Key Vault")
            secret = GeminiService._secret_client.get_secret("GOOGLE-API-KEY")
            GeminiService._gemini_api_key = secret.value
            
            if not GeminiService._gemini_api_key:
                raise KeyVaultError("Retrieved API key is empty or None")
            
            logging.info("Successfully retrieved Gemini API key from Key Vault")
            return GeminiService._gemini_api_key
            
        except Exception as e:
            error_msg = (
                "Failed to retrieve Gemini API key from Key Vault. "
                "Ensure you're authenticated with 'az login' for local development, "
                "or that Managed Identity is configured in Azure."
            )
            logging.error(f"{error_msg} Details: {str(e)}")
            raise KeyVaultError(error_msg, original_error=e)
    
    def _initialize_client(self) -> genai.Client:
        """
        Initialize Gemini API client (with caching).
        
        Returns:
            genai.Client: Initialized Gemini client
            
        Raises:
            GeminiApiError: If client initialization fails
        """
        # Return cached client if available
        if GeminiService._gemini_client:
            return GeminiService._gemini_client
        
        try:
            api_key = self._get_api_key()
            logging.info("Initializing Gemini API client")
            GeminiService._gemini_client = genai.Client(api_key=api_key)
            return GeminiService._gemini_client
            
        except KeyVaultError:
            raise  # Re-raise KeyVaultError as-is
        except Exception as e:
            error_msg = "Failed to initialize Gemini API client"
            logging.error(f"{error_msg}: {str(e)}")
            raise GeminiApiError(error_msg, original_error=e)
    
    def _build_prompt(self, youtube_url: str) -> str:
        """
        Generate structured prompt for Gemini video analysis.
        
        Args:
            youtube_url: Validated YouTube URL
            
        Returns:
            str: Formatted prompt for Gemini
        """
        prompt = f"""
        Please analyze this attached YouTube video and provide a comprehensive summary in JSON format.
        Provide insights I can save on a second brain system in Notion. The Title should be the original video title from YouTube.
        If the native language of the video is in spanish, match the summary language to spanish, otherwise use english.

        Return your response as a JSON object with the following structure:
        {{
            "title": "The original title from YouTube",
            "tags": ["tag1", "tag2", "tag3"],
            "url": "{youtube_url}",
            "brief_summary": "Concise paragraph summarizing the video content.",
            "summary_bullets": [
                "Key point 1",
                "Key point 2",
                "Key point 3"
            ],
            "tools_and_technologies": [
                {{
                    "tool": "Tool name",
                    "purpose": "What it was used for in the video"
                }}
            ]
        }}
        
        Make the summary informative and actionable. Focus on key takeaways, main concepts, and practical applications.
        """
        return prompt
    
    def _parse_response(self, response_text: str) -> dict:
        """
        Parse and validate Gemini response as JSON.
        
        Args:
            response_text: Raw text response from Gemini
            
        Returns:
            dict: Parsed JSON summary or fallback structure
        """
        try:
            # Extract JSON from markdown code blocks if present
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                summary_json = json.loads(response_text[json_start:json_end].strip())
            elif '```' in response_text:
                json_start = response_text.find('```') + 3
                json_end = response_text.find('```', json_start)
                summary_json = json.loads(response_text[json_start:json_end].strip())
            else:
                summary_json = json.loads(response_text)
            
            logging.info("Successfully parsed Gemini response as JSON")
            return summary_json
            
        except json.JSONDecodeError as e:
            logging.warning(f"Could not parse Gemini response as JSON: {str(e)}")
            # Return fallback structure with raw response
            return {
                "raw_response": response_text,
                "note": "Response was not in expected JSON format"
            }
    
    def summarize_video(self, youtube_url: str) -> dict:
        """
        Summarize YouTube video using Gemini AI.
        
        This method:
        1. Initializes Gemini client (with Key Vault authentication)
        2. Sends video URL and structured prompt to Gemini
        3. Processes video with LOW media resolution (supports up to ~3 hour videos)
        4. Parses and returns JSON-formatted summary
        
        Args:
            youtube_url: Validated and sanitized YouTube URL
            
        Returns:
            dict: Structured summary containing:
                - title: Video title
                - tags: List of relevant tags
                - url: Original YouTube URL
                - brief_summary: Paragraph overview
                - summary_bullets: Key points as bullet list
                - tools_and_technologies: List of tools mentioned
                
        Raises:
            GeminiApiError: If video processing fails
            KeyVaultError: If Key Vault access fails
        """
        try:
            # Initialize client
            client = self._initialize_client()
            
            # Build prompt
            prompt = self._build_prompt(youtube_url)
            
            # Log processing details
            logging.info(f"Processing YouTube video: {youtube_url}")
            logging.info("Using LOW media resolution to prevent token limit errors")
            logging.info("Low resolution: ~100 tokens/second vs default ~300 tokens/second")
            logging.info("This allows processing videos up to ~3 hours instead of ~1 hour")
            
            # Call Gemini API with LOW media resolution
            # This reduces token consumption by ~66% (300 -> 100 tokens/second)
            response = client.models.generate_content(
                model='gemini-2.5-pro',
                contents=[
                    types.Part(
                        file_data=types.FileData(file_uri=youtube_url)
                    ),
                    types.Part(text=prompt)
                ],
                config=types.GenerateContentConfig(
                    media_resolution=types.MediaResolution.MEDIA_RESOLUTION_LOW
                )
            )
            
            # Extract and validate response
            summary_text = response.text
            if not summary_text:
                raise GeminiApiError("Gemini returned empty response")
            
            logging.info("Successfully received response from Gemini")
            logging.info(f"Gemini Response:\n{summary_text}")
            
            # Parse and return JSON
            return self._parse_response(summary_text)
            
        except KeyVaultError:
            raise  # Re-raise KeyVaultError as-is
        except GeminiApiError:
            raise  # Re-raise GeminiApiError as-is
        except Exception as e:
            error_msg = f"Failed to process video with Gemini: {str(e)}"
            logging.error(error_msg)
            raise GeminiApiError(error_msg, original_error=e)
