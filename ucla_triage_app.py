import streamlit as st
from datetime import datetime
import json

# Page config
st.set_page_config(
    page_title="UCLA AI Triage Prototype",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for UCLA styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2774AE;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #005587;
        margin-bottom: 2rem;
    }
    .clinic-card {
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid;
    }
    .dbp-card {
        background-color: #E8F4FA;
        border-left-color: #2774AE;
    }
    .can-card {
        background-color: #FFF9E6;
        border-left-color: #FFD100;
    }
    .ppc-card {
        background-color: #F0F7FB;
        border-left-color: #005587;
    }
    .confidence-high {
        color: #2774AE;
        font-weight: bold;
    }
    .confidence-medium {
        color: #FFB81C;
        font-weight: bold;
    }
    .confidence-low {
        color: #C62828;
        font-weight: bold;
    }
    div[data-testid="stButton"] button {
        border-color: #2774AE;
        border-width: 2px;
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    div[data-testid="stButton"] button[kind="secondary"] {
        background-color: #f5f5f5;
        color: #666;
        border-color: #ddd;
    }
    div[data-testid="stButton"] button[kind="secondary"]:hover {
        background-color: #E8F4FA;
        border-color: #2774AE;
        color: #2774AE;
    }
    div[data-testid="stButton"] button[kind="primary"] {
        background-color: #2774AE;
        border-color: #2774AE;
        color: white;
        font-weight: 600;
    }
    div[data-testid="stButton"] button[kind="primary"]:hover {
        background-color: #005587;
        border-color: #005587;
    }
    .section-header {
        font-size: 15px;
        font-weight: bold;
        margin-top: 8px;
        margin-bottom: 8px;
        padding: 8px 12px;
        border-radius: 6px;
    }
    /* Checkbox styling - condensed */
    div[data-testid="stCheckbox"] {
        padding: 2px 0;
        margin: 0;
    }
    div[data-testid="stCheckbox"] label {
        font-size: 14px;
        color: #333;
        line-height: 1.3;
    }
    div[data-testid="stCheckbox"] label:hover {
        color: #2774AE;
    }
    /* Reduce spacing between elements */
    .stMarkdown {
        margin-bottom: 0.3rem;
    }
    /* Reduce text area spacing */
    div[data-testid="stTextArea"] {
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'feedback_data' not in st.session_state:
    st.session_state.feedback_data = []
if 'edge_cases' not in st.session_state:
    st.session_state.edge_cases = []
if 'current_mode' not in st.session_state:
    st.session_state.current_mode = "Test the Logic"

# Clinic definitions (7 UCLA clinics)
CLINICS = {
    "CAN": {
        "name": "CAN Clinic",
        "description": "Neurodevelopmental and neurogenetic syndromes (incl. rare chromatinopathies), syndromic autism, early motor issues, epilepsy + NDD, full team evaluations",
        "color": "#FFB81C"
    },
    "NEURO": {
        "name": "Pediatric Neurology – Neurodevelopmental Disorders (NDD)",
        "description": "Autism+ and ADHD+, epilepsy + NDD, regression, developmental delay of unknown cause; Angelman, Dup15q and HNRNPH2 clinics",
        "color": "#8237FF"
    },
    "DBP": {
        "name": "Developmental & Behavioral Pediatrics",
        "description": "Autism and ID evaluation, ADHD evaluation and medication, anxiety and disruptive-behavior medication",
        "color": "#2774AE"
    },
    "HRIF": {
        "name": "High-Risk Infant Follow-up (HRIF)",
        "description": "NICU graduates; early identification of cerebral palsy",
        "color": "#00A5E5"
    },
    "LEND": {
        "name": "UC-LEND",
        "description": "Med-Peds and pediatricians; cases with psychosocial complexity (no full evaluations)",
        "color": "#00C389"
    },
    "MPAC": {
        "name": "MPAC – Neuropsychological Testing",
        "description": "Neuropsychological testing only",
        "color": "#8BB8E8"
    },
    "PPC": {
        "name": "Child & Adolescent Psychiatry",
        "description": "Primary psychiatric conditions: depression, PTSD, bipolar disorder, OCD, safety concerns",
        "color": "#005587"
    },
}

# Mapping of button IDs to clinical flags
ITEM_FLAGS = {
    # Flags are used for school-support/service signals (dbp_flag) and summaries.
    # Clinic routing rules live in route_patient_new (see the rule lists above it).
    # Neurogenetic conditions
    "hx_tuberous_sclerosis": ["neuro_flag", "high_acuity_flag"],
    "dx_angelman": ["neuro_flag", "neurogenetic_flag"],
    "dx_asxl": ["neuro_flag", "neurogenetic_flag"],
    "dx_cdkl5": ["neuro_flag", "neurogenetic_flag"],
    "dx_dup15q": ["neuro_flag", "neurogenetic_flag"],
    "dx_hnrnph2": ["neuro_flag", "neurogenetic_flag"],
    "dx_kabuki": ["neuro_flag", "neurogenetic_flag"],
    "dx_prader_willi": ["neuro_flag", "neurogenetic_flag"],
    # Recorded only, no routing flags yet
    "dx_rett": [],
    "dx_down": [],
    "dx_neurofibromatosis": [],

    # Neurologic conditions
    "hx_frequent_headaches_migraines": ["neuro_flag"],
    "hx_seizures_epilepsy": ["neuro_flag", "high_acuity_flag"],
    "hx_cerebral_palsy": ["neuro_flag", "high_acuity_flag"],
    "hx_tics": [],  # recorded only, no routing flags yet
    "hx_motor_delays": [],  # recorded only, no routing flags yet
    "hx_acquired_brain_injury": [],  # recorded only, no routing flags yet

    # Neurodevelopmental conditions: recorded only, no routing flags yet.
    # To wire into decision logic later, add flags (e.g., ["dbp_flag"]).
    "dx_adhd": [],
    "dx_autism": [],
    "dx_global_developmental_delay": [],
    "dx_intellectual_disability": [],
    "dx_speech_language_disorder": [],
    "dx_specific_learning_disability": [],

    # Mental Health History
    "hx_bipolar": ["psych_flag", "high_acuity_flag"],
    "hx_ocd": ["psych_flag"],
    "hx_ptsd": ["psych_flag"],
    "hx_psychotic_disorders": [],  # recorded only, no routing flags yet
    "hx_anxiety_panic": ["psych_flag"],
    "hx_depression": ["psych_flag"],
    "hx_suicidal_ideation_or_attempt": ["psych_flag", "high_acuity_flag", "safety_flag"],
    
    # Development & Education
    "has_iep": ["dbp_flag"],
    "has_504": ["dbp_flag"],
    # Recorded only, no routing flags yet
    "edu_special_education": [],
    "edu_one_on_one_aide": [],
    "edu_fba": [],
    "edu_bip": [],
    "edu_school_counseling": [],
    "edu_emotional_regulation": [],
    
    # Current Services
    "receives_occupational_therapy": ["dbp_flag"],
    "receives_aba_therapy": ["dbp_flag"],
    "receives_speech_therapy": ["dbp_flag"],
    "receives_social_skills_training": ["dbp_flag"],
    "receives_cbt_therapy": ["dbp_flag"],
    "receives_physical_therapy": ["dbp_flag"],
    # Recorded only, no routing flags yet
    "receives_respite_care": [],
    "receives_self_determination_program": []
}

# Parent-identified goals: what the family is hoping to get from the visit.
# Recorded for research only; they do NOT affect routing yet.
PARENT_GOALS = [  # shown in this order (not alphabetized)
    ("goal_testing_autism", "Autism testing"),
    ("goal_adhd_evaluation", "ADHD evaluation"),
    ("goal_testing_neuropsychiatric", "Comprehensive neuropsychological testing"),
    ("goal_testing_cognitive", "Cognitive testing"),
    ("goal_testing_academic", "Academic/achievement testing"),
    ("goal_testing_genetic", "Genetic testing"),
    ("goal_brain_imaging", "Brain imaging (MRI)"),
    ("goal_neurophysiological_testing", "Neurophysiological testing (EEG)"),
    ("goal_medication_management", "Medication management"),
    ("goal_therapy_counseling", "Therapy or counseling"),
    ("goal_access_to_services", "Access to services (ABA, OT, speech, Regional Center)"),
    ("goal_school_support", "School support or IEP/504 advocacy"),
    ("goal_research_involvement", "Research involvement"),
    ("goal_second_opinion", "Second opinion on an existing diagnosis"),
]

# Routing flags for each parent goal. Empty = no effect on routing.
# To wire a goal into the decision logic later, add flags here
# (e.g., "goal_testing_autism": ["dbp_flag"]) and pass parent_goals
# into route_patient_new.
PARENT_GOAL_FLAGS = {goal_id: [] for goal_id, _ in PARENT_GOALS}
PARENT_GOAL_LABELS = dict(PARENT_GOALS)

# Checkbox sections shown in the Routing Simulator
SECTIONS = {
    "neurodevelopmental_diagnoses": {
        "title": "🧠 Has your child been diagnosed with one of the following neurodevelopmental conditions?",
        "color": "#2774AE",
        "items": [
            ("dx_adhd", "Attention-Deficit/Hyperactivity Disorder"),
            ("dx_autism", "Autism Spectrum Disorder"),
            ("dx_global_developmental_delay", "Global Developmental Delay"),
            ("dx_intellectual_disability", "Intellectual Disability"),
            ("dx_specific_learning_disability", "Specific Learning Disability"),
            ("dx_speech_language_disorder", "Speech and Language Disorders")
        ]
    },
    "neurogenetic_conditions": {
        "title": "🧬 Has your child been diagnosed with one of the following neurogenetic conditions?",
        "color": "#2774AE",
        "items": [
            ("dx_angelman", "Angelman Syndrome"),
            ("dx_asxl", "ASXL-Related Disorders"),
            ("dx_cdkl5", "CDKL5"),
            ("dx_down", "Down Syndrome"),
            ("dx_dup15q", "Dup15q Syndrome"),
            ("dx_hnrnph2", "HNRNPH2"),
            ("dx_kabuki", "Kabuki Syndrome"),
            ("dx_neurofibromatosis", "Neurofibromatosis"),
            ("dx_prader_willi", "Prader-Willi Syndrome"),
            ("dx_rett", "Rett Syndrome"),
            ("hx_tuberous_sclerosis", "Tuberous Sclerosis Complex")
        ]
    },
    "neurologic_conditions": {
        "title": "⚡ Has your child been diagnosed with one of the following neurologic conditions?",
        "color": "#2774AE",
        "items": [
            ("hx_frequent_headaches_migraines", "Frequent headaches/migraines"),
            ("hx_seizures_epilepsy", "Epilepsy/seizure disorder"),
            ("hx_cerebral_palsy", "Cerebral palsy"),
            ("hx_tics", "Tic disorders/Tourette's Syndrome"),  # 4th item = right column, directly under Epilepsy/seizure disorder
            ("hx_motor_delays", "Gross/fine motor delays"),
            ("hx_acquired_brain_injury", "Acquired brain injury")
        ]
    },
    "mental_health_history": {
        "title": "💭 Has your child been diagnosed with one of the following mental health conditions?",
        "color": "#2774AE",
        "items": [
            ("hx_anxiety_panic", "Anxiety or panic attacks"),
            ("hx_bipolar", "Bipolar Disorder"),
            ("hx_depression", "Major Depressive Disorder"),
            ("hx_ocd", "Obsessive-Compulsive Disorder"),
            ("hx_ptsd", "Post-Traumatic Stress Disorder"),
            ("hx_psychotic_disorders", "Psychotic Disorder"),
            ("hx_suicidal_ideation_or_attempt", "Suicidal ideation or suicide attempt")
        ]
    },
    "development_education_supports": {
        "title": "📚 Does your child receive any of the following educational supports?",
        "color": "#2774AE",
        "items": [
            # shown in this order (not alphabetized)
            ("has_iep", "Individualized Education Program (IEP)"),
            ("has_504", "Section 504 Plan"),
            ("edu_special_education", "Special education services"),
            ("edu_one_on_one_aide", "One-on-one instructional aide or paraprofessional"),
            ("edu_fba", "Functional Behavioral Assessment (FBA)"),
            ("edu_bip", "Behavior Intervention Plan (BIP)"),
            ("edu_school_counseling", "School counseling"),
            ("edu_emotional_regulation", "Emotional regulation support")
        ]
    },
    "current_services": {
        "title": "🏥 Does your child currently receive any of the following services?",
        "color": "#2774AE",
        "items": [
            # shown in this order (not alphabetized)
            ("receives_aba_therapy", "ABA Therapy"),
            ("receives_speech_therapy", "Speech Therapy"),
            ("receives_occupational_therapy", "Occupational Therapy"),
            ("receives_physical_therapy", "Physical Therapy"),
            ("receives_cbt_therapy", "Cognitive Behavioral Therapy"),
            ("receives_social_skills_training", "Social Skills Training"),
            ("receives_respite_care", "Respite Care"),
            ("receives_self_determination_program", "Self-Determination Program")
        ]
    }
}

# Readable label for every checkbox item ID
ITEM_LABELS = {item_id: label for sec in SECTIONS.values() for item_id, label in sec["items"]}

def concern_label(item_id):
    """Readable label for a checkbox item ID."""
    return ITEM_LABELS.get(item_id, item_id.removeprefix("hx_").replace("_", " ").capitalize())

# Options for specialists the child has already seen
SPECIALIST_TYPES = [
    "Developmental-behavioral pediatrician",
    "Child neurologist",
    "Child psychiatrist",
    "Psychologist or neuropsychologist",
    "Therapist or counselor",
    "Other",
]
SPECIALIST_LOCATIONS = ["At UCLA", "Outside UCLA"]
LAST_SEEN_OPTIONS = [
    "Within the past 6 months",
    "Within the past year",
    "1–3 years ago",
    "More than 3 years ago",
]
PRIOR_SPECIALIST_KEYS = ["name", "type", "where", "clinic", "last_seen"]

def collect_prior_specialists():
    """Specialists entered in the form (rows with at least one field filled)."""
    rows = []
    for i in range(st.session_state.get("prior_specialist_count", 1)):
        row = {f: (st.session_state.get(f"prior_spec_{i}_{f}") or "").strip() for f in PRIOR_SPECIALIST_KEYS}
        if row["where"] != "Outside UCLA":
            row["clinic"] = ""
        if any(row.values()):
            rows.append(row)
    return rows

def format_specialist(row):
    """One-line summary, e.g. 'Dr. Lee · Child neurologist · Outside UCLA (CHLA) · Last seen within the past year'."""
    where = row.get("where", "")
    if where and row.get("clinic"):
        where = f"{where} ({row['clinic']})"
    last_seen = f"Last seen {row['last_seen'][0].lower()}{row['last_seen'][1:]}" if row.get("last_seen") else ""
    return " · ".join(v for v in [row.get("name", ""), row.get("type", ""), where, last_seen] if v)

def clinic_codes(result):
    """'CAN' or 'CAN + PPC' for a routing result."""
    return " + ".join([result['clinic']] + result.get('also_recommend', []))

# ─── Routing rule inputs ────────────────────────────────────────────────
# Every judgment call awaiting clinical confirmation is marked "ASSUMPTION".
NEURO_CLINIC_SYNDROMES = ["dx_angelman", "dx_dup15q", "dx_hnrnph2"]      # dedicated Peds Neuro NDD clinics
CAN_SYNDROMES = ["dx_kabuki", "dx_asxl", "dx_prader_willi"]               # chromatinopathies / neurogenetic syndromes
CAN_SYNDROMES_UNCONFIRMED = ["dx_cdkl5", "dx_rett", "dx_down"]            # ASSUMPTION: CAN (could be Peds Neuro)
NDD_DIAGNOSES = ["dx_adhd", "dx_autism", "dx_global_developmental_delay", "dx_intellectual_disability",
                 "dx_specific_learning_disability", "dx_speech_language_disorder"]
PRIMARY_PSYCH = ["hx_depression", "hx_ptsd", "hx_bipolar", "hx_ocd"]      # DBP and Peds Neuro do not see these alone
NEURO_ONLY = ["hx_seizures_epilepsy", "hx_frequent_headaches_migraines", "hx_tics"]
MOTOR = ["hx_cerebral_palsy", "hx_motor_delays"]
AUTISM_ADHD_PLUS = ["hx_frequent_headaches_migraines", "hx_tics", "hx_cerebral_palsy", "hx_motor_delays",
                    "dx_global_developmental_delay"]                      # ASSUMPTION: what makes a case "Autism+ / ADHD+"
MPAC_GOALS = ["goal_testing_neuropsychiatric", "goal_testing_academic"]
HRIF_MAX_AGE = 3              # ASSUMPTION: HRIF follows children up to age 3 (notes say 3 or 5)
DBP_ID_MAX_AGE = 12           # ASSUMPTION: DBP doesn't take "older" patients whose main question is ID
UNCONFIRMED = "⚠️ Assumption pending clinical review"

def route_patient_new(age, selected_items, parent_goals=()):
    """
    Route a patient to one of 7 UCLA clinics. Rules run in order; the first match wins.
    Returns: (clinic, confidence, reasoning, also_recommend)
        also_recommend: additional clinic codes recommended alongside clinic
    """
    sel = set(selected_items)
    goals = set(parent_goals)
    has = lambda ids: [i for i in ids if i in sel]
    names = lambda ids: ", ".join(ITEM_LABELS.get(i, i) for i in ids)
    flags = set()
    for item_id in sel:
        flags.update(ITEM_FLAGS.get(item_id, []))
    ndd = has(NDD_DIAGNOSES)
    psych = has(PRIMARY_PSYCH)
    anxiety = "hx_anxiety_panic" in sel
    seizures = "hx_seizures_epilepsy" in sel
    reasoning, also = [], []

    def finish(clinic, confidence):
        # Add-on: neuropsych/academic testing goal or a learning disability → MPAC as well
        if clinic != "MPAC" and (goals & set(MPAC_GOALS) or "dx_specific_learning_disability" in sel):
            reasoning.append("➕ Testing need (neuropsych/academic testing or learning disability) → also MPAC")
            also.append("MPAC")
        return clinic, confidence, reasoning, list(dict.fromkeys(c for c in also if c != clinic))

    # 1. SAFETY
    if "hx_suicidal_ideation_or_attempt" in sel:
        reasoning += ["🚨 SAFETY PRIORITY: suicidal ideation or attempt reported",
                      "→ Child & Adolescent Psychiatry first"]
        return finish("PPC", "High")

    # 2. NAMED NEUROGENETIC SYNDROMES
    syndrome_clinic = None
    if has(NEURO_CLINIC_SYNDROMES):
        reasoning += [f"🧬 {names(has(NEURO_CLINIC_SYNDROMES))}: dedicated Peds Neuro NDD clinic"]
        syndrome_clinic, conf = "NEURO", "High"
    elif has(CAN_SYNDROMES):
        reasoning += [f"🧬 {names(has(CAN_SYNDROMES))}: neurogenetic syndrome → CAN"]
        syndrome_clinic, conf = "CAN", "High"
    elif has(CAN_SYNDROMES_UNCONFIRMED):
        reasoning += [f"🧬 {names(has(CAN_SYNDROMES_UNCONFIRMED))}: neurogenetic syndrome → CAN", UNCONFIRMED]
        syndrome_clinic, conf = "CAN", "Medium"
    if syndrome_clinic:
        if psych or anxiety:
            reasoning.append(f"💭 Psychiatric concern also present: {names(psych + (['hx_anxiety_panic'] if anxiety else []))} → also Psychiatry")
            also.append("PPC")
        return finish(syndrome_clinic, conf)

    # 3. TUBEROUS SCLEROSIS COMPLEX
    if "hx_tuberous_sclerosis" in sel:
        reasoning.append("🧬 Tuberous Sclerosis Complex → DBP for autism and learning evaluation")
        if seizures:
            reasoning.append("⚡ Seizures also present → also Peds Neuro (epilepsy + NDD)")
            also.append("NEURO")
        return finish("DBP", "High")

    # 4. HRIF: early motor / CP in young children
    if age < HRIF_MAX_AGE and has(MOTOR):
        reasoning += [f"👶 Age under {HRIF_MAX_AGE} with {names(has(MOTOR))} → HRIF (early CP identification)",
                      UNCONFIRMED + f" (HRIF age cutoff {HRIF_MAX_AGE}; NICU history not asked)"]
        return finish("HRIF", "Medium")

    # 5. EPILEPSY + NDD
    if seizures and (ndd or has(MOTOR)):
        reasoning += [f"⚡ Epilepsy/seizure disorder with {names(ndd + has(MOTOR))} → Peds Neuro (epilepsy + NDD)",
                      "Note: CAN also sees epilepsy + NDD"]
        return finish("NEURO", "High")

    # 6. PRIMARY PSYCHIATRIC CONDITIONS
    if psych:
        reasoning += [f"💭 {names(psych)}: primary psychiatric condition → Psychiatry",
                      "DBP and Peds Neuro do not see primary psychiatric conditions"]
        if ndd:
            reasoning.append(f"Developmental diagnosis also present ({names(ndd)}) → also DBP")
            also.append("DBP")
        return finish("PPC", "High")

    # 7. UNDER 2: early-intervention fast track
    if age < 2 and sel:
        reasoning += ["👶 Age under 2: early intervention priority → DBP"]
        return finish("DBP", "High")

    # 8. AUTISM+ / ADHD+
    core = has(["dx_autism", "dx_adhd"])
    plus = has(AUTISM_ADHD_PLUS)
    if core and (plus or len(core) == 2):
        reasoning += [f"🧩 {names(core)} with co-occurring {names(plus) if plus else 'condition'} → Peds Neuro (Autism+/ADHD+)",
                      UNCONFIRMED + " (definition of '+'; CAN also sees syndromic autism)"]
        return finish("NEURO", "Medium")

    # 9. GLOBAL DEVELOPMENTAL DELAY
    if "dx_global_developmental_delay" in sel:
        reasoning.append("🧩 Global developmental delay → Peds Neuro (developmental delay of unknown cause)")
        return finish("NEURO", "High")

    # 10. NEUROLOGIC CONDITIONS
    if has(NEURO_ONLY):
        reasoning.append(f"⚡ {names(has(NEURO_ONLY))} → Pediatric Neurology")
        return finish("NEURO", "High")
    if has(MOTOR):
        reasoning.append(f"🦵 {names(has(MOTOR))} → CAN (motor issues)")
        return finish("CAN", "High")

    # 11. ANXIETY
    if anxiety:
        if ndd:
            reasoning.append(f"💭 Anxiety with {names(ndd)} → DBP (anxiety medication management with NDD)")
            return finish("DBP", "High")
        reasoning.append("💭 Anxiety without a developmental diagnosis → Psychiatry")
        return finish("PPC", "High")

    # 12. INTELLECTUAL DISABILITY
    if "dx_intellectual_disability" in sel:
        if age >= DBP_ID_MAX_AGE:
            reasoning += [f"Age {age:.0f} with intellectual disability: DBP doesn't take older patients with a primary ID question → CAN",
                          UNCONFIRMED + f" (age cutoff {DBP_ID_MAX_AGE})"]
            return finish("CAN", "Medium")
        reasoning.append("Intellectual disability → DBP (ID evaluation)")
        return finish("DBP", "High")

    # 13. AUTISM / ADHD / SPEECH-LANGUAGE ALONE
    if core or "dx_speech_language_disorder" in sel:
        reasoning.append(f"🧩 {names(core + has(['dx_speech_language_disorder']))} → DBP (evaluation and medication management)")
        return finish("DBP", "High")

    # 14. LEARNING DISABILITY ALONE
    if "dx_specific_learning_disability" in sel:
        reasoning += ["📚 Specific learning disability → MPAC (neuropsychological testing)",
                      "Peds Neuro does not see learning disability"]
        return finish("MPAC", "High")

    # 15. SCHOOL SUPPORTS AND SERVICES ONLY
    dbp_items = [i for i in sel if "dbp_flag" in ITEM_FLAGS.get(i, [])]
    if dbp_items:
        reasoning.append(f"📚 School supports or services: {names(sorted(dbp_items, key=list(ITEM_LABELS).index))} → DBP")
        return finish("DBP", "High" if len(dbp_items) >= 2 else "Medium")
    if sel:
        reasoning += ["Some items selected, but none that point to a specific clinic → DBP",
                      "May benefit from a clinical triage discussion"]
        return finish("DBP", "Low")
    if goals & set(MPAC_GOALS):
        reasoning.append("Only goal selected is testing → MPAC")
        return finish("MPAC", "Medium")
    reasoning.append("No concerns selected: enter the child's conditions, supports or services to route")
    return finish("DBP", "Low")

# Header
st.markdown('<div class="main-header">🏥 UCLA AI Triage Prototype</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Helping patients and their families connect to the right UCLA specialist: Psychiatry · Pediatrics · Medicine</div>', unsafe_allow_html=True)

# Mode selector
col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
with col1:
    if st.button("🎯 Test the Logic", use_container_width=True, type="primary" if st.session_state.current_mode == "Test the Logic" else "secondary"):
        st.session_state.current_mode = "Test the Logic"
with col2:
    if st.button("🔍 Edge Case Explorer", use_container_width=True, type="primary" if st.session_state.current_mode == "Edge Case Explorer" else "secondary"):
        st.session_state.current_mode = "Edge Case Explorer"
with col3:
    if st.button("📊 Session Data", use_container_width=True, type="primary" if st.session_state.current_mode == "Session Data" else "secondary"):
        st.session_state.current_mode = "Session Data"
with col4:
    if st.button("🚀 AI Vision", use_container_width=True, type="primary" if st.session_state.current_mode == "AI Vision" else "secondary"):
        st.session_state.current_mode = "AI Vision"

st.markdown("---")

# MODE 1: Test the Logic
if st.session_state.current_mode == "Test the Logic":
    st.subheader("🎯 Interactive Routing Simulator")
    st.markdown("*Use this tool to test routing logic with real-world patient presentations*")
    
    # Initialize selected items in session state
    if 'selected_items' not in st.session_state:
        st.session_state.selected_items = set()
    
    # Initialize parent concerns text in session state
    
    st.markdown("### Patient Information")
    
    # Age input
    st.markdown(f'<div class="section-header" style="background: linear-gradient(90deg, #2774AE22 0%, rgba(255,255,255,0) 100%); border-left: 4px solid #2774AE;">🎂 What is your child&#39;s age?</div>', unsafe_allow_html=True)
    age_years = st.slider("Age (years)", 0, 30, 8)
    
    if age_years < 2:
        age_months = st.slider("Age in Months", 0, 23, age_years * 12)
        age = age_months / 12.0
        st.caption(f"Total age: {age_months} months ({age:.1f} years)")
    else:
        age = age_years
    
    # Selected items counter
    num_selected = len(st.session_state.selected_items)
    if num_selected > 0:
        st.info(f"✓ {num_selected} concern(s) selected")
    else:
        st.warning("⚠️ No concerns selected - select relevant items below")
    
    # Family goals section (checkboxes) - AT TOP
    st.markdown(f'<div class="section-header" style="background: linear-gradient(90deg, #2774AE22 0%, rgba(255,255,255,0) 100%); border-left: 4px solid #2774AE;">👨‍👩‍👧‍👦 What are your main goals for connecting with a specialist at UCLA?</div>', unsafe_allow_html=True)

    # Parent goals checkboxes (recorded only; not used in routing yet)
    if 'parent_goals' not in st.session_state:
        st.session_state.parent_goals = set()
    st.markdown("**Select all that apply:**")
    st.caption("Recorded for research. Does not affect routing yet.")
    for goal_id, goal_label in PARENT_GOALS:
        if st.checkbox(goal_label, key=f"chk_{goal_id}"):
            st.session_state.parent_goals.add(goal_id)
        else:
            st.session_state.parent_goals.discard(goal_id)

    # Prior specialist question (recorded only; not used in routing)
    st.markdown(f'<div class="section-header" style="background: linear-gradient(90deg, #2774AE22 0%, rgba(255,255,255,0) 100%); border-left: 4px solid #2774AE;">🩺 Has your child been seen by a neurodevelopmental or mental health specialist?</div>', unsafe_allow_html=True)
    seen_before = st.radio(
        "Has your child been seen by a neurodevelopmental or mental health specialist?",
        ["No", "Yes"],
        index=None,
        horizontal=True,
        key="prior_specialist_seen",
        label_visibility="collapsed",
    )
    if seen_before == "Yes":
        if "prior_specialist_count" not in st.session_state:
            st.session_state.prior_specialist_count = 1
        st.caption("Optional. Prototype only: please don't enter real patient or provider information.")
        for i in range(st.session_state.prior_specialist_count):
            if st.session_state.prior_specialist_count > 1:
                st.markdown(f"**Specialist {i + 1}**")
            col_a, col_b = st.columns(2)
            with col_a:
                st.text_input("Provider's name", key=f"prior_spec_{i}_name")
            with col_b:
                st.selectbox("Type of specialist", SPECIALIST_TYPES, index=None,
                             placeholder="Select type", key=f"prior_spec_{i}_type")
            col_a, col_b = st.columns(2)
            with col_a:
                where = st.selectbox("Where?", SPECIALIST_LOCATIONS, index=None,
                                     placeholder="Select location", key=f"prior_spec_{i}_where")
                if where == "Outside UCLA":
                    st.text_input("Clinic or practice name", key=f"prior_spec_{i}_clinic")
            with col_b:
                st.selectbox("When were they last seen?", LAST_SEEN_OPTIONS, index=None,
                             placeholder="Select timeframe", key=f"prior_spec_{i}_last_seen")
        if st.button("➕ Add another specialist"):
            st.session_state.prior_specialist_count += 1
            st.rerun()
    
    sections_data = SECTIONS
    
    # Render all sections in single column
    for section_id, section_data in sections_data.items():
        st.markdown(f'<div class="section-header" style="background: linear-gradient(90deg, {section_data["color"]}22 0%, rgba(255,255,255,0) 100%); border-left: 4px solid {section_data["color"]};">{section_data["title"]}</div>', unsafe_allow_html=True)
        st.markdown("**Select all that apply:**")
        
        # Render checkboxes in 2-column grid within each section
        items = section_data["items"]
        for i in range(0, len(items), 2):
            cols = st.columns(2)
            
            # First checkbox in the row
            item_id, item_label = items[i]
            with cols[0]:
                is_selected = item_id in st.session_state.selected_items
                if st.checkbox(
                    item_label,
                    value=is_selected,
                    key=f"chk_{item_id}"
                ):
                    if item_id not in st.session_state.selected_items:
                        st.session_state.selected_items.add(item_id)
                else:
                    if item_id in st.session_state.selected_items:
                        st.session_state.selected_items.remove(item_id)
            
            # Second checkbox in the row (if exists)
            if i + 1 < len(items):
                item_id, item_label = items[i + 1]
                with cols[1]:
                    is_selected = item_id in st.session_state.selected_items
                    if st.checkbox(
                        item_label,
                        value=is_selected,
                        key=f"chk_{item_id}"
                    ):
                        if item_id not in st.session_state.selected_items:
                            st.session_state.selected_items.add(item_id)
                    else:
                        if item_id in st.session_state.selected_items:
                            st.session_state.selected_items.remove(item_id)
    
    # Route and Clear buttons
    col_route, col_clear = st.columns(2)
    with col_route:
        if st.button("🔍 Route Patient", type="primary", use_container_width=True):
            # Convert selected items to the format the routing function expects
            selected_concerns = [i for i in ITEM_LABELS if i in st.session_state.selected_items]
            
            clinic, confidence, reasoning, also_recommend = route_patient_new(
                age, selected_concerns, [g for g, _ in PARENT_GOALS if g in st.session_state.parent_goals])
            
            st.session_state.last_routing = {
                "age": age,
                "selected_concerns": selected_concerns,
                "parent_goals": [g for g, _ in PARENT_GOALS if g in st.session_state.parent_goals],
                "prior_specialist_seen": st.session_state.get("prior_specialist_seen"),
                "prior_specialists": collect_prior_specialists() if st.session_state.get("prior_specialist_seen") == "Yes" else [],
                "clinic": clinic,
                "also_recommend": also_recommend,
                "confidence": confidence,
                "reasoning": reasoning,
                "timestamp": datetime.now().isoformat()
            }
    
    with col_clear:
        if st.button("🔄 Clear All", use_container_width=True):
            st.session_state.selected_items = set()
            st.session_state.parent_goals = set()
            for key in [k for k in st.session_state if str(k).startswith("prior_spec")]:
                del st.session_state[key]
            for goal_id, _ in PARENT_GOALS:
                st.session_state.pop(f"chk_{goal_id}", None)
            for item_id in ITEM_LABELS:
                st.session_state.pop(f"chk_{item_id}", None)
            if 'last_routing' in st.session_state:
                del st.session_state.last_routing
            st.rerun()
    
    # Routing Recommendation (Bottom of page)
    if 'last_routing' in st.session_state:
        st.markdown("---")
        st.markdown("### 🎯 Routing Recommendation")
        
        result = st.session_state.last_routing
        recommended = [result['clinic']] + result.get('also_recommend', [])
        if len(recommended) > 1:
            st.markdown(f"**Recommend {len(recommended)} clinics:**")
        
        # Display one card per recommended clinic
        for code in recommended:
            clinic_info = CLINICS[code]
            st.markdown(f"""
            <div class="clinic-card" style="background-color: {clinic_info['color']}14; border-left-color: {clinic_info['color']};">
                <h2>{clinic_info['name']}</h2>
                <p>{clinic_info['description']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Confidence level
        if result['confidence'] == "High":
            conf_class = "confidence-high"
            conf_emoji = "✅"
        elif result['confidence'] == "Medium":
            conf_class = "confidence-medium"
            conf_emoji = "⚠️"
        else:
            conf_class = "confidence-low"
            conf_emoji = "❓"
        
        st.markdown(f"**Confidence Level:** <span class='{conf_class}'>{conf_emoji} {result['confidence']}</span>", unsafe_allow_html=True)
        
        # Reasoning
        st.markdown("**Routing Reasoning:**")
        for reason in result['reasoning']:
            st.markdown(f"• {reason}")
        
        # Selected items summary
        col_summary1, col_summary2 = st.columns(2)
        
        with col_summary1:
            if result['selected_concerns']:
                st.markdown("**Selected Concerns:**")
                for concern in result['selected_concerns']:
                    st.markdown(f"• {concern_label(concern)}")
        
        with col_summary2:
            if result.get('parent_goals'):
                st.markdown("**Family Goals:** *(not used in routing yet)*")
                for goal_id in result['parent_goals']:
                    st.markdown(f"• {PARENT_GOAL_LABELS.get(goal_id, goal_id)}")
            if result.get('prior_specialist_seen'):
                st.markdown(f"**Seen a specialist before:** {result['prior_specialist_seen']}")
                for row in result.get('prior_specialists', []):
                    st.markdown(f"• {format_specialist(row)}")

        # Feedback collection
        st.markdown("---")
        st.markdown("### 🎓 Clinical Validation")
        st.markdown("*This is where we learn from your expertise*")
        
        matches = st.radio(
            "Does this match your clinical judgment?",
            ["Yes - This routing is correct", "No - I would route differently", "Uncertain - Complex case"],
            key="feedback_radio"
        )
        
        if matches != "Yes - This routing is correct":
            correct_clinic = st.selectbox(
                "Where would you route this patient?",
                list(CLINICS) + ["Needs more than one clinic", "Needs triage call"],
                format_func=lambda c: CLINICS[c]['name'] if c in CLINICS else c,
                key="correct_clinic"
            )
            
            explanation = st.text_area(
                "What clinical factors influenced your decision?",
                placeholder="This helps us understand the nuances...",
                key="explanation"
            )
            
            if st.button("💾 Save Feedback", use_container_width=True):
                feedback = result.copy()
                feedback['clinician_judgment'] = correct_clinic
                feedback['clinician_reasoning'] = explanation
                feedback['match_type'] = matches
                st.session_state.feedback_data.append(feedback)
                st.success("✅ Feedback saved! This data is gold for understanding edge cases.")
        else:
            if st.button("💾 Confirm Match", use_container_width=True):
                feedback = result.copy()
                feedback['clinician_judgment'] = clinic_codes(result)
                feedback['match_type'] = "Match"
                st.session_state.feedback_data.append(feedback)
                st.success("✅ Match confirmed!")

# MODE 2: Edge Case Explorer
elif st.session_state.current_mode == "Edge Case Explorer":
    st.subheader("🔍 Edge Case Explorer")
    st.markdown("*Where the current logic breaks down - and where the research begins*")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### Current Routing Logic: UCLA Pediatric Triage System")
        st.markdown("""
        ```
        ═══════════════════════════════════════════════════════════════
        UCLA TRIAGE: 7 CLINICS (rules run in order; first match wins)
        ═══════════════════════════════════════════════════════════════
        CAN · Peds Neuro NDD · DBP · HRIF · UC-LEND · MPAC · Psychiatry
        (* = assumption pending clinical review)

         1. Suicidal ideation/attempt ............ → PSYCHIATRY
         2. Angelman, Dup15q, HNRNPH2 ............ → PEDS NEURO
            Kabuki, ASXL, Prader-Willi ........... → CAN
            CDKL5, Rett, Down syndrome ........... → CAN *
            (+ PSYCHIATRY if a psych concern is also present)
         3. Tuberous Sclerosis Complex ........... → DBP
            (+ PEDS NEURO if seizures)
         4. Under 3 with CP or motor delays ...... → HRIF *
         5. Seizures + developmental diagnosis ... → PEDS NEURO
         6. Depression, PTSD, bipolar, OCD ....... → PSYCHIATRY
            (+ DBP if a developmental diagnosis)
         7. Under 2, any concern ................. → DBP
         8. Autism/ADHD + co-occurring condition . → PEDS NEURO *
         9. Global developmental delay ........... → PEDS NEURO
        10. Seizures, headaches, tics ............ → PEDS NEURO
            CP or motor delays (age 3+) .......... → CAN
        11. Anxiety + developmental diagnosis .... → DBP
            Anxiety alone ........................ → PSYCHIATRY
        12. Intellectual disability .............. → DBP
            (age 12+ → CAN *)
        13. Autism, ADHD, speech/language ........ → DBP
        14. Learning disability alone ............ → MPAC
        15. School supports / services only ...... → DBP

        ADD-ON: neuropsych or academic testing goal, or a
        learning disability → also MPAC

        UC-LEND: not yet reachable. The form doesn't ask about
        psychosocial complexity.
        ═══════════════════════════════════════════════════════════════
        ```
        """)
        
        st.markdown("### Core Principles")
        st.info("""
        **Prioritization:**
        1. **Safety first**: suicidal ideation or attempt routes to Psychiatry
        2. **Named syndromes go to their home clinic**: Peds Neuro's dedicated clinics, or CAN
        3. **Match the question to the clinic's stated scope**: each clinic's "sees" and "does not see" lists
        4. **Recommend more than one clinic when needed**, e.g. a syndrome plus a psych concern, or a testing need (MPAC)

        **Does NOT see (per clinic notes):**
        - **Peds Neuro NDD:** learning disability, psychiatric conditions alone
        - **DBP:** primary psych (ODD, conduct disorder, PTSD, depression), initial CP identification outside HRIF, older kids with a primary ID question
        - **HRIF:** follow-up after age 3 (or 5)
        - **UC-LEND:** full evaluations
        """)
    
    with col2:
        st.markdown("### Add an Edge Case")
        st.markdown("*Describe a patient who doesn't fit the flowchart*")
        
        with st.form("edge_case_form"):
            case_description = st.text_area(
                "Patient Presentation",
                placeholder="Example: 7-year-old with autism diagnosis since age 3, now presenting with new onset generalized tonic-clonic seizures...",
                height=150
            )
            
            why_edge_case = st.text_area(
                "Why is this challenging to route?",
                placeholder="Needs both DBP for autism management and CAN for new seizure workup, but unclear which should be primary...",
                height=100
            )
            
            clinical_decision = st.text_input(
                "What did you decide? (and why)",
                placeholder="Routed to CAN first for seizure management, plan to loop in DBP for behavioral support..."
            )
            
            submitted = st.form_submit_button("📝 Add Edge Case", use_container_width=True)
            
            if submitted and case_description:
                edge_case = {
                    "description": case_description,
                    "challenge": why_edge_case,
                    "decision": clinical_decision,
                    "timestamp": datetime.now().isoformat()
                }
                st.session_state.edge_cases.append(edge_case)
                st.success("✅ Edge case added! These become your research data.")
        
        # Display existing edge cases
        if st.session_state.edge_cases:
            st.markdown("### Collected Edge Cases")
            for idx, case in enumerate(st.session_state.edge_cases, 1):
                with st.expander(f"Case {idx}: {case['description'][:50]}..."):
                    st.markdown(f"**Full Description:**")
                    st.markdown(case['description'])
                    st.markdown(f"**Challenge:**")
                    st.markdown(case['challenge'])
                    if case['decision']:
                        st.markdown(f"**Clinical Decision:**")
                        st.markdown(case['decision'])

# MODE 3: Session Data
elif st.session_state.current_mode == "Session Data":
    st.subheader("📊 Research Data from This Session")
    st.markdown("*Every disagreement is a data point. Every edge case is a research question.*")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Routing Tests", len(st.session_state.feedback_data))
    with col2:
        st.metric("Edge Cases Documented", len(st.session_state.edge_cases))
    
    # Feedback data
    if st.session_state.feedback_data:
        st.markdown("### Routing Validation Data")
        
        # Calculate agreement rate
        matches = sum(1 for f in st.session_state.feedback_data if f.get('match_type') == "Match")
        total = len(st.session_state.feedback_data)
        agreement_rate = (matches / total * 100) if total > 0 else 0
        
        st.markdown(f"**Algorithm Agreement Rate:** {agreement_rate:.1f}% ({matches}/{total} cases)")
        
        # Show disagreements (the interesting data!)
        disagreements = [f for f in st.session_state.feedback_data if f.get('match_type') != "Match"]
        if disagreements:
            st.markdown("#### Cases Where Clinical Judgment Differed")
            for idx, case in enumerate(disagreements, 1):
                concerns = [
                    concern_label(c)
                    for c in case.get('selected_concerns', [])
                ]
                age = case.get('age', 0)
                age_label = f"{round(age * 12)} months" if age < 2 else f"{age:.0f} yrs"
                if concerns:
                    summary = ", ".join(concerns[:2]) + (f" +{len(concerns) - 2} more" if len(concerns) > 2 else "")
                else:
                    summary = "No concerns selected"
                with st.expander(f"Case {idx}: Age {age_label}, {summary}"):
                    if concerns:
                        st.markdown(f"**Selected concerns:** {', '.join(concerns)}")
                    if case.get('parent_goals'):
                        goals = ", ".join(PARENT_GOAL_LABELS.get(g, g) for g in case['parent_goals'])
                        st.markdown(f"**Family goals:** {goals}")
                    if case.get('prior_specialist_seen'):
                        prior = "; ".join(format_specialist(row) for row in case.get('prior_specialists', []))
                        st.markdown(f"**Seen a specialist before:** {case['prior_specialist_seen']}" + (f" ({prior})" if prior else ""))
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Algorithm Recommended:**")
                        st.markdown(f"{clinic_codes(case)} (Confidence: {case['confidence']})")
                        st.markdown("**Reasoning:**")
                        for reason in case['reasoning']:
                            st.markdown(f"• {reason}")
                    with col2:
                        st.markdown("**Clinician Decision:**")
                        st.markdown(case.get('clinician_judgment', 'Not specified'))
                        if case.get('clinician_reasoning'):
                            st.markdown("**Clinical Reasoning:**")
                            st.markdown(case['clinician_reasoning'])
        
        # Export button
        if st.button("📥 Export Session Data (JSON)", use_container_width=True):
            export_data = {
                "session_timestamp": datetime.now().isoformat(),
                "routing_tests": st.session_state.feedback_data,
                "edge_cases": st.session_state.edge_cases,
                "summary": {
                    "total_tests": total,
                    "matches": matches,
                    "agreement_rate": agreement_rate
                }
            }
            st.download_button(
                label="💾 Download JSON",
                data=json.dumps(export_data, indent=2),
                file_name=f"ucla_routing_session_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json"
            )
    
    # Edge cases
    if st.session_state.edge_cases:
        st.markdown("### Edge Case Documentation")
        for idx, case in enumerate(st.session_state.edge_cases, 1):
            with st.expander(f"Edge Case {idx}"):
                st.markdown(f"**Description:** {case['description']}")
                st.markdown(f"**Challenge:** {case['challenge']}")
                if case['decision']:
                    st.markdown(f"**Resolution:** {case['decision']}")
    
    if not st.session_state.feedback_data and not st.session_state.edge_cases:
        st.info("No data collected yet. Use 'Test the Logic' or 'Edge Case Explorer' to generate research data.")

# MODE 4: AI Vision
elif st.session_state.current_mode == "AI Vision":
    st.subheader("🚀 The AI Vision: From Rules to Intelligence")
    st.markdown("*How this prototype could evolve into an AI-powered triage system*")
    
    # Three phases
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="clinic-card dbp-card">
            <h3>📋 Phase 1: Today</h3>
            <h4>Rule-Based Prototype</h4>
            <p><strong>What:</strong> Simple decision tree based on age, symptoms, comorbidities</p>
            <p><strong>Purpose:</strong> Validate logic, identify edge cases, establish baseline</p>
            <p><strong>Status:</strong> ✅ Demo ready</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="clinic-card ppc-card">
            <h3>🧠 Phase 2: 6-12 Months</h3>
            <h4>AI Learning System</h4>
            <p><strong>What:</strong> AI observes clinician routing decisions and learns patterns</p>
            <p><strong>Purpose:</strong> Build training dataset of expert clinical reasoning</p>
            <p><strong>Requires:</strong> IRB approval, data collection protocol</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="clinic-card can-card">
            <h3>⚡ Phase 3: 12-24 Months</h3>
            <h4>Intelligent Triage</h4>
            <p><strong>What:</strong> AI routes 60-70% of cases automatically, flags complex cases</p>
            <p><strong>Purpose:</strong> Operational efficiency + continuous learning</p>
            <p><strong>Impact:</strong> Scales expertise, improves with use</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # What AI enables
    st.markdown("### 🎯 What AI Enables (That Rules Can't Do)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **1. Learns from Ambiguity**
        - Rules: "If age < 10, route to DBP"
        - AI: "For 9-year-olds with anxiety, you route to PPC 40% of the time and DBP 60%. The difference correlates with school refusal severity."
        
        **2. Handles Unstructured Data**
        - Rules: Need structured dropdowns
        - AI: Processes free-text referral notes
        - Example: "Mom reports 'meltdowns'" → AI recognizes behavioral regulation concern
        
        **3. Continuous Improvement**
        - Rules: Static, require manual updates
        - AI: Gets better with every referral
        - After 10,000 cases: Better than junior staff
        """)
    
    with col2:
        st.markdown("""
        **4. Generates Research Insights**
        - "Autism + mood symptoms route to PPC 3x more often when patient is >12 years old"
        - "Referrals mentioning 'school refusal' have 60% anxiety comorbidity"
        - These patterns become publications
        
        **5. Provides Explanations**
        - "I recommend CAN because:
          - New onset seizures (85% CAN probability)
          - Age 7 (young age increases CAN likelihood)
          - Similar to 47 past cases, 89% went to CAN"
        """)
    
    st.markdown("---")
    
    # How it works
    st.markdown("### 🔄 How Intelligent Triage Works")
    
    scenarios = [
        {
            "title": "Straightforward Cases (60-70%)",
            "emoji": "✅",
            "color": "#E8F4FA",
            "border": "#2774AE",
            "description": "AI routes automatically with high confidence",
            "example": "8-year-old with ADHD, no comorbidities → DBP",
            "action": "Clinician can override if needed"
        },
        {
            "title": "Complex Cases (20-30%)",
            "emoji": "⚠️",
            "color": "#FFF9E6",
            "border": "#FFD100",
            "description": "AI flags for expert review with reasoning",
            "example": "13-year-old autism + new suicidal ideation",
            "action": "System explains: 'Medium confidence - psychiatric symptoms in developmentally complex patient'"
        },
        {
            "title": "Urgent Cases (5-10%)",
            "emoji": "🚨",
            "color": "#FFEBEE",
            "border": "#C62828",
            "description": "AI detects crisis language and escalates immediately",
            "example": "Active suicidal plan with specific method",
            "action": "Immediate crisis pathway activation"
        },
        {
            "title": "Novel Cases (Edge Cases)",
            "emoji": "❓",
            "color": "#F0F7FB",
            "border": "#005587",
            "description": "System recognizes unfamiliar patterns",
            "example": "Presentation doesn't match any training data",
            "action": "Expert review required - system is learning"
        }
    ]
    
    for scenario in scenarios:
        st.markdown(f"""
        <div style="background-color: {scenario['color']}; padding: 15px; border-radius: 10px; margin: 10px 0; border-left: 5px solid {scenario['border']};">
            <h4>{scenario['emoji']} {scenario['title']}</h4>
            <p><strong>How it works:</strong> {scenario['description']}</p>
            <p><strong>Example:</strong> {scenario['example']}</p>
            <p><strong>Action:</strong> {scenario['action']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Value proposition
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💼 Operational Value")
        st.markdown("""
        - **40-60% time reduction** on routine referrals
        - **Consistent routing** across all staff
        - **Handle volume growth** without adding headcount
        - **Reduce routing errors** (wrong clinic = care delays)
        - **Flag multi-clinic** consultation needs
        """)
        
        st.markdown("### 🏆 Strategic Value")
        st.markdown("""
        - **UCLA becomes leader** in pediatric neuro AI
        - **First-of-its-kind** in behavioral neurology
        - **Attract research funding** and partnerships
        - **Licensable model** for other medical centers
        """)
    
    with col2:
        st.markdown("### 🔬 Research Value")
        st.markdown("""
        - **Publications** on clinical decision-making patterns
        - **Training data** for national pediatric neuro AI
        - **Grant opportunities** in implementation science
        - **Study question:** "How do expert clinicians make routing decisions in complex cases?"
        """)
        
        st.markdown("### 📈 Proven Precedents")
        st.markdown("""
        - **Epic Sepsis Prediction:** 100+ hospitals, mortality reduction
        - **Stanford Radiology AI:** 30% workload reduction
        - **Mass General ED Triage:** 15% wait time reduction
        
        *Your system would be the first in pediatric behavioral neurology*
        """)
    
    st.markdown("---")
    
    # The immediate collaboration
    st.markdown("### 🤝 The Immediate Next Steps (3 Months)")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **1. Validate Prototype**
        - Test with 20-30 real cases
        - Document where logic breaks
        - Refine routing criteria
        """)
    
    with col2:
        st.markdown("""
        **2. Document Edge Cases**
        - Systematic collection
        - Capture expert reasoning
        - Build initial training data
        """)
    
    with col3:
        st.markdown("""
        **3. Establish Baseline**
        - Current routing patterns
        - Agreement rates
        - Pursue IRB approval
        """)
    
    st.markdown("---")
    
    # The vision
    st.info("""
    **The Vision:** A system where families get same-day routing responses, clinicians focus expertise on 
    truly complex cases, the system learns from every decision, UCLA publishes groundbreaking research, 
    and other medical centers adopt your model.
    
    *"This is about scaling your expertise, not replacing it. Every referral you route becomes training 
    data for an AI that gets smarter with every decision you make."*
    """)
    
    # The research question
    st.success("""
    **Core Research Question:** What clinical factors predict disagreement between rule-based routing 
    and expert clinical judgment in complex pediatric neurology referrals?
    
    This question is publishable regardless of whether we build the AI system. The prototype you're 
    testing today is already collecting that research data.
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #005587; padding: 2rem;'>
    <p><strong>UCLA AI Triage Prototype</strong></p>
    <p>A research tool for understanding clinical decision-making patterns in pediatric neurology referrals</p>
    <p style='font-size: 0.9rem; margin-top: 1rem;'>
        Built to facilitate collaboration between clinical expertise and systems engineering<br>
        Every routing decision, every edge case, every disagreement is valuable research data
    </p>
</div>
""", unsafe_allow_html=True)
