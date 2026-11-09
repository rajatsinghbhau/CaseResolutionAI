"""
CaseResolutionAI - Grievance Letter & Notice Generation Service
Generates 4 distinct formal representations in English, Hindi, and Kannada:
1. Seller Customer Support Email
2. Formal Legal Grievance Representation Notice
3. Executive Grievance Officer Escalation Letter
4. National Consumer Helpline (NCH / Commission) Draft
"""

from datetime import date
from typing import Dict, Any


def get_evidence_text(case_data: Dict[str, Any]) -> str:
    """Formats evidence items into a readable bulleted list."""
    items = case_data.get("evidence_items", [])
    valid_items = [e for e in items if e.get("verification_status") not in ["Awaiting User Upload", "Pending Attachment"]]
    if not valid_items:
        return "   (No documentary attachments registered yet)"
    lines = []
    for idx, e in enumerate(valid_items):
        lines.append(f"   [{idx+1}] {e.get('file_type', 'Document')}: {e.get('file_name', 'File')} — {e.get('description', 'Attached artifact')}")
    return "\n".join(lines)


def get_timeline_text(case_data: Dict[str, Any]) -> str:
    """Formats chronology events into a readable text list."""
    events = case_data.get("timeline", [])
    if not events:
        return f"   - {case_data.get('purchase_date', 'Order Date')}: Order placed and transaction completed."
    lines = []
    for ev in events:
        lines.append(f"   - {ev.get('date', '')}: {ev.get('event', '')} ({ev.get('details', '')}) [Source: {ev.get('source', 'Record')}]")
    return "\n".join(lines)


# =========================================================
# 1. SELLER CUSTOMER SUPPORT COMPLAINT EMAIL
# =========================================================
def generate_seller_email(case_data: Dict[str, Any], language: str = "English") -> str:
    today_str = date.today().strftime("%d %B %Y")
    
    if language == "Hindi (हिन्दी)":
        return f"""ईमेल विषय: तत्काल शिकायत: {case_data.get('product_name')} (आर्डर सं: {case_data.get('support_ticket_ref', 'रिफ़र संलग्न')}) के संबंध में

महोदय / महोदया,

मैं यह ईमेल अपने आर्डर {case_data.get('support_ticket_ref', 'N/A')} के संबंध में भेज रहा/रही हूँ।
मैंने दिनांक {case_data.get('purchase_date')} को ₹ {case_data.get('purchase_amount', 0):,.2f} का भुगतान करके {case_data.get('product_name')} खरीदा था।

डिलीवरी के बाद निम्नलिखित समस्या उत्पन्न हुई:
{case_data.get('user_statement', '').strip()}

कंपनी द्वारा दिया गया आश्वासन: {case_data.get('seller_promises', 'मानक समाधान समय-सीमा')}
वर्तमान स्थिति: {case_data.get('refund_status', 'लंबित / अनिर्णीत')}

मैं आपसे अनुरोध करता/करती हूँ कि कृपया इस मामले का तत्काल संज्ञान लें और मुझे {case_data.get('relief_sought', 'उचित रिफंड')} प्रदान करें।

संलग्न दस्तावेज़: खरीद इनवॉइस एवं क्षति के छायाचित्र।

भवदीय,
{case_data.get('customer_name', 'जागरूक उपभोक्ता')}
"""
    elif language == "Kannada (ಕನ್ನಡ)":
        return f"""ಇಮೇಲ್ ವಿಷಯ: ತುರ್ತು ದೂರು: {case_data.get('product_name')} (ಆರ್ಡರ್ ಸಂಖ್ಯೆ: {case_data.get('support_ticket_ref', 'N/A')}) ಮರುಪಾವತಿ ಕುರಿತು

ಮಾನ್ಯರೇ,

ದಿನಾಂಕ {case_data.get('purchase_date')} ರಂದು ನಾನು ₹ {case_data.get('purchase_amount', 0):,.2f} ಪಾವತಿಸಿ ಖರೀದಿಸಿದ {case_data.get('product_name')} ಉತ್ಪನ್ನದಲ್ಲಿ ಗಂಭೀರ ದೋಷ ಕಂಡುಬಂದಿದೆ.

ಸಮಸ್ಯೆಯ ವಿವರ:
{case_data.get('user_statement', '').strip()}

ಗ್ರಾಹಕ ಸೇವಾ ಕೇಂದ್ರದ ಭರವಸೆ: {case_data.get('seller_promises', 'ಪರಿಹಾರ ನೀಡುವುದಾಗಿ ತಿಳಿಸಿದ್ದರು')}
ಪ್ರಸ್ತುತ ಸ್ಥಿತಿ: {case_data.get('refund_status', 'ವಿಳಂಬವಾಗಿದೆ')}

ದಯವಿಟ್ಟು ನನಗೆ {case_data.get('relief_sought', 'ಪೂರ್ಣ ಮರುಪಾವತಿ')} ಒದಗಿಸಬೇಕಾಗಿ ವಿನಂತಿಸುತ್ತೇನೆ.

ಇಂತಿ,
{case_data.get('customer_name', 'ಗ್ರಾಹಕರು')}
"""
    else: # English
        return f"""Subject: URGENT RESOLUTION REQUEST: Order Ref {case_data.get('support_ticket_ref', 'N/A')} — {case_data.get('product_name')}

Date: {today_str}
To: Customer Support Team, {case_data.get('seller_name', 'Seller')}

Dear Customer Support Team,

I am writing regarding my purchase of {case_data.get('product_name')} for INR {case_data.get('purchase_amount', 0):,.2f} on {case_data.get('purchase_date')}.

Order / Ticket Reference: {case_data.get('support_ticket_ref', 'N/A')}

ISSUE SUMMARY:
{case_data.get('user_statement', '').strip()}

CUSTOMER CARE COMMITMENT:
{case_data.get('seller_promises', 'Resolution promised within standard timeframe.')}

CURRENT STATUS:
{case_data.get('refund_status', 'Resolution/Refund pending past turnaround time.')}

REQUESTED ACTION:
I respectfully request an immediate {case_data.get('relief_sought', 'full refund to the original payment method')}.
Supporting evidence (tax invoice and photographs) is attached to this email.

Please confirm receipt and provide the escalated ticket number within 48 hours.

Sincerely,
{case_data.get('customer_name', 'A Concerned Consumer')}
"""


# =========================================================
# 2. FORMAL LEGAL GRIEVANCE NOTICE
# =========================================================
def generate_formal_legal_notice(case_data: Dict[str, Any], language: str = "English") -> str:
    today_str = date.today().strftime("%d %B %Y")
    timeline_str = get_timeline_text(case_data)
    evidence_str = get_evidence_text(case_data)
    
    return f"""FORMAL GRIEVANCE & DEMAND FOR RESOLUTION
(Notice of Consumer Grievance under Fair Trade Guidelines)

Date: {today_str}
Case Dossier Reference: {case_data.get('id', 'N/A')}

TO:
The Customer Grievance Cell / Legal Affairs Division
{case_data.get('seller_name', '[Company Name]')}
Email / Contact: {case_data.get('seller_email', 'Official Grievance Channel')}

SUBJECT: Formal Notice regarding deficiency of service / defective delivery of {case_data.get('product_name')} (Ref: {case_data.get('support_ticket_ref', 'Attached')})

Dear Sir / Madam,

PLEASE TAKE NOTICE that the undersigned consumer ({case_data.get('customer_name', 'Consumer')}) hereby serves this formal representation regarding an unfulfilled transaction:

1. PARTICULARS OF THE TRANSACTION:
   - Product / Service: {case_data.get('product_name')} ({case_data.get('product_category', 'Consumer Goods')})
   - Transaction Value: INR {case_data.get('purchase_amount', 0):,.2f} (Paid in Full)
   - Purchase Date: {case_data.get('purchase_date')}
   - Delivery / Discovery Date: {case_data.get('delivery_date', case_data.get('incident_date'))}
   - Reference / Ticket ID: {case_data.get('support_ticket_ref', 'N/A')}

2. CHRONOLOGY OF FACTS:
{timeline_str}

3. STATEMENT OF GRIEVANCE (CONSUMER FACTUAL STATEMENT):
\"\"\"
{case_data.get('user_statement', '').strip()}
\"\"\"

4. EVIDENTIARY ARTIFACTS ATTACHED IN SUPPORT:
{evidence_str}

5. REMEDY SOUGHT & 7-DAY CURE PERIOD:
In light of the documented delay and failure to honor the resolution timeline:
- The consumer requires: {case_data.get('relief_sought', 'Immediate full refund')}.
- You are requested to communicate written compliance within 7 business days from receipt of this notice.

Failing a satisfactory resolution within 7 days, the consumer reserves the right to escalate this documented dossier to the National Consumer Helpline (NCH 1915 / INGRAM) and seek redressal before the Competent Consumer Disputes Redressal Commission under the Consumer Protection Act, 2019.

Yours faithfully,
{case_data.get('customer_name', 'The Undersigned Consumer')}
"""


# =========================================================
# 3. EXECUTIVE / NODAL GRIEVANCE OFFICER ESCALATION LETTER
# =========================================================
def generate_nodal_escalation_letter(case_data: Dict[str, Any], language: str = "English") -> str:
    today_str = date.today().strftime("%d %B %Y")
    evidence_str = get_evidence_text(case_data)
    
    return f"""ESCALATION TO NODAL GRIEVANCE REDRESSAL OFFICER
(Under Rule 4 of the Consumer Protection (E-Commerce) Rules, 2020)

Date: {today_str}
Case Reference: {case_data.get('id', 'N/A')}

To,
The Nodal Grievance Officer
{case_data.get('seller_name', '[Company Name]')}
Official Grievance Email: {case_data.get('seller_email', 'grievance-officer@company.example')}

Subject: Level-2 Escalation regarding unresolved dispute for Order Ref {case_data.get('support_ticket_ref', 'N/A')}

Dear Grievance Officer,

I am compelled to escalate this dispute to your office due to the failure of frontline customer service to resolve my complaint within reasonable SLA turnaround limits.

1. BASIC TRANSACTION DETAILS:
   - Consumer: {case_data.get('customer_name', 'Consumer')}
   - Product: {case_data.get('product_name')}
   - Total Amount: INR {case_data.get('purchase_amount', 0):,.2f}
   - Purchase Date: {case_data.get('purchase_date')}
   - Customer Service Ticket: {case_data.get('support_ticket_ref', 'N/A')}

2. NATURE OF BREACH & SERVICE DEFICIENCY:
   The customer support division promised: \"{case_data.get('seller_promises', 'Refund within promised window')}\".
   However, as of today, the status remains \"{case_data.get('refund_status', 'Unresolved')}\".
   
   Consumer's statement:
   {case_data.get('user_statement', '').strip()}

3. DOCUMENTARY PROOF ON RECORD:
{evidence_str}

4. RELIEF REQUESTED:
Under statutory e-commerce guidelines, entities are obligated to acknowledge grievances within 48 hours and redress them within one month. I request your prompt intervention to process:
- {case_data.get('relief_sought', 'Full refund of purchase consideration')}.

Kindly issue a formal grievance registration number and updated resolution date.

Yours sincerely,
{case_data.get('customer_name', 'Aggrieved Consumer')}
"""


# =========================================================
# 4. NATIONAL CONSUMER HELPLINE (NCH 1915) COMPLAINT DRAFT
# =========================================================
def generate_nch_complaint_draft(case_data: Dict[str, Any], language: str = "English") -> str:
    today_str = date.today().strftime("%d-%m-%Y")
    
    return f"""NATIONAL CONSUMER HELPLINE (NCH / INGRAM) MEDIATION DRAFT
Portal: consumerhelpline.gov.in | Helpline: 1915

[1] RESPONDENT COMPANY PARTICULARS:
Company Name: {case_data.get('seller_name')}
Company Email / Website: {case_data.get('seller_email', 'N/A')}

[2] COMPLAINT PARTICULARS:
Product / Service Name: {case_data.get('product_name')}
Product Category: {case_data.get('product_category')}
Transaction Date: {case_data.get('purchase_date')}
Disputed Amount: INR {case_data.get('purchase_amount', 0):,.2f}
Order / Transaction Reference: {case_data.get('support_ticket_ref', 'N/A')}

[3] GRIEVANCE DETAILS (Factual Summary):
{case_data.get('user_statement', '').strip()}

[4] COMPANY'S RESPONSE / FAILED COMMITMENT:
Seller promised: {case_data.get('seller_promises', 'Standard resolution')}
Current Situation: {case_data.get('refund_status', 'Delayed / Refused')}

[5] RELIEF CLAIMED:
{case_data.get('relief_sought', 'Full refund')}

[6] DECLARATION:
The information provided represents the consumer's factual account. Supporting invoices and evidence are archived in CaseResolutionAI Dossier Ref {case_data.get('id')}.
"""

