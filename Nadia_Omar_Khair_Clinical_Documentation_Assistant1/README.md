# Clinical Documentation Assistant

## Project Overview

A generative AI application that helps healthcare professionals summarize patient notes and draft clinical reports to reduce administrative burden. The system uses advanced language models with safety mechanisms to ensure responsible AI deployment in healthcare.

**Student:** Nadia Omar Khair  
**Course:** Generative AI (YGA Upskilling Program)  
**Date:** January 31, 2026  
**Institution:** Al Hussein Technical University

---

## Project Structure

```
clinical-documentation-assistant/
│
├── app.py                          # Flask web application
├── backend.py                      # Processing logic & AI integration
├── requirements.txt                # Python dependencies
├── run.bat                         # Windows run script
├── run.sh                          # Linux/Mac run script
│
├── templates/
│   └── index.html                 # Frontend interface
│
├── CLINICAL_DOC_ASSISTANT/         # Package directory
│   └── __pycache__/               # Python cache
│
├── README.md                       # Project documentation
├── .env                            # Environment variables (not committed)
├── .gitignore                      # Git ignore rules
├── SETUP_INTEGRATED.md             # Setup instructions
│
└── docs/
    ├── TECHNICAL_REPORT.pdf       # Detailed technical documentation
    ├── TEST_CASES.pdf             # Comprehensive test cases
    ├── SAFETY_FRAMEWORK.pdf       # Escalation triggers & safety
    ├── ARCHITECTURE.png           # System architecture diagram
    └── USER_FLOW.png              # User flow diagram
```

---

## Key Features

### 1. **AI-Powered Summarization**
- Uses GitHub Models API (GPT-4o mini) for medical text summarization
- Generates structured clinical summaries from raw notes
- Prevents diagnostic claims and maintains professional boundaries

### 2. **Privacy & Security**
- De-identifies clinical text (removes names, IDs, locations, SSNs)
- HIPAA-like privacy compliance
- Comprehensive audit trails for all operations

### 3. **Safety Mechanisms**
- 5 escalation triggers for critical situations
- Red flag detection for emergency symptoms
- Hallucination prevention with content validation
- Confidence scoring for output quality

### 4. **Data Processing Pipeline**
- Abbreviation expansion (50+ medical abbreviations)
- PII removal and de-identification
- Clinical section extraction (7 sections)
- Standardized output formatting

### 5. **Comprehensive Testing**
- 19 test cases with 100% pass rate
- Input validation, data processing, safety, and output quality tests
- Evaluation metrics for accuracy and reliability

---

## Installation & Setup

### Prerequisites
- Python 3.8+
- Flask
- GitHub Models API access

### Installation Steps

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   Create a `.env` file with:
   ```
   GITHUB_TOKEN=your_github_token_here
   FLASK_ENV=development
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

4. **Access the web interface:**
   Open your browser and navigate to `http://localhost:5000`

---

## Usage

### Basic Workflow

1. **Enter Clinical Note:** Paste raw clinical documentation in the input area
2. **System Processing:** 
   - Validates input (checks for diagnostic questions)
   - De-identifies patient information
   - Expands medical abbreviations
   - Extracts clinical sections
3. **AI Summarization:** Generates structured summary using LLM
4. **Safety Checks:** Detects red flags and validates output
5. **View Results:** Display summary with confidence scores and alerts

### Example Input
```
Pt Profile: 52yo male. HPI: severe chest pain for 30 minutes, radiating to left arm.
PMH: HTN, high cholesterol. Notes: patient appears anxious.
```

### Example Output
```
CLINICAL SUMMARY
Patient Demographics: 52-year-old male
Chief Complaint: Severe chest pain with radiation pattern
Medical History: Hypertension, high cholesterol
Observations: Patient appears anxious

⚠️ CRITICAL SYMPTOMS DETECTED
Chest pain with radiation pattern suggests possible cardiac event.
🏥 Seek immediate medical attention.
```

---

## Safety Framework

### 5 Escalation Triggers

| Trigger | Severity | Action |
|---------|----------|--------|
| **T-001: Diagnostic Question** | 🔴 Critical | Block processing + Red alert |
| **T-002: Critical Red Flags** | 🔴 Critical | Continue + Orange warning |
| **T-003: High Uncertainty** | 🟡 High | Continue + Yellow warning |
| **T-004: Hallucination Risk** | 🟡 High | Continue + Blue info |
| **T-005: API Failure** | 🟠 Medium | Fallback mode + Gray info |

### Red Flag Categories
- **Cardiovascular:** Chest pain, heart attack, severe palpitations
- **Respiratory:** Severe shortness of breath, acute respiratory distress
- **Neurological:** Loss of consciousness, stroke symptoms, seizures
- **Trauma:** Severe bleeding, head trauma, spinal injury
- **Allergic:** Anaphylaxis, severe allergic reactions

---

## Test Results

**Total Test Cases:** 19  
**Pass Rate:** 100%  
**Categories:**
- Input Validation: 5/5 ✅
- Data Processing: 5/5 ✅
- Safety & Compliance: 5/5 ✅
- Output Quality: 4/4 ✅

---

## Technical Stack

- **Backend:** Flask (Python)
- **Frontend:** HTML5, CSS3, JavaScript
- **AI Model:** GitHub Models API (GPT-4o mini)
- **Data Processing:** Pure Python
- **Environment:** Windows 10, VS Code

---

## Learning Outcomes Achieved

✅ **LO1:** Apply and adapt pre-trained generative models  
✅ **LO2:** Prepare and manage data pipelines  
✅ **LO3:** Design effective prompts and strategies  
✅ **LO4:** Evaluate model performance and optimize  
✅ **LO5:** Apply ethical guidelines and best practices  

---

## Limitations & Future Work

### Current Limitations
- Section extraction finds 5-6 out of 7 sections on average
- Abbreviation dictionary contains 50+ abbreviations
- Red flag detection uses keyword matching
- 5000-character input limit

### Future Enhancements
- Expand abbreviation dictionary (100+ more abbreviations)
- Improve section recognition (support more clinical note formats)
- ML-based red flag detection instead of keyword matching
- Multi-language support (Spanish, French, German)
- Vector database integration (FAISS for semantic search)
- Mobile app (iOS/Android)
- EHR system integration

---

## Ethical Considerations

This system is designed with strict ethical guidelines:

1. **No Diagnostic Advice:** System explicitly prevents diagnostic claims
2. **Privacy First:** All patient identifiers are removed
3. **Transparency:** Users are informed of system limitations
4. **Audit Trails:** All operations are logged for compliance
5. **Safety Disclaimers:** Clear warnings on all outputs

---

## Documentation

- **Technical Report:** See `REPORTS/02_TECHNICAL_REPORT_PERSONALIZED.pdf`
- **Test Cases:** See `REPORTS/03_TEST_CASES_AND_EVALUATION.pdf`
- **Safety Framework:** See `REPORTS/05_ESCALATION_TRIGGERS_AND_PATHS.pdf`

---

## Contact & Support

**Student:** Nadia Omar Khair  
**Course:** Generative AI  
**Institution:** Al Hussein Technical University  
**Date:** January 31, 2026

---

## License

This project is submitted as part of the YGA Upskilling Program at Al Hussein Technical University.

---

**Status:** Production-Ready ✅  

