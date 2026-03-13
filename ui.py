"""
UI rendering functions for the Deterministic Guardrail Engine.
All Streamlit display logic lives here.
"""

import streamlit as st
from config import WORKFLOW_STATES, SAMPLE_CONTEXT
from guardrail_engine import fill_template


# HEADER

def render_header():
    """Render the app header."""
    st.markdown("""
        <div style="margin-bottom: 8px;">
            <span class="header-badge">
                <span class="header-dot"></span>
                Deterministic Guardrail Engine
            </span>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("# Solving Non-Determinism in Healthcare AI")
    st.markdown(
        "<p style='font-size:14px; color:#7A8BA3; max-width:700px; line-height:1.6; margin-top:-8px;'>"
        "LLMs are inherently non-deterministic. This engine wraps AI output inside a "
        "deterministic state machine with validation rules and safe fallbacks — ensuring "
        "every patient interaction is compliant, consistent, and auditable."
        "</p>",
        unsafe_allow_html=True,
    )


# STATE CONFIGURATION PANEL

def render_state_config(state_id: str):
    """Render the state configuration panel."""
    state = WORKFLOW_STATES[state_id]

    st.markdown(f"""
        <div class="section-label">Current State</div>
        <div style="font-family:'DM Mono',monospace; font-size:16px; color:#00D4AA; font-weight:600; margin-bottom:16px;">
            {state['label']}
        </div>
    """, unsafe_allow_html=True)

    # Instruction
    st.markdown('<div class="section-label">Agent Instruction</div>', unsafe_allow_html=True)
    st.markdown(f"""
        <div style="background:#1A222C; padding:12px; border-radius:8px; border:1px solid #243040;
                    font-size:13px; color:#E8ECF1; line-height:1.6; margin-bottom:16px;">
            {state['instruction']}
        </div>
    """, unsafe_allow_html=True)

    # Validation Rules
    st.markdown('<div class="section-label">Validation Rules</div>', unsafe_allow_html=True)
    for rule in state["validation_rules"]:
        if rule["type"] == "must_not_contain":
            badge_class = "rule-block"
            badge_text = "BLOCK"
        elif rule["type"] == "must_contain_concept":
            badge_class = "rule-require"
            badge_text = "REQUIRE"
        else:
            badge_class = "rule-limit"
            badge_text = "LIMIT"

        st.markdown(f"""
            <div style="font-size:12px; color:#7A8BA3; padding:6px 0; border-bottom:1px solid #243040;">
                <span class="rule-badge {badge_class}">{badge_text}</span>
                {rule['description']}
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # Fallback
    st.markdown('<div class="section-label">Safe Fallback Template</div>', unsafe_allow_html=True)
    fallback_filled = fill_template(state["fallback_template"], SAMPLE_CONTEXT)
    st.markdown(f"""
        <div class="fallback-box">"{fallback_filled}"</div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # Transitions
    st.markdown('<div class="section-label">Valid Transitions</div>', unsafe_allow_html=True)
    if state["valid_transitions"]:
        transitions_html = " ".join(
            f'<span class="transition-badge">→ {WORKFLOW_STATES[t]["label"]}</span>'
            for t in state["valid_transitions"]
        )
        st.markdown(transitions_html, unsafe_allow_html=True)
    else:
        st.markdown(
            "<span style='font-family:DM Mono,monospace; font-size:11px; color:#4A5B70;'>END OF CALL</span>",
            unsafe_allow_html=True,
        )


# VALIDATION RESULTS

def render_validation_results(results: list, label: str = None, override_status: str = None, override_color: str = None):
    """Render validation results with optional label override."""
    all_passed = all(r["passed"] for r in results)

    if override_status and override_color:
        status_text = override_status
        status_color = override_color
        dot_class = "dot-green" if "PASSED" in override_status else "dot-red"
    else:
        dot_class = "dot-green" if all_passed else "dot-red"
        status_color = "#00D4AA" if all_passed else "#FF5A5A"
        status_text = "ALL VALIDATIONS PASSED" if all_passed else "VALIDATION FAILED"

    if label:
        st.markdown(f"""
            <div style="font-family:'DM Mono',monospace; font-size:10px; color:#4A5B70;
                        letter-spacing:0.08em; text-transform:uppercase; margin-bottom:8px;">
                {label}
            </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:12px;">
            <span class="status-dot {dot_class}"></span>
            <span style="font-family:'DM Mono',monospace; font-size:11px; color:{status_color}; letter-spacing:0.05em;">
                {status_text}
            </span>
        </div>
    """, unsafe_allow_html=True)

    for r in results:
        icon = "✓" if r["passed"] else "✗"
        color = "#7A8BA3" if r["passed"] else "#FF5A5A"
        violation_html = ""
        if not r["passed"] and r.get("violation"):
            violation_html = (
                f'<span style="font-family:DM Mono,monospace; font-size:10px; '
                f'background:rgba(255,90,90,0.1); padding:2px 6px; border-radius:4px; '
                f'color:#FF5A5A; margin-left:8px;">found: "{r["violation"]}"</span>'
            )
        st.markdown(f"""
            <div style="display:flex; align-items:center; gap:8px; padding:4px 0; font-size:12px; color:{color};">
                <span style="font-size:14px; flex-shrink:0;">{icon}</span>
                <span>{r['rule']}</span>
                {violation_html}
            </div>
        """, unsafe_allow_html=True)


# SINGLE GENERATION RESULT

def render_single_result(result: dict):
    """Render generation result — raw vs corrected vs final."""

    # Route badge
    route_color = {
        "PASSED": "#00D4AA",
        "SOFT_FAIL → CORRECTED": "#5B9DF0",
        "HARD_FAIL → FALLBACK": "#FF5A5A",
        "SOFT_FAIL → CORRECTION_FAILED → FALLBACK": "#FFAA33",
    }.get(result["route"], "#7A8BA3")

    st.markdown(f"""
        <div style="display:inline-flex; align-items:center; gap:8px;
                    padding:6px 14px; border-radius:20px; margin-bottom:16px;
                    background:{route_color}15; border:1px solid {route_color}40;">
            <span style="font-family:'DM Mono',monospace; font-size:11px;
                         color:{route_color}; letter-spacing:0.06em;">
                Route: {result['route']}
            </span>
        </div>
    """, unsafe_allow_html=True)

    # Determine columns
    if result["used_correction"]:
        col1, col2, col3 = st.columns(3)
    else:
        col1, col2 = st.columns(2)
        col3 = None

    # Raw output
    with col1:
        st.markdown(f"""
            <div class="output-card output-card-raw">
                <div style="display:flex; align-items:center; gap:8px;
                            margin-bottom:12px;">
                    <span class="status-dot dot-amber"></span>
                    <span style="font-family:'DM Mono',monospace;
                                 font-size:11px; color:#FFAA33;">
                        RAW LLM OUTPUT
                    </span>
                </div>
                <div style="font-size:13px; line-height:1.65;
                            color:#E8ECF1;">
                    {result['raw_output']}
                </div>
            </div>
        """, unsafe_allow_html=True)

    # Corrected output (if applicable)
    if col3 and result["corrected_output"]:
        with col2:
            st.markdown(f"""
                <div class="output-card"
                     style="border:1px solid rgba(91,157,240,0.25);">
                    <div style="display:flex; align-items:center;
                                gap:8px; margin-bottom:12px;">
                        <span class="status-dot"
                              style="background:#5B9DF0;
                                     box-shadow:0 0 8px #5B9DF0;">
                        </span>
                        <span style="font-family:'DM Mono',monospace;
                                     font-size:11px; color:#5B9DF0;">
                            LLM SELF-CORRECTION
                        </span>
                    </div>
                    <div style="font-size:13px; line-height:1.65;
                                color:#E8ECF1;">
                        {result['corrected_output']}
                    </div>
                </div>
            """, unsafe_allow_html=True)
        final_col = col3
    else:
        final_col = col2

    # Final output
    with final_col:
        if result["used_fallback"]:
            card_border = "rgba(255,170,51,0.25)"
            dot_class = "dot-amber"
            label_color = "#FFAA33"
            label_text = "FALLBACK"
        else:
            card_border = "rgba(0,212,170,0.25)"
            dot_class = "dot-green"
            label_color = "#00D4AA"
            label_text = (
                "CORRECTED & PASSED"
                if result["used_correction"]
                else "PASSED"
            )

        st.markdown(f"""
            <div class="output-card"
                 style="border:1px solid {card_border};">
                <div style="display:flex; align-items:center;
                            gap:8px; margin-bottom:12px;">
                    <span class="status-dot {dot_class}"></span>
                    <span style="font-family:'DM Mono',monospace;
                                 font-size:11px; color:{label_color};">
                        FINAL → {label_text}
                    </span>
                </div>
                <div style="font-size:13px; line-height:1.65;
                            color:#E8ECF1;">
                    {result['final_output']}
                </div>
            </div>
        """, unsafe_allow_html=True)

    # Validation details
    if result["used_correction"] and result["correction_results"]:
        # Show both validation passes side by side
        vcol1, vcol2 = st.columns(2)
        with vcol1:
            st.markdown('<div class="state-card">', unsafe_allow_html=True)
            render_validation_results(
                result["validation_results"],
                label="Pass 1 — Raw Output",
                override_status="SOFT FAIL → SENT TO CORRECTION",
                override_color="#FFAA33",
            )
            st.markdown('</div>', unsafe_allow_html=True)
        with vcol2:
            st.markdown('<div class="state-card">', unsafe_allow_html=True)
            all_fixed = all(r["passed"] for r in result["correction_results"])
            if all_fixed:
                render_validation_results(
                    result["correction_results"],
                    label="Pass 2 — Corrected Output",
                    override_status="ALL VALIDATIONS PASSED",
                    override_color="#00D4AA",
                )
            else:
                render_validation_results(
                    result["correction_results"],
                    label="Pass 2 — Corrected Output",
                    override_status="STILL FAILING → FALLBACK",
                    override_color="#FF5A5A",
                )
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        # Single validation pass (direct pass or hard fail)
        st.markdown('<div class="state-card">', unsafe_allow_html=True)
        render_validation_results(result["validation_results"])
        st.markdown('</div>', unsafe_allow_html=True)


# CONSISTENCY TEST RESULTS

def render_consistency_results(results: list):
    """Render consistency test results with metrics."""
    if not results:
        return

    pass_rate = round(sum(1 for r in results if r["all_passed"]) / len(results) * 100)
    fallback_rate = round(sum(1 for r in results if r["used_fallback"]) / len(results) * 100)
    avg_len = round(sum(len(r["final_output"]) for r in results) / len(results))

    # Metrics row
    col1, col2, col3 = st.columns(3)

    with col1:
        color = "#00D4AA" if pass_rate == 100 else "#FFAA33"
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value" style="color:{color};">{pass_rate}%</div>
                <div class="metric-label">Validation Pass Rate</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        color = "#00D4AA" if fallback_rate == 0 else "#FFAA33"
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value" style="color:{color};">{fallback_rate}%</div>
                <div class="metric-label">Fallback Usage</div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value" style="color:#5B9DF0;">{avg_len}</div>
                <div class="metric-label">Avg Output Length (chars)</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # Individual runs
    for i, r in enumerate(results):
        badge_class = "badge-pass" if r["all_passed"] else "badge-fail"
        badge_text = "PASS" if r["all_passed"] else "FAIL"
        fallback_badge = '<span class="run-badge badge-fallback">FALLBACK</span>' if r["used_fallback"] else ""

        st.markdown(f"""
            <div style="padding:10px 14px; border-bottom:1px solid #243040; display:flex; gap:12px; align-items:flex-start; font-size:12px;">
                <span style="font-family:'DM Mono',monospace; color:#4A5B70; flex-shrink:0; width:28px;">#{i+1}</span>
                <span style="color:{'#7A8BA3' if r['all_passed'] else '#FF5A5A'}; flex:1; line-height:1.5;">
                    {r['final_output']}
                </span>
                <div style="display:flex; gap:4px; flex-shrink:0;">
                    <span class="run-badge {badge_class}">{badge_text}</span>
                    {fallback_badge}
                </div>
            </div>
        """, unsafe_allow_html=True)


# HOW IT WORKS

def render_how_it_works():
    """Render the How It Works section."""
    steps = [
        ("01", "Deterministic State Machine",
         "The conversation flow is a finite state machine. The LLM never decides what step comes next — the workflow engine does. Each state has defined valid transitions, eliminating unpredictable branching."),
        ("02", "Constrained Generation",
         "At each state, the LLM receives only the instruction for that specific step plus relevant context. It generates natural language within tight boundaries — it chooses the words, not the actions."),
        ("03", "Output Validation Layer",
         "Every LLM response passes through rule-based validators before reaching the patient. Rules check for required content, forbidden topics (medical advice, sensitive data), and length constraints."),
        ("04", "Safe Fallback Templates",
         "If validation fails, the system substitutes a pre-approved template response. The call continues without interruption. The patient never receives non-compliant output — guaranteed."),
    ]

    st.markdown("""
        <div style="font-family:'DM Mono',monospace; font-size:11px; color:#5B9DF0;
                    letter-spacing:0.08em; text-transform:uppercase; margin-bottom:16px;">
            How It Works
        </div>
    """, unsafe_allow_html=True)

    for num, title, desc in steps:
        st.markdown(f"""
            <div class="how-it-works-step">
                <span class="step-num">{num}</span>
                <div>
                    <div class="step-title">{title}</div>
                    <div class="step-desc">{desc}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)