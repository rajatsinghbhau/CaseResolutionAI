"""
CaseResolutionAI — Complete AI-Powered Consumer Complaint Resolution Platform
Tagline: An AI that fights the case you don't have time to fight.
Built for the Great Indian AI Internship Challenge by Gnani AI.
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime
import io
import os
import json

# Local Domain Services
from case_store import (
    initialize_cases, 
    get_sample_demo_case, 
    calculate_readiness_score,
    SAMPLE_SPOKEN_SCENARIOS,
    ESCALATION_STAGES,
    format_for_nch_portal,
    export_cases_json,
    generate_hindi_grievance_draft,
    generate_kannada_grievance_draft
)
import gnani_service
import db_service
import letter_service
import dossier_pdf_service


# ---------------------------------------------------------
# Helper Functions for Case Management & Authentication
# ---------------------------------------------------------
def get_current_user_cases() -> list:
    """Retrieves cases for the current user or guest session."""
    user = st.session_state.get("current_user")
    if user:
        db_cases = db_service.get_user_cases_from_db(user["id"])
        if not db_cases and "demo_seeded" not in st.session_state:
            # Seed demo case for new users so they can immediately explore
            demo = get_sample_demo_case()
            db_service.save_case_to_db(demo, user["id"])
            st.session_state.demo_seeded = True
            db_cases = db_service.get_user_cases_from_db(user["id"])
        return db_cases
    else:
        if "guest_cases" not in st.session_state:
            st.session_state.guest_cases = initialize_cases()
        return st.session_state.guest_cases


def save_case(case_dict: dict):
    """Saves a case to the database if logged in, or to session state if guest."""
    user = st.session_state.get("current_user")
    if user:
        db_service.save_case_to_db(case_dict, user["id"])
    else:
        if "guest_cases" not in st.session_state:
            st.session_state.guest_cases = initialize_cases()
        # Update or append
        found = False
        for idx, c in enumerate(st.session_state.guest_cases):
            if c["id"] == case_dict["id"]:
                st.session_state.guest_cases[idx] = case_dict
                found = True
                break
        if not found:
            st.session_state.guest_cases.append(case_dict)


def delete_case(case_id: str):
    """Deletes a case from database or guest session."""
    user = st.session_state.get("current_user")
    if user:
        db_service.delete_case_from_db(case_id, user["id"])
    else:
        if "guest_cases" in st.session_state:
            st.session_state.guest_cases = [c for c in st.session_state.guest_cases if c["id"] != case_id]


def find_case_by_id(case_id: str, cases_list: list = None):
    """Retrieves a case by ID."""
    items = cases_list if cases_list is not None else get_current_user_cases()
    for c in items:
        if c["id"] == case_id:
            return c
    return items[0] if items else None


def generate_formal_grievance_draft(case_data: dict) -> str:
    """Wrapper for backward compatibility."""
    return letter_service.generate_formal_legal_notice(case_data, language="English")


def generate_printable_html_dossier(case_data: dict) -> str:
    """Generates a clean, professional, print-ready HTML case dossier."""
    today_str = date.today().strftime("%d %B %Y")
    readiness = calculate_readiness_score(case_data)
    
    timeline_html = "".join([
        f"<tr><td><strong>{t['date']}</strong></td><td>{t['event']}</td><td><span style='color:#666;'>{t.get('source', '')}</span></td><td>{t['details']}</td></tr>"
        for t in case_data.get("timeline", [])
    ])
    
    evidence_html = "".join([
        f"<li><strong>{item['file_name']}</strong> ({item['file_type']}) - <em>{item.get('verification_status', 'Attached')}</em><br/><small>{item.get('description', '')}</small></li>"
        for item in case_data.get("evidence_items", [])
    ])

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Consumer Dispute Dossier - {case_data.get('id')}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; color: #1e293b; max-width: 820px; margin: 40px auto; padding: 0 20px; }}
        h1 {{ color: #1e3a8a; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; margin-bottom: 4px; }}
        .header-meta {{ font-size: 0.9em; color: #64748b; margin-bottom: 20px; }}
        .disclaimer-box {{ background: #fefce8; border-left: 4px solid #eab308; padding: 12px; margin-bottom: 20px; font-size: 0.85em; color: #713f12; }}
        .section-title {{ font-size: 1.15em; font-weight: 700; color: #0f172a; margin-top: 25px; margin-bottom: 8px; border-bottom: 1px solid #cbd5e1; padding-bottom: 4px; }}
        .card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 14px; margin-bottom: 15px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
        th, td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid #e2e8f0; font-size: 0.9em; }}
        th {{ background: #f1f5f9; }}
        .badge-statement {{ background: #fef3c7; color: #92400e; padding: 3px 8px; border-radius: 4px; font-size: 0.8em; font-weight: 600; }}
        .badge-evidence {{ background: #dcfce7; color: #166534; padding: 3px 8px; border-radius: 4px; font-size: 0.8em; font-weight: 600; }}
        @media print {{ body {{ margin: 0; padding: 15mm; }} .no-print {{ display: none; }} }}
    </style>
</head>
<body>
    <div class="no-print" style="margin-bottom: 20px;">
        <button onclick="window.print()" style="background:#2563eb; color:white; border:none; padding:10px 18px; border-radius:6px; cursor:pointer; font-weight:600;">🖨️ Print or Save as PDF</button>
    </div>
    <h1>CaseResolutionAI — Consumer Dispute Dossier</h1>
    <div class="header-meta">Case ID: <strong>{case_data.get('id')}</strong> | Generated on: {today_str} | Dossier Readiness: {readiness['score']}/100</div>

    <div class="disclaimer-box">
        <strong>Notice:</strong> This dossier is a structured compilation of consumer records and factual statements. It is prepared for personal organization and formal communication with company grievance officers or the National Consumer Helpline. It does not constitute formal legal counsel.
    </div>

    <div class="section-title">1. Transaction Overview</div>
    <div class="card">
        <p><strong>Consumer Name:</strong> {case_data.get('customer_name', 'Consumer')}</p>
        <p><strong>Product / Service:</strong> {case_data.get('product_name')} ({case_data.get('product_category')})</p>
        <p><strong>Seller / Company:</strong> {case_data.get('seller_name')}</p>
        <p><strong>Amount Paid:</strong> INR {case_data.get('purchase_amount', 0):,.2f} | <strong>Purchase Date:</strong> {case_data.get('purchase_date')}</p>
        <p><strong>Order / Support Reference:</strong> {case_data.get('support_ticket_ref', 'N/A')}</p>
        <p><strong>Remedy Requested:</strong> {case_data.get('relief_sought')}</p>
    </div>

    <div class="section-title">2. Consumer Narrative <span class="badge-statement">User Statement</span></div>
    <div class="card" style="font-style: italic;">
        {case_data.get('user_statement', '').replace(chr(10), '<br/>')}
    </div>

    <div class="section-title">3. Chronology of Events</div>
    <table>
        <thead>
            <tr><th>Date</th><th>Event</th><th>Record Source</th><th>Details</th></tr>
        </thead>
        <tbody>
            {timeline_html}
        </tbody>
    </table>

    <div class="section-title">4. Documented Evidence & Proof <span class="badge-evidence">Attached Artifacts</span></div>
    <ul>
        {evidence_html}
    </ul>
</body>
</html>
"""
    return html


# ---------------------------------------------------------
# Main UI Application
# ---------------------------------------------------------
def main():
    db_service.init_db()

    st.set_page_config(
        page_title="CaseResolutionAI — AI Consumer Grievance Platform",
        page_icon="⚖️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS Styling — Legal-Tech Professional Aesthetic
    st.markdown("""
    <style>
        .main .block-container {
            padding-top: 1.8rem;
            padding-bottom: 3.5rem;
            max-width: 1200px;
        }
        
        /* Hero Banner */
        .hero-banner {
            background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 60%, #2563eb 100%);
            color: #ffffff;
            padding: 2.5rem 2.8rem;
            border-radius: 16px;
            margin-bottom: 2rem;
            box-shadow: 0 10px 25px -5px rgba(30, 58, 138, 0.25);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .hero-badge {
            display: inline-block;
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(8px);
            color: #93c5fd;
            font-size: 0.8rem;
            font-weight: 700;
            padding: 0.35rem 0.8rem;
            border-radius: 9999px;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            margin-bottom: 1rem;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .hero-title {
            font-size: 2.5rem;
            font-weight: 800;
            line-height: 1.2;
            margin-bottom: 0.8rem;
            color: #ffffff;
        }
        .hero-sub {
            font-size: 1.15rem;
            color: #cbd5e1;
            line-height: 1.6;
            max-width: 820px;
        }
        
        /* Stats Strip */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
            margin-bottom: 2rem;
        }
        .stat-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1.2rem;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        .stat-num {
            font-size: 1.6rem;
            font-weight: 800;
            color: #1e3a8a;
            margin-bottom: 0.2rem;
        }
        .stat-label {
            font-size: 0.82rem;
            color: #64748b;
            font-weight: 600;
        }

        /* Disclaimer Cards */
        .disclaimer-card {
            background-color: #fefce8;
            border-left: 5px solid #eab308;
            padding: 1.1rem 1.4rem;
            border-radius: 8px;
            margin-bottom: 1.6rem;
            color: #713f12;
            font-size: 0.92rem;
            line-height: 1.5;
        }

        /* Badges */
        .tag-statement {
            display: inline-block;
            background-color: #fef3c7;
            color: #92400e;
            border: 1px solid #fde68a;
            padding: 0.25rem 0.65rem;
            border-radius: 9999px;
            font-weight: 600;
            font-size: 0.78rem;
            text-transform: uppercase;
        }
        .tag-evidence {
            display: inline-block;
            background-color: #dcfce7;
            color: #166534;
            border: 1px solid #bbf7d0;
            padding: 0.25rem 0.65rem;
            border-radius: 9999px;
            font-weight: 600;
            font-size: 0.78rem;
            text-transform: uppercase;
        }

        /* Timeline and Stage */
        .timeline-item {
            border-left: 3px solid #3b82f6;
            padding-left: 1.2rem;
            margin-bottom: 1.1rem;
            position: relative;
        }
        .stage-pill {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 700;
        }
        .stage-active { background: #dbeafe; color: #1d4ed8; border: 1px solid #93c5fd; }
        .stage-done { background: #dcfce7; color: #15803d; border: 1px solid #86efac; }
        .stage-pending { background: #f1f5f9; color: #64748b; border: 1px solid #cbd5e1; }
    </style>
    """, unsafe_allow_html=True)

    # Initialize Session State
    if "current_user" not in st.session_state:
        st.session_state.current_user = None

    cases = get_current_user_cases()
    if "active_case_id" not in st.session_state:
        st.session_state.active_case_id = cases[0]["id"] if cases else "CASE-2026-001"

    if "voice_transcript" not in st.session_state:
        st.session_state.voice_transcript = ""

    if "extracted_voice_data" not in st.session_state:
        st.session_state.extracted_voice_data = None

    # Sidebar Navigation & User Profile
    with st.sidebar:
        st.markdown("### ⚖️ CaseResolutionAI")
        st.caption("An AI that fights the case you don't have time to fight.")

        # User Authentication Status
        current_user = st.session_state.get("current_user")
        if current_user:
            st.success(f"Signed in as: **{current_user.get('username')}**")
            if st.button("🚪 Log Out", key="logout_btn"):
                st.session_state.current_user = None
                st.rerun()
        else:
            st.info("Mode: **Guest / Demo Session**")
            with st.expander("👤 Sign In / Create Account"):
                auth_tab1, auth_tab2 = st.tabs(["Login", "Register"])
                with auth_tab1:
                    l_ident = st.text_input("Username or Email", key="l_ident")
                    l_pass = st.text_input("Password", type="password", key="l_pass")
                    if st.button("Sign In", key="l_btn", use_container_width=True):
                        res = db_service.authenticate_user(l_ident, l_pass)
                        if res["success"]:
                            st.session_state.current_user = res["user"]
                            st.success(f"Welcome back, {res['user']['username']}!")
                            st.rerun()
                        else:
                            st.error(res["error"])

                with auth_tab2:
                    r_uname = st.text_input("Username", key="r_uname")
                    r_email = st.text_input("Email", key="r_email")
                    r_pass = st.text_input("Password (min 6 chars)", type="password", key="r_pass")
                    r_name = st.text_input("Full Name (optional)", key="r_name")
                    if st.button("Create Account", key="r_btn", use_container_width=True):
                        res = db_service.register_user(r_uname, r_email, r_pass, r_name)
                        if res["success"]:
                            st.session_state.current_user = res["user"]
                            st.success("Account created successfully!")
                            st.rerun()
                        else:
                            st.error(res["error"])

        st.markdown("---")
        navigation = st.radio(
            "Navigation Menu",
            options=[
                "🏛️ Home & Product Vision",
                "🎙️ AI Complaint Intake",
                "📊 Case Dashboard",
                "📜 AI Grievance Letter Generator",
                "📑 Download Case Dossier",
                "💻 Sample Demonstration Case",
                "⚖️ Indian Consumer Rights Guide"
            ],
            index=0
        )

        st.markdown("---")
        st.markdown("#### 🎙️ Gnani AI Integration")
        if gnani_service.is_gnani_api_configured():
            st.success("Gnani Prisma STT: **Live & Active**")
        else:
            st.warning("Gnani STT: **Key Required** in `.env`")

        st.markdown("---")
        st.markdown("#### 🛡️ Safe Use Guardrails")
        st.info(
            "• **Organizational Aid:** Does not replace legal counsel.\n"
            "• **No Guarantee of Refund:** Redressal depends on dispute facts.\n"
            "• **Human-in-the-Loop:** You review and approve every filing.\n"
            "• **Private Storage:** Encrypted & isolated database."
        )

    # =========================================================
    # MODULE A: MODERN LANDING PAGE
    # =========================================================
    if navigation == "🏛️ Home & Product Vision":
        st.markdown("""
        <div class="hero-banner">
            <span class="hero-badge">Next-Gen Consumer Legal-Tech</span>
            <div class="hero-title">CaseResolutionAI</div>
            <div class="hero-sub">
                <strong>An AI that fights the case you don't have time to fight.</strong><br/>
                Every year, millions of Indian consumers lose hard-earned money to defective deliveries, 
                delayed refunds, cancelled flights, and broken warranty commitments. CaseResolutionAI turns your 
                voice into an evidence-backed legal grievance dossier ready for resolution.
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Platform Highlights
        c_stat1, c_stat2, c_stat3, c_stat4 = st.columns(4)
        c_stat1.metric("Voice Languages", "3 (KN, HI, EN)", "Gnani Prisma v3.0")
        c_stat2.metric("Grievance Notice Types", "4 Formats", "Email to Legal Draft")
        c_stat3.metric("Case Completeness Engine", "11 Key Parameters", "Zero Hallucination")
        c_stat4.metric("Dossier Export Formats", "PDF & HTML", "Court & NCH Ready")

        st.markdown("---")

        # Action Buttons
        callout_c1, callout_c2 = st.columns(2)
        with callout_c1:
            st.markdown("""
            ### 🎙️ Have an Unresolved Consumer Issue?
            Speak or type what happened in Kannada, Hindi, or Indian English. 
            CaseResolutionAI will analyze your problem, extract key details, and assemble your evidence dossier.
            """)
            if st.button("🚀 Start My Complaint Now", type="primary", use_container_width=True):
                # Switch to Complaint Intake
                st.info("Navigate to '🎙️ AI Complaint Intake' from the sidebar to begin your intake.")
        
        with callout_c2:
            st.markdown("""
            ### 💻 Explore the Sample Laptop Demo Case
            Inspect how a real-world ₹58,499 damaged laptop dispute with a delayed refund 
            is structured, timeline-tracked, and compiled into a downloadable legal dossier.
            """)
            if st.button("👉 Open Sample Demonstration Case", use_container_width=True):
                st.session_state.active_case_id = "CASE-2026-001"
                st.info("Switched to Sample Demo Case. Click '💻 Sample Demonstration Case' in the sidebar.")

        st.markdown("---")
        st.subheader("How CaseResolutionAI Works")
        step_col1, step_col2, step_col3, step_col4 = st.columns(4)
        with step_col1:
            st.markdown("""
            #### 1. Voice Intake
            Speak naturally in Kannada, Hindi, or English. Gnani AI Prisma STT captures your statement accurately.
            """)
        with step_col2:
            st.markdown("""
            #### 2. Evidence Tagging
            Upload invoices, damage photos, courier slips, and chat logs. The AI checks and validates each document.
            """)
        with step_col3:
            st.markdown("""
            #### 3. Gap Analysis
            The system asks targeted follow-up inquiries for any missing facts instead of inventing details.
            """)
        with step_col4:
            st.markdown("""
            #### 4. Resolution Dossier
            Generates 4 formal grievance drafts, an NCH portal copy, and a full downloadable PDF dossier.
            """)

        st.markdown("---")
        # Trust & Security Section
        st.subheader("🛡️ Trust, Privacy & Ethical AI Principles")
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            st.markdown("""
            - **No Fabricated Legal Claims:** The AI never guarantees a refund or makes false legal promises.
            - **Statement vs Evidence Distinction:** Clearly labels consumer assertions as subjective accounts and attached receipts as objective proof.
            - **Human in the Loop:** Complaints are never submitted automatically without your manual approval and action.
            """)
        with t_col2:
            st.markdown("""
            - **Encrypted Local Database:** Case records and user credentials use PBKDF2 cryptographic hashing.
            - **Official Gnani API:** Uses live Gnani Prisma STT without hardcoded secrets or data leakage.
            - **Official Redressal Channels:** Follows statutory pathways under the *Consumer Protection Act, 2019*.
            """)

        st.markdown("---")
        # FAQ Accordion
        st.subheader("Frequently Asked Questions")
        with st.expander("Does CaseResolutionAI submit complaints automatically to companies or consumer courts?"):
            st.write("No. Responsible design dictates that consumers retain 100% control over their representation. CaseResolutionAI compiles your timeline, evidence, and structured grievance letters. You review, approve, and send them to the company's Grievance Officer or the National Consumer Helpline.")
        with st.expander("Which languages are supported for voice complaints?"):
            st.write("We support Kannada (`kn-IN`), Hindi (`hi-IN`), and Indian English (`en-IN`) powered by Gnani AI Prisma v3.0 speech-to-text.")
        with st.expander("What documents should I attach to my case?"):
            st.write("The most effective documents are: (1) The tax invoice with the seller's GSTIN, (2) Photos or unboxing video of the defect, (3) Customer support chat or email transcripts, and (4) Courier pickup or delivery slips.")

        st.markdown("---")
        st.caption("CaseResolutionAI © 2026 | Built for the Great Indian AI Internship Challenge by Gnani AI.")

    # =========================================================
    # MODULE B & C: AI VOICE COMPLAINT INTAKE & UNDERSTANDING
    # =========================================================
    elif navigation == "🎙️ AI Complaint Intake":
        st.title("🎙️ AI Consumer Complaint Intake")
        st.markdown("Speak or type what happened. CaseResolutionAI structures your narrative, validates evidence, and generates your case dossier.")

        st.markdown("""
        <div class="disclaimer-card">
            <strong>Security & Privacy Reminder:</strong> Your data is stored locally. 
            Never enter passwords, ATM pins, or CVVs. All statements are reviewed by you before any notice is created.
        </div>
        """, unsafe_allow_html=True)

        intake_tab1, intake_tab2 = st.tabs([
            "🎙️ Voice Complaint Intake (Gnani AI Prisma STT)",
            "✍️ Structured Written Complaint Form"
        ])

        # -----------------------------------------------------
        # TAB 1: VOICE INTAKE
        # -----------------------------------------------------
        with intake_tab1:
            st.markdown("""
            <div style="background:#f0fdf4; border:1px solid #86efac; border-radius:10px; padding:1.2rem; margin-bottom:1.2rem;">
                <h4 style="margin-top:0; color:#166534;">🎙️ Multilingual Voice Complaint Intake</h4>
                <p style="margin-bottom:0; color:#14532d; font-size:0.95rem;">
                    Speak naturally in <strong>Kannada, Hindi, or Indian English</strong>. 
                    Gnani AI's <strong>Prisma v3.0 Speech-to-Text</strong> engine will transcribe your voice. 
                    Our complaint engine will then extract all 11 grievance parameters and identify any missing facts.
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Language Selection
            lang_col1, lang_col2 = st.columns([1, 2])
            with lang_col1:
                selected_lang_label = st.selectbox(
                    "Select Your Spoken Language *",
                    options=list(gnani_service.SUPPORTED_LANGUAGES.keys()),
                    index=0,
                    key="voice_lang_selector"
                )
                selected_lang_code = gnani_service.SUPPORTED_LANGUAGES[selected_lang_label]["code"]

            with lang_col2:
                st.markdown(f"**Target Model:** `prisma-v3.0` | **Language Code:** `{selected_lang_code}`")
                st.caption("Optimized for Indian accents, regional terminology, and e-commerce transactions.")

            st.markdown("---")
            st.subheader("1. Record Your Spoken Complaint")
            st.caption("Tell us: (1) Your name, (2) What you bought, (3) From which seller, (4) Amount paid in ₹, (5) What went wrong, and (6) What customer support promised.")

            mic_col, file_col = st.columns(2)
            with mic_col:
                st.markdown("**Option A: Microphone Recording**")
                recorded_audio = st.audio_input("Click the microphone icon to record", key="voice_mic_input")
                if recorded_audio is not None:
                    st.caption("🎧 Listen to recorded audio:")
                    st.audio(recorded_audio)

            with file_col:
                st.markdown("**Option B: Audio File Upload**")
                uploaded_audio_file = st.file_uploader(
                    "Or upload a pre-recorded audio file (.wav, .mp3, .m4a)",
                    type=["wav", "mp3", "ogg", "m4a"],
                    key="voice_audio_upload"
                )
                if uploaded_audio_file is not None:
                    st.caption("🎧 Listen to uploaded audio:")
                    st.audio(uploaded_audio_file)

            # Evaluator Demo Quick-Loader
            with st.expander("🧪 Evaluator Quick-Test: Load Sample Voice Narrative (For Reviewers)"):
                st.caption("Testing without a microphone? Click below to instantly load a realistic spoken dispute narrative in your chosen language:")
                sc_choice = st.selectbox("Select Demonstration Scenario:", list(SAMPLE_SPOKEN_SCENARIOS.keys()), key="evaluator_scenario_selector")
                sc_data = SAMPLE_SPOKEN_SCENARIOS[sc_choice]
                st.markdown(f"**Case:** {sc_data['title']} — *{sc_data['notes']}*")
                if st.button("👉 Load this Demonstration Spoken Statement", use_container_width=True, key="btn_load_demo_voice"):
                    st.session_state.voice_transcript = sc_data["audio_text"]
                    target_code = gnani_service.SUPPORTED_LANGUAGES[sc_choice]["code"]
                    st.session_state.extracted_voice_data = gnani_service.extract_complaint_fields(sc_data["audio_text"], language_code=target_code)
                    st.success(f"Loaded {sc_choice} spoken statement! Review the extracted fields below.")
                    st.rerun()

            # Transcribe Button
            st.markdown("---")
            if st.button("✨ Transcribe Voice with Gnani AI Prisma STT", type="primary", use_container_width=True, key="btn_transcribe_voice"):
                audio_bytes_to_send = None
                filename_to_send = "audio.wav"

                if recorded_audio is not None:
                    audio_bytes_to_send = recorded_audio.read()
                    filename_to_send = "recorded_complaint.wav"
                elif uploaded_audio_file is not None:
                    audio_bytes_to_send = uploaded_audio_file.read()
                    filename_to_send = uploaded_audio_file.name

                if not audio_bytes_to_send:
                    st.error("Please record audio using the microphone or upload an audio file first.")
                else:
                    with st.spinner(f"Transcribing audio with Gnani AI Prisma STT ({selected_lang_label})..."):
                        result = gnani_service.transcribe_audio_gnani(
                            audio_bytes=audio_bytes_to_send,
                            language_code=selected_lang_code,
                            file_name=filename_to_send
                        )

                    if result["success"]:
                        st.session_state.voice_transcript = result["transcript"]
                        st.session_state.extracted_voice_data = gnani_service.extract_complaint_fields(
                            result["transcript"],
                            language_code=selected_lang_code
                        )
                        st.success("Transcription completed successfully!")
                    else:
                        st.error(f"Transcription failed: {result['error']}")

            # Transcript Review & Editing
            st.markdown("---")
            st.subheader("2. Review & Edit Transcription")
            st.caption("You can edit the transcribed text below to correct any specific model numbers, dates, or prices:")

            edited_transcript = st.text_area(
                "Transcribed Narrative (Editable) *",
                value=st.session_state.voice_transcript,
                height=130,
                placeholder="The transcribed speech will appear here. You can also paste or type directly to test field extraction."
            )

            if st.button("🔍 Extract & Analyze Complaint Particulars", key="btn_reextract"):
                if not edited_transcript.strip():
                    st.error("Please provide or transcribe a complaint statement first.")
                else:
                    st.session_state.voice_transcript = edited_transcript
                    st.session_state.extracted_voice_data = gnani_service.extract_complaint_fields(
                        edited_transcript,
                        language_code=selected_lang_code
                    )

            # Extracted Fields & Follow-up Questions
            if st.session_state.extracted_voice_data:
                st.markdown("---")
                st.subheader("3. Extracted Complaint Particulars & Verification")
                ext = st.session_state.extracted_voice_data

                # Follow-Up Inquiries for Missing Data
                if ext.get("missing_fields"):
                    st.markdown("""
                    <div style="background:#fffbeb; border-left:4px solid #f59e0b; padding:12px 14px; border-radius:6px; margin-bottom:14px;">
                        <strong style="color:#b45309;">⚠️ Additional Information Needed (Targeted Inquiries)</strong><br/>
                        <span style="font-size:0.9em; color:#78350f;">
                            Rather than assuming or inventing answers, our AI identified the following missing details. 
                            Please provide them in the form below before proceeding:
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                    for q in ext.get("follow_up_questions", []):
                        st.markdown(f"• *{q}*")
                    st.markdown("<br/>", unsafe_allow_html=True)

                # Editable Extracted Form
                with st.form("voice_verification_form"):
                    v_col1, v_col2 = st.columns(2)
                    with v_col1:
                        v_cname = st.text_input("Consumer Name *", value=ext.get("customer_name") or (st.session_state.current_user["full_name"] if st.session_state.current_user and st.session_state.current_user.get("full_name") else "Concerned Consumer"))
                        v_product = st.text_input("Product or Service Name *", value=ext.get("product_name") or "")
                        v_category = st.selectbox(
                            "Product Category *",
                            [
                                "Electronics & Computers", "Home Appliances", "E-Commerce & Retail Goods",
                                "Travel, Airlines & Hospitality", "Telecom & Internet Services",
                                "Banking, Payments & FinTech", "EdTech & Online Courses", "Other Consumer Goods/Services"
                            ]
                        )
                        v_seller = st.text_input("Seller / Service Provider Name *", value=ext.get("seller_name") or "")
                        v_amount = st.number_input(
                            "Purchase Amount (₹ INR) *",
                            min_value=0.0,
                            value=float(ext.get("purchase_amount") or 0.0),
                            step=100.0,
                            format="%.2f"
                        )

                    with v_col2:
                        v_order_id = st.text_input("Order ID / Ticket Reference", value=ext.get("order_id") or "")
                        v_purch_date = st.text_input("Purchase Date", value=ext.get("purchase_date") or str(date.today()))
                        v_deliv_date = st.text_input("Delivery Date", value=ext.get("delivery_date") or str(date.today()))
                        v_promises = st.text_input("Seller Promises / Return SLA", value=ext.get("seller_promises") or "Standard customer support resolution promised")
                        v_status = st.text_input("Refund / Resolution Status", value=ext.get("refund_resolution_status") or "Refund Delayed / Pending")

                    st.markdown("**Problem Description**")
                    v_desc = st.text_area("Detailed Problem Narrative *", value=ext.get("problem_description") or edited_transcript, height=100)
                    v_relief = st.selectbox(
                        "Remedy / Relief Sought *",
                        [
                            "Full Refund to Original Payment Method",
                            "Free Replacement with Brand New Sealed Unit",
                            "Immediate Repair under Manufacturer Warranty",
                            "Partial Refund / Compensation for Delay",
                            "Cancellation of Subscription & Refund"
                        ]
                    )

                    st.markdown("---")
                    st.subheader("4. Evidence Upload Area")
                    st.caption("Upload receipts, photos, or screenshots to support your voice complaint:")
                    v_files = st.file_uploader(
                        "Upload Proof (Invoices, Photos, Courier Slips)",
                        type=["png", "jpg", "jpeg", "pdf"],
                        accept_multiple_files=True,
                        key="voice_evidence_files"
                    )

                    v_confirm = st.form_submit_button("✅ Confirm & Create Complaint Dossier", type="primary", use_container_width=True)

                    if v_confirm:
                        if not v_product.strip() or not v_seller.strip() or v_amount <= 0:
                            st.error("Please fill in the required fields: Product Name, Seller Name, and a valid Purchase Amount.")
                        elif not v_desc.strip():
                            st.error("Please provide a description of the problem in your narrative.")
                        else:
                            new_id = f"CASE-2026-{len(get_current_user_cases()) + 1:03d}"
                            
                            evidence_list = []
                            if v_files:
                                for f in v_files:
                                    ftype = "Document / Proof"
                                    if f.name.lower().endswith(('.png', '.jpg', '.jpeg')):
                                        ftype = "Photographic Artifact"
                                    elif f.name.lower().endswith('.pdf'):
                                        ftype = "Official PDF Document"
                                    evidence_list.append({
                                        "file_name": f.name,
                                        "file_type": ftype,
                                        "verification_status": "Document Attached",
                                        "description": f"Uploaded {f.name} ({f.size / 1024:.1f} KB)"
                                    })
                            else:
                                evidence_list.append({
                                    "file_name": "No files uploaded during voice intake",
                                    "file_type": "Pending Attachment",
                                    "verification_status": "Awaiting User Upload",
                                    "description": "User can attach receipts and proof at any time."
                                })

                            new_case = {
                                "id": new_id,
                                "title": f"{v_product} — {v_status}",
                                "customer_name": v_cname,
                                "product_name": v_product,
                                "product_category": v_category,
                                "seller_name": v_seller,
                                "purchase_amount": float(v_amount),
                                "purchase_date": str(v_purch_date),
                                "delivery_date": str(v_deliv_date),
                                "problem_category": ext.get("complaint_category") or "Damaged on Delivery & Delayed Refund",
                                "status": "Evidence Documented",
                                "relief_sought": v_relief,
                                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "user_statement": v_desc,
                                "timeline": [
                                    {
                                        "date": str(v_purch_date),
                                        "event": "Purchase / Order Placed",
                                        "source": "Voice Intake Record",
                                        "details": f"Purchased {v_product} for ₹{v_amount:,.2f} from {v_seller}."
                                    },
                                    {
                                        "date": str(v_deliv_date),
                                        "event": "Delivery & Defect Discovery",
                                        "source": "Voice Intake Record",
                                        "details": f"Defect reported. Seller promised: {v_promises}."
                                    }
                                ],
                                "evidence_items": evidence_list,
                                "support_ticket_ref": v_order_id or "Not Provided",
                                "seller_email": "Not Provided",
                                "seller_promises": v_promises,
                                "refund_status": v_status,
                                "consumer_notes": f"Voice intake processed via Gnani AI Prisma STT ({selected_lang_label})."
                            }

                            save_case(new_case)
                            st.session_state.active_case_id = new_id
                            st.success(f"🎉 Case **{new_id}** created successfully! You can manage it in the Case Dashboard.")

        # -----------------------------------------------------
        # TAB 2: STRUCTURED WRITTEN COMPLAINT FORM
        # -----------------------------------------------------
        with intake_tab2:
            st.subheader("Structured Written Complaint Form")
            st.caption("Fill out the structured form manually if you prefer typing over voice recording.")

            with st.form("manual_complaint_form"):
                st.markdown("#### 1. Consumer, Seller & Purchase Details")
                m_c1, m_c2 = st.columns(2)
                with m_c1:
                    m_cname = st.text_input("Your Full Name *", value=st.session_state.current_user["full_name"] if st.session_state.current_user and st.session_state.current_user.get("full_name") else "Concerned Consumer")
                    m_pname = st.text_input("Product or Service Name *", placeholder="e.g. UltraView 43-inch 4K Smart TV")
                    m_pcat = st.selectbox(
                        "Product Category *",
                        [
                            "Electronics & Computers", "Home Appliances", "E-Commerce & Retail Goods",
                            "Travel, Airlines & Hospitality", "Telecom & Internet Services",
                            "Banking, Payments & FinTech", "EdTech & Online Courses", "Other Consumer Goods/Services"
                        ],
                        key="manual_cat_select"
                    )
                    m_sname = st.text_input("Seller / Service Provider Name *", placeholder="e.g. PrimeGoods Retail Pvt Ltd")

                with m_c2:
                    m_amount = st.number_input("Purchase Amount (in ₹ INR) *", min_value=0.0, value=0.0, step=100.0, format="%.2f", key="manual_amt")
                    m_purch_date = st.date_input("Date of Purchase *", value=date.today(), key="manual_pdate")
                    m_deliv_date = st.date_input("Date of Delivery / Issue Discovery *", value=date.today(), key="manual_ddate")
                    m_support_ref = st.text_input("Order ID / Support Ticket Reference (if any)", placeholder="e.g. ORD-102948 or TKT-55410", key="manual_ref")

                st.markdown("---")
                st.markdown("#### 2. Nature of Dispute & User Statement")
                m_prob_cat = st.selectbox(
                    "Primary Grievance Category *",
                    [
                        "Damaged on Delivery", "Defective / Non-Functional Product", "Delayed or Refused Refund",
                        "Wrong Item Delivered", "Service Deficiency / Incomplete Service",
                        "Misleading Advertisement / Specification Mismatch", "Overcharging / Billing Irregularity"
                    ],
                    key="manual_prob_cat"
                )

                st.markdown("<span class='tag-statement'>User Statement</span> Describe what happened chronologically:", unsafe_allow_html=True)
                m_statement = st.text_area(
                    "Your Statement of Facts *",
                    height=130,
                    placeholder="On [Date], I received the package. Upon opening, I observed... I contacted customer care under ticket... They promised a resolution within 5 days, but...",
                    key="manual_statement_text"
                )

                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    m_relief = st.selectbox(
                        "Remedy / Relief Sought *",
                        [
                            "Full Refund to Original Payment Method", "Free Replacement with Brand New Sealed Unit",
                            "Immediate Repair under Manufacturer Warranty", "Partial Refund / Compensation for Delay",
                            "Cancellation of Subscription & Refund"
                        ],
                        key="manual_relief"
                    )
                with col_r2:
                    m_seller_email = st.text_input("Seller's Grievance Email (optional)", placeholder="e.g. grievance@sellerdomain.example", key="manual_email")

                st.markdown("---")
                st.markdown("#### 3. Evidence Upload Area")
                m_files = st.file_uploader(
                    "Upload Proof (Invoices, Photos, Courier Slips)",
                    type=["png", "jpg", "jpeg", "pdf"],
                    accept_multiple_files=True,
                    key="manual_evidence_uploader"
                )
                m_notes = st.text_input("Summary note for uploaded evidence (optional)", placeholder="e.g. Official tax invoice attached with hinge photos", key="manual_ev_notes")

                st.markdown("---")
                m_submit = st.form_submit_button("📁 Save to Case Dossier", type="primary", use_container_width=True)

                if m_submit:
                    if not m_pname.strip() or not m_sname.strip() or m_amount <= 0:
                        st.error("Please fill in the required fields: Product Name, Seller Name, and a valid Purchase Amount.")
                    elif not m_statement.strip():
                        st.error("Please provide a description of the problem in your statement.")
                    else:
                        new_id = f"CASE-2026-{len(get_current_user_cases()) + 1:03d}"
                        evidence_list = []
                        if m_files:
                            for f in m_files:
                                ftype = "Document / Proof"
                                if f.name.lower().endswith(('.png', '.jpg', '.jpeg')):
                                    ftype = "Photographic Artifact"
                                elif f.name.lower().endswith('.pdf'):
                                    ftype = "Official PDF Document"
                                evidence_list.append({
                                    "file_name": f.name,
                                    "file_type": ftype,
                                    "verification_status": "Document Attached",
                                    "description": m_notes if m_notes else f"Uploaded {f.name} ({f.size / 1024:.1f} KB)"
                                })
                        else:
                            evidence_list.append({
                                "file_name": "No files uploaded during initial intake",
                                "file_type": "Pending Attachment",
                                "verification_status": "Awaiting User Upload",
                                "description": "User can attach receipts and proof at any time."
                            })

                        new_case = {
                            "id": new_id,
                            "title": f"{m_pname} — {m_prob_cat}",
                            "customer_name": m_cname,
                            "product_name": m_pname,
                            "product_category": m_pcat,
                            "seller_name": m_sname,
                            "purchase_amount": float(m_amount),
                            "purchase_date": str(m_purch_date),
                            "delivery_date": str(m_deliv_date),
                            "problem_category": m_prob_cat,
                            "status": "Evidence Documented",
                            "relief_sought": m_relief,
                            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "user_statement": m_statement,
                            "timeline": [
                                {
                                    "date": str(m_purch_date),
                                    "event": "Purchase / Order Date",
                                    "source": "Invoice / Bank Record",
                                    "details": f"Purchased for ₹{m_amount:,.2f} from {m_sname}."
                                },
                                {
                                    "date": str(m_deliv_date),
                                    "event": "Delivery & Defect Discovery",
                                    "source": "User Statement",
                                    "details": f"Problem identified: {m_prob_cat}."
                                }
                            ],
                            "evidence_items": evidence_list,
                            "support_ticket_ref": m_support_ref or "Not Provided",
                            "seller_email": m_seller_email or "Not Provided",
                            "seller_promises": "Standard customer service SLA",
                            "refund_status": "Pending",
                            "consumer_notes": "Case filed via structured written form."
                        }

                        save_case(new_case)
                        st.session_state.active_case_id = new_id
                        st.success(f"Case **{new_id}** created successfully! View it in the Case Dashboard.")

    # =========================================================
    # MODULE H & E: CASE DASHBOARD & AI CASE BUILDER
    # =========================================================
    elif navigation == "📊 Case Dashboard":
        st.title("📊 Consumer Case Dashboard")
        st.markdown("Track, organize, and advance your consumer dispute dossiers.")

        user_cases = get_current_user_cases()
        if not user_cases:
            st.warning("No cases found in your session. Please file a complaint first.")
        else:
            # Overview Metrics
            total_cases = len(user_cases)
            total_value = sum(c.get("purchase_amount", 0) for c in user_cases)
            active_cases = len([c for c in user_cases if c.get("status") != "Resolved / Closed"])
            resolved_cases = len([c for c in user_cases if c.get("status") == "Resolved / Closed"])

            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            m_col1.metric("Total Documented Cases", total_cases)
            m_col2.metric("Active Disputes", active_cases)
            m_col3.metric("Resolved Cases", resolved_cases)
            m_col4.metric("Disputed Value (₹)", f"₹ {total_value:,.2f}")

            st.markdown("---")

            # Search & Filter
            dash_s1, dash_s2 = st.columns([2, 1])
            with dash_s1:
                search_q = st.text_input("🔍 Search cases by product, seller, or ID", placeholder="e.g. Laptop, NovaCart, or CASE-2026")
            with dash_s2:
                cat_filter = st.selectbox("Filter by Category", ["All Categories"] + sorted(list(set(c["product_category"] for c in user_cases))))

            filtered = user_cases
            if search_q.strip():
                q = search_q.lower()
                filtered = [c for c in filtered if q in c["product_name"].lower() or q in c["seller_name"].lower() or q in c["id"].lower()]
            if cat_filter != "All Categories":
                filtered = [c for c in filtered if c["product_category"] == cat_filter]

            if not filtered:
                st.info("No cases matched your filter.")
                filtered = user_cases

            case_options = {c["id"]: f"{c['id']} — {c['title']} (₹{c['purchase_amount']:,.0f})" for c in filtered}
            default_idx = 0
            if st.session_state.active_case_id in case_options:
                default_idx = list(case_options.keys()).index(st.session_state.active_case_id)

            selected_id = st.selectbox(
                "Select Case to View & Manage:",
                options=list(case_options.keys()),
                format_func=lambda x: case_options[x],
                index=default_idx
            )
            st.session_state.active_case_id = selected_id
            current_case = find_case_by_id(selected_id, user_cases)

            if current_case:
                st.markdown(f"### {current_case['title']}")

                # Header summary row
                h_c1, h_c2, h_c3, h_c4 = st.columns(4)
                h_c1.markdown(f"**Case ID:** `{current_case['id']}`")
                h_c2.markdown(f"**Seller:** {current_case['seller_name']}")
                h_c3.markdown(f"**Amount:** ₹ {current_case['purchase_amount']:,.2f}")
                h_c4.markdown(f"**Status:** `{current_case.get('status', 'Active')}`")

                # Visual Escalation Progress Bar
                st.markdown("#### 🚀 Dispute Escalation Lifecycle")
                current_status = current_case.get("status", "Evidence Documented")
                stage_cols = st.columns(5)
                for idx, stg in enumerate(ESCALATION_STAGES):
                    with stage_cols[idx]:
                        is_active = (current_status == stg["label"])
                        pill_class = "stage-active" if is_active else "stage-pending"
                        st.markdown(
                            f"""
                            <div class="stage-pill {pill_class}">
                                Stage {stg['stage']}: {stg['label']}
                            </div>
                            <div style="font-size:0.75rem; color:#64748b; margin-top:4px;">{stg['desc']}</div>
                            """,
                            unsafe_allow_html=True
                        )

                st.markdown("---")

                # Completeness Engine
                readiness = calculate_readiness_score(current_case)
                st.markdown("#### 🎯 AI Case Completeness Assessment")
                sc_col1, sc_col2 = st.columns([1, 2])
                with sc_col1:
                    st.metric("Dossier Completeness", f"{readiness['score']} / 100")
                    st.markdown(f"<span style='color:{readiness['color']}; font-weight:700;'>● {readiness['label']}</span>", unsafe_allow_html=True)
                    st.caption("Evaluates factual & documentary completeness before approaching consumer forums.")
                with sc_col2:
                    st.markdown("**Completeness Checklist:**")
                    for chk in readiness["checks"]:
                        icon = "✅" if chk["passed"] else "⚠️"
                        st.markdown(f"{icon} **{chk['item']}**: {chk['detail']}")

                st.markdown("---")

                # Statements vs Evidence Comparison
                st.markdown("#### ⚖️ Separation: User Statement vs Documented Evidence")
                st_col, ev_col = st.columns(2)
                with st_col:
                    st.markdown("<span class='tag-statement'>User-Provided Statement</span>", unsafe_allow_html=True)
                    st.info(current_case.get("user_statement", "No statement provided."))
                    st.caption(f"**Remedy Requested:** {current_case.get('relief_sought')}")
                    st.caption(f"**Ticket/Order Reference:** {current_case.get('support_ticket_ref', 'N/A')}")

                with ev_col:
                    st.markdown("<span class='tag-evidence'>Attached Evidence & Artifacts</span>", unsafe_allow_html=True)
                    evidence_items = current_case.get("evidence_items", [])
                    if evidence_items:
                        for idx, item in enumerate(evidence_items):
                            with st.container():
                                st.markdown(
                                    f"""
                                    <div class="artifact-card">
                                        <strong>[{idx+1}] {item['file_name']}</strong><br/>
                                        <small>Type: <em>{item['file_type']}</em> | Status: <code>{item.get('verification_status', 'Attached')}</code></small><br/>
                                        <small style="color:#475569;">{item.get('description', '')}</small>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                    else:
                        st.write("No evidence items attached yet.")

                st.markdown("---")

                # Chronological Timeline & Milestone Logger
                st.markdown("#### 🕒 Chronology of Events")
                for t in current_case.get("timeline", []):
                    st.markdown(
                        f"""
                        <div class="timeline-item">
                            <strong>{t['date']}</strong> — <strong>{t['event']}</strong> 
                            <span style="font-size: 0.8rem; color: #64748b; margin-left: 8px;">[Source: {t.get('source', 'Record')}]</span><br/>
                            <span style="font-size: 0.95rem; color: #334155;">{t['details']}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                with st.expander("➕ Log a New Interaction / Event to this Timeline"):
                    with st.form(f"add_event_{current_case['id']}"):
                        ev_c1, ev_c2 = st.columns(2)
                        with ev_c1:
                            new_ev_date = st.date_input("Event Date", value=date.today())
                            new_ev_title = st.text_input("Event Title", placeholder="e.g. Call with Grievance Desk")
                        with ev_c2:
                            new_ev_source = st.selectbox("Record Source", ["Support Ticket / Email", "Phone Call Log", "Courier Tracking", "Personal Statement"])
                            new_ev_details = st.text_input("Details / Response", placeholder="e.g. Company promised supervisor callback within 24 hours.")
                        if st.form_submit_button("Add Event to Timeline"):
                            if new_ev_title.strip() and new_ev_details.strip():
                                current_case.setdefault("timeline", []).append({
                                    "date": str(new_ev_date),
                                    "event": new_ev_title,
                                    "source": new_ev_source,
                                    "details": new_ev_details
                                })
                                save_case(current_case)
                                st.success("Timeline milestone added!")
                                st.rerun()

                st.markdown("---")

                # Actions: Status Update, Export, Delete
                st.markdown("#### ⚙️ Case Operations")
                op_c1, op_c2 = st.columns(2)
                with op_c1:
                    st.markdown("**Update Dispute Status**")
                    status_opts = [s["label"] for s in ESCALATION_STAGES]
                    cur_idx = status_opts.index(current_case.get("status")) if current_case.get("status") in status_opts else 0
                    new_st = st.selectbox("Dispute Progress:", status_opts, index=cur_idx, key=f"status_sel_{current_case['id']}")
                    if st.button("Save Status Update", key=f"save_status_{current_case['id']}"):
                        current_case["status"] = new_st
                        save_case(current_case)
                        st.success(f"Status updated to: {new_st}")
                        st.rerun()

                with op_c2:
                    st.markdown("**Delete / Archive Case**")
                    st.caption("Permanently removes this case from your active dashboard.")
                    if st.button("🗑️ Delete This Case", key=f"del_case_{current_case['id']}", type="secondary"):
                        delete_case(current_case["id"])
                        st.success("Case deleted.")
                        st.rerun()

    # =========================================================
    # MODULE F: AI GRIEVANCE LETTER GENERATOR
    # =========================================================
    elif navigation == "📜 AI Grievance Letter Generator":
        st.title("📜 AI Grievance Representation Generator")
        st.markdown("Generate 4 distinct, fact-based consumer resolution letters tailored to your escalation level.")

        user_cases = get_current_user_cases()
        if not user_cases:
            st.warning("Please file or select a case first.")
        else:
            case_options = {c["id"]: f"{c['id']} — {c['title']}" for c in user_cases}
            sel_case_id = st.selectbox("Select Case for Representation:", list(case_options.keys()), format_func=lambda x: case_options[x])
            c_case = find_case_by_id(sel_case_id, user_cases)

            # Choose Representation Format
            st.markdown("---")
            format_choice = st.radio(
                "Choose Grievance Representation Format:",
                [
                    "1. Seller Customer Support Email (Direct Resolution)",
                    "2. Formal Legal Grievance Notice (7-Day Cure Period)",
                    "3. Nodal Grievance Officer Escalation Letter (Rule 4 CPA Rules)",
                    "4. National Consumer Helpline (NCH / INGRAM) Draft"
                ],
                horizontal=False
            )

            lang_choice = st.radio("Language:", ["English", "Hindi (हिन्दी)", "Kannada (ಕನ್ನಡ)"], horizontal=True)

            # Generate Selected Letter
            if "Customer Support Email" in format_choice:
                letter_text = letter_service.generate_seller_email(c_case, language=lang_choice)
                doc_title = "Support_Complaint_Email"
            elif "Formal Legal Grievance Notice" in format_choice:
                letter_text = letter_service.generate_formal_legal_notice(c_case, language=lang_choice)
                doc_title = "Formal_Legal_Notice"
            elif "Nodal Grievance Officer" in format_choice:
                letter_text = letter_service.generate_nodal_escalation_letter(c_case, language=lang_choice)
                doc_title = "Nodal_Escalation_Letter"
            else:
                letter_text = letter_service.generate_nch_complaint_draft(c_case, language=lang_choice)
                doc_title = "NCH_Mediation_Draft"

            st.markdown("#### Generated Document Preview (Editable)")
            edited_letter = st.text_area("Representation Text", value=letter_text, height=340)

            # Action Buttons
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                st.download_button(
                    label=f"📥 Download Grievance Letter (.txt)",
                    data=edited_letter,
                    file_name=f"{c_case['id']}_{doc_title}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            with btn_col2:
                # NCH Portal Quick-Copy Box
                nch_snippet = format_for_nch_portal(c_case)
                with st.expander("📋 Copy Formatted Text for NCH / INGRAM Portal"):
                    st.caption("Characters formatted under 1000 characters for direct pasting into consumerhelpline.gov.in:")
                    st.code(nch_snippet, language="text")

    # =========================================================
    # MODULE I: COMPLETE CASE DOSSIER (PDF & HTML)
    # =========================================================
    elif navigation == "📑 Download Case Dossier":
        st.title("📑 Complete Consumer Case Dossier")
        st.markdown("Export a comprehensive, court and mediation ready Case Dossier including cover banner, timeline, statements, and evidence index.")

        user_cases = get_current_user_cases()
        if not user_cases:
            st.warning("Please file or select a case first.")
        else:
            case_options = {c["id"]: f"{c['id']} — {c['title']}" for c in user_cases}
            sel_case_id = st.selectbox("Select Case to Export:", list(case_options.keys()), format_func=lambda x: case_options[x], key="dossier_case_sel")
            c_case = find_case_by_id(sel_case_id, user_cases)

            st.markdown("---")
            d_col1, d_col2 = st.columns(2)

            with d_col1:
                st.markdown("""
                ### 📄 Download PDF Dossier
                - Generated via **ReportLab**
                - Includes Case Cover, Summary, Chronology Table, Evidence Index & Escalation Guide.
                - Formatted for legal counsel, mediators, or company grievance officers.
                """)
                pdf_bytes = dossier_pdf_service.generate_case_dossier_pdf(c_case)
                st.download_button(
                    label="📥 Download Official PDF Dossier",
                    data=pdf_bytes,
                    file_name=f"{c_case['id']}_Complete_Dossier.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )

            with d_col2:
                st.markdown("""
                ### 🖨️ Download Printable HTML Dossier
                - Opens directly in any browser.
                - Includes **One-Click Print / Save as PDF** button.
                - Responsive layout for physical printing.
                """)
                html_str = generate_printable_html_dossier(c_case)
                st.download_button(
                    label="🖨️ Download Printable HTML Dossier",
                    data=html_str,
                    file_name=f"{c_case['id']}_Printable_Dossier.html",
                    mime="text/html",
                    use_container_width=True
                )

            # JSON Backup Export
            st.markdown("---")
            with st.expander("💾 Backup All Cases (JSON Format)"):
                st.caption("Download all case dossiers as a JSON backup file for offline archival:")
                all_cases_json = export_cases_json(user_cases)
                st.download_button(
                    label="Download All Cases Backup (.json)",
                    data=all_cases_json,
                    file_name="CaseResolutionAI_Backup.json",
                    mime="application/json"
                )

    # =========================================================
    # MODULE G: SAMPLE DEMONSTRATION CASE
    # =========================================================
    elif navigation == "💻 Sample Demonstration Case":
        st.title("💻 Demonstration Case: Damaged Laptop & Delayed Refund")
        st.markdown("A realistic walkthrough showing how CaseResolutionAI turns an unresolved dispute into a structured, evidence-backed dossier.")

        sample_case = get_sample_demo_case()
        readiness = calculate_readiness_score(sample_case)

        st.markdown("""
        <div class="disclaimer-card">
            <strong>Fictional Demonstration Scenario:</strong><br/>
            All parties (NovaCart, AeroBook, AeroShip) and references used below are strictly fictional 
            to demonstrate the platform without using personal data or compromising consumer privacy.
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;">
                <h3 style="margin:0; color: #1e293b;">{sample_case['title']}</h3>
                <span style="background-color: {readiness['color']}; color: white; padding: 4px 10px; border-radius: 9999px; font-size: 0.85rem; font-weight: 700;">
                    Dossier Completeness: {readiness['score']}/100
                </span>
            </div>
            <p style="margin-bottom: 0.4rem;"><strong>Disputed Amount:</strong> ₹{sample_case['purchase_amount']:,.2f} | <strong>Seller:</strong> {sample_case['seller_name']}</p>
            <p style="margin-bottom: 0.4rem;"><strong>Purchase Date:</strong> {sample_case['purchase_date']} | <strong>Incident Date:</strong> {sample_case['incident_date']}</p>
            <p style="margin-bottom: 0;"><strong>Current Status:</strong> <span style="background-color:#dbeafe; color:#1e40af; padding: 3px 8px; border-radius:4px; font-weight:600;">{sample_case['status']}</span></p>
        </div>
        """, unsafe_allow_html=True)

        sc_c1, sc_c2 = st.columns(2)
        with sc_c1:
            st.markdown("<span class='tag-statement'>User-Provided Narrative</span>", unsafe_allow_html=True)
            st.info(sample_case["user_statement"])
            st.markdown(f"**Remedy Requested:** `{sample_case['relief_sought']}`")

        with sc_c2:
            st.markdown("<span class='tag-evidence'>Documented Proof & Artifacts</span>", unsafe_allow_html=True)
            for idx, item in enumerate(sample_case["evidence_items"]):
                st.markdown(
                    f"""
                    <div class="artifact-card">
                        <strong>[{idx+1}] {item['file_name']}</strong><br/>
                        🏷️ <em>{item['file_type']}</em> | Status: <code>{item['verification_status']}</code><br/>
                        <small style="color: #475569;">{item['description']}</small>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        st.markdown("---")
        st.subheader("Step-by-Step Chronology")
        for t in sample_case["timeline"]:
            st.markdown(
                f"""
                <div class="timeline-item">
                    <span style="font-weight:700; color:#1e40af;">{t['date']}</span> — <strong>{t['event']}</strong> 
                    <span style="font-size:0.8rem; background:#f1f5f9; padding:2px 6px; border-radius:4px; margin-left:6px;">{t['source']}</span><br/>
                    <span style="color:#334155;">{t['details']}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("---")
        st.subheader("Export Demonstrative Dossier")
        demo_pdf = dossier_pdf_service.generate_case_dossier_pdf(sample_case)
        st.download_button(
            label="📥 Download Sample Case PDF Dossier",
            data=demo_pdf,
            file_name="Sample_Case_Laptop_Dossier.pdf",
            mime="application/pdf",
            type="primary"
        )

    # =========================================================
    # MODULE G: INDIAN CONSUMER RIGHTS GUIDE
    # =========================================================
    elif navigation == "⚖️ Indian Consumer Rights Guide":
        st.title("⚖️ Indian Consumer Rights & Fair Practice Guide")
        st.markdown("Practical guidance for navigating disputes under the **Consumer Protection Act, 2019** (India).")

        st.markdown("""
        <div class="disclaimer-card">
            <strong>Information Notice:</strong> This guide provides general educational awareness regarding official consumer 
            redressal avenues in India. It does not constitute legal counsel.
        </div>
        """, unsafe_allow_html=True)

        st.subheader("Four-Stage Escalation Matrix for Indian Consumers")
        st.markdown("""
        1. **Level 1: Seller / E-Commerce Platform Customer Support**
           - Register an official ticket or complaint through their app or website.
           - Always record the **Ticket Number / Reference ID** and date of contact.
           - Allow reasonable SLA (typically 3 to 7 business days).
           
        2. **Level 2: Nodal Grievance Redressal Officer**
           - Under the *Consumer Protection (E-Commerce) Rules, 2020*, every e-commerce entity operating in India must designate a Grievance Officer.
           - Forward your structured dispute representation along with invoices and photos to their published grievance email.
           
        3. **Level 3: National Consumer Helpline (NCH / INGRAM)**
           - If the company fails to resolve within reasonable time, register a complaint with the Ministry of Consumer Affairs:
             - **Toll-Free Helpline:** `1915` (or `1800-11-4000`)
             - **Web Portal:** [consumerhelpline.gov.in](https://consumerhelpline.gov.in)
             - **NCH App:** National Consumer Helpline App on Google Play / App Store
           - The NCH acts as a direct mediation platform connecting the consumer with registered companies.
           
        4. **Level 4: e-Daakhil (Consumer Disputes Redressal Commission)**
           - If mediation fails, consumers can file an online case with the appropriate District or State Consumer Commission via [edaakhil.nic.in](https://edaakhil.nic.in).
        """)

        st.markdown("---")
        st.subheader("Sector-Specific Regulators & Ombudsmen in India")
        st.markdown("""
        - 🏦 **Banking & FinTech / UPI Disputes:** Reserve Bank of India (RBI) Integrated Ombudsman (`cms.rbi.org.in`).
        - ✈️ **Flight Cancellations & Airline Delays:** Directorate General of Civil Aviation (DGCA) & AirSewa Portal (`airsewa.gov.in`).
        - 📱 **Telecom & Broadband Deficiencies:** Telecom Regulatory Authority of India (TRAI) & Telecom Consumer Grievance.
        - 🛡️ **Insurance Claim Rejections:** Insurance Regulatory and Development Authority of India (IRDAI) Bima Bharosa.
        """)


if __name__ == "__main__":
    main()
