# UCLA Neuro Clinic Routing Prototype

A research tool for understanding clinical decision-making patterns in pediatric neurology referrals.

## Quick Start (For Tomorrow's Demo)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

If you don't have pip installed or get errors, try:
```bash
pip3 install -r requirements.txt
```

### 2. Run the App

```bash
streamlit run ucla_triage_app.py
```

The app will open automatically in your browser at `http://localhost:8501`

If it doesn't open automatically, copy that URL and paste it into your browser.

### 3. Stop the App

Press `Ctrl+C` in the terminal when you're done.

---

## What This Tool Does

This is a **research collaboration tool** that helps Dr. Jeste see her own clinical decision-making patterns in a new way. It's designed to:

1. **Validate routing logic** with real-world cases
2. **Capture edge cases** where the logic breaks
3. **Collect data** on clinical judgment vs. algorithmic recommendations
4. **Generate research questions** about decision-making patterns

---

## Demo Script for Your Meeting

### Opening (2 minutes)

**"Dr. Jeste, I built this prototype because I wanted to understand how you think about routing decisions across DBP, CAN, and PPC. I'm hoping we can break it together - because every time you tell me 'No, that's wrong,' we're collecting valuable data about clinical decision-making."**

### Mode 1: Test the Logic (5-7 minutes)

**Start with a straightforward case:**
- Age: 7
- Primary Concern: ADHD Only
- No comorbidities
- **Expected result:** Routes to DBP with high confidence

**"This one's easy, right? Let's try something messier..."**

**Try an edge case:**
- Age: 13
- Primary Concern: Autism Spectrum  
- Comorbidities: Depression, Suicidal Ideation
- **Expected result:** Routes to PPC (Medium confidence)

**"Now here's where I need your expertise - does this match how you'd route this patient?"**

Let her explain why this is or isn't correct. **Every disagreement is gold** - that's the data you want to capture.

### Mode 2: Edge Case Explorer (5-7 minutes)

**"I know there are cases that don't fit any flowchart. Can you describe a patient who broke your routing logic?"**

Common edge cases she might mention:
- Young child with autism + new onset seizures
- Teenager with long-standing ADHD presenting with first psychotic episode  
- Complex genetic syndrome with multiple neurological features
- Patient currently in crisis who needs immediate psychiatric care

**Document 2-3 real examples from her clinical experience.**

### Mode 3: Session Data (2-3 minutes)

**"Here's what's powerful - every routing test we just did, every edge case you described, that's all research data. This could be the foundation for a paper on clinical decision-making patterns."**

Show the export function:
- **"We can export this as JSON data for analysis"**
- **"Imagine doing this with 100 referrals - we'd start to see patterns in where the logic breaks"**

### The Ask (2 minutes)

**"What I'm proposing is a research collaboration where:**
- **You provide the clinical expertise** (the routing logic, the edge cases, the 'ground truth')
- **I provide the systems thinking** (building tools, analyzing patterns, structuring the data)
- **Together we study** how clinical decision-making works in complex pediatric neurology referrals

This aligns perfectly with your vision for an integrated next-gen clinic, because what we're really building is a shared language between DBP, CAN, and PPC."**

---

## Technical Notes

### What This Tool IS:
- A research prototype for understanding clinical workflows
- A collaborative tool for capturing expert knowledge
- A data collection system for edge cases and clinical reasoning

### What This Tool IS NOT:
- A production system (not HIPAA compliant, no PHI should be entered)
- A replacement for clinical judgment
- An AI system (it's rule-based logic that you can see and edit)

### The Business Case:

If Dr. Jeste is thinking about this from a departmental efficiency perspective:

**Current state:** Every referral requires manual triage by skilled staff who understand the nuances of all three clinics.

**Future state:** A validated routing system that:
- Handles straightforward cases automatically (60-70% of referrals?)
- Flags complex cases for human review
- Routes crisis cases to immediate care pathways
- Generates data on referral patterns over time

**Research value:** This tool helps you build the training data you'd need for a production system - but more importantly, it generates insights about clinical decision-making that could be publishable.

---

## After the Meeting

### If she's interested:

1. **Next technical step:** Validate the routing logic with 20-30 real (anonymized) referral cases
2. **Research question:** "What clinical factors predict disagreement between rule-based routing and expert clinical judgment?"
3. **Grant opportunity:** This could be pilot data for an implementation science grant

### If she wants to go deeper:

- Build a version that integrates with UCLA's actual referral system (read-only at first)
- Add natural language processing to extract symptoms from referral text
- Create a "consultation request" pathway for complex cases
- Analyze historical referral data to find patterns

---

## Troubleshooting

**App won't start?**
- Make sure you're in the right directory: `cd /path/to/folder`
- Check Python version: `python --version` (need 3.8+)
- Try: `python -m streamlit run ucla_triage_app.py`

**Import errors?**
- Reinstall: `pip install --upgrade streamlit pandas`

**App is slow?**
- Close and restart it
- Check for other apps using port 8501

---

## Contact

Questions during the demo? The app should be self-explanatory, but if Dr. Jeste asks technical questions:

**"This is a Streamlit app - it's just Python with a web interface. The routing logic is simple if-then rules right now, intentionally, so we can see where it breaks. The real value is in the data collection - every feedback point you give becomes training data."**

---

## Good Luck! 🎉

Remember: **You're not trying to sell her a product. You're inviting her to collaborate on research.** The tool is just a way to make that collaboration tangible.

The magic moment is when she says: "Oh, but what about patients who..." - that's when you know she's engaged with the problem and seeing the research possibilities.
