"""
Flask Web Application - Clinical Documentation Assistant
Integrated with complete Colab backend (RAG, GitHub Models API, safety checks)
"""


from flask import Flask, render_template, request, jsonify
from datetime import datetime
import json
import os


# Import the clinical backend
from backend import summarize_clinical_note


app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False


# ============================================
# ROUTES
# ============================================
@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')


@app.route('/api/summarize', methods=['POST'])
def api_summarize():
    """API endpoint for clinical note summarization"""
    try:
        data = request.json
        clinical_note = data.get('note', '')
        
        # Call the integrated backend
        result = summarize_clinical_note(clinical_note)
        
        # Format response for frontend
        if result['success']:
            response = {
                "success": True,
                "sections": result['sections'],
                "ai_summary": result.get('ai_summary', ''),
                "final_summary": result.get('final_summary', ''),
                "is_safe": result['is_safe'],
                "has_red_flags": result['has_red_flags'],
                "red_flags": result['red_flags'],
                "confidence": result['confidence'],
                "sections_found": result['sections_found'],
                "timestamp": datetime.now().isoformat()
            }
        elif result.get('is_diagnostic_question'):
            # Handle diagnostic questions - pass through to frontend
            response = {
                "success": False,
                "is_diagnostic_question": True,
                "error": result.get('error', 'Diagnostic question detected'),
                "message": result.get('message', 'Please consult a qualified healthcare professional'),
                "suggestion": result.get('suggestion', '')
            }
        else:
            response = {
                "success": False,
                "error": result.get('error', 'Unknown error')
            }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500


@app.route('/api/status', methods=['GET'])
def api_status():
    """API status endpoint"""
    github_token_configured = bool(os.getenv("GITHUB_MODELS_TOKEN", ""))
    
    return jsonify({
        "status": "online",
        "version": "2.0.0",
        "features": {
            "abbreviation_expansion": True,
            "deidentification": True,
            "section_extraction": True,
            "ai_summarization": github_token_configured,
            "red_flag_detection": True,
            "hallucination_detection": True,
            "safety_checks": True,
            "diagnostic_question_detection": True
        },
        "github_models_api": "configured" if github_token_configured else "not configured",
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/config', methods=['GET'])
def api_config():
    """Get application configuration"""
    return jsonify({
        "app_name": "Clinical Documentation Assistant",
        "version": "2.0.0",
        "features": [
            "Abbreviation Expansion",
            "PII De-identification",
            "Clinical Section Extraction",
            "AI-Powered Summarization (with GitHub Models API)",
            "Red Flag Detection",
            "Hallucination Prevention",
            "Safety Compliance Checks",
            "RAG-Grounded Responses",
            "Diagnostic Question Detection"
        ],
        "max_note_length": 5000,
        "min_note_length": 10
    })


if __name__ == '__main__':
    print("=" * 70)
    print("Clinical Documentation Assistant - Integrated Version")
    print("=" * 70)
    print("\nFeatures:")
    print("✅ Abbreviation Expansion (DM → diabetes mellitus)")
    print("✅ PII De-identification (removes emails, phone numbers, SSNs)")
    print("✅ Clinical Section Extraction")
    print("✅ AI-Powered Summarization (GitHub Models API)")
    print("✅ Red Flag Detection (chest pain, shortness of breath, etc.)")
    print("✅ Hallucination Prevention")
    print("✅ Safety Compliance Checks")
    print("✅ Diagnostic Question Detection")
    print("✅ RAG-Grounded Responses")
    print("\nStarting Flask server...")
    print("Open your browser to: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 70)
    
    app.run(debug=True, host='0.0.0.0', port=5000)