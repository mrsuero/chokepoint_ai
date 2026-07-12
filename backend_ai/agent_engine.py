import json
import os
import sys
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

try:
    from langfuse import Langfuse
except Exception:
    Langfuse = None

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("[ERROR] GEMINI_API_KEY environment variable is missing. Core routing halted.")
    sys.exit(1)

client = genai.Client(api_key=API_KEY)
langfuse_client = None

LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

if Langfuse and LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY:
    try:
        langfuse_client = Langfuse(
            public_key=LANGFUSE_PUBLIC_KEY,
            secret_key=LANGFUSE_SECRET_KEY,
            host=LANGFUSE_HOST,
        )
    except Exception as error:
        print(f"[WARN] Langfuse init skipped: {error}")

CRITICAL_TICKET_START_TIME = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)


def resolve_frontend_public_path(filename):
    return os.path.join(PROJECT_ROOT, "frontend_ui", "public", filename)


INPUT_METRICS_PATH = resolve_frontend_public_path("chokepoint_metrics.json")
OUTPUT_UI_STATE_PATH = resolve_frontend_public_path("agent_ui_state.json")


DEFAULT_METRICS = {
    "current_queue_density": 5,
    "avg_wait_time_minutes": 2.1,
    "avg_processing_time_minutes": 1.8,
    "accumulation_rate_per_min": 0.1,
    "trend_analysis": {"proc_time_slope": "STABLE", "consecutive_cycles_of_increase": 0},
    "trigger_incident": None,
    "system_timestamp": time.time(),
}


def load_metrics_data():
    """
    Imports metrics payload generated dynamically by the computer vision process.
    Falls back to defaults if the file is missing, empty, or mid-write (e.g. the
    CV process is in the middle of writing it when we try to read it).
    """
    if not os.path.exists(INPUT_METRICS_PATH):
        return DEFAULT_METRICS

    try:
        with open(INPUT_METRICS_PATH, "r", encoding="utf-8") as file_handle:
            content = file_handle.read()
            if not content.strip():
                print("[WARN] Metrics file is empty (likely mid-write). Using defaults for this cycle.")
                return DEFAULT_METRICS
            return json.loads(content)
    except json.JSONDecodeError as error:
        print(f"[WARN] Metrics file contains invalid JSON ({error}). Using defaults for this cycle.")
        return DEFAULT_METRICS
    except OSError as error:
        print(f"[WARN] Could not read metrics file ({error}). Using defaults for this cycle.")
        return DEFAULT_METRICS


def call_gemini_agent_decision(metrics_payload):
    """
    Leverages Gemini 2.5 Flash with Structured Outputs to analyze airport metrics.
    """
    system_instruction = (
        "You are the executive Agentic Brain of ChokePoint AI, deployed at an airport terminal checkpoint. "
        "Your duty is to evaluate mathematical metrics and trigger accurate mitigation actions. "
        "Operational Thresholds:\n"
        "- Severity NOMINAL: Default state when wait times and density are low.\n"
        "- Severity MINIMAL (AUTO Mode): Triggered if wait time is between 5 and 12 minutes.\n"
        "- Severity WARNING (MANUAL Mode): Triggered if a SUSPECTED_LUGGAGE_DISPUTE is flagged OR if processing time is rising non-stop.\n"
        "- Severity CRITICAL (MANUAL_PENDING Mode): Triggered if a MEDICAL_EMERGENCY is active or wait time equals/exceeds 12 minutes."
    )

    user_content = f"Current Terminal Telemetry Data Context:\n{json.dumps(metrics_payload, indent=2)}"

    trace = None
    if langfuse_client:
        try:
            trace = langfuse_client.trace(
                name="chokepoint-agent-decision",
                metadata={
                    "dispatch_target": "airport_checkpoint",
                    "model": "gemini-3-flash-preview",
                },
                input=metrics_payload,
            )
        except Exception as error:
            print(f"[WARN] Langfuse trace creation skipped: {error}")

    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=user_content,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "dispatch_mode": types.Schema(type=types.Type.STRING, enum=["AUTO", "MANUAL", "MANUAL_PENDING"]),
                        "severity": types.Schema(type=types.Type.STRING, enum=["NOMINAL", "MINIMAL", "WARNING", "CRITICAL"]),
                        "ai_thought": types.Schema(type=types.Type.STRING),
                        "operator_instruction": types.Schema(type=types.Type.STRING),
                        "admin_pop_up_title": types.Schema(type=types.Type.STRING),
                        "admin_description": types.Schema(type=types.Type.STRING),
                        "admin_proposed_action": types.Schema(type=types.Type.STRING),
                        "admin_log_summary": types.Schema(type=types.Type.STRING),
                    },
                    required=["dispatch_mode", "severity", "ai_thought"],
                ),
            ),
        )
        decision = json.loads(response.text)

        if trace:
            try:
                trace.update(output=decision)
                trace.end()
            except Exception as error:
                print(f"[WARN] Langfuse trace update skipped: {error}")

        return decision
    except Exception as error:
        print(f"[LLM INFERENCE ERROR] Failed to parse agent decision: {error}")
        if trace:
            try:
                trace.update(output={"error": str(error)})
                trace.end(status_message="error")
            except Exception:
                pass
        return None


def process_and_sync_state():
    """
    Main orchestration loop. Handles state alignment and local time-out checks.
    """
    global CRITICAL_TICKET_START_TIME
    current_time = time.time()

    metrics = load_metrics_data()
    llm_decision = call_gemini_agent_decision(metrics)
    if not llm_decision:
        return

    final_state = {
        "dispatch_mode": llm_decision["dispatch_mode"],
        "severity": llm_decision["severity"],
        "ai_thought": llm_decision["ai_thought"],
        "operator_view": {"banner": "", "instruction": llm_decision.get("operator_instruction", "")},
        "admin_view": {"log_summary": llm_decision.get("admin_log_summary", "")},
        "timestamp": current_time,
    }

    if llm_decision["dispatch_mode"] == "MANUAL_PENDING" or llm_decision["severity"] == "CRITICAL":
        if CRITICAL_TICKET_START_TIME is None:
            CRITICAL_TICKET_START_TIME = current_time

        elapsed_seconds = current_time - CRITICAL_TICKET_START_TIME
        remaining_time = max(0, int(20.0 - elapsed_seconds))

        if elapsed_seconds > 20.0:
            final_state["dispatch_mode"] = "AUTO_EMERGENCY_BYPASS"
            final_state["ai_thought"] = "Administrative window exceeded 20s. Enforcing dynamic autonomous bypass."
            final_state["operator_view"] = {
                "banner": "CRITICAL EMERGENCY OVERRIDE ACTIVATED",
                "instruction": "AI Agent has autonomously deployed Station A Medical Responders due to command latency.",
            }
            final_state["admin_view"] = {
                "alert": "SECURITY DEPLOYMENT FORCE BYPASS",
                "details": "SLA window expired without user validation. Autonomous emergency response executed.",
            }
        else:
            final_state["operator_view"] = {
                "banner": "AWAITING EXECUTIVE VALIDATION",
                "instruction": "Emergency alert routed to command terminal. Prepare station zone for responder arrival.",
            }
            final_state["admin_view"] = {
                "pop_up_title": llm_decision.get("admin_pop_up_title", "CRITICAL INCIDENT ALERT"),
                "description": llm_decision.get("admin_description", ""),
                "proposed_action": llm_decision.get("admin_proposed_action", ""),
                "countdown_seconds": remaining_time,
                "action_buttons_enabled": True,
            }
    else:
        CRITICAL_TICKET_START_TIME = None
        if llm_decision["dispatch_mode"] == "MANUAL":
            final_state["operator_view"]["banner"] = "COUNTER EFFICIENCY DEGRADATION WARNING"
            final_state["admin_view"] = {
                "pop_up_title": llm_decision.get("admin_pop_up_title", "OPERATION DEGRADATION ESCALATION"),
                "description": llm_decision.get("admin_description", ""),
                "proposed_action": llm_decision.get("admin_proposed_action", ""),
                "action_buttons_enabled": True,
            }
        elif llm_decision["dispatch_mode"] == "AUTO" and llm_decision["severity"] == "MINIMAL":
            final_state["operator_view"]["banner"] = "AUTOMATED ROUTING UPDATE ACTIVE"

    os.makedirs(os.path.dirname(OUTPUT_UI_STATE_PATH), exist_ok=True)
    with open(OUTPUT_UI_STATE_PATH, "w", encoding="utf-8") as file_handle:
        json.dump(final_state, file_handle, ensure_ascii=False, indent=4)


def start_agent_daemon():
    print("[INIT] ChokePoint AI Agent Engine processing loops successfully bound to Gemini API.")
    while True:
        process_and_sync_state()
        time.sleep(20)


if __name__ == "__main__":
    start_agent_daemon()