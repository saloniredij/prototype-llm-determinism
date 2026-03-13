"""
Configuration for the Deterministic Guardrail Engine.
Contains workflow state machine definitions, sample patient context, and UI styles.
"""

# WORKFLOW STATE MACHINE DEFINITION

WORKFLOW_STATES = {
    "GREETING": {
        "label": "Greeting",
        "instruction": "Greet the patient by name and identify yourself as calling from the healthcare provider. State the purpose: appointment reminder.",
        "required_entities": [],
        "valid_transitions": ["VERIFY_IDENTITY"],
        "validation_rules": [
            {"type": "must_contain_concept", "concepts": ["greeting", "appointment", "calling on behalf", "hello", "hi"], "description": "Must mention greeting and purpose"},
            {"type": "must_not_contain", "forbidden": ["diagnos", "prescri", "medic", "treatment", "dosage", "symptom"], "description": "Must not discuss medical topics"},
            {"type": "max_length", "value": 280, "description": "Must be concise (under 280 chars)"},
        ],
        "fallback_template": "Hello, am I speaking with {patient_name}? This is an automated call from {provider_name} regarding your upcoming appointment.",
    },
    "VERIFY_IDENTITY": {
        "label": "Verify Identity",
        "instruction": "Ask the patient to confirm their date of birth for identity verification. Do not proceed without verification.",
        "required_entities": ["date_of_birth"],
        "valid_transitions": ["CONFIRM_APPOINTMENT", "VERIFICATION_FAILED"],
        "validation_rules": [
            {"type": "must_contain_concept", "concepts": ["date of birth", "verify", "confirm", "birth"], "description": "Must ask for DOB verification"},
            {"type": "must_not_contain", "forbidden": ["social security", "SSN", "credit card", "bank", "insurance number"], "description": "Must not request sensitive non-medical data"},
            {"type": "max_length", "value": 200, "description": "Must be concise"},
        ],
        "fallback_template": "For verification purposes, could you please confirm your date of birth?",
    },
    "CONFIRM_APPOINTMENT": {
        "label": "Confirm Appointment",
        "instruction": "State the appointment details (doctor, date, time, location) and ask if the patient can confirm attendance.",
        "required_entities": ["confirmation"],
        "valid_transitions": ["CONFIRMED", "RESCHEDULE", "CLOSING"],
        "validation_rules": [
            {"type": "must_contain_concept", "concepts": ["appointment", "doctor", "dr.", "confirm"], "description": "Must state appointment details"},
            {"type": "must_not_contain", "forbidden": ["diagnos", "prescri", "test result", "lab result", "treatment plan"], "description": "Must not discuss clinical information"},
            {"type": "max_length", "value": 350, "description": "Must be concise"},
        ],
        "fallback_template": "You have an appointment with {doctor_name} on {appointment_date} at {appointment_time} at {location}. Can you confirm you'll be able to attend?",
    },
    "RESCHEDULE": {
        "label": "Reschedule",
        "instruction": "Offer to help reschedule. Provide 2-3 available time slots. Do not make medical decisions about urgency.",
        "required_entities": ["new_time_preference"],
        "valid_transitions": ["CONFIRMED", "CLOSING"],
        "validation_rules": [
            {"type": "must_contain_concept", "concepts": ["reschedule", "available", "time", "slot"], "description": "Must offer rescheduling"},
            {"type": "must_not_contain", "forbidden": ["urgent", "critical", "you should come", "dangerous to wait", "risk"], "description": "Must not make urgency judgments"},
            {"type": "max_length", "value": 350, "description": "Must be concise"},
        ],
        "fallback_template": "I can help reschedule. We have availability on {slot_1} and {slot_2}. Would either of those work for you?",
    },
    "CONFIRMED": {
        "label": "Confirmed",
        "instruction": "Confirm the appointment is set. Provide a brief reminder about what to bring. Close warmly.",
        "required_entities": [],
        "valid_transitions": ["CLOSING"],
        "validation_rules": [
            {"type": "must_contain_concept", "concepts": ["confirmed", "set", "see you", "appointment", "looking forward"], "description": "Must confirm the appointment"},
            {"type": "must_not_contain", "forbidden": ["diagnos", "prescri", "treatment"], "description": "Must not discuss clinical information"},
            {"type": "max_length", "value": 280, "description": "Must be concise"},
        ],
        "fallback_template": "Your appointment is confirmed. Please remember to bring your insurance card and arrive 15 minutes early. We look forward to seeing you!",
    },
    "CLOSING": {
        "label": "Closing",
        "instruction": "Thank the patient and end the call politely. Provide a callback number.",
        "required_entities": [],
        "valid_transitions": [],
        "validation_rules": [
            {"type": "must_contain_concept", "concepts": ["thank", "goodbye", "bye", "take care"], "description": "Must thank and close"},
            {"type": "must_not_contain", "forbidden": ["diagnos", "prescri", "treatment", "medical advice"], "description": "Must not discuss clinical information"},
            {"type": "max_length", "value": 200, "description": "Must be concise"},
        ],
        "fallback_template": "Thank you for your time, {patient_name}. If you have any questions, you can reach us at {callback_number}. Goodbye!",
    },
    "VERIFICATION_FAILED": {
        "label": "Verification Failed",
        "instruction": "Politely inform that verification could not be completed and suggest calling the office directly.",
        "required_entities": [],
        "valid_transitions": ["CLOSING"],
        "validation_rules": [
            {"type": "must_not_contain", "forbidden": ["appointment detail", "doctor name", "schedule", "dr."], "description": "Must not reveal appointment details without verification"},
            {"type": "max_length", "value": 200, "description": "Must be concise"},
        ],
        "fallback_template": "I wasn't able to verify your identity. For your security, please call our office directly at {callback_number} for appointment information.",
    },
}


# SAMPLE PATIENT CONTEXT

SAMPLE_CONTEXT = {
    "patient_name": "Mary Johnson",
    "provider_name": "CareBridge Health",
    "doctor_name": "Dr. Sarah Chen",
    "appointment_date": "March 18th",
    "appointment_time": "2:30 PM",
    "location": "CareBridge Main Campus, Suite 204",
    "callback_number": "(555) 234-5678",
    "slot_1": "March 19th at 10:00 AM",
    "slot_2": "March 20th at 3:00 PM",
}


# CSS STYLES

APP_STYLES = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

    /* Global */
    .stApp {
        background-color: #0B0F14;
        color: #E8ECF1;
        font-family: 'DM Sans', sans-serif;
    }

    /* Hide default streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #131920;
        border-right: 1px solid #243040;
    }
    [data-testid="stSidebar"] .stMarkdown p {
        color: #7A8BA3;
    }

    /* Custom components */
    .header-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 4px 12px;
        background: rgba(0,212,170,0.1);
        border: 1px solid rgba(0,212,170,0.25);
        border-radius: 20px;
        font-family: 'DM Mono', monospace;
        font-size: 11px;
        color: #00D4AA;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }
    .header-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #00D4AA;
        box-shadow: 0 0 12px #00D4AA;
        display: inline-block;
    }

    .section-label {
        font-family: 'DM Mono', monospace;
        font-size: 10px;
        color: #4A5B70;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    .state-card {
        background: #131920;
        border: 1px solid #243040;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
    }

    .rule-badge {
        display: inline-block;
        font-family: 'DM Mono', monospace;
        font-size: 9px;
        padding: 2px 8px;
        border-radius: 4px;
        margin-right: 6px;
    }
    .rule-block {
        background: rgba(255,90,90,0.1);
        color: #FF5A5A;
    }
    .rule-require {
        background: rgba(91,157,240,0.08);
        color: #5B9DF0;
    }
    .rule-limit {
        background: rgba(255,170,51,0.1);
        color: #FFAA33;
    }

    .output-card {
        background: #131920;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 12px;
    }
    .output-card-pass {
        border: 1px solid rgba(0,212,170,0.25);
    }
    .output-card-fail {
        border: 1px solid rgba(255,170,51,0.25);
    }
    .output-card-raw {
        border: 1px solid #243040;
    }

    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
    }
    .dot-green {
        background: #00D4AA;
        box-shadow: 0 0 8px #00D4AA;
    }
    .dot-amber {
        background: #FFAA33;
        box-shadow: 0 0 8px #FFAA33;
    }
    .dot-red {
        background: #FF5A5A;
        box-shadow: 0 0 8px #FF5A5A;
    }

    .metric-box {
        background: #1A222C;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
    }
    .metric-value {
        font-size: 28px;
        font-weight: 700;
        font-family: 'DM Sans', sans-serif;
    }
    .metric-label {
        font-family: 'DM Mono', monospace;
        font-size: 10px;
        color: #4A5B70;
        margin-top: 4px;
    }

    .fallback-box {
        background: rgba(255,170,51,0.08);
        border-radius: 8px;
        padding: 12px;
        font-size: 13px;
        color: #FFAA33;
        font-style: italic;
        line-height: 1.6;
    }

    .transition-badge {
        display: inline-block;
        font-family: 'DM Mono', monospace;
        font-size: 11px;
        padding: 3px 10px;
        border-radius: 4px;
        background: #1A222C;
        color: #7A8BA3;
        border: 1px solid #243040;
        margin-right: 6px;
    }

    .run-badge {
        display: inline-block;
        font-family: 'DM Mono', monospace;
        font-size: 9px;
        padding: 2px 8px;
        border-radius: 4px;
    }
    .badge-pass {
        background: rgba(0,212,170,0.1);
        color: #00D4AA;
    }
    .badge-fail {
        background: rgba(255,90,90,0.1);
        color: #FF5A5A;
    }
    .badge-fallback {
        background: rgba(255,170,51,0.1);
        color: #FFAA33;
    }

    .how-it-works-step {
        display: flex;
        gap: 16px;
        padding: 14px 0;
        border-bottom: 1px solid #243040;
    }
    .step-num {
        font-family: 'DM Mono', monospace;
        font-size: 14px;
        color: #00D4AA;
        font-weight: 700;
        flex-shrink: 0;
    }
    .step-title {
        font-size: 14px;
        font-weight: 600;
        color: #E8ECF1;
        margin-bottom: 4px;
    }
    .step-desc {
        font-size: 12.5px;
        color: #7A8BA3;
        line-height: 1.6;
    }

    /* Button override */
    .stButton > button {
        background: #00D4AA !important;
        color: #0B0F14 !important;
        font-family: 'DM Mono', monospace !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 8px 24px !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background: #00E8BB !important;
        box-shadow: 0 0 20px rgba(0,212,170,0.3) !important;
    }
    .stButton > button:disabled {
        background: #1A222C !important;
        color: #4A5B70 !important;
    }

    /* Radio buttons */
    [data-testid="stRadio"] label {
        color: #7A8BA3 !important;
        font-family: 'DM Mono', monospace !important;
        font-size: 12px !important;
    }

    /* Expander */
    [data-testid="stExpander"] {
        background: #131920;
        border: 1px solid #243040;
        border-radius: 12px;
    }
</style>
"""