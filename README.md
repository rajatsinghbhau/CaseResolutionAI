# CaseResolutionAI — AI-Powered Consumer Complaint Resolution Assistant

> **Tagline:** *An AI that fights the case you don't have time to fight.*  
> **Built for:** The Great Indian AI Internship Challenge by Gnani.ai

---

## 📌 Project Overview & Submission Details

- **Project Title:** CaseResolutionAI – AI-Powered Consumer Complaint Resolution Assistant
- **Project Category:** AI / LegalTech / ConsumerTech
- **Project Type:** Solo project (Participating individually)
- **Target Audience:** Indian consumers facing unresolved complaints involving e-commerce platforms, sellers, defective products, delayed refunds, delivery services, and other consumer-related issues.

### 🛑 Problem Being Solved
Millions of consumers face unresolved complaints involving defective products, failed refunds, delivery problems, and poor customer service. Consumers often struggle to organise evidence, understand their rights, and prepare formal complaints. Existing processes are confusing, stressful, and time-consuming.

### 💡 Our Solution
CaseResolutionAI is an AI-powered consumer grievance assistant that allows users to explain their problems through voice or text. It uses Gnani AI technology for multilingual voice complaint intake and combines AI-powered complaint understanding, evidence organisation, case building, and grievance letter generation to help consumers prepare professional, court and mediation-ready complaint dossiers.

### 🎙️ Gnani AI Technology Used (Exact Implementation)
- **Technology & Service:** **Gnani AI Prisma Speech-to-Text (STT)**
- **API Endpoint:** Official REST API `https://api.vachana.ai/stt/v3`
- **Model Used:** **`prisma-v3.0`** (Gnani's flagship multilingual speech recognition model)
- **Authentication:** Secure header `X-API-Key-ID: <GNANI_API_KEY>` loaded securely from `.env`
- **Supported Languages:**
  - 🇮🇳 **Kannada (`kn-IN`)**: `ಕನ್ನಡ`
  - 🇮🇳 **Hindi (`hi-IN`)**: `हिन्दी`
  - 🇮🇳 **Indian English (`en-IN`)**: `English (Indian)`
- **Functionality Implemented:** 
  - Real-time in-browser microphone recording with live audio playback and retry capability.
  - Multi-format audio file upload (`.wav`, `.mp3`, `.m4a`, `.ogg`).
  - High-accuracy transcription of Indian accents and code-switching.
  - Interactive transcript review and editing.
  - Evaluator quick-test tool with pre-loaded spoken scenarios in Kannada, Hindi, and English.

---

## 🚀 Key Platform Features

### 1. 🏛️ Premium Legal-Tech Interface & Landing Page
- Modern legal-tech UI with deep navy and royal blue styling, platform statistics, and an intuitive "Start My Complaint" journey.
- Educational primer on the 4-stage escalation matrix under the **Consumer Protection Act, 2019** (Company Support ➔ Grievance Officer ➔ National Consumer Helpline 1915 ➔ e-Daakhil).

### 2. 🔍 11-Parameter Complaint Understanding Engine
Extracts 11 structured fields directly from spoken or written statements:
1. Customer Name
2. Seller / Company Name
3. Product / Service Name
4. Purchase Date
5. Delivery / Discovery Date
6. Order ID / Support Reference
7. Purchase Amount (in ₹ INR)
8. Complaint Category (e.g. Damaged on Delivery, Delayed Refund)
9. Problem Narrative
10. Seller Commitments & SLA
11. Refund / Resolution Status & Remedy Sought

### 3. ❓ Zero-Hallucination Follow-Up Inquiries
If any critical piece of information is missing from the consumer's spoken narrative, the AI **never** guesses or invents facts. Instead, it displays an alert with targeted follow-up inquiries so the consumer can provide the missing details.

### 4. 📁 Evidence Management & Validation
- Multi-file drag-and-drop supporting PDF, PNG, JPG, JPEG.
- Categorization tags: *Tax Invoice*, *Damage Photograph*, *Customer Support Chat Transcript*, *Logistics Handover Slip*, *Warranty Document*.
- Explicit visual separation between **"User-Provided Statements"** (unverified consumer narrative) and **"Documented Evidence Artifacts"** (objective documents).

### 5. 🎯 Case Builder & Completeness Engine
- Dynamic **Dossier Completeness Score (0 to 100%)** providing an objective checklist of case preparation.
- **Visual Dispute Progress Bar** tracking stages from evidence documentation to final resolution.
- Interactive chronological milestone logger for ongoing updates.

### 6. 📜 4-in-1 Formal Grievance Letter Generator
Generates 4 tailored legal-tech grievance formats in **English**, **Hindi**, and **Kannada**:
1. **Seller Customer Support Email**: Direct, concise resolution request.
2. **Formal Legal Grievance Notice**: Structured representation with 7-day cure period.
3. **Executive / Nodal Grievance Officer Escalation Letter**: Level-2 escalation under Rule 4 of the *Consumer Protection (E-Commerce) Rules, 2020*.
4. **National Consumer Helpline (NCH / INGRAM) Draft**: Pre-formatted under 1000 characters for direct copy-pasting into `consumerhelpline.gov.in`.

### 7. 📑 Downloadable Case Dossier (PDF & HTML)
- **Official PDF Dossier (ReportLab):** Generates a downloadable PDF containing the cover header, transaction particulars, chronology table, evidence index, and redressal guide.
- **Printable HTML Dossier:** One-click browser print layout with `window.print()` integration.
- **JSON Backup:** One-click export of all case records for offline archival.

### 8. 🔒 Security, Authentication & Local SQLite Persistence
- Self-contained local **SQLite database** (`case_resolution.db`).
- Cryptographic password hashing using **PBKDF2 with SHA-256** and per-user unique salt.
- Full multi-user isolation (users only see and edit their own private cases).
- Zero secret exposure: `.env` is excluded via `.gitignore`.

---

## 🧪 Automated Test Suite (13 Tests Passing)

The project includes an automated test suite verifying all components:
```bash
python test_app.py
```
Output:
```
Ran 13 tests in 1.221s — OK (All tests passing)
```

---

## 🛠️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/rajatsinghbhau/CaseResolutionAI.git
cd CaseResolutionAI
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Your Environment
Create a `.env` file in the root directory (based on `.env.example`):
```ini
GNANI_API_KEY=your_official_gnani_api_key_here
```

### 4. Run the Application
```bash
streamlit run app.py
```
Open **`http://localhost:8501`** in your browser.

---

## 📂 Project Architecture

```
CaseResolutionAI/
├── app.py                  # Main Streamlit web application & user interface
├── db_service.py           # SQLite database persistence & PBKDF2 authentication
├── gnani_service.py        # Official Gnani AI Prisma STT & 11-field extraction engine
├── letter_service.py       # 4-in-1 grievance notice generator (English, Hindi, Kannada)
├── dossier_pdf_service.py  # ReportLab professional PDF Case Dossier generator
├── case_store.py           # Data structures, readiness engine & preloaded laptop case
├── test_app.py             # 13 automated unit tests
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
├── .gitignore              # Ignores .env, database, and uploads
└── README.md               # Complete project documentation & challenge submission details
```

---

*CaseResolutionAI — Empowering everyday consumers across India with structured, evidence-backed dispute resolution.*
