"""
Wine label analysis service using OpenAI GPT-4 Vision.

This module provides functionality to analyze wine bottle label images
and extract structured information about the wine.
"""
import base64
import json
import logging
from io import BytesIO
from typing import Optional

from django.conf import settings
from PIL import Image
from thefuzz import fuzz

logger = logging.getLogger(__name__)


class LabelAnalysisError(Exception):
    """Exception raised when label analysis fails."""
    pass


ANALYSIS_PROMPT = """Analyze this wine bottle label image and extract the following information.
Return a JSON object with these fields:

{
  "name": "The wine name/brand (string or null)",
  "vintage": "The year the wine was produced (integer or null)",
  "wine_type": "One of: red, white, rosé, sparkling (string or null)",
  "country": "ISO 3166-1 alpha-2 country code, e.g. FR, IT, ES (string or null)",
  "region": "Wine region or appellation, e.g. Bordeaux, Rioja, Chianti (string or null)",
  "grape_varieties": "Comma-separated list of grape varieties (string or null)",
  "alcohol_percentage": "Alcohol percentage as decimal, e.g. 13.5 (number or null)",
  "confidence": {
    "name": 0.0-1.0,
    "vintage": 0.0-1.0,
    "wine_type": 0.0-1.0,
    "country": 0.0-1.0,
    "region": 0.0-1.0,
    "grape_varieties": 0.0-1.0,
    "alcohol_percentage": 0.0-1.0
  },
  "raw_text": "All readable text from the label"
}

Important:
- Use null for any field you cannot determine with reasonable confidence
- For country, always use ISO 3166-1 alpha-2 codes (FR, IT, ES, DE, US, AU, etc.)
- For wine_type, only use: red, white, rosé, sparkling
- Confidence scores should reflect how certain you are about each field (0.0 = guess, 1.0 = certain)
- Include ALL readable text in raw_text for transparency

Return ONLY valid JSON, no markdown formatting or explanation."""


def _resize_image(image: Image.Image, max_size: int) -> Image.Image:
    """
    Resize image to fit within max_size while maintaining aspect ratio.
    
    Args:
        image: PIL Image object
        max_size: Maximum dimension (width or height) in pixels
        
    Returns:
        Resized PIL Image object
    """
    width, height = image.size
    
    if width <= max_size and height <= max_size:
        return image
    
    if width > height:
        new_width = max_size
        new_height = int(height * (max_size / width))
    else:
        new_height = max_size
        new_width = int(width * (max_size / height))
    
    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


def _image_to_base64(image: Image.Image) -> str:
    """
    Convert PIL Image to base64 encoded string.
    
    Args:
        image: PIL Image object
        
    Returns:
        Base64 encoded string of the image in JPEG format
    """
    # Convert to RGB if necessary (handles RGBA, P mode images)
    if image.mode in ('RGBA', 'P', 'LA'):
        image = image.convert('RGB')
    
    buffer = BytesIO()
    image.save(buffer, format='JPEG', quality=85)
    buffer.seek(0)
    
    return base64.b64encode(buffer.read()).decode('utf-8')


def _call_openai_vision(base64_image: str) -> dict:
    """
    Call OpenAI Vision API to analyze the wine label.
    
    Args:
        base64_image: Base64 encoded image string
        
    Returns:
        Parsed JSON response from OpenAI
        
    Raises:
        LabelAnalysisError: If API call fails or response is invalid
    """
    # Import here to avoid import errors when openai is not installed
    from openai import OpenAI, APIError, APIConnectionError, RateLimitError
    
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise LabelAnalysisError("OpenAI API key not configured")
    
    model = getattr(settings, 'OPENAI_MODEL', 'gpt-4o')
    
    try:
        client = OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": ANALYSIS_PROMPT
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000,
            temperature=0.1  # Low temperature for more consistent extraction
        )
        
        content = response.choices[0].message.content
        if not content:
            raise LabelAnalysisError("Empty response from AI service")
        
        # Clean up response - remove markdown code blocks if present
        content = content.strip()
        if content.startswith('```json'):
            content = content[7:]
        if content.startswith('```'):
            content = content[3:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        
        return json.loads(content)
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse OpenAI response as JSON: {e}")
        raise LabelAnalysisError("Could not parse AI response")
    except RateLimitError:
        logger.warning("OpenAI rate limit exceeded")
        raise LabelAnalysisError("AI service rate limit exceeded. Please try again later.")
    except APIConnectionError:
        logger.error("Could not connect to OpenAI API")
        raise LabelAnalysisError("AI service temporarily unavailable")
    except APIError as e:
        logger.error(f"OpenAI API error: {e}")
        raise LabelAnalysisError("AI service error occurred")
    except Exception as e:
        logger.error(f"Unexpected error calling OpenAI: {e}")
        raise LabelAnalysisError(f"Unexpected error: {str(e)}")


def _find_matching_region(region_name: Optional[str], country_code: Optional[str]) -> Optional[dict]:
    """
    Find a matching region in the database using fuzzy matching.
    
    Args:
        region_name: The region name extracted from the label
        country_code: The ISO country code extracted from the label
        
    Returns:
        Dictionary with matched region info and score, or None if no match found
    """
    if not region_name:
        return None
    
    from winemanager.models import Region
    
    # Get candidate regions, prioritizing same country
    if country_code:
        # First try regions in the same country
        candidates = list(Region.objects.filter(country=country_code))
        # Then add regions from other countries
        candidates.extend(list(Region.objects.exclude(country=country_code)))
    else:
        candidates = list(Region.objects.all())
    
    if not candidates:
        return None
    
    best_match = None
    best_score = 0
    
    region_name_lower = region_name.lower()
    
    for region in candidates:
        # Calculate fuzzy match score
        score = fuzz.ratio(region_name_lower, region.name.lower())
        
        # Boost score if country matches
        if country_code and str(region.country) == country_code:
            score = min(100, score + 10)
        
        if score > best_score:
            best_score = score
            best_match = region
    
    # Only return if score is above threshold (80%)
    if best_match and best_score >= 80:
        return {
            "id": best_match.id,
            "name": best_match.name,
            "country": str(best_match.country),
            "match_score": best_score / 100.0
        }
    
    return None


def analyze_wine_label(image_file) -> dict:
    """
    Analyze a wine label image and extract structured information.
    
    Args:
        image_file: A file-like object containing the image data
        
    Returns:
        Dictionary containing extracted wine information with confidence scores
        
    Raises:
        LabelAnalysisError: If the image cannot be processed or analyzed
    """
    # Validate and load image
    try:
        image = Image.open(image_file)
        image.verify()  # Verify it's a valid image
        
        # Re-open after verify (verify() can only be called once)
        image_file.seek(0)
        image = Image.open(image_file)
        
    except Exception as e:
        logger.warning(f"Invalid image file: {e}")
        raise LabelAnalysisError("Invalid image format. Supported formats: JPEG, PNG, WebP")
    
    # Resize image to limit API costs
    max_size = getattr(settings, 'OPENAI_MAX_IMAGE_SIZE', 1024)
    image = _resize_image(image, max_size)
    
    # Convert to base64
    base64_image = _image_to_base64(image)
    
    # Call OpenAI Vision API
    ai_response = _call_openai_vision(base64_image)
    
    # Extract fields from response
    data = {
        "name": ai_response.get("name"),
        "vintage": ai_response.get("vintage"),
        "wine_type": ai_response.get("wine_type"),
        "country": ai_response.get("country"),
        "grape_varieties": ai_response.get("grape_varieties"),
        "alcohol_percentage": ai_response.get("alcohol_percentage"),
        "suggested_region_name": ai_response.get("region"),
    }
    
    # Validate wine_type
    valid_types = ["red", "white", "rosé", "sparkling"]
    if data["wine_type"] and data["wine_type"] not in valid_types:
        data["wine_type"] = None
    
    # Find matching region in database
    matched_region = _find_matching_region(
        ai_response.get("region"),
        ai_response.get("country")
    )
    
    # Build response
    result = {
        "success": True,
        "data": {
            **data,
            "matched_region": matched_region
        },
        "confidence": ai_response.get("confidence", {}),
        "raw_text": ai_response.get("raw_text", "")
    }
    
    return result
