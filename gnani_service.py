"""
CaseResolutionAI - Gnani AI Prisma Speech-to-Text & Information Extraction Service
Integrates official Gnani AI APIs (https://docs.gnani.ai/api/introduction/introduction)
"""

import os
import re
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Official Gnani AI API Endpoints & Headers
GNANI_API_BASE_URL = "https://api.vachana.ai"
GNANI_STT_ENDPOINT = f"{GNANI_API_BASE_URL}/stt/v3"

# Supported Language Mappings
SUPPORTED_LANGUAGES = {
    "English (Indian)": {
        "code": "en-IN",
        "name": "Indian English",
        "native": "English"
    },
    "Hindi (हिन्दी)": {
        "code": "hi-IN",
        "name": "Hindi",
        "native": "हिन्दी"
    },
    "Kannada (ಕನ್ನಡ)": {
        "code": "kn-IN",
        "name": "Kannada",
        "native": "ಕನ್ನಡ"
    }
}


def get_gnani_api_key() -> Optional[str]:
    """
    Safely retrieves the Gnani API key from the environment.
    Never prints or logs the key.
    """
    load_dotenv()
    key = os.getenv("GNANI_API_KEY", "").strip()
    return key if key else None


def is_gnani_api_configured() -> bool:
    """Checks whether a valid non-empty API key is present in environment."""
    key = get_gnani_api_key()
    return bool(key and key != "your_gnani_api_key_here")


def transcribe_audio_gnani(
    audio_bytes: bytes,
    language_code: str = "en-IN",
    file_name: str = "complaint_audio.wav"
) -> Dict[str, Any]:
    """
    Transcribes audio bytes using the official Gnani AI Prisma Speech-to-Text REST API.
    
    Security:
      - Reads GNANI_API_KEY from environment.
      - Never hardcodes or logs keys.
      - Returns clean, explicit error messages if unconfigured or unauthorized.
      - Never uses fake/invented responses.
    """
    api_key = get_gnani_api_key()
    
    if not api_key or api_key == "your_gnani_api_key_here":
        return {
            "success": False,
            "error_type": "MISSING_KEY",
            "error": (
                "Gnani API Key is not configured. Please add your key to the local .env file "
                "under GNANI_API_KEY to enable live voice transcription."
            )
        }
    
    if not audio_bytes or len(audio_bytes) < 100:
        return {
            "success": False,
            "error_type": "EMPTY_AUDIO",
            "error": "The recorded audio is empty or too short. Please speak clearly into the microphone."
        }
    
    headers = {
        "X-API-Key-ID": api_key
    }
    
    payload = {
        "model": "prisma-v3.0",
        "language_code": language_code
    }
    
    # Infer mime-type from file_name
    mime_type = "audio/wav"
    if file_name.lower().endswith(".mp3"):
        mime_type = "audio/mpeg"
    elif file_name.lower().endswith(".ogg"):
        mime_type = "audio/ogg"
    elif file_name.lower().endswith(".m4a"):
        mime_type = "audio/m4a"

    files = {
        "audio_file": (file_name, audio_bytes, mime_type)
    }

    try:
        response = requests.post(
            GNANI_STT_ENDPOINT,
            headers=headers,
            files=files,
            data=payload,
            timeout=35
        )
        
        if response.status_code == 200:
            data = response.json()
            transcript = data.get("transcript", "").strip()
            return {
                "success": True,
                "transcript": transcript,
                "detected_language": data.get("detected_language_code", language_code),
                "model": data.get("model", "prisma-v3.0"),
                "raw_response": data
            }
        elif response.status_code == 401:
            return {
                "success": False,
                "error_type": "UNAUTHORIZED",
                "error": "Authentication failed (401 Unauthorized). The GNANI_API_KEY in your .env file is invalid or expired. Please check your credentials in the Gnani dashboard."
            }
        elif response.status_code == 403:
            return {
                "success": False,
                "error_type": "FORBIDDEN",
                "error": "Access forbidden (403 Forbidden). Ensure your Gnani account has active credits or permission for Prisma STT v3."
            }
        else:
            return {
                "success": False,
                "error_type": f"HTTP_{response.status_code}",
                "error": f"Gnani STT API error (HTTP {response.status_code}): {response.text}"
            }
            
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error_type": "TIMEOUT",
            "error": "Request timed out while communicating with Gnani AI STT servers. Please check your network connection and try again."
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error_type": "NETWORK_ERROR",
            "error": f"Network communication error: {str(e)}"
        }


def extract_complaint_fields(transcript: str, language_code: str = "en-IN") -> Dict[str, Any]:
    """
    Extracts structured consumer complaint fields from the transcript text.
    Extracts all 11 core parameters specified in the platform blueprint:
    - customer_name, seller_name, product_name, purchase_date, delivery_date,
      order_id, purchase_amount, complaint_category, problem_description,
      seller_promises, refund_resolution_status, desired_resolution.
    
    If information is missing, identifies missing fields and generates
    targeted follow-up questions without hallucinating.
    """
    t_clean = transcript.strip()
    if not t_clean:
        return {
            "customer_name": None,
            "seller_name": None,
            "product_name": None,
            "purchase_date": None,
            "delivery_date": None,
            "order_id": None,
            "purchase_amount": None,
            "complaint_category": None,
            "problem_description": None,
            "seller_promises": None,
            "refund_resolution_status": None,
            "desired_resolution": None,
            "missing_fields": [
                "customer_name", "product_name", "seller_name", "purchase_amount", 
                "purchase_date", "delivery_date", "order_id", "complaint_category",
                "problem_description", "seller_promises", "refund_resolution_status", "desired_resolution"
            ],
            "follow_up_questions": [
                "What is your full name?",
                "What product or service did you purchase?",
                "Which seller, website, or company did you buy from?",
                "How much did you pay (in ₹ INR)?",
                "On what date was the purchase made?",
                "When was the product delivered to you?",
                "What is your order reference number or support ticket ID?",
                "What is the category of your complaint (e.g., Damaged Product, Delayed Refund)?",
                "What was the exact defect or problem encountered?",
                "Did the seller promise a refund, replacement, or repair?",
                "What is the current status of your refund or complaint?",
                "What specific remedy or resolution do you seek (e.g., Full Refund)?"
            ]
        }

    extracted = {
        "customer_name": None,
        "seller_name": None,
        "product_name": None,
        "purchase_date": None,
        "delivery_date": None,
        "order_id": None,
        "purchase_amount": None,
        "complaint_category": None,
        "problem_description": None,
        "seller_promises": None,
        "refund_resolution_status": None,
        "desired_resolution": None
    }

    t_lower = t_clean.lower()

    # 1. Customer Name Extraction
    name_match = re.search(r'(?:my\s+name\s+is|i\s+am|myself|this\s+is)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)', t_lower)
    if name_match:
        c_name = name_match.group(1).strip().title()
        if c_name.lower() not in ["writing", "facing", "reporting", "a", "an", "the"]:
            extracted["customer_name"] = c_name

    # 2. Purchase Amount Extraction (₹, Rs, Rupees, numbers)
    amount_match = re.search(r'(?:₹|rs\.?|rupees|inr|amount\s+of|cost\s+of|paid)\s*[:=]?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?|[0-9]+)', t_lower)
    if not amount_match:
        amount_match = re.search(r'([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?|[0-9]{3,})\s*(?:rupees|rs|bucks|inr)', t_lower)
    
    if amount_match:
        try:
            amt_str = amount_match.group(1).replace(',', '')
            val = float(amt_str)
            if val > 0:
                extracted["purchase_amount"] = val
        except ValueError:
            pass

    # 3. Seller Name Extraction
    seller_patterns = [
        r'(?:bought\s+from|purchased\s+from|ordered\s+from|seller(?:\s+is|\s+name)?|from\s+website|from\s+store)\s+([A-Za-z0-9\s&.\'\-]+?)(?:\s+(?:on|for|at|under|with|but|and|in)|[.,;\n]|$)',
        r'(amazon|flipkart|myntra|croma|reliance\s+digital|tata\s+cliq|meesho|novacart|ajio|nykaa)'
    ]
    for pat in seller_patterns:
        s_match = re.search(pat, t_lower)
        if s_match:
            s_name = s_match.group(1).strip().title()
            if len(s_name) > 1 and s_name.lower() not in ["the", "a", "an", "this", "my"]:
                extracted["seller_name"] = s_name
                break

    # 4. Product Name Extraction
    product_patterns = [
        r'(?:ordered\s+a|ordered\s+an|purchased\s+a|purchased\s+an|bought\s+a|bought\s+an|item\s+is\s+a?|product\s+is\s+a?)\s+([A-Za-z0-9\s\-_/]+?)(?:\s+(?:from|on|worth|for|costing|with|delivered)|[.,;\n]|$)',
        r'(laptop|phone|smartphone|mobile|television|tv|refrigerator|washing\s+machine|headphones|air\s+conditioner|tablet|watch|earbuds)'
    ]
    for pat in product_patterns:
        p_match = re.search(pat, t_lower)
        if p_match:
            p_name = p_match.group(1).strip().title()
            if len(p_name) > 2 and p_name.lower() not in ["the", "this", "my", "package", "order"]:
                extracted["product_name"] = p_name
                break

    # 5. Order ID / Ticket ID Extraction
    order_id_match = re.search(r'(?:order\s+(?:id|number|no|ref)|ticket\s+(?:id|number|no|ref)|ref\s+no)\s*[:=]?\s*#?([A-Za-z0-9\-_]+)', t_lower)
    if not order_id_match:
        order_id_match = re.search(r'#([A-Za-z0-9\-_]{4,})', t_clean)
    if order_id_match:
        extracted["order_id"] = order_id_match.group(1).upper()

    # 6. Dates Extraction: Purchase Date vs Delivery Date
    date_regex = r'(?:[0-9]{1,2}(?:st|nd|rd|th)?\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)(?:\s+[0-9]{4})?|[0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})'
    
    purch_date_match = re.search(r'(?:purchased|ordered|bought)(?:[a-zA-Z0-9\s\-_#.:]{0,100})\s+on\s+(' + date_regex + ')', t_lower)
    if not purch_date_match:
        purch_date_match = re.search(r'(?:order\s+date|booking\s+date)(?:\s+is|\s+was)?\s+(' + date_regex + ')', t_lower)
    if purch_date_match:
        extracted["purchase_date"] = purch_date_match.group(1).title()

    deliv_date_match = re.search(r'(?:delivered|received|package\s+arrived)(?:[a-zA-Z0-9\s\-_#.:]{0,60})\s+on\s+(' + date_regex + ')', t_lower)
    if not deliv_date_match:
        deliv_date_match = re.search(r'(?:delivery\s+date|delivery\s+was\s+on)\s+(' + date_regex + ')', t_lower)
    if deliv_date_match:
        extracted["delivery_date"] = deliv_date_match.group(1).title()

    # 7. Problem Description
    issue_keywords = ["broken", "damaged", "crack", "defective", "not working", "screen bleed", "torn", "missing", "delay", "fake", "faulty", "bad"]
    if any(k in t_lower for k in issue_keywords):
        extracted["problem_description"] = t_clean
    else:
        if len(t_clean) >= 40:
            extracted["problem_description"] = t_clean

    # 8. Complaint Category Classification
    if "damage" in t_lower or "crack" in t_lower or "broken" in t_lower:
        extracted["complaint_category"] = "Damaged on Delivery"
    elif "defect" in t_lower or "not working" in t_lower or "faulty" in t_lower:
        extracted["complaint_category"] = "Defective / Non-Functional Product"
    elif "refund" in t_lower and ("delay" in t_lower or "not received" in t_lower or "refused" in t_lower):
        extracted["complaint_category"] = "Delayed or Refused Refund"
    elif "wrong" in t_lower or "fake" in t_lower or "mismatch" in t_lower:
        extracted["complaint_category"] = "Wrong Item / Specification Mismatch"
    else:
        extracted["complaint_category"] = "Consumer Grievance"

    # 9. Seller Promises (commitments to refund, replace, repair within N days)
    promise_match = re.search(r'(?:promised|assured|committed|guaranteed|agreed\s+to|told\s+me\s+they\s+would)\s+([A-Za-z0-9\s,.\'-]+?)(?:\.|$)', t_lower)
    if promise_match:
        extracted["seller_promises"] = promise_match.group(0).capitalize()
    elif "7 days" in t_lower or "seven days" in t_lower or "48 hours" in t_lower or "within a week" in t_lower:
        extracted["seller_promises"] = "Seller promised resolution / refund within standard SLA timeline."

    # 10. Refund or Resolution Status
    if any(w in t_lower for w in ["not refunded", "no refund", "delayed refund", "waiting for refund", "refund pending", "refund not received", "still waiting"]):
        extracted["refund_resolution_status"] = "Refund Delayed / Pending (Not Received)"
    elif "under review" in t_lower:
        extracted["refund_resolution_status"] = "Under Review / Awaiting Logistics Hub"
    elif "replacement" in t_lower and ("pending" in t_lower or "not sent" in t_lower):
        extracted["refund_resolution_status"] = "Replacement Not Provided"

    # 11. Desired Resolution
    if "refund" in t_lower:
        extracted["desired_resolution"] = "Full Refund of Purchase Amount"
    elif "replacement" in t_lower or "replace" in t_lower:
        extracted["desired_resolution"] = "Free Replacement with Brand New Sealed Unit"
    elif "repair" in t_lower:
        extracted["desired_resolution"] = "Free Repair under Manufacturer Warranty"
    else:
        extracted["desired_resolution"] = "Full Refund / Product Resolution"

    # Identify Missing Fields and Targeted Follow-Up Questions
    missing_fields = []
    follow_up_questions = []

    field_questions = {
        "product_name": "What product or service did you purchase (e.g., brand and model name)?",
        "seller_name": "What is the name of the seller or platform you purchased from?",
        "purchase_amount": "What was the total purchase price paid in ₹ (INR)?",
        "purchase_date": "On what date was the purchase made or ordered?",
        "delivery_date": "On what date was the item delivered to you?",
        "order_id": "What is the order ID, invoice number, or support ticket reference?",
        "problem_description": "Can you describe what was damaged or defective about the item?",
        "seller_promises": "Did customer care or the seller promise a specific resolution time or return window?",
        "refund_resolution_status": "What is the current status of your refund or complaint?"
    }

    for key, prompt_q in field_questions.items():
        if not extracted.get(key):
            missing_fields.append(key)
            follow_up_questions.append(prompt_q)

    return {
        **extracted,
        "missing_fields": missing_fields,
        "follow_up_questions": follow_up_questions
    }
