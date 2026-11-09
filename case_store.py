"""
CaseResolutionAI - Case Data Store, Multilingual Templates & Readiness Engine
Manages case records, readiness scoring, Indic language notice templates, 
NCH portal formatting, and session persistence.
"""

import json
from datetime import date, datetime
from typing import Dict, List, Any


# ---------------------------------------------------------
# Multilingual Spoken Sample Scenarios for Testing
# ---------------------------------------------------------
SAMPLE_SPOKEN_SCENARIOS = {
    "English (Indian)": {
        "title": "Damaged Laptop with Delayed Refund",
        "audio_text": (
            "I ordered an AeroBook X14 laptop from NovaCart on 24th October for 58499 rupees. "
            "It was delivered on 26th October with a broken hinge and cracked screen. "
            "I reported it within 2 hours under ticket RET-884129. "
            "Customer support promised a full refund within 7 business days after courier pickup, "
            "which happened on 28th October. Today more than 10 days have passed, and no refund has been received."
        ),
        "notes": "Covers all 8 complaint parameters."
    },
    "Hindi (हिन्दी)": {
        "title": "खराब टीवी और लंबित रिफंड (Defective Smart TV)",
        "audio_text": (
            "मैंने 15 अक्टूबर को NovaCart से 32000 रुपये में UltraView 43 इंच स्मार्ट टीवी खरीदा था। "
            "यह 18 अक्टूबर को डिलीवर हुआ लेकिन स्क्रीन चालू ही नहीं हो रही है। "
            "कस्टमर केयर ने कहा था कि 5 दिनों में रिप्लेसमेंट या रिफंड हो जाएगा। "
            "अब तक कोई रिफंड या सहायता नहीं मिली है।"
        ),
        "notes": "Covers purchase price, delivery defect, and delayed resolution in Hindi."
    },
    "Kannada (ಕನ್ನಡ)": {
        "title": "ದೋಷಯುಕ್ತ ಮೊಬೈಲ್ ಫೋನ್ ಮತ್ತು ಮರುಪಾವತಿ ವಿಳಂಬ (Defective Mobile)",
        "audio_text": (
            "ನಾನು 20 ಅಕ್ಟೋಬರ್ ರಂದು NovaCart ನಲ್ಲಿ 24999 ರೂಪಾಯಿಗೆ Nova5G ಮೊಬೈಲ್ ಫೋನ್ ಆರ್ಡರ್ ಮಾಡಿದ್ದೆ. "
            "ಇದು 22 ಅಕ್ಟೋಬರ್ ರಂದು ಡೆಲಿವರಿ ಆಯಿತು, ಆದರೆ ಬ್ಯಾಟರಿ ಸರಿಯಾಗಿ ಚಾರ್ಜ್ ಆಗುತ್ತಿಲ್ಲ. "
            "ಗ್ರಾಹಕ ಸೇವಾ ಕೇಂದ್ರವು 7 ದಿನಗಳಲ್ಲಿ ಹೊಸ ಫೋನ್ ನೀಡುತ್ತೇವೆ ಎಂದು ಭರವಸೆ ನೀಡಿದ್ದರು, "
            "ಆದರೆ ಇದುವರೆಗೆ ಯಾವುದೇ ಪರಿಹಾರ ಸಿಕ್ಕಿಲ್ಲ."
        ),
        "notes": "Covers purchase, delivery, defect, and SLA breach in Kannada."
    }
}


# ---------------------------------------------------------
# Escalation Stage Definition
# ---------------------------------------------------------
ESCALATION_STAGES = [
    {"stage": 1, "label": "Evidence Documented", "desc": "Receipts and photos collected"},
    {"stage": 2, "label": "Notice Sent to Seller", "desc": "Customer care ticket logged"},
    {"stage": 3, "label": "Grievance Officer Escalated", "desc": "Formal notice sent to Nodal Officer"},
    {"stage": 4, "label": "Reported to NCH (1915)", "desc": "Registered on National Consumer Helpline"},
    {"stage": 5, "label": "Resolved / Closed", "desc": "Refund or replacement received"}
]


def calculate_readiness_score(case_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes an objective, rule-based dossier completeness score.
    Does NOT predict legal outcomes or guarantee refunds; 
    evaluates whether necessary factual records are assembled.
    """
    score = 0
    checks = []

    # 1. Purchase Information Completeness (20 pts)
    if case_data.get("product_name") and case_data.get("purchase_amount", 0) > 0 and case_data.get("purchase_date"):
        score += 20
        checks.append({"item": "Basic Purchase Information", "passed": True, "detail": "Product name, price, and purchase date recorded."})
    else:
        checks.append({"item": "Basic Purchase Information", "passed": False, "detail": "Missing purchase price or date."})

    # 2. Support Reference / Ticket ID (20 pts)
    ticket_ref = str(case_data.get("support_ticket_ref", "")).strip()
    if ticket_ref and ticket_ref.lower() not in ["not provided", "n/a", "none", "", "generated from voice intake"]:
        score += 20
        checks.append({"item": "Prior Support Reference ID", "passed": True, "detail": f"Official reference logged: {ticket_ref}"})
    elif ticket_ref == "Generated from Voice Intake":
        score += 15
        checks.append({"item": "Prior Support Reference ID", "passed": True, "detail": "Voice reference logged; adding official ticket ID is recommended."})
    else:
        checks.append({"item": "Prior Support Reference ID", "passed": False, "detail": "No prior ticket or complaint reference number logged."})

    # 3. Chronological Narrative (20 pts)
    statement = str(case_data.get("user_statement", "")).strip()
    if len(statement) >= 80:
        score += 20
        checks.append({"item": "Detailed Statement of Facts", "passed": True, "detail": "Clear descriptive statement of the dispute sequence."})
    elif len(statement) > 0:
        score += 10
        checks.append({"item": "Detailed Statement of Facts", "passed": False, "detail": "Statement is brief; adding exact dates and events strengthens clarity."})
    else:
        checks.append({"item": "Detailed Statement of Facts", "passed": False, "detail": "No factual statement provided."})

    # 4. Documentary Proof & Evidence Attached (25 pts)
    evidence_items = case_data.get("evidence_items", [])
    valid_evidence = [e for e in evidence_items if e.get("verification_status") not in ["Awaiting User Upload", "Pending Attachment"]]
    if len(valid_evidence) >= 2:
        score += 25
        checks.append({"item": "Documentary Evidence Attached", "passed": True, "detail": f"{len(valid_evidence)} supporting proof items attached."})
    elif len(valid_evidence) == 1:
        score += 15
        checks.append({"item": "Documentary Evidence Attached", "passed": False, "detail": "Only 1 proof item attached; adding invoices or photos is recommended."})
    else:
        checks.append({"item": "Documentary Evidence Attached", "passed": False, "detail": "No proof files attached yet."})

    # 5. Clear Remedial Request (15 pts)
    relief = str(case_data.get("relief_sought", "")).strip()
    if relief:
        score += 15
        checks.append({"item": "Specific Remedy Stated", "passed": True, "detail": f"Remedy specified: {relief}"})
    else:
        checks.append({"item": "Specific Remedy Stated", "passed": False, "detail": "No specific relief or remedy selected."})

    # Categorize readiness level
    if score >= 80:
        status_label = "High Readiness (Comprehensive Dossier)"
        status_color = "#16a34a" # Green
    elif score >= 50:
        status_label = "Moderate Readiness (Missing Key Records)"
        status_color = "#d97706" # Amber
    else:
        status_label = "Low Readiness (Action Required)"
        status_color = "#dc2626" # Red

    return {
        "score": score,
        "label": status_label,
        "color": status_color,
        "checks": checks
    }


def format_for_nch_portal(case_data: dict) -> str:
    """
    Formats the grievance into a concise, structured text under 1000 characters,
    specifically optimized for copy-pasting into the National Consumer Helpline (INGRAM) portal.
    """
    text = (
        f"GRIEVANCE REGISTRATION (NCH INGRAM)\n"
        f"Company: {case_data.get('seller_name')}\n"
        f"Product: {case_data.get('product_name')}\n"
        f"Order/Ticket Ref: {case_data.get('support_ticket_ref', 'N/A')}\n"
        f"Amount Disputed: INR {case_data.get('purchase_amount', 0):,.2f}\n"
        f"Purchase Date: {case_data.get('purchase_date')}\n\n"
        f"SUMMARY OF DISPUTE:\n"
        f"{case_data.get('user_statement', '').strip()[:600]}\n\n"
        f"RELIEF SOUGHT: {case_data.get('relief_sought')}\n"
        f"EVIDENCE: Invoice and photographic proof available in personal dossier."
    )
    return text


def export_cases_json(cases_list: List[Dict[str, Any]]) -> str:
    """Exports cases to a clean, formatted JSON string for backup."""
    return json.dumps(cases_list, indent=2)


def generate_hindi_grievance_draft(case_data: dict) -> str:
    """Generates a polite, structured grievance letter in Hindi."""
    today_str = date.today().strftime("%d-%m-%Y")
    return f"""औपचारिक उपभोक्ता शिकायत एवं समाधान पत्र (Grievance Representation)
दिनांक: {today_str}
संदर्भ मामला संख्या (Case ID): {case_data.get('id', 'N/A')}

सेवा में,
शिकायत निवारण अधिकारी (Grievance Redressal Officer)
{case_data.get('seller_name', '[कंपनी का नाम]')}

विषय: {case_data.get('product_name', 'उत्पाद')} के संबंध में औपचारिक शिकायत (रिफंड/समाधान हेतु)

महोदय / महೋದಯ,

मैं यह शिकायत पत्र अपने द्वारा खरीदे गए उत्पाद के संबंध में समाधान एवं {case_data.get('relief_sought', 'उचित रिफंड')} प्राप्त करने हेतु प्रेषित कर रहा/रही हूँ।

1. खरीद एवं लेन-देन विवरण:
   - उत्पाद का नाम: {case_data.get('product_name')}
   - कुल भुगतान राशि: ₹ {case_data.get('purchase_amount', 0):,.2f}
   - खरीद की तिथि: {case_data.get('purchase_date')}
   - टिकट / आर्डर संख्या: {case_data.get('support_ticket_ref', 'N/A')}

2. समस्या का विवरण (उपभोक्ता द्वारा दिया गया विवरण):
\"\"\"
{case_data.get('user_statement', '').strip()}
\"\"\"

3. संलग्न साक्ष्य एवं दस्तावेज़:
   - टैक्स इनवॉइस / खरीद रसीद
   - उत्पाद क्षति के छायाचित्र (Photos)
   - पूर्व बातचीत का विवरण

4. विनम्र अनुरोध:
उपरोक्त तथ्यों के दृष्टिगत आपसे सविनय अनुरोध है कि मेरे मामले का 7 कार्य दिवसों के भीतर संज्ञान लेते हुए {case_data.get('relief_sought', 'रिफंड या समाधान')} की कृपा करें।

भवदीय,
जागरूक उपभोक्ता
"""


def generate_kannada_grievance_draft(case_data: dict) -> str:
    """Generates a polite, structured grievance letter in Kannada."""
    today_str = date.today().strftime("%d-%m-%Y")
    return f"""ಔಪಚಾರಿಕ ಗ್ರಾಹಕ ಕುಂದುಕೊರತೆ ಮತ್ತು ಪರಿಹಾರ ಕೋರಿಕೆ ಪತ್ರ
ದಿನಾಂಕ: {today_str}
ಪ್ರಕರಣ ಸಂಖ್ಯೆ (Case ID): {case_data.get('id', 'N/A')}

ರವರಿಗೆ,
ಕುಂದುಕೊರತೆ ಪರಿಹಾರ ಅಧಿಕಾರಿ (Grievance Redressal Officer)
{case_data.get('seller_name', '[ಸಂಸ್ಥೆಯ ಹೆಸರು]')}

ವಿಷಯ: {case_data.get('product_name', 'ಖರೀದಿಸಿದ ಉತ್ಪನ್ನ')} ಕುರಿತು ಔಪಚಾರಿಕ ಕುಂದುಕೊರತೆ ಅರ್ಜಿ (ಮರುಪಾವತಿ / ಪರಿಹಾರಕ್ಕಾಗಿ)

ಮಾನ್ಯರೇ,

ನಾನು ಖರೀದಿಸಿದ ಉತ್ಪನ್ನದಲ್ಲಿನ ದೋಷ ಮತ್ತು ಸೇವಾ ನ್ಯೂನತೆಯ ಕುರಿತು {case_data.get('relief_sought', 'ಪೂರ್ಣ ಮರುಪಾವತಿ')} ಪಡೆಯಲು ಈ ಅರ್ಜಿಯನ್ನು ಸಲ್ಲಿಸುತ್ತಿದ್ದೇನೆ.

1. ವಹಿವಾಟು ಮತ್ತು ಉತ್ಪನ್ನ ವಿವರಗಳು:
   - ಉತ್ಪನ್ನದ ಹೆಸರು: {case_data.get('product_name')}
   - ಪಾವತಿಸಿದ ಮೊತ್ತ: ₹ {case_data.get('purchase_amount', 0):,.2f}
   - ಖರೀದಿಸಿದ ದಿನಾಂಕ: {case_data.get('purchase_date')}
   - ಆರ್ಡರ್ / ಟಿಕೆಟ್ ಸಂಖ್ಯೆ: {case_data.get('support_ticket_ref', 'N/A')}

2. ಘಟನೆಯ ವಿವರ (ಗ್ರಾಹಕರು ನೀಡಿದ ಹೇಳಿಕೆ):
\"\"\"
{case_data.get('user_statement', '').strip()}
\"\"\"

3. ಲಗತ್ತಿಸಲಾದ ದಾಖಲೆಗಳು ಮತ್ತು ಪುರಾವೆಗಳು:
   - ಅಧಿಕೃತ ತೆರಿಗೆ ಸರಕುಪಟ್ಟಿ (Tax Invoice)
   - ಉತ್ಪನ್ನ ಹಾನಿಯ ಫೋಟೋಗಳು (Damage Photos)
   - ಗ್ರಾಹಕ ಸೇವಾ ಚಾಟ್ ದಾಖಲೆಗಳು

4. ಕೋರಿಕೆ:
ಮೇಲ್ಕಂಡ ವಾಸ್ತವಗಳನ್ನು ಪರಿಗಣಿಸಿ, 7 ವ್ಯವಹಾರ ದಿನಗಳೊಳಗೆ {case_data.get('relief_sought', 'ಪರಿಹಾರ')} ಒದಗಿಸಬೇಕಾಗಿ ವಿನಮ್ರವಾಗಿ ಕೋರುತ್ತೇನೆ.

ಇಂತಿ,
ಗ್ರಾಹಕರು
"""


def get_sample_demo_case() -> Dict[str, Any]:
    """
    Returns a realistic demonstration case involving a damaged laptop
    and a delayed refund. Uses strictly fictional details and non-personal data.
    """
    return {
        "id": "CASE-2026-001",
        "title": "AeroBook X14 Laptop - Damaged Screen & Unresolved Refund",
        "product_name": "AeroBook X14 (16GB RAM / 512GB SSD)",
        "product_category": "Electronics & Computers",
        "seller_name": "NovaCart Retail Logistics Pvt. Ltd.",
        "purchase_amount": 58499.00,
        "purchase_date": "2026-10-24",
        "incident_date": "2026-10-26",
        "problem_category": "Damaged on Delivery & Delayed Refund",
        "status": "Evidence Documented",
        "relief_sought": "Full Refund of ₹58,499 to original payment method",
        "created_at": "2026-10-27 11:30:00",
        
        "user_statement": (
            "I ordered an AeroBook X14 laptop during the festive sale. The parcel was "
            "delivered on October 26, 2026. Upon opening the outer carton, I noticed the "
            "inner product seal was already torn and the laptop display hinge was cracked, "
            "with visible internal screen bleeding when powered on.\n\n"
            "I contacted NovaCart customer support within 2 hours of delivery and raised "
            "Return Ticket #RET-884129. The support executive confirmed that a reverse pickup "
            "and full refund would be completed within 7 business days. A courier picked up the "
            "damaged unit on October 28, 2026.\n\n"
            "As of today, more than 10 business days have passed since the return was confirmed. "
            "Customer care representatives now state the refund is 'under review by the logistics hub' "
            "with no resolution date or supervisor escalation provided."
        ),
        
        "timeline": [
            {
                "date": "2026-10-24",
                "event": "Order Placed & Paid",
                "source": "Verified Invoice",
                "details": "Order #NC-89104 paid online via UPI for ₹58,499."
            },
            {
                "date": "2026-10-26",
                "event": "Package Delivered Damaged",
                "source": "User Statement + Photos",
                "details": "Delivery received at 14:15. Box crushed at corner; display hinge cracked."
            },
            {
                "date": "2026-10-26",
                "event": "Return Request Registered",
                "source": "Support Ticket Confirmation",
                "details": "Ticket #RET-884129 opened. Seller promised resolution within 7 days."
            },
            {
                "date": "2026-10-28",
                "event": "Reverse Pickup Completed",
                "source": "Courier Receipt Slip",
                "details": "Courier tracking #AeroShip-4491 indicates item was collected."
            },
            {
                "date": "2026-11-04",
                "event": "7-Day Refund SLA Breached",
                "source": "User Statement",
                "details": "No refund initiated. Customer care gave automated delay replies."
            }
        ],
        
        "evidence_items": [
            {
                "file_name": "Tax_Invoice_NC89104.pdf",
                "file_type": "Tax Invoice / Purchase Receipt",
                "verification_status": "Document Attached",
                "description": "Official retail tax invoice displaying order number, seller GSTIN, and ₹58,499 paid amount."
            },
            {
                "file_name": "Packaging_Damage_Box_Corner.jpg",
                "file_type": "Photographic Proof",
                "verification_status": "Visual Artifact Attached",
                "description": "Clear photograph of crushed transit carton and torn security seal taken upon unboxing."
            },
            {
                "file_name": "Hinge_Crack_And_ScreenBleed.jpg",
                "file_type": "Photographic Proof",
                "verification_status": "Visual Artifact Attached",
                "description": "High-resolution photo showing physical crack on left hinge and screen defect upon power-on."
            },
            {
                "file_name": "Reverse_Pickup_Receipt_AeroShip.pdf",
                "file_type": "Logistics Handover Slip",
                "verification_status": "Document Attached",
                "description": "Physical receipt signed by pickup executive acknowledging collection of the item on Oct 28."
            },
            {
                "file_name": "Customer_Support_Email_Thread.pdf",
                "file_type": "Written Communication",
                "verification_status": "Transcript Attached",
                "description": "Email thread with support@novacart.example acknowledging receipt and promising 7-day refund."
            }
        ],
        
        "support_ticket_ref": "Ticket #RET-884129",
        "seller_email": "grievance-officer@novacart.example",
        "consumer_notes": "All communications have been politely documented. Ready for official grievance notice."
    }


def initialize_cases() -> List[Dict[str, Any]]:
    """Initializes the default case list containing the sample demo case."""
    return [get_sample_demo_case()]
