import streamlit as st
import pandas as pd
from datetime import datetime
import json

# Page config
st.set_page_config(
    page_title="UCLA Triage Prototype",
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
    }
    div[data-testid="stButton"] button[kind="primary"] {
        background-color: #2774AE;
        border-color: #2774AE;
    }
    div[data-testid="stButton"] button[kind="primary"]:hover {
        background-color: #005587;
        border-color: #005587;
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

# Clinic definitions
CLINICS = {
    "DBP": {
        "name": "Developmental & Behavioral Pediatrics",
        "description": "Autism, ADHD, developmental delays in younger children",
        "color": "#2774AE"
    },
    "CAN": {
        "name": "Child & Adolescent Neurology",
        "description": "Epilepsy, complex neurological conditions, movement disorders",
        "color": "#FFD100"
    },
    "PPC": {
        "name": "Pediatric Psychiatry Clinic",
        "description": "Mood disorders, anxiety, behavioral health in older children/adolescents",
        "color": "#005587"
    }
}

def route_patient(age, primary_concern, comorbidities):
    """
    Clinical triage logic: DBP vs Neurology vs Psychiatry
    Based on UCLA's structured triage system prioritizing safety, early intervention, and appropriate specialty scope
    Returns: (clinic, confidence, reasoning)
    """
    reasoning = []
    confidence = "High"
    
    # Helper function to check for specific concerns
    def has_concern(concern_list, check_list):
        return any(concern in comorbidities or concern in [primary_concern] for concern in check_list)
    
    # STEP 2: SAFETY SCREEN (OVERRIDES ALL AGE-BASED ROUTING)
    safety_concerns = ["Suicidal Ideation", "Suicide Attempt", "Acute Psychiatric Crisis"]
    if has_concern(comorbidities, safety_concerns):
        reasoning.append("🚨 SAFETY PRIORITY: Acute psychiatric safety concern detected")
        reasoning.append("Immediate referral to Child & Adolescent Psychiatry required")
        reasoning.append("DBP is not appropriate as first-line care for acute safety concerns")
        return "PPC", "High", reasoning
    
    # STEP 3: NEUROLOGIC DISEASE SCREEN (OVERRIDES AGE FOR SPECIFIC CONDITIONS)
    neurologic_conditions = [
        "Uncontrolled Seizures", "Epilepsy", "Serious Head Injury", 
        "Tuberous Sclerosis", "Cerebral Palsy", "Abnormal Neurogenetic Testing",
        "Frequent Headaches/Migraines"
    ]
    if has_concern(comorbidities, neurologic_conditions):
        reasoning.append("🧠 NEUROLOGIC CONDITION: Primary neurologic disease detected")
        reasoning.append("Refer to Pediatric Neurology first for neurologic evaluation")
        
        # Check if developmental concerns also present
        developmental_concerns = [
            "Developmental Delay", "Autism Spectrum", "IEP or 504 Plan",
            "Regional Center Services"
        ]
        if has_concern(comorbidities, developmental_concerns):
            reasoning.append("Note: Developmental/behavioral concerns also present")
            reasoning.append("DBP may follow after neurologic evaluation for developmental impact")
            confidence = "Medium"
        
        return "CAN", confidence, reasoning
    
    # STEP 1: AGE-BASED PRIORITIZATION
    
    # AGE < 2 YEARS: DBP Fast-Track
    if age < 2:
        reasoning.append("👶 Age < 2 years: DBP Fast-Track Priority")
        reasoning.append("Early intervention is critical for developmental and behavioral concerns")
        
        # Check for DBP-relevant concerns
        developmental_concerns = [
            "Developmental Delay", "Autism Concern", "Autism Concern (Need Evaluation)",
            "Milestone Loss/Plateau", "Feeding Difficulties", "Sleep Difficulties", 
            "Regulation Difficulties", "Regional Center Services", 
            "Abnormal Developmental Screening", "Language Disorder"
        ]
        
        if has_concern(comorbidities + [primary_concern], developmental_concerns):
            reasoning.append("Developmental, behavioral, or regulatory concern present → DBP")
            return "DBP", "High", reasoning
        
        # For very young children, default to DBP for almost any concern
        if primary_concern not in ["Uncontrolled Seizures", "Epilepsy Follow-up (No Developmental Concerns)"]:
            reasoning.append("Any developmental or behavioral concern in child <2 years → DBP")
            return "DBP", "High", reasoning
    
    # AGE 2-5 YEARS: DBP Preferred
    elif age >= 2 and age < 6:
        reasoning.append("🧒 Age 2-5 years: DBP Preferred for Developmental Concerns")
        
        # DBP-preferred conditions
        dbp_conditions = [
            "Autism Spectrum (Diagnosed)", "Autism Concern (Need Evaluation)", 
            "Autism Evaluation Needed", "Developmental Delay / Milestone Concerns",
            "Language Disorder", "ADHD vs Autism Diagnostic Question",
            "Global Developmental Delay", "Multidomain Concerns"
        ]
        
        if primary_concern in dbp_conditions or has_concern(comorbidities, [
            "IEP or 504 Plan", "Early Childhood Special Education", "Multidomain Concerns"
        ]):
            reasoning.append("Complex developmental presentation requiring DBP evaluation")
            return "DBP", "High", reasoning
        
        # Check for primary psychiatric condition requiring medication
        if primary_concern in [
            "Major Depressive Disorder", "Severe Anxiety Disorder",
            "Mood Disorder Requiring Medication"
        ]:
            if not has_concern(comorbidities, ["Developmental Delay", "Autism Spectrum", "Learning Disability"]):
                reasoning.append("Primary mood/anxiety disorder requiring medication management")
                reasoning.append("No significant developmental concerns → Psychiatry appropriate")
                return "PPC", "High", reasoning
        
        # Default to DBP for this age range
        reasoning.append("Preschool age with behavioral/developmental concern → DBP preferred")
        return "DBP", "High", reasoning
    
    # AGE ≥ 6 YEARS: Selective DBP Use
    else:
        reasoning.append(f"📚 Age {age:.0f} years: Selective DBP criteria apply")
        
        # STEP 4: PRIMARY PSYCHIATRIC CONDITION SCREEN
        primary_psychiatric_concerns = [
            "Bipolar Disorder", "Moderate to Severe OCD", "Major Depressive Disorder",
            "Severe Anxiety Disorder", "Severe Anxiety or Panic Attacks"
        ]
        
        if primary_concern in primary_psychiatric_concerns or has_concern(comorbidities, [
            "Bipolar Disorder", "Psychiatric Hospitalization History"
        ]):
            reasoning.append("Primary psychiatric condition identified")
            reasoning.append("Refer to Child & Adolescent Psychiatry")
            
            developmental_complexity = [
                "IEP or 504 Plan", "Autism Spectrum", "ADHD", "Learning Disability"
            ]
            if has_concern(comorbidities, developmental_complexity):
                reasoning.append("Note: Developmental concerns present - DBP may co-manage later")
                confidence = "Medium"
            
            return "PPC", confidence, reasoning
        
        # STEP 5: DEVELOPMENTAL / SYSTEMS-BASED COMPLEXITY
        # Check for DBP-appropriate complexity
        if primary_concern == "Complex Neurodevelopmental Profile":
            reasoning.append("✅ Complex neurodevelopmental profile identified")
            reasoning.append("Multiple domains affected - DBP evaluation appropriate")
            return "DBP", "High", reasoning
        
        if primary_concern == "Diagnostic Uncertainty Across Domains":
            reasoning.append("✅ Diagnostic uncertainty across developmental domains")
            reasoning.append("DBP evaluation needed for diagnostic clarification and integration")
            return "DBP", "High", reasoning
        
        dbp_complexity_indicators = [
            "IEP or 504 Plan",
            "Regional Center Services",
            "Receives Multiple Therapies (OT/PT/Speech/ABA)",
            "School-System Complexity",
            "Prior Neuro/Psych Care Insufficient",
            "Autism Spectrum + ADHD + Learning Disability"
        ]
        
        if has_concern(comorbidities, dbp_complexity_indicators):
            reasoning.append("✅ DBP-Appropriate Complexity Identified:")
            
            complexity_factors = []
            if "IEP or 504 Plan" in comorbidities:
                complexity_factors.append("School system involvement (IEP/504)")
            if has_concern(comorbidities, ["Autism Spectrum", "ADHD", "Learning Disability"]):
                complexity_factors.append("Multiple neurodevelopmental domains")
            if "Receives Multiple Therapies (OT/PT/Speech/ABA)" in comorbidities:
                complexity_factors.append("Multiple therapy services")
            if "Regional Center Services" in comorbidities:
                complexity_factors.append("Regional Center services")
            if "School-System Complexity" in comorbidities:
                complexity_factors.append("School-system complexity requiring navigation")
            
            for factor in complexity_factors:
                reasoning.append(f"  • {factor}")
            
            reasoning.append("Concerns span multiple domains requiring diagnostic integration")
            reasoning.append("DBP appropriate for systems-based complexity and school navigation")
            return "DBP", "High", reasoning
        
        # DBP GUARDRAILS (Age ≥ 6) - DO NOT refer to DBP for these
        if primary_concern in [
            "Isolated Depression (No Developmental Concerns)",
            "Isolated Anxiety (No Developmental Concerns)",
            "Isolated OCD"
        ]:
            reasoning.append("❌ DBP Guardrail: Isolated psychiatric concern without developmental complexity")
            reasoning.append("This does not meet DBP criteria for older children")
            reasoning.append("→ Refer to Child & Adolescent Psychiatry")
            return "PPC", "High", reasoning
        
        if primary_concern in [
            "Straightforward Migraine Management",
            "Epilepsy Follow-up (No Developmental Concerns)"
        ]:
            reasoning.append("❌ DBP Guardrail: Isolated neurologic concern without developmental complexity")
            reasoning.append("This does not meet DBP criteria")
            reasoning.append("→ Refer to Pediatric Neurology")
            return "CAN", "High", reasoning
        
        if primary_concern == "Medication Refills Only":
            reasoning.append("❌ DBP Guardrail: Medication management without diagnostic complexity")
            reasoning.append("This does not meet DBP criteria")
            reasoning.append("→ Coordinate with primary care or existing specialist")
            return "PPC", "Medium", reasoning
        
        # Check for autism/ADHD in older children
        if primary_concern in ["Autism Spectrum (Diagnosed)", "Autism Concern (Need Evaluation)"]:
            if has_concern(comorbidities, ["IEP or 504 Plan", "School-System Complexity", "Learning Disability"]):
                reasoning.append("Autism with school/learning complexity → DBP appropriate")
                return "DBP", "High", reasoning
            else:
                reasoning.append("Autism in older child without clear complexity indicators")
                reasoning.append("Consider if diagnostic integration truly needed")
                confidence = "Medium"
                return "DBP", confidence, reasoning
        
        # Check for straightforward ADHD
        if primary_concern == "ADHD (Straightforward)":
            if not has_concern(comorbidities, ["Autism Spectrum", "Learning Disability", "IEP or 504 Plan"]):
                reasoning.append("Straightforward ADHD in school-age child")
                reasoning.append("Can be managed by Psychiatry or primary care")
                reasoning.append("DBP referral not necessary without complicating factors")
                return "PPC", "High", reasoning
            else:
                reasoning.append("ADHD with developmental/learning complexity → DBP appropriate")
                return "DBP", "High", reasoning
        
        # Check for diagnostic complexity
        if primary_concern == "ADHD vs Autism Diagnostic Question":
            reasoning.append("Diagnostic complexity requiring differentiation")
            reasoning.append("DBP evaluation needed for diagnostic clarification")
            return "DBP", "High", reasoning
        
        # Developmental delay in older children
        if primary_concern == "Developmental Delay / Milestone Concerns":
            reasoning.append("Developmental concerns in school-age child")
            if has_concern(comorbidities, ["IEP or 504 Plan"]):
                reasoning.append("School services involved → DBP appropriate")
                return "DBP", "High", reasoning
            else:
                reasoning.append("Consider if multidomain complexity present")
                return "DBP", "Medium", reasoning
        
        # Learning disability
        if primary_concern == "Learning Disability":
            if has_concern(comorbidities, ["ADHD", "Autism Spectrum", "IEP or 504 Plan"]):
                reasoning.append("Learning disability with neurodevelopmental complexity")
                return "DBP", "High", reasoning
            else:
                reasoning.append("⚠️ Isolated learning disability may not require DBP")
                reasoning.append("Consider neuropsychological evaluation or school-based support")
                return "DBP", "Medium", reasoning
        
        # Neurologic conditions in older children
        if primary_concern in ["Uncontrolled Seizures", "Frequent Headaches/Migraines"]:
            reasoning.append("Primary neurologic concern → Neurology")
            if has_concern(comorbidities, ["Developmental Delay", "Autism Spectrum"]):
                reasoning.append("Note: Developmental concerns present - DBP may be needed later")
                confidence = "Medium"
            return "CAN", confidence, reasoning
        
        # Default for older children without clear complexity
        reasoning.append("⚠️ Older child: Evaluate if DBP complexity criteria are met")
        reasoning.append("Consider whether developmental integration is truly needed")
        confidence = "Medium"
        
        # Make educated guess based on what's present
        if has_concern(comorbidities, ["ADHD", "Autism Spectrum", "Developmental Delay"]):
            reasoning.append("Neurodevelopmental concerns present → DBP may be appropriate")
            return "DBP", confidence, reasoning
        elif has_concern(comorbidities + [primary_concern], ["Depression", "Anxiety", "Bipolar"]):
            reasoning.append("Psychiatric concerns predominate → Psychiatry likely appropriate")
            return "PPC", confidence, reasoning
        else:
            reasoning.append("Unclear presentation - recommend clinical triage discussion")
            return "DBP", "Low", reasoning

# Header
st.markdown('<div class="main-header">🏥 UCLA Neuro Clinic Routing Prototype</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Building the Next Generation Integrated Clinic • DBP • CAN • PPC</div>', unsafe_allow_html=True)

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
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### Patient Information")
        
        age_years = st.slider("Patient Age (years)", 0, 18, 8)
        
        if age_years < 2:
            age_months = st.slider("Age in Months", 0, 23, age_years * 12)
            age = age_months / 12.0
            st.caption(f"Total age: {age_months} months ({age:.1f} years)")
        else:
            age = age_years
        
        primary_concern = st.selectbox(
            "Primary Presenting Concern",
            [
                "Autism Concern (Need Evaluation)",
                "Autism Spectrum (Diagnosed)",
                "ADHD (Straightforward)",
                "ADHD vs Autism Diagnostic Question",
                "Developmental Delay / Milestone Concerns",
                "Language Disorder",
                "Learning Disability",
                "Major Depressive Disorder",
                "Severe Anxiety Disorder",
                "Bipolar Disorder",
                "Moderate to Severe OCD",
                "Isolated Depression (No Developmental Concerns)",
                "Isolated Anxiety (No Developmental Concerns)",
                "Isolated OCD",
                "Uncontrolled Seizures",
                "Epilepsy Follow-up (No Developmental Concerns)",
                "Frequent Headaches/Migraines",
                "Straightforward Migraine Management",
                "Complex Neurodevelopmental Profile",
                "Diagnostic Uncertainty Across Domains",
                "Medication Refills Only"
            ]
        )
        
        st.markdown("**Comorbidities / Additional Concerns**")
        comorbidities = st.multiselect(
            "Select all that apply:",
            [
                # Safety Concerns
                "Suicidal Ideation",
                "Suicide Attempt",
                "Acute Psychiatric Crisis",
                
                # Neurologic Conditions
                "Uncontrolled Seizures",
                "Epilepsy",
                "Serious Head Injury",
                "Tuberous Sclerosis",
                "Cerebral Palsy",
                "Abnormal Neurogenetic Testing",
                "Frequent Headaches/Migraines",
                
                # Developmental/Neurodevelopmental
                "Autism Spectrum",
                "ADHD",
                "Developmental Delay",
                "Learning Disability",
                "Language Disorder",
                "Milestone Loss/Plateau",
                "Abnormal Developmental Screening",
                
                # Psychiatric
                "Depression",
                "Anxiety",
                "Bipolar Disorder",
                "Moderate to Severe OCD",
                "Severe Anxiety or Panic Attacks",
                "Psychiatric Hospitalization History",
                "Mood Disorder Requiring Medication",
                
                # Systems/Services
                "IEP or 504 Plan",
                "Early Childhood Special Education",
                "Regional Center Services",
                "Receives Multiple Therapies (OT/PT/Speech/ABA)",
                "School-System Complexity",
                "Prior Neuro/Psych Care Insufficient",
                
                # Other Concerns
                "Feeding Difficulties",
                "Sleep Difficulties",
                "Regulation Difficulties",
                "Multidomain Concerns",
                "Autism Spectrum + ADHD + Learning Disability"
            ]
        )
        
        additional_notes = st.text_area(
            "Additional Clinical Notes (optional)",
            placeholder="Any other relevant information..."
        )
        
        if st.button("🔍 Route Patient", type="primary", use_container_width=True):
            clinic, confidence, reasoning = route_patient(age, primary_concern, comorbidities)
            
            st.session_state.last_routing = {
                "age": age,
                "primary_concern": primary_concern,
                "comorbidities": comorbidities,
                "notes": additional_notes,
                "clinic": clinic,
                "confidence": confidence,
                "reasoning": reasoning,
                "timestamp": datetime.now().isoformat()
            }
    
    with col2:
        st.markdown("### Routing Recommendation")
        
        if 'last_routing' in st.session_state:
            result = st.session_state.last_routing
            clinic_info = CLINICS[result['clinic']]
            
            # Display clinic recommendation
            if result['clinic'] == "DBP":
                card_class = "dbp-card"
            elif result['clinic'] == "CAN":
                card_class = "can-card"
            else:
                card_class = "ppc-card"
            
            st.markdown(f"""
            <div class="clinic-card {card_class}">
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
                    ["DBP", "CAN", "PPC", "Needs dual assessment", "Needs triage call"],
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
                    feedback['clinician_judgment'] = result['clinic']
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
        STRUCTURED PEDIATRIC TRIAGE: DBP vs NEUROLOGY vs PSYCHIATRY
        ═══════════════════════════════════════════════════════════════
        
        STEP 2: SAFETY SCREEN (Overrides All Age-Based Routing)
        ────────────────────────────────────────────────────────────
        → Suicidal ideation/attempt → PSYCHIATRY (Immediate)
        → Acute psychiatric crisis → PSYCHIATRY (Immediate)
        
        
        STEP 3: NEUROLOGIC DISEASE SCREEN (Overrides Age)
        ────────────────────────────────────────────────────────────
        → Uncontrolled seizures → NEUROLOGY
        → Serious head injury → NEUROLOGY
        → Tuberous sclerosis → NEUROLOGY
        → Cerebral palsy → NEUROLOGY
        → Abnormal neurogenetic testing → NEUROLOGY
        → Frequent headaches/migraines → NEUROLOGY
        
        (Note: DBP may follow for developmental/behavioral impact)
        
        
        STEP 1: AGE-BASED PRIORITIZATION
        ────────────────────────────────────────────────────────────
        
        AGE < 2 YEARS: DBP FAST-TRACK
        ▸ Default to DBP for ANY developmental/behavioral concern:
          • Developmental delay (any domain)
          • Autism concern
          • Milestone loss or plateau
          • Feeding, sleep, or regulation difficulties
          • Regional Center referral
          • Abnormal developmental screening
        
        
        AGE 2-5 YEARS: DBP PREFERRED
        ▸ Refer to DBP for:
          • Autism evaluation or diagnostic clarification
          • Global developmental delay
          • Language disorder
          • ADHD vs autism vs anxiety diagnostic question
          • Has IEP or early childhood special education
          • Multidomain concerns across home and school
        
        ▸ Psychiatry preferred ONLY if:
          • Primary mood/anxiety requiring medication
          • No significant developmental concerns
        
        
        AGE ≥ 6 YEARS: SELECTIVE DBP USE
        ▸ Refer to DBP ONLY if:
          • Complex neurodevelopmental profile
            (e.g., ASD + ADHD + learning disability)
          • Diagnostic uncertainty across domains
          • School-system complexity (IEP/504 + behavioral)
          • Prior Neuro/Psych care insufficient
          • Integration across specialties required
        
        
        STEP 4: PRIMARY PSYCHIATRIC CONDITION SCREEN (Age ≥ 6)
        ────────────────────────────────────────────────────────────
        → Bipolar disorder → PSYCHIATRY
        → Moderate to severe OCD → PSYCHIATRY
        → Major depressive disorder → PSYCHIATRY
        → Severe anxiety/panic attacks → PSYCHIATRY
        → Psychiatric hospitalization history → PSYCHIATRY
        
        (Note: DBP may co-manage later for developmental/school issues)
        
        
        STEP 5: DEVELOPMENTAL/SYSTEMS COMPLEXITY (Age ≥ 6)
        ────────────────────────────────────────────────────────────
        Refer to DBP when concerns span multiple domains:
        ▸ Has IEP or 504 Plan
        ▸ Regional Center services
        ▸ Receives OT, PT, speech, ABA, or counseling
        ▸ Family needs diagnostic integration + school navigation
        ▸ No acute neuro/psych condition explains full presentation
        
        
        DBP GUARDRAILS (Age ≥ 6) - DO NOT REFER TO DBP:
        ────────────────────────────────────────────────────────────
        ✗ Isolated depression, anxiety, or OCD
        ✗ Bipolar disorder
        ✗ Active suicidal ideation
        ✗ Straightforward migraine management
        ✗ Epilepsy follow-up without developmental concerns
        ✗ Medication refills without diagnostic complexity
        
        ═══════════════════════════════════════════════════════════════
        ```
        """)
        
        st.markdown("### Core Principles")
        st.info("""
        **Prioritization:**
        1. **Safety first**: Acute psychiatric crises override all other routing
        2. **Early intervention**: Children <2 years default to DBP for developmental concerns
        3. **Appropriate scope**: Route to the specialty best suited for the primary concern
        4. **Preserve DBP access**: For older children, reserve DBP for complex, multidomain cases
        
        **DBP is most appropriate when:**
        - Multiple developmental domains affected
        - Diagnostic uncertainty across areas
        - School system complexity requires navigation
        - Integration across specialties needed
        
        **DBP is NOT appropriate for:**
        - Isolated psychiatric conditions
        - Straightforward neurologic disease
        - Medication management only
        - Single-domain concerns in older children
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
                with st.expander(f"Case {idx}: Age {case['age']}, {case['primary_concern']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Algorithm Recommended:**")
                        st.markdown(f"{case['clinic']} (Confidence: {case['confidence']})")
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
    <p><strong>UCLA Neuro Clinic Routing Prototype</strong></p>
    <p>A research tool for understanding clinical decision-making patterns in pediatric neurology referrals</p>
    <p style='font-size: 0.9rem; margin-top: 1rem;'>
        Built to facilitate collaboration between clinical expertise and systems engineering<br>
        Every routing decision, every edge case, every disagreement is valuable research data
    </p>
</div>
""", unsafe_allow_html=True)
