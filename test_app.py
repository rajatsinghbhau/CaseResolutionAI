"""
Comprehensive test suite for CaseResolutionAI
Testing DB persistence, PDF Dossier generation, 4 Grievance Formats,
and Gnani AI Multilingual Voice Extraction.
"""

import unittest
import os
from case_store import (
    initialize_cases, 
    get_sample_demo_case, 
    calculate_readiness_score,
    generate_hindi_grievance_draft,
    generate_kannada_grievance_draft
)
from app import generate_formal_grievance_draft, generate_printable_html_dossier, find_case_by_id
import gnani_service
import db_service
import letter_service
import dossier_pdf_service


class TestCaseResolutionAI(unittest.TestCase):
    def setUp(self):
        self.cases = initialize_cases()
        db_service.init_db()

    # -----------------------------------------------------
    # Core Application & Sample Case Tests
    # -----------------------------------------------------
    def test_sample_case_structure(self):
        sample = get_sample_demo_case()
        self.assertEqual(sample["id"], "CASE-2026-001")
        self.assertIn("AeroBook", sample["product_name"])
        self.assertIn("NovaCart", sample["seller_name"])
        self.assertEqual(sample["purchase_amount"], 58499.00)
        self.assertTrue(len(sample["timeline"]) >= 4)
        self.assertTrue(len(sample["evidence_items"]) >= 3)
        self.assertIn("user_statement", sample)
        self.assertIn("relief_sought", sample)

    def test_find_case_by_id(self):
        found = find_case_by_id("CASE-2026-001", self.cases)
        self.assertIsNotNone(found)
        self.assertEqual(found["id"], "CASE-2026-001")

        fallback = find_case_by_id("NONEXISTENT_ID", self.cases)
        self.assertIsNotNone(fallback)
        self.assertEqual(fallback["id"], "CASE-2026-001")

    def test_readiness_scoring(self):
        sample = get_sample_demo_case()
        readiness = calculate_readiness_score(sample)
        self.assertGreaterEqual(readiness["score"], 80)
        self.assertIn("Comprehensive Dossier", readiness["label"])
        self.assertEqual(len(readiness["checks"]), 5)

    def test_grievance_letter_generation(self):
        sample = get_sample_demo_case()
        letter = generate_formal_grievance_draft(sample)
        self.assertIn("FORMAL GRIEVANCE", letter)
        self.assertIn("NovaCart Retail Logistics Pvt. Ltd.", letter)
        self.assertIn("INR 58,499.00", letter)
        self.assertIn("Tax_Invoice_NC89104.pdf", letter)
        self.assertIn("Ticket #RET-884129", letter)
        self.assertNotIn("guaranteed refund", letter.lower())

    def test_multilingual_grievance_drafts(self):
        sample = get_sample_demo_case()
        hindi_letter = generate_hindi_grievance_draft(sample)
        self.assertIn("औपचारिक उपभोक्ता शिकायत एवं समाधान पत्र", hindi_letter)
        self.assertIn("NovaCart", hindi_letter)
        self.assertIn("58,499.00", hindi_letter)

        kannada_letter = generate_kannada_grievance_draft(sample)
        self.assertIn("ಔಪಚಾರಿಕ ಗ್ರಾಹಕ ಕುಂದುಕೊರತೆ", kannada_letter)
        self.assertIn("NovaCart", kannada_letter)
        self.assertIn("58,499.00", kannada_letter)

    def test_printable_html_dossier(self):
        sample = get_sample_demo_case()
        html = generate_printable_html_dossier(sample)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("CASE-2026-001", html)
        self.assertIn("AeroBook X14", html)
        self.assertIn("window.print()", html)

    # -----------------------------------------------------
    # PDF Dossier Generation Tests
    # -----------------------------------------------------
    def test_pdf_dossier_generation(self):
        sample = get_sample_demo_case()
        pdf_bytes = dossier_pdf_service.generate_case_dossier_pdf(sample)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 1000)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    # -----------------------------------------------------
    # 4 Distinct Grievance Formats Tests
    # -----------------------------------------------------
    def test_four_grievance_formats(self):
        sample = get_sample_demo_case()
        
        # 1. Email format
        email = letter_service.generate_seller_email(sample, "English")
        self.assertIn("Subject: URGENT RESOLUTION REQUEST", email)
        self.assertIn("NovaCart", email)
        
        # 2. Formal legal notice
        legal = letter_service.generate_formal_legal_notice(sample, "English")
        self.assertIn("FORMAL GRIEVANCE & DEMAND FOR RESOLUTION", legal)
        self.assertIn("7-DAY CURE PERIOD", legal)
        
        # 3. Nodal escalation letter
        nodal = letter_service.generate_nodal_escalation_letter(sample, "English")
        self.assertIn("ESCALATION TO NODAL GRIEVANCE REDRESSAL OFFICER", nodal)
        self.assertIn("Rule 4 of the Consumer Protection", nodal)
        
        # 4. NCH portal mediation draft
        nch = letter_service.generate_nch_complaint_draft(sample, "English")
        self.assertIn("NATIONAL CONSUMER HELPLINE (NCH / INGRAM) MEDIATION DRAFT", nch)
        self.assertIn("consumerhelpline.gov.in", nch)

    # -----------------------------------------------------
    # Database Persistence & Isolation Tests
    # -----------------------------------------------------
    def test_database_user_and_case_lifecycle(self):
        import uuid
        test_uname = f"user_{uuid.uuid4().hex[:6]}"
        test_email = f"{test_uname}@example.com"
        
        # Register
        reg = db_service.register_user(test_uname, test_email, "securepwd123", "Unit Test User")
        self.assertTrue(reg["success"])
        user_id = reg["user"]["id"]
        
        # Authenticate
        auth = db_service.authenticate_user(test_uname, "securepwd123")
        self.assertTrue(auth["success"])
        self.assertEqual(auth["user"]["id"], user_id)
        
        # Save Case
        test_case = {
            "id": f"CASE-UNIT-{uuid.uuid4().hex[:4]}",
            "title": "Unit Test Laptop Issue",
            "customer_name": "Unit Test User",
            "product_name": "Test Laptop",
            "product_category": "Electronics & Computers",
            "seller_name": "Test Retail",
            "purchase_amount": 45000.0,
            "purchase_date": "2026-10-01",
            "delivery_date": "2026-10-03",
            "problem_category": "Damaged on Delivery",
            "status": "Active",
            "relief_sought": "Full Refund",
            "user_statement": "Screen cracked upon unboxing.",
            "timeline": [{"date": "2026-10-01", "event": "Ordered", "details": "Paid online"}],
            "evidence_items": [{"file_name": "photo.jpg", "file_type": "Photo", "verification_status": "Attached"}]
        }
        saved = db_service.save_case_to_db(test_case, user_id)
        self.assertTrue(saved)
        
        # Retrieve Cases
        user_cases = db_service.get_user_cases_from_db(user_id)
        self.assertEqual(len(user_cases), 1)
        self.assertEqual(user_cases[0]["id"], test_case["id"])
        
        # Isolation: another user should not see this case
        other_cases = db_service.get_user_cases_from_db("different-random-user-id")
        self.assertEqual(len(other_cases), 0)
        
        # Delete Case
        deleted = db_service.delete_case_from_db(test_case["id"], user_id)
        self.assertTrue(deleted)
        self.assertEqual(len(db_service.get_user_cases_from_db(user_id)), 0)

    # -----------------------------------------------------
    # Gnani AI Voice Intake & Information Extraction Tests
    # -----------------------------------------------------
    def test_gnani_unconfigured_error_message(self):
        original = os.environ.get("GNANI_API_KEY")
        try:
            os.environ["GNANI_API_KEY"] = ""
            res = gnani_service.transcribe_audio_gnani(b"dummy_audio_bytes" * 20, language_code="en-IN")
            self.assertFalse(res["success"])
            self.assertIn("error", res)
            self.assertIn("GNANI_API_KEY", res["error"])
        finally:
            if original is not None:
                os.environ["GNANI_API_KEY"] = original

    def test_gnani_supported_languages(self):
        langs = gnani_service.SUPPORTED_LANGUAGES
        self.assertIn("English (Indian)", langs)
        self.assertIn("Hindi (हिन्दी)", langs)
        self.assertIn("Kannada (ಕನ್ನಡ)", langs)
        self.assertEqual(langs["English (Indian)"]["code"], "en-IN")
        self.assertEqual(langs["Hindi (हिन्दी)"]["code"], "hi-IN")
        self.assertEqual(langs["Kannada (ಕನ್ನಡ)"]["code"], "kn-IN")

    def test_extract_complaint_fields_complete(self):
        spoken_transcript = (
            "I ordered an AeroBook laptop from NovaCart under order #NC-89104 on 24th October for 58499 rupees. "
            "It was delivered on 26th October with broken hinge and screen crack. "
            "Customer care promised refund within 7 days, but no refund has been received."
        )
        extracted = gnani_service.extract_complaint_fields(spoken_transcript, language_code="en-IN")
        
        self.assertEqual(extracted["product_name"], "Aerobook Laptop")
        self.assertEqual(extracted["seller_name"], "Novacart")
        self.assertEqual(extracted["purchase_amount"], 58499.0)
        self.assertEqual(extracted["order_id"], "NC-89104")
        self.assertIn("24Th October", extracted["purchase_date"])
        self.assertIn("26Th October", extracted["delivery_date"])
        self.assertIsNotNone(extracted["problem_description"])
        self.assertIsNotNone(extracted["seller_promises"])
        self.assertEqual(extracted["refund_resolution_status"], "Refund Delayed / Pending (Not Received)")
        self.assertEqual(len(extracted["missing_fields"]), 0)
        self.assertEqual(len(extracted["follow_up_questions"]), 0)

    def test_extract_complaint_fields_missing_triggers_followup_questions(self):
        sparse_transcript = "My package arrived damaged with a cracked screen."
        extracted = gnani_service.extract_complaint_fields(sparse_transcript, language_code="en-IN")
        
        self.assertIn("purchase_amount", extracted["missing_fields"])
        self.assertIn("seller_name", extracted["missing_fields"])
        self.assertTrue(len(extracted["follow_up_questions"]) > 0)
        
        follow_ups = " ".join(extracted["follow_up_questions"])
        self.assertIn("purchase price", follow_ups)
        self.assertIn("seller", follow_ups)


if __name__ == "__main__":
    unittest.main()
