"""
Core guardrail engine — validation, LLM interaction, and generation pipeline.
"""

from openai import OpenAI
from config import WORKFLOW_STATES, SAMPLE_CONTEXT


# TEMPLATE HELPERS

def fill_template(template: str, context: dict) -> str:
    """Fill a template string with context variables."""
    result = template
    for key, val in context.items():
        result = result.replace(f"{{{key}}}", val)
    return result


# VALIDATION ENGINE

def validate_output(text: str, rules: list) -> tuple[list, bool, bool]:
    """
    Validate LLM output against rules.
    Returns: (results, has_hard_fail, has_soft_fail)
    """
    results = []
    has_hard_fail = False
    has_soft_fail = False

    for rule in rules:
        if rule["type"] == "must_not_contain":
            violation = None
            for forbidden in rule["forbidden"]:
                if forbidden.lower() in text.lower():
                    violation = forbidden
                    break
            passed = violation is None
            results.append({
                "rule": rule["description"],
                "passed": passed,
                "type": rule["type"],
                "severity": "hard",
                "violation": violation,
            })
            if not passed:
                has_hard_fail = True

        elif rule["type"] == "must_contain_concept":
            found = any(
                c.lower() in text.lower()
                for c in rule["concepts"]
            )
            results.append({
                "rule": rule["description"],
                "passed": found,
                "type": rule["type"],
                "severity": "soft",
            })
            if not found:
                has_soft_fail = True

        elif rule["type"] == "max_length":
            passed = len(text) <= rule["value"]
            results.append({
                "rule": rule["description"],
                "passed": passed,
                "type": rule["type"],
                "severity": "soft",
                "actual": len(text),
                "max": rule["value"],
            })
            if not passed:
                has_soft_fail = True

    return results, has_hard_fail, has_soft_fail


# LLM INTERACTION

def call_llm(state_id: str, api_key: str, temperature: float = 0.7) -> str:
    """Call LLM via OpenRouter to generate a response for the given state."""
    state = WORKFLOW_STATES[state_id]

    system_prompt = f"""You are a healthcare appointment reminder voice agent. You are currently in the "{state['label']}" step of the call.

Context:
- Patient: {SAMPLE_CONTEXT['patient_name']}
- Provider: {SAMPLE_CONTEXT['provider_name']}
- Doctor: {SAMPLE_CONTEXT['doctor_name']}
- Date: {SAMPLE_CONTEXT['appointment_date']}
- Time: {SAMPLE_CONTEXT['appointment_time']}
- Location: {SAMPLE_CONTEXT['location']}

Instruction: {state['instruction']}

Respond with ONLY what the agent would say to the patient. No quotes, no meta-text, no stage directions. Just the spoken words. Keep it natural and conversational."""

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    response = client.chat.completions.create(
        model="anthropic/claude-sonnet-4",
        max_tokens=1000,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Generate the agent's spoken response for this step."},
        ],
    )

    return response.choices[0].message.content.strip()


def build_correction_prompt(raw_output: str, failed_rules: list) -> str:
    """Build a prompt asking the LLM to fix soft failures."""
    issues = []
    for r in failed_rules:
        if r["type"] == "max_length":
            issues.append(
                f"- Shorten to under {r['max']} characters "
                f"(currently {r['actual']})"
            )
        elif r["type"] == "must_contain_concept":
            issues.append(
                f"- Must mention: {r['rule']}"
            )

    issues_text = "\n".join(issues)

    return f"""Here is a voice agent response that needs minor fixes:

"{raw_output}"

Fix ONLY these issues while keeping the natural tone:
{issues_text}

Return ONLY the corrected spoken response. Nothing else."""


def call_llm_correction(
    raw_output: str,
    failed_rules: list,
    api_key: str,
) -> str:
    """Ask the LLM to fix soft validation failures."""
    prompt = build_correction_prompt(raw_output, failed_rules)

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    response = client.chat.completions.create(
        model="anthropic/claude-sonnet-4",
        max_tokens=1000,
        temperature=0.3,
        messages=[
            {
                "role": "system",
                "content": "You fix voice agent responses. "
                           "Make minimal changes. "
                           "Preserve the natural tone.",
            },
            {"role": "user", "content": prompt},
        ],
    )

    return response.choices[0].message.content.strip()


# GUARDRAILED GENERATION PIPELINE

def run_guardrailed_generation(
    state_id: str,
    api_key: str,
    temperature: float = 0.9,
) -> dict:
    """
    Run a guardrailed generation with tiered validation:
      1. Generate raw output
      2. Validate → hard fail → fallback
      3. Validate → soft fail → correction → re-validate
      4. All pass → use as-is
    """
    state = WORKFLOW_STATES[state_id]

    # Step 1: Generate raw output
    raw_output = call_llm(state_id, api_key, temperature)

    # Step 2: First validation pass
    results, has_hard_fail, has_soft_fail = validate_output(
        raw_output, state["validation_rules"]
    )

    # Step 3: Route based on failure type
    if not has_hard_fail and not has_soft_fail:
        return {
            "raw_output": raw_output,
            "final_output": raw_output,
            "validation_results": results,
            "all_passed": True,
            "used_fallback": False,
            "used_correction": False,
            "corrected_output": None,
            "correction_results": None,
            "route": "PASSED",
        }

    if has_hard_fail:
        fallback = fill_template(
            state["fallback_template"], SAMPLE_CONTEXT
        )
        return {
            "raw_output": raw_output,
            "final_output": fallback,
            "validation_results": results,
            "all_passed": False,
            "used_fallback": True,
            "used_correction": False,
            "corrected_output": None,
            "correction_results": None,
            "route": "HARD_FAIL → FALLBACK",
        }

    # Soft fail only → attempt correction
    soft_failures = [r for r in results if not r["passed"]]
    corrected = call_llm_correction(raw_output, soft_failures, api_key)

    # Re-validate the corrected output
    correction_results, still_hard, still_soft = validate_output(
        corrected, state["validation_rules"]
    )

    if not still_hard and not still_soft:
        return {
            "raw_output": raw_output,
            "final_output": corrected,
            "validation_results": results,
            "all_passed": True,
            "used_fallback": False,
            "used_correction": True,
            "corrected_output": corrected,
            "correction_results": correction_results,
            "route": "SOFT_FAIL → CORRECTED",
        }
    else:
        fallback = fill_template(
            state["fallback_template"], SAMPLE_CONTEXT
        )
        return {
            "raw_output": raw_output,
            "final_output": fallback,
            "validation_results": results,
            "all_passed": False,
            "used_fallback": True,
            "used_correction": True,
            "corrected_output": corrected,
            "correction_results": correction_results,
            "route": "SOFT_FAIL → CORRECTION_FAILED → FALLBACK",
        }