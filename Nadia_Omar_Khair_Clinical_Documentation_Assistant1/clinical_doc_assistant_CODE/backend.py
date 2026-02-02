"""
Clinical Documentation Assistant - Windows-Compatible Backend v3.3
FIXED: Section extraction without capturing next marker labels
"""

import os
import re
import json
import time
import requests
from typing import Dict, Tuple, List, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================
# ABBREVIATIONS DICTIONARY
# ============================================
ABBREVIATIONS = {
    "pt": "patient", "hx": "history", "dx": "diagnosis", "tx": "treatment",
    "rx": "prescription", "sx": "symptoms", "bp": "blood pressure",
    "hr": "heart rate", "rr": "respiratory rate", "temp": "temperature",
    "yo": "year old", "c/o": "complaining of", "s/p": "status post",
    "w/": "with", "w/o": "without", "sob": "shortness of breath",
    "cp": "chest pain", "abd": "abdominal", "htn": "hypertension",
    "dm": "diabetes mellitus", "cad": "coronary artery disease",
    "chf": "congestive heart failure", "copd": "chronic obstructive pulmonary disease",
    "uti": "urinary tract infection", "bid": "twice daily", "tid": "three times daily",
    "qid": "four times daily", "prn": "as needed", "po": "by mouth",
    "iv": "intravenous", "im": "intramuscular", "npo": "nothing by mouth",
    "wbc": "white blood cell", "rbc": "red blood cell", "hgb": "hemoglobin",
    "plt": "platelets", "bmp": "basic metabolic panel", "cbc": "complete blood count",
    "ekg": "electrocardiogram", "cxr": "chest x-ray", "ct": "computed tomography",
    "mri": "magnetic resonance imaging", "hpi": "history of present illness",
    "pmh": "past medical history", "psh": "past surgical history", "fhx": "family history",
    "pe": "physical examination", "yo": "year old", "yoa": "year old adult"
}

# ============================================
# ICD-10 REFERENCE DATABASE
# ============================================
ICD10_CODES = {
    "diabetes mellitus": "E11.9",
    "hypertension": "I10",
    "chest pain": "R07.9",
    "shortness of breath": "R06.02",
    "fever": "R50.9",
    "fatigue": "R53.83",
    "abdominal pain": "R10.9",
    "headache": "R51.9",
    "cough": "R05.9",
    "nausea": "R11.0",
    "vomiting": "R11.10",
    "diarrhea": "K59.1",
    "constipation": "K59.0",
    "back pain": "M54.5",
    "joint pain": "M25.5",
    "anxiety": "F41.9",
    "depression": "F32.9",
    "insomnia": "G47.00",
    "asthma": "J45.9",
    "pneumonia": "J18.9",
    "urinary tract infection": "N39.0",
    "gastroesophageal reflux": "K21.9",
    "migraine": "G43.9",
    "allergic rhinitis": "J30.9",
    "sinusitis": "J32.9",
    "bronchitis": "J20.9",
    "pharyngitis": "J02.9"
}

# ============================================
# GITHUB MODELS API CONFIGURATION
# ============================================
GITHUB_TOKEN = os.getenv("GITHUB_MODELS_TOKEN", "")
MODEL_ID = os.getenv("MODEL_ID", "gpt-4o-mini")
GITHUB_API_URL = os.getenv("GITHUB_API_URL", "https://models.inference.ai.azure.com/chat/completions")

# ============================================
# RAG KNOWLEDGE BASE
# ============================================
RAG_KNOWLEDGE_BASE = [
    {
        "id": "policy_001",
        "title": "Safety Policy",
        "content": "The AI assistant must NOT provide medical diagnosis or treatment advice. Only document and summarize existing clinical information.",
        "keywords": ["safety", "diagnosis", "advice", "document", "summarize"]
    },
    {
        "id": "policy_002",
        "title": "Red Flag Escalation",
        "content": "Red flag symptoms requiring immediate clinician notification: chest pain, shortness of breath, signs of stroke, severe bleeding, loss of consciousness.",
        "keywords": ["red flag", "chest pain", "shortness of breath", "stroke", "bleeding", "consciousness"]
    },
    {
        "id": "policy_003",
        "title": "Documentation Standards",
        "content": "All summaries must use neutral, professional language. Include disclaimer that this is for documentation support only.",
        "keywords": ["documentation", "standards", "professional", "language", "disclaimer"]
    },
    {
        "id": "policy_004",
        "title": "SOAP Note Format",
        "content": "Standard format: S (Subjective - patient reported), O (Objective - measured data), A (Assessment - clinical findings), P (Plan - next steps).",
        "keywords": ["SOAP", "subjective", "objective", "assessment", "plan", "format"]
    },
    {
        "id": "policy_005",
        "title": "PII Protection",
        "content": "Always de-identify patient information: remove names, email addresses, phone numbers, medical record numbers, and social security numbers.",
        "keywords": ["PII", "de-identify", "privacy", "names", "email", "phone", "SSN"]
    },
    {
        "id": "policy_006",
        "title": "Abbreviation Standards",
        "content": "Expand all medical abbreviations for clarity: BP (blood pressure), HR (heart rate), DM (diabetes mellitus), HTN (hypertension).",
        "keywords": ["abbreviation", "expand", "BP", "HR", "DM", "HTN", "clarity"]
    }
]

DISCLAIMER = "This output is for informational purposes only. Not for diagnosis or treatment advice. Always consult with qualified healthcare professionals."

# ============================================
# AUDIT TRAIL SYSTEM
# ============================================
class AuditTrail:
    def __init__(self):
        self.events = []
    
    def log_event(self, event_type: str, details: Dict, status: str = "success"):
        """Log an operation event"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "details": details,
            "status": status
        }
        self.events.append(event)
    
    def get_trail(self):
        """Get complete audit trail"""
        return self.events
    
    def get_summary(self):
        """Get audit trail summary"""
        return {
            "total_events": len(self.events),
            "event_types": list(set(e["type"] for e in self.events)),
            "success_count": sum(1 for e in self.events if e["status"] == "success"),
            "error_count": sum(1 for e in self.events if e["status"] == "error"),
            "start_time": self.events[0]["timestamp"] if self.events else None,
            "end_time": self.events[-1]["timestamp"] if self.events else None
        }

# ============================================
# SIMPLE RAG SYSTEM
# ============================================
class SimpleRAGSystem:
    def __init__(self):
        self.documents = RAG_KNOWLEDGE_BASE
    
    def retrieve_relevant_docs(self, query: str, top_k: int = 3) -> List[Dict]:
        """Retrieve relevant documents using keyword matching"""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        scored_docs = []
        for doc in self.documents:
            score = 0
            doc_content_lower = doc["content"].lower()
            for word in query_words:
                if word in doc_content_lower:
                    score += 2
            
            for keyword in doc["keywords"]:
                if keyword in query_lower:
                    score += 3
            
            if score > 0:
                scored_docs.append((doc, score))
        
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for doc, score in scored_docs[:top_k]:
            results.append({
                "document": doc,
                "score": min(score / 10.0, 1.0),
                "citation": f"[Policy {doc['id']}]"
            })
        return results

# ============================================
# METRICS CALCULATION
# ============================================
class MetricsCalculator:
    @staticmethod
    def calculate_rouge_score(reference: str, candidate: str) -> float:
        """Calculate simplified ROUGE-L score"""
        ref_words = set(reference.lower().split())
        cand_words = set(candidate.lower().split())
        
        if len(ref_words) == 0 or len(cand_words) == 0:
            return 0.0
        
        overlap = len(ref_words & cand_words)
        precision = overlap / len(cand_words) if len(cand_words) > 0 else 0
        recall = overlap / len(ref_words) if len(ref_words) > 0 else 0
        
        if precision + recall == 0:
            return 0.0
        
        f1 = 2 * (precision * recall) / (precision + recall)
        return round(f1, 3)
    
    @staticmethod
    def calculate_bleu_score(reference: str, candidate: str) -> float:
        """Calculate simplified BLEU score (1-gram)"""
        ref_words = reference.lower().split()
        cand_words = candidate.lower().split()
        
        if len(cand_words) == 0:
            return 0.0
        
        matches = sum(1 for word in cand_words if word in ref_words)
        return round(matches / len(cand_words), 3)
    
    @staticmethod
    def calculate_confidence_explanation(sections_found: int, 
                                        has_red_flags: bool,
                                        has_hallucinations: bool,
                                        rag_score: float) -> Dict:
        """Generate detailed confidence explanation"""
        factors = []
        confidence_score = 0.5
        
        section_factor = min(sections_found / 7, 1.0) * 0.3
        confidence_score += section_factor
        factors.append({
            "factor": "Section Completeness",
            "value": f"{sections_found}/7 sections found",
            "contribution": f"+{round(section_factor, 2)}"
        })
        
        if not has_hallucinations:
            safety_factor = 0.2
            confidence_score += safety_factor
            factors.append({
                "factor": "Safety Check",
                "value": "No hallucinations detected",
                "contribution": f"+{safety_factor}"
            })
        else:
            factors.append({
                "factor": "Safety Check",
                "value": "Hallucinations detected",
                "contribution": "-0.2"
            })
            confidence_score -= 0.2
        
        if has_red_flags:
            red_flag_factor = -0.1
            confidence_score += red_flag_factor
            factors.append({
                "factor": "Red Flags",
                "value": "Red flags present - requires attention",
                "contribution": f"{red_flag_factor}"
            })
        
        rag_factor = rag_score * 0.2
        confidence_score += rag_factor
        factors.append({
            "factor": "RAG Grounding",
            "value": f"Knowledge base match: {round(rag_score, 2)}",
            "contribution": f"+{round(rag_factor, 2)}"
        })
        
        confidence_score = min(max(confidence_score, 0.0), 1.0)
        
        return {
            "overall_confidence": round(confidence_score, 2),
            "factors": factors,
            "explanation": f"Confidence is {round(confidence_score * 100)}% based on section completeness ({sections_found}/7), safety checks, and knowledge base grounding."
        }

# ============================================
# UTILITY FUNCTIONS
# ============================================

def check_for_diagnostic_question(text: str) -> bool:
    """Check if user is asking for diagnosis instead of providing clinical notes"""
    diagnostic_patterns = [
        # Diagnosis-related questions
        r"what\s+is\s+(?:the\s+)?diagnos[ie]s?",
        r"what\s+are\s+the\s+diagnos[ie]s?",
        r"what\s+diagnos[ie]s?",
        r"\bdiagnos[ie]s?\b.*\?",
        r"my\s+diagnos[ie]s?",
        r"what\s+is\s+my\s+diagnos[ie]s?",
        
        # Disease-related questions (NEW)
        r"what\s+is\s+(?:the\s+)?disease",
        r"what\s+are\s+(?:the\s+)?diseases",
        r"what\s+disease\s+do\s+i\s+have",
        r"what\s+diseases\s+do\s+i\s+have",
        r"my\s+disease",
        r"my\s+diseases",
        r"what\s+is\s+my\s+disease",
        r"what\s+is\s+my\s+diseases",
        r"\bdisease\b.*\?",
        r"\bdiseases\b.*\?",
        
        # Condition-related questions
        r"what\s+is\s+(?:the\s+)?condition",
        r"what\s+are\s+(?:the\s+)?conditions",
        r"what\s+condition\s+do\s+i\s+have",
        r"what\s+conditions\s+do\s+i\s+have",
        r"my\s+condition",
        r"my\s+conditions",
        r"what\s+is\s+my\s+condition",
        r"what\s+is\s+my\s+conditions",
        r"\bcondition\b.*\?",
        r"\bconditions\b.*\?",
        
        # Illness-related questions
        r"what\s+is\s+(?:the\s+)?illness",
        r"what\s+are\s+(?:the\s+)?illnesses",
        r"what\s+illness\s+do\s+i\s+have",
        r"what\s+illnesses\s+do\s+i\s+have",
        r"my\s+illness",
        r"my\s+illnesses",
        r"what\s+is\s+my\s+illness",
        r"what\s+is\s+my\s+illnesses",
        r"\billness\b.*\?",
        r"\billnesses\b.*\?",
        
        # Disorder-related questions
        r"what\s+is\s+(?:the\s+)?disorder",
        r"what\s+are\s+(?:the\s+)?disorders",
        r"my\s+disorder",
        r"my\s+disorders",
        r"what\s+is\s+my\s+disorder",
        r"what\s+is\s+my\s+disorders",
        r"\bdisorder\b.*\?",
        r"\bdisorders\b.*\?",
        
        # Syndrome-related questions
        r"what\s+is\s+(?:the\s+)?syndrome",
        r"what\s+are\s+(?:the\s+)?syndromes",
        r"my\s+syndrome",
        r"my\s+syndromes",
        r"what\s+is\s+my\s+syndrome",
        r"what\s+is\s+my\s+syndromes",
        r"\bsyndrome\b.*\?",
        r"\bsyndromes\b.*\?",
        
        # Ailment-related questions
        r"what\s+is\s+(?:the\s+)?ailment",
        r"what\s+are\s+(?:the\s+)?ailments",
        r"my\s+ailment",
        r"my\s+ailments",
        r"what\s+is\s+my\s+ailment",
        r"what\s+is\s+my\s+ailments",
        r"\bailment\b.*\?",
        r"\bailments\b.*\?",
        
        # General medical questions
        r"what\s+do\s+i\s+have",
        r"diagnose\s+me",
        r"what\s+is\s+wrong\s+with\s+me",
        r"what\s+should\s+i\s+take",
        r"what\s+medication\s+should\s+i\s+take",
        r"should\s+i\s+take",
        r"what\s+treatment\s+do\s+i\s+need",
        r"what\s+should\s+i\s+do",
        r"am\s+i\s+sick",
        r"do\s+i\s+have",
        r"is\s+this\s+serious",
        r"is\s+this\s+dangerous",
        r"will\s+i\s+be\s+okay",
        r"how\s+long\s+will\s+i\s+live",
        r"is\s+it\s+cancer",
        r"is\s+it\s+covid",
        r"should\s+i\s+see",
        r"should\s+i\s+go",
        r"should\s+i\s+visit",
        r"what\s+doctor",
        r"what\s+specialist",
        r"what\s+medicine",
        r"what\s+drug",
        r"what\s+cure",
        r"how\s+to\s+treat",
        r"how\s+to\s+cure",
        r"how\s+to\s+fix"
    ]
    
    text_lower = text.lower()
    for pattern in diagnostic_patterns:
        if re.search(pattern, text_lower):
            return True
    return False

def expand_abbreviations(note: str) -> str:
    """Expand medical abbreviations in clinical notes"""
    if not isinstance(note, str):
        return ""
    
    expanded = note
    for abbr, full in ABBREVIATIONS.items():
        pattern = rf'\b{re.escape(abbr)}\b'
        expanded = re.sub(pattern, full, expanded, flags=re.IGNORECASE)
    return expanded

def deidentify_text(text: str) -> str:
    """Remove PII from text"""
    if not isinstance(text, str):
        return ""
    
    text = re.sub(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', '[REDACTED_EMAIL]', text)
    text = re.sub(r'\b(\+?\d{1,3}[-.\s]?)?(\(?\d{2,3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b', 
                  '[REDACTED_PHONE]', text)
    text = re.sub(r'\b(MRN|ID|PatientID|PID)[:\s-]*[A-Za-z0-9]+\b', 
                  '[REDACTED_ID]', text, flags=re.IGNORECASE)
    text = re.sub(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', '[PATIENT]', text)
    
    return text

def check_for_hallucinations(text: str) -> bool:
    """Check if text contains diagnostic language (hallucinations)"""
    forbidden_patterns = [
        "diagnosed with",
        "suffering from",
        "patient has",
        "treatment is",
        "recommend",
        "suggests",
        "prescribe",
        "medication should"
    ]
    
    text_lower = text.lower()
    for pattern in forbidden_patterns:
        if pattern in text_lower:
            return True
    return False

def check_for_red_flags(text: str) -> List[str]:
    """Check for red flag symptoms that need escalation"""
    red_flags = [
        "chest pain",
        "shortness of breath",
        "stroke",
        "severe bleeding",
        "loss of consciousness",
        "difficulty breathing"
    ]
    
    text_lower = text.lower()
    found_flags = [flag for flag in red_flags if flag in text_lower]
    return found_flags

def extract_icd10_codes(note: str) -> List[Dict]:
    """Extract relevant ICD-10 codes from clinical note"""
    note_lower = note.lower()
    found_codes = []
    
    for condition, code in ICD10_CODES.items():
        if condition in note_lower:
            found_codes.append({
                "condition": condition,
                "icd10_code": code,
                "description": f"{condition.title()} - {code}"
            })
    
    return found_codes

def call_github_models_api(prompt: str, max_tokens: int = 500, retries: int = 3) -> str:
    """Call GitHub Models API with retry logic"""
    
    if not GITHUB_TOKEN:
        return "GitHub Models API token not configured."
    
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messages": [
            {"role": "system", "content": "You are a clinical documentation specialist. Provide summaries only, no diagnosis."},
            {"role": "user", "content": prompt}
        ],
        "model": MODEL_ID,
        "temperature": 0.3,
        "max_tokens": max_tokens
    }
    
    for attempt in range(retries):
        try:
            response = requests.post(GITHUB_API_URL, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                return "Error: Unexpected API response format"
                
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            else:
                return f"API Error after {retries} retries: {str(e)}"
    
    return "Failed to get response from GitHub Models API"

def clean_generic_descriptors(text: str) -> str:
    """Remove generic age descriptors like young adult, middle-aged adult, etc."""
    text = re.sub(r'\b(young|middle-aged|elderly|old)\s+adult\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\badult\b', '', text, flags=re.IGNORECASE)
    return text.strip()

def hybrid_summarize_with_rag(expanded_note: str, rag_system, sections: Dict = None) -> tuple:
    """Hybrid summarization using role-based prompting and RAG"""
    
    relevant_docs = rag_system.retrieve_relevant_docs(expanded_note, top_k=3)
    
    context = "Relevant Policies:\n"
    citations = []
    for doc_result in relevant_docs:
        doc = doc_result["document"]
        context += f"- {doc['title']}: {doc['content']}\n"
        citations.append({
            "source": doc["id"],
            "title": doc["title"],
            "relevance_score": doc_result["score"]
        })
    
    # Build demographics string for the prompt
    demographics_str = ""
    if sections and sections.get('demographics') and sections['demographics'] != "Not available":
        demographics_str = f"Patient Demographics: {sections['demographics']}\n"
    
    prompt = f"""{context}

You are a Clinical Documentation Specialist with 15+ years of experience.

Your task is to summarize clinical notes into a professional, structured format.

STRICT RULES: 
- Only extract stated facts
- NO diagnoses
- NO treatments  
- NO interpretations
- If patient demographics are provided, use them EXACTLY as stated in the summary
- Do NOT reformat or reinterpret the demographics

{demographics_str}
Current Note:
{expanded_note}

Provide a structured summary with the following format:
**Patient Demographics:** {sections.get('demographics', 'Not available') if sections else 'Not available'}
**History of Present Illness:** [extract from note]
**Past Medical History:** [extract from note]
**Family History:** [extract from note]
**Notes:** [extract from note]

Professional Summary:"""
    
    summary = call_github_models_api(prompt)
    return summary, citations

def extract_sections(note: str) -> Dict[str, str]:
    """
    Extract clinical sections using improved approach
    FIXED: Only extract content immediately after each marker, not including next marker
    """
    
    sections = {
        "demographics": "Not available",
        "chief_complaint": "Not available",
        "medical_history": "Not available",
        "medications": "Not available",
        "allergies": "Not available",
        "vital_signs": "Not available",
        "observations": "Not available"
    }
    
    # Define section markers with their section types
    markers = [
        (r'pt\s+profile', "demographics"),
        (r'demographics', "demographics"),
        (r'hpi', "chief_complaint"),
        (r'history\s+of\s+present\s+illness', "chief_complaint"),
        (r'chief\s+complaint', "chief_complaint"),
        (r'cc\b', "chief_complaint"),
        (r'presenting\s+complaint', "chief_complaint"),
        (r'pmh', "medical_history"),
        (r'past\s+medical\s+history', "medical_history"),
        (r'psh', "medical_history"),
        (r'past\s+surgical\s+history', "medical_history"),
        (r'fhx', "medical_history"),
        (r'family\s+history', "medical_history"),
        (r'medications', "medications"),
        (r'meds\b', "medications"),
        (r'allergies', "allergies"),
        (r'allergy\b', "allergies"),
        (r'nkda', "allergies"),
        (r'vital\s+signs', "vital_signs"),
        (r'vs\b', "vital_signs"),
        (r'vitals', "vital_signs"),
        (r'pe\b', "observations"),
        (r'physical\s+exam', "observations"),
        (r'physical\s+examination', "observations"),
        (r'observations', "observations"),
        (r'findings', "observations"),
        (r'notes\b', "observations"),
    ]
    
    text_lower = note.lower()
    
    # Find all marker positions
    marker_positions = []
    for pattern, section_type in markers:
        for match in re.finditer(pattern, text_lower):
            marker_positions.append({
                'start': match.start(),
                'end': match.end(),
                'section': section_type,
                'marker': match.group(0)
            })
    
    # Sort by position
    marker_positions.sort(key=lambda x: x['start'])
    
    # Extract content for each marker
    for i, marker_info in enumerate(marker_positions):
        section_type = marker_info['section']
        content_start = marker_info['end']
        
        # Find where content ends (at next marker or end of text)
        if i + 1 < len(marker_positions):
            content_end = marker_positions[i + 1]['start']
        else:
            content_end = len(note)
        
        # Extract content
        content = note[content_start:content_end].strip()
        
        # Remove leading punctuation/colons
        content = re.sub(r'^[\s:;,.-]+', '', content)
        
        # Remove trailing punctuation but keep period if it's end of sentence
        content = re.sub(r'[\s:;,.-]+$', '', content)
        
        # Limit content length to avoid huge sections
        if len(content) > 150:
            # Find last space before 150 chars
            truncated = content[:150]
            last_space = truncated.rfind(' ')
            if last_space > 0:
                content = truncated[:last_space] + "..."
            else:
                content = truncated + "..."
        
        # Only add if content is not empty and meaningful
        if content and len(content) > 2 and content != "Not available":
            # Don't overwrite if already found from earlier marker
            if sections[section_type] == "Not available":
                sections[section_type] = content
    
    # Special handling for demographics - extract age descriptor and gender
    # Try to find Pt Profile in the text
    pt_profile_match = re.search(r'(?:\[PATIENT\]|pt|patient)\s*(?:profile)?\s*:?\s*([^.]+)', note, flags=re.IGNORECASE)
    if pt_profile_match:
        profile_text = pt_profile_match.group(1).strip()
        
        # Remove extra spaces left by clean_generic_descriptors
        profile_text = re.sub(r'\s+', ' ', profile_text).strip()
        
        # If profile_text is too short (only age), it was cleaned too much
        if len(profile_text) < 5:
            # Try to extract from text_lower which might have original content
            age_match = re.search(r'(\d+)\s*(?:year|yo|y\.o\.)', text_lower)
            if age_match:
                age = age_match.group(1)
                # Look for age descriptor nearby
                age_context = note[max(0, age_match.start()-20):age_match.end()+50].lower()
                
                gender = None
                if 'female' in age_context or 'woman' in age_context:
                    gender = "female"
                elif 'male' in age_context or 'man' in age_context:
                    gender = "male"
                
                # Try to extract age descriptor
                descriptor_match = re.search(r'(\w+\s+)?\d+\s*(?:year|yo)', note, flags=re.IGNORECASE)
                if descriptor_match:
                    desc_text = descriptor_match.group(0)
                    if gender:
                        sections["demographics"] = f"{desc_text} - Gender: {gender}"
                    else:
                        sections["demographics"] = f"{desc_text} - Gender: Not mentioned"
        else:
            # Profile text is intact
            gender = None
            if 'female' in profile_text.lower() or 'woman' in profile_text.lower():
                gender = "female"
            elif 'male' in profile_text.lower() or 'man' in profile_text.lower():
                gender = "male"
            
            if gender:
                sections["demographics"] = f"{profile_text} - Gender: {gender}"
            else:
                sections["demographics"] = f"{profile_text} - Gender: Not mentioned"
    
    # Special handling for allergies
    if re.search(r'no\s+(?:known\s+)?allergies|nkda', text_lower):
        sections["allergies"] = "No known allergies"
    
    return sections

# ============================================
# MAIN SUMMARIZATION FUNCTION
# ============================================

def summarize_clinical_note(clinical_note: str) -> Dict:
    """
    Main function to summarize clinical notes with all features
    Windows-compatible version (no scikit-learn)
    FIXED: Proper section extraction without capturing next marker labels
    """
    
    audit_trail = AuditTrail()
    rag_system = SimpleRAGSystem()
    metrics = MetricsCalculator()
    
    audit_trail.log_event("summarization_started", {"note_length": len(clinical_note)})
    
    # CHECK FOR DIAGNOSTIC QUESTIONS FIRST
    if check_for_diagnostic_question(clinical_note):
        audit_trail.log_event("diagnostic_question_detected", {"note": clinical_note[:50]})
        return {
            "success": False,
            "is_diagnostic_question": True,
            "error": "This tool is for SUMMARIZING existing clinical notes only, not for providing medical diagnosis or treatment advice.",
            "message": "Please consult a qualified healthcare professional for medical advice.",
            "suggestion": "This summarizer is designed to help organize and document clinical notes that have already been written. It cannot provide medical diagnosis or treatment recommendations."
        }
    
    # Length validation
    if not clinical_note or len(clinical_note) < 10:
        audit_trail.log_event("validation_failed", {"reason": "note_too_short"}, "error")
        return {
            "success": False,
            "error": "Note too short (minimum 10 characters)"
        }
    
    if len(clinical_note) > 5000:
        audit_trail.log_event("validation_failed", {"reason": "note_too_long"}, "error")
        return {
            "success": False,
            "error": "Note too long (maximum 5000 characters)"
        }
    
    try:
        # Step 1: De-identify
        audit_trail.log_event("deidentification", {"original_length": len(clinical_note)})
        deidentified = deidentify_text(clinical_note)
        
        # Step 2: Expand abbreviations
        audit_trail.log_event("abbreviation_expansion", {"abbreviations_found": len([a for a in ABBREVIATIONS if a in clinical_note.lower()])})
        expanded = expand_abbreviations(deidentified)
        
        # Step 3: Extract sections (FIXED)
        audit_trail.log_event("section_extraction", {})
        sections = extract_sections(expanded)
        sections_found = sum(1 for v in sections.values() if v != "Not available")
        
        # Step 4: Extract ICD-10 codes
        audit_trail.log_event("icd10_extraction", {})
        icd10_codes = extract_icd10_codes(clinical_note)
        
        # Step 5: Check for red flags
        audit_trail.log_event("red_flag_detection", {})
        red_flags = check_for_red_flags(clinical_note)
        
        # Step 6: Generate AI summary with RAG
        audit_trail.log_event("ai_summarization", {"rag_enabled": True})
        ai_summary = ""
        rag_citations = []
        rag_score = 0.0
        
        if GITHUB_TOKEN:
            ai_summary, rag_citations = hybrid_summarize_with_rag(expanded, rag_system, sections)
            rag_score = sum(c["relevance_score"] for c in rag_citations) / len(rag_citations) if rag_citations else 0.0
        
        # Step 7: Check for hallucinations
        audit_trail.log_event("hallucination_check", {})
        has_hallucinations = check_for_hallucinations(ai_summary) if ai_summary else False
        
        # Step 8: Calculate metrics
        audit_trail.log_event("metrics_calculation", {})
        rouge_score = metrics.calculate_rouge_score(clinical_note, ai_summary) if ai_summary else 0.0
        bleu_score = metrics.calculate_bleu_score(clinical_note, ai_summary) if ai_summary else 0.0
        
        # Step 9: Generate confidence explanation
        audit_trail.log_event("confidence_calculation", {})
        confidence_data = metrics.calculate_confidence_explanation(
            sections_found,
            len(red_flags) > 0,
            has_hallucinations,
            rag_score
        )
        
        # Step 10: Finalize with disclaimer
        final_summary = ai_summary + f"\n\n**DISCLAIMER:** {DISCLAIMER}" if ai_summary else ""
        
        audit_trail.log_event("summarization_completed", {"success": True})
        
        return {
            "success": True,
            "original_note": clinical_note,
            "deidentified_note": deidentified,
            "expanded_note": expanded,
            "sections": sections,
            "ai_summary": ai_summary,
            "final_summary": final_summary,
            "is_safe": not has_hallucinations,
            "has_red_flags": len(red_flags) > 0,
            "red_flags": red_flags,
            "icd10_codes": icd10_codes,
            "rag_citations": rag_citations,
            "confidence": confidence_data["overall_confidence"],
            "confidence_explanation": confidence_data["explanation"],
            "confidence_factors": confidence_data["factors"],
            "sections_found": sections_found,
            "metrics": {
                "rouge_score": rouge_score,
                "bleu_score": bleu_score,
                "rag_grounding_score": round(rag_score, 3)
            },
            "audit_trail": audit_trail.get_trail(),
            "audit_summary": audit_trail.get_summary(),
            "timestamp": time.time()
        }
        
    except Exception as e:
        audit_trail.log_event("error", {"error": str(e)}, "error")
        return {
            "success": False,
            "error": f"Error processing note: {str(e)}",
            "audit_trail": audit_trail.get_trail()
        }


if __name__ == "__main__":
    # Test the backend
    test_note = """Pt Profile: 32yo young adult. HPI: progressive SOB for two days. PMH/PSH: Hx of DM; no prior surgeries. FHx: no significant family history. Notes: no acute distress noted."""
    
    result = summarize_clinical_note(test_note)
    print(json.dumps(result, indent=2, default=str))