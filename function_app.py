import azure.functions as func
import logging
import json
import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import google.generativeai as genai

app = func.FunctionApp(http_auth_level=func.AuthLevel.ADMIN)

@app.route(route="ytSummarizeToNotion", methods=["POST"])
def ytSummarizeToNotion(req: func.HttpRequest) -> func.HttpResponse:
    """
    Secure Azure Function that accepts YouTube URLs and generates summaries using Gemini.
    Requires ADMIN authentication (x-functions-key header).
    """
    logging.info('YouTube Summarize to Notion function triggered.')
    
    try:
        # Step 1: Parse and validate the incoming request
        try:
            req_body = req.get_json()
        except ValueError:
            logging.error("Invalid JSON in request body")
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON format"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Extract YouTube URL from request
        youtube_url = req_body.get('url')
        
        if not youtube_url:
            logging.error("Missing 'url' field in request body")
            return func.HttpResponse(
                json.dumps({"error": "Missing 'url' field in request body"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Basic YouTube URL validation
        if not ('youtube.com' in youtube_url or 'youtu.be' in youtube_url):
            logging.error(f"Invalid YouTube URL: {youtube_url}")
            return func.HttpResponse(
                json.dumps({"error": "Invalid YouTube URL. Must be a youtube.com or youtu.be link"}),
                status_code=400,
                mimetype="application/json"
            )
        
        logging.info(f"Processing YouTube URL: {youtube_url}")
        
        # Step 2: Retrieve secrets from Azure Key Vault
        key_vault_url = os.environ.get("KEY_VAULT_URL")
        
        if not key_vault_url:
            logging.error("KEY_VAULT_URL not configured")
            return func.HttpResponse(
                json.dumps({"error": "Server configuration error"}),
                status_code=500,
                mimetype="application/json"
            )
        
        logging.info(f"Connecting to Key Vault: {key_vault_url}")
        
        try:
            # Use DefaultAzureCredential for authentication
            # In local dev, this uses Azure CLI credentials (az login)
            # In Azure, this uses Managed Identity
            credential = DefaultAzureCredential()
            secret_client = SecretClient(vault_url=key_vault_url, credential=credential)
            
            # Retrieve Gemini API key from Key Vault
            logging.info("Retrieving GOOGLE-API-KEY from Key Vault")
            gemini_key = secret_client.get_secret("GOOGLE-API-KEY").value
            
            # Notion key retrieval is commented out for now (step 3b stops before Notion integration)
            # logging.info("Retrieving NOTION-API-KEY from Key Vault")
            # notion_key = secret_client.get_secret("NOTION-API-KEY").value
            
            logging.info("Successfully retrieved secrets from Key Vault")
            
        except Exception as e:
            logging.error(f"Failed to retrieve secrets from Key Vault: {str(e)}")
            return func.HttpResponse(
                json.dumps({"error": "Failed to authenticate with Key Vault. Ensure you're logged in with 'az login'"}),
                status_code=500,
                mimetype="application/json"
            )
        
        # Step 3: Configure Gemini API
        genai.configure(api_key=gemini_key)
        
        # Step 4: Create prompt for Gemini to summarize YouTube video
        # The prompt instructs Gemini to format output as JSON compatible with Notion
        prompt = f"""
        Please analyze this attached YouTube video and provide a comprehensive summary in JSON format.
        Provide insights I can save on a second brain system in Notion.
        
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
        
        logging.info("Sending request to Gemini API for video analysis")
        
        try:
            # Use Gemini's native video processing capability
            # Gemini 2.5 Pro and Flash models can process YouTube URLs directly
            model = genai.GenerativeModel('gemini-2.5-pro')
            
            # Format the request according to Gemini API specification
            response = model.generate_content([
                prompt,
                {"file_data" :{"file_uri": youtube_url}}
            ])
            
            # Extract the response text
            summary_text = response.text
            logging.info("Successfully received response from Gemini")
            
            # Log the raw summary for verification
            logging.info(f"Gemini Response:\n{summary_text}")
            
            # Try to parse the response as JSON
            try:
                # Extract JSON from markdown code blocks if present
                if '```json' in summary_text:
                    json_start = summary_text.find('```json') + 7
                    json_end = summary_text.find('```', json_start)
                    summary_json = json.loads(summary_text[json_start:json_end].strip())
                elif '```' in summary_text:
                    json_start = summary_text.find('```') + 3
                    json_end = summary_text.find('```', json_start)
                    summary_json = json.loads(summary_text[json_start:json_end].strip())
                else:
                    summary_json = json.loads(summary_text)
                
                logging.info("Successfully parsed Gemini response as JSON")
                
            except json.JSONDecodeError:
                logging.warning("Could not parse Gemini response as JSON, returning as text")
                summary_json = {
                    "raw_response": summary_text,
                    "note": "Response was not in expected JSON format"
                }
            
            # Step 5: Return the summary (Notion integration will be added later)
            return func.HttpResponse(
                json.dumps({
                    "status": "success",
                    "youtube_url": youtube_url,
                    "summary": summary_json,
                    "note": "Video summarized successfully. Notion integration pending."
                }, indent=2),
                status_code=200,
                mimetype="application/json"
            )
            
        except Exception as e:
            logging.error(f"Gemini API error: {str(e)}")
            return func.HttpResponse(
                json.dumps({"error": f"Failed to process video with Gemini: {str(e)}"}),
                status_code=500,
                mimetype="application/json"
            )
    
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Internal server error: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )
