"""
Deterministic Guardrail Engine for Healthcare Voice AI
=======================================================
A prototype demonstrating how to wrap non-deterministic LLM output
inside a deterministic state machine with validation and safe fallbacks.

Built for: Attune (Agentic Voice for Healthcare)
Run: streamlit run app.py
Requires: pip install streamlit openai
"""

import streamlit as st
import time

from config import WORKFLOW_STATES, SAMPLE_CONTEXT, APP_STYLES
from guardrail_engine import run_guardrailed_generation
from ui import (
    render_header,
    render_state_config,
    render_single_result,
    render_consistency_results,
    render_how_it_works,
)


# PAGE CONFIG & STYLES

st.set_page_config(
    page_title="Deterministic Guardrail Engine",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(APP_STYLES, unsafe_allow_html=True)


# SIDEBAR

with st.sidebar:
    st.markdown("""
        <div style="font-family:'DM Mono',monospace; font-size:11px; color:#00D4AA;
                    letter-spacing:0.08em; text-transform:uppercase; margin-bottom:12px;">
            Configuration
        </div>
    """, unsafe_allow_html=True)

    api_key = st.text_input(
        "OpenRouter API Key",
        type="password",
        help="Required to generate LLM responses. Get one at openrouter.ai/keys",
    )

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    st.markdown("""
        <div style="font-family:'DM Mono',monospace; font-size:11px; color:#00D4AA;
                    letter-spacing:0.08em; text-transform:uppercase; margin-bottom:12px;">
            Mode
        </div>
    """, unsafe_allow_html=True)

    mode = st.radio(
        "Select mode",
        ["Explore States", "Consistency Test"],
        label_visibility="collapsed",
    )

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    st.markdown("""
        <div style="font-family:'DM Mono',monospace; font-size:11px; color:#00D4AA;
                    letter-spacing:0.08em; text-transform:uppercase; margin-bottom:12px;">
            Sample Patient Context
        </div>
    """, unsafe_allow_html=True)

    for key, val in SAMPLE_CONTEXT.items():
        label = key.replace("_", " ").title()
        st.markdown(f"""
            <div style="font-size:11px; padding:3px 0; border-bottom:1px solid #243040;">
                <span style="color:#4A5B70; font-family:'DM Mono',monospace;">{label}:</span>
                <span style="color:#7A8BA3; margin-left:6px;">{val}</span>
            </div>
        """, unsafe_allow_html=True)


# MAIN LAYOUT

render_header()
st.markdown("---")

# State selector
st.markdown('<div class="section-label">Workflow State Machine</div>', unsafe_allow_html=True)

state_labels = {sid: s["label"] for sid, s in WORKFLOW_STATES.items()}
state_cols = st.columns(len(WORKFLOW_STATES))

# Initialize session state
if "current_state" not in st.session_state:
    st.session_state.current_state = "GREETING"
if "result" not in st.session_state:
    st.session_state.result = None
if "consistency_results" not in st.session_state:
    st.session_state.consistency_results = []

for i, (sid, label) in enumerate(state_labels.items()):
    with state_cols[i]:
        is_active = st.session_state.current_state == sid
        if st.button(
            label,
            key=f"state_{sid}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            st.session_state.current_state = sid
            st.session_state.result = None
            st.session_state.consistency_results = []
            st.rerun()

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

current_state = st.session_state.current_state

# Layout: config + output
left_col, right_col = st.columns([1, 2])

with left_col:
    render_state_config(current_state)

with right_col:
    if mode == "Explore States":
        if st.button(
            f"Generate \"{WORKFLOW_STATES[current_state]['label']}\" Response",
            disabled=not api_key,
            use_container_width=True,
        ):
            with st.spinner("Generating with guardrails..."):
                try:
                    result = run_guardrailed_generation(current_state, api_key, temperature=0.9)
                    st.session_state.result = result
                except Exception as e:
                    st.error(f"Error: {str(e)}")

        if not api_key:
            st.caption("← Enter your OpenRouter API key in the sidebar to generate responses.")

        if st.session_state.result:
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            render_single_result(st.session_state.result)
        elif api_key:
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            render_how_it_works()

    else:  # Consistency Test
        num_runs = st.slider("Number of runs", min_value=3, max_value=10, value=5)

        if st.button(
            f"Run {num_runs}x Consistency Test",
            disabled=not api_key,
            use_container_width=True,
        ):
            st.session_state.consistency_results = []
            progress_bar = st.progress(0, text="Running consistency tests...")

            results = []
            for i in range(num_runs):
                try:
                    result = run_guardrailed_generation(current_state, api_key, temperature=0.9)
                    results.append(result)
                    progress_bar.progress(
                        (i + 1) / num_runs,
                        text=f"Run {i+1}/{num_runs} — {'PASS' if result['all_passed'] else 'FAIL → FALLBACK'}",
                    )
                    time.sleep(0.5)
                except Exception as e:
                    st.error(f"Error on run {i+1}: {str(e)}")
                    break

            progress_bar.empty()
            st.session_state.consistency_results = results

        if not api_key:
            st.caption("← Enter your OpenRouter API key in the sidebar to run tests.")

        if st.session_state.consistency_results:
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            render_consistency_results(st.session_state.consistency_results)
        elif api_key:
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            render_how_it_works()