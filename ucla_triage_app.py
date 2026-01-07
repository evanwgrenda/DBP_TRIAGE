import streamlit as st
import pandas as pd
from datetime import datetime
import json

# Page config
st.set_page_config(
    page_title="UCLA Neuro Clinic Routing Prototype",
    page_icon="🏥",
    layout="wide"
)

# Custom CSS for professional medical styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2C5F8D;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .clinic-card {
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid;
    }
    .dbp-card {
        background-color: #E3F2FD;
        border-left-color: #1976D2;
    }
    .can-card {
        background-color: #F3E5F5;
        border-left-color: #7B1FA2;
    }
    .ppc-card {
        background-color: #E8F5E9;
        border-left-color: #388E3C;
    }
    .confidence-high {
        color: #2E7D32;
        font-weight: bold;
    }
    .confidence-medium {
        color: #F57C00;
        font-weight: bold;
    }
    .confidence-low {
        color: #C62828;
        font-weight: bold;
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
        "color": "#1976D2"
    },
    "CAN": {
        "name": "Child & Adolescent Neurology",
        "description": "Epilepsy, complex neurological conditions, movement disorders",
        "color": "#7B1FA2"
    },
    "PPC": {
        "name": "Pediatric Psychiatry Clinic",
        "description": "Mood disorders, anxiety, behavioral health in older children/adolescents",
        "color": "#388E3C"
    }
}

def route_patient(age, primary_concern, comorbidities):
    """
    Core routing logic - intentionally simple to expose edge cases
    Returns: (clinic, confidence, reasoning)
    """
    reasoning = []
    confidence = "High"
    
    # Age-based initial routing
    if age < 5:
        reasoning.append(f"Patient age {age} suggests early developmental focus")
        if "Seizures/Epilepsy" in comorbidities:
            confidence = "Medium"
            reasoning.append("⚠️ Young child with seizures - may need dual DBP/CAN assessment")
            return "CAN", confidence, reasoning
        return "DBP", "High", reasoning
    
    # Primary concern routing
    if primary_concern == "Autism Spectrum":
        if age > 10 and any(mood in comorbidities for mood in ["Depression", "Anxiety", "Suicidal Ideation"]):
            confidence = "Medium"
            reasoning.append("⚠️ Older child with autism AND significant mood concerns")
            reasoning.append("May need PPC for psychiatric symptoms, DBP for autism management")
            return "PPC", confidence, reasoning
        reasoning.append("Autism spectrum concerns route to DBP")
        return "DBP", "High", reasoning
    
    if primary_concern == "ADHD Only":
        if age < 8:
            reasoning.append("Younger child with ADHD - developmental lens preferred")
            return "DBP", "High", reasoning
        if "School Refusal" in comorbidities or "Anxiety" in comorbidities:
            reasoning.append("ADHD with behavioral/anxiety components suggests psychiatric evaluation")
            return "PPC", "High", reasoning
        reasoning.append("Straightforward ADHD in school-age child")
        return "DBP", "High", reasoning
    
    if primary_concern in ["Depression/Mood Disorder", "Anxiety Disorder"]:
        if age < 10:
            confidence = "Medium"
            reasoning.append("⚠️ Young child with mood disorder - consider developmental factors")
        reasoning.append("Primary mood/anxiety disorder routes to PPC")
        return "PPC", "High" if age >= 10 else "Medium", reasoning
    
    if primary_concern == "Seizures/Epilepsy":
        if "Autism Spectrum" in comorbidities or "Developmental Delay" in comorbidities:
            confidence = "Medium"
            reasoning.append("⚠️ Seizures with developmental concerns - complex case")
            reasoning.append("CAN for neurological management, may need DBP consultation")
        else:
            reasoning.append("Primary seizure disorder routes to CAN")
        return "CAN", confidence, reasoning
    
    if primary_concern == "Tics/Movement Disorder":
        if "ADHD" in comorbidities and age < 10:
            confidence = "Medium"
            reasoning.append("⚠️ Tics with ADHD - could be neurological or developmental")
            return "CAN", confidence, reasoning
        reasoning.append("Movement disorders route to CAN neurology")
        return "CAN", "High", reasoning
    
    if primary_concern == "Behavioral Problems":
        if age >= 10:
            reasoning.append("Behavioral problems in adolescent suggest psychiatric evaluation")
            return "PPC", "High", reasoning
        else:
            reasoning.append("Behavioral problems in younger child - developmental assessment")
            return "DBP", "High", reasoning
    
    # Default fallback
    return "DBP", "Low", ["⚠️ Unclear presentation - defaulting to DBP for initial assessment"]

# Header
st.markdown('<div class="main-header">🏥 UCLA Neuro Clinic Routing Prototype</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Building the Next Generation Integrated Clinic</div>', unsafe_allow_html=True)

# Mode selector
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    if st.button("🎯 Test the Logic", use_container_width=True, type="primary" if st.session_state.current_mode == "Test the Logic" else "secondary"):
        st.session_state.current_mode = "Test the Logic"
with col2:
    if st.button("🔍 Edge Case Explorer", use_container_width=True, type="primary" if st.session_state.current_mode == "Edge Case Explorer" else "secondary"):
        st.session_state.current_mode = "Edge Case Explorer"
with col3:
    if st.button("📊 Session Data", use_container_width=True, type="primary" if st.session_state.current_mode == "Session Data" else "secondary"):
        st.session_state.current_mode = "Session Data"

st.markdown("---")

# MODE 1: Test the Logic
if st.session_state.current_mode == "Test the Logic":
    st.subheader("🎯 Interactive Routing Simulator")
    st.markdown("*Use this tool to test routing logic with real-world patient presentations*")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### Patient Information")
        
        age = st.slider("Patient Age", 2, 18, 8)
        
        primary_concern = st.selectbox(
            "Primary Presenting Concern",
            [
                "Autism Spectrum",
                "ADHD Only",
                "Depression/Mood Disorder",
                "Anxiety Disorder",
                "Seizures/Epilepsy",
                "Tics/Movement Disorder",
                "Behavioral Problems",
                "Developmental Delay"
            ]
        )
        
        st.markdown("**Comorbidities / Additional Concerns**")
        comorbidities = st.multiselect(
            "Select all that apply:",
            [
                "Autism Spectrum",
                "ADHD",
                "Depression",
                "Anxiety",
                "Suicidal Ideation",
                "Seizures/Epilepsy",
                "Developmental Delay",
                "School Refusal",
                "Sleep Problems",
                "Eating Problems"
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
        st.markdown("### Current Routing Logic")
        st.markdown("""
        ```
        START: Patient Referral
        │
        ├─ Age < 5 years?
        │   ├─ YES → Check for seizures
        │   │   ├─ Seizures present → CAN (Medium confidence)
        │   │   └─ No seizures → DBP (High confidence)
        │   │
        │   └─ NO → Continue to primary concern
        │
        ├─ Primary Concern: Autism
        │   ├─ Age > 10 AND mood symptoms? → PPC (Medium confidence)
        │   └─ Otherwise → DBP (High confidence)
        │
        ├─ Primary Concern: ADHD
        │   ├─ Age < 8 → DBP (High confidence)
        │   ├─ Age ≥ 8 + anxiety/behavioral → PPC (High confidence)
        │   └─ Age ≥ 8, straightforward → DBP (High confidence)
        │
        ├─ Primary Concern: Mood/Anxiety
        │   ├─ Age < 10 → PPC (Medium confidence - consider developmental)
        │   └─ Age ≥ 10 → PPC (High confidence)
        │
        ├─ Primary Concern: Seizures/Epilepsy
        │   ├─ + Developmental concerns → CAN (Medium confidence)
        │   └─ No developmental concerns → CAN (High confidence)
        │
        ├─ Primary Concern: Tics/Movement
        │   ├─ + ADHD, Age < 10 → CAN (Medium confidence)
        │   └─ Otherwise → CAN (High confidence)
        │
        └─ Primary Concern: Behavioral Problems
            ├─ Age ≥ 10 → PPC (High confidence)
            └─ Age < 10 → DBP (High confidence)
        ```
        """)
        
        st.markdown("### Known Limitations")
        st.warning("""
        **Where this logic fails:**
        - Dual diagnoses (e.g., autism + new onset psychosis)
        - Medical complexity (e.g., genetic syndromes)
        - Family preference/history with specific clinics
        - Insurance/access constraints
        - Cases requiring immediate crisis intervention
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

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p><strong>UCLA Neuro Clinic Routing Prototype</strong></p>
    <p>A research tool for understanding clinical decision-making patterns in pediatric neurology referrals</p>
    <p style='font-size: 0.9rem; margin-top: 1rem;'>
        Built to facilitate collaboration between clinical expertise and systems engineering<br>
        Every routing decision, every edge case, every disagreement is valuable research data
    </p>
</div>
""", unsafe_allow_html=True)
