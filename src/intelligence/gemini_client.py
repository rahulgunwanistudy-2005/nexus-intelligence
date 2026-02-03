import os
import json
import requests
from dotenv import load_dotenv
from loguru import logger
from typing import Dict, Any

# Load secrets
load_dotenv()

class GeminiIntelligence:
    """
    The Brain of Nexus.
    Uses Direct REST API (Bulletproof Mode) with Gemini 2.0 Flash.
    """

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            logger.critical("GOOGLE_API_KEY is missing in .env file")
            raise ValueError("API Key missing")

        # --- CONFIGURATION ---
        # Using the model confirmed by your diagnostic script
        self.model_name = "gemini-flash-latest"
        
        # Using v1beta endpoint which has the widest model support
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    def analyze_product_appeal(self, product_title: str, price: float) -> Dict[str, Any]:
        """
        Analyzes a product title to infer target audience and features.
        """
        # 1. Construct the URL
        url = f"{self.base_url}/{self.model_name}:generateContent?key={self.api_key}"
        
        # 2. Construct the Payload (Prompt)
        prompt_text = f"""
        You are a Market Research Expert. Analyze this product from Amazon India.
        
        Product: "{product_title}"
        Price: ₹{price}
        
        Return a valid JSON object (NO markdown formatting, just the raw JSON) with exactly these fields:
        {{
            "category": "Broad category (e.g. Audio, Gaming)",
            "target_audience": ["List of 2 potential buyer personas"],
            "implied_features": ["List of 3 tech specs mentioned or implied"],
            "value_proposition": "One short sentence on why this sells at this price"
        }}
        """
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt_text}]
            }],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.2
            }
        }

        try:
            logger.info(f"🧠 POSTing to Gemini ({self.model_name})...")
            
            # 3. Send Request with Timeout
            response = requests.post(
                url, 
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=30
            )

            # 4. Handle Errors Manually
            if response.status_code != 200:
                logger.error(f"❌ API Error {response.status_code}: {response.text}")
                return self._fallback_response()

            # 5. Parse Response
            data = response.json()
            try:
                # Extract text from the complex JSON structure
                if 'candidates' in data and data['candidates']:
                    raw_text = data['candidates'][0]['content']['parts'][0]['text']
                    
                    # Clean markdown if present (e.g., ```json ... ```)
                    if raw_text.startswith("```json"):
                        raw_text = raw_text.replace("```json", "").replace("```", "")
                    elif raw_text.startswith("```"):
                        raw_text = raw_text.replace("```", "")
                        
                    return json.loads(raw_text)
                else:
                    logger.warning("⚠️ Gemini returned no candidates (Safety block?)")
                    return self._fallback_response()

            except (KeyError, IndexError, json.JSONDecodeError) as e:
                logger.error(f"❌ Failed to parse JSON response: {e}")
                return self._fallback_response()

        except Exception as e:
            logger.error(f"❌ Network/Client Error: {e}")
            return self._fallback_response()

    def _fallback_response(self):
        """Returns empty structure so pipeline doesn't crash."""
        return {
            "category": "Unknown",
            "target_audience": [],
            "implied_features": [],
            "value_proposition": "Analysis unavailable"
        }

# --- Quick Test ---
if __name__ == "__main__":
    brain = GeminiIntelligence()
    print(f"Testing Connectivity to: {brain.model_name}")
    # Simple smoke test
    analysis = brain.analyze_product_appeal("Boat Rockerz 450 Bluetooth On Ear Headphones", 1499.0)
    print(json.dumps(analysis, indent=2))