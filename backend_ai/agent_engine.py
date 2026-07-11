import json
import time
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

API_KEY_OPENAI = os.getenv("OPENAI_API_KEY")
API_KEY_GEMINI = os.getenv("GEMINI_API_KEY")

if not API_KEY_OPENAI or not API_KEY_GEMINI:
    raise ValueError("API keys for OpenAI and Gemini must be set in the .env file.")

CRITICAL_TICKET_START_TIME = None

def load_metrics_data(filepath="chokepoint_metrics.json"):
    """
    Imports metrics payload generated dynamically by the computer vision process.
    """
    if not os.path.exists(filepath):
        return {
            "current_queue_density": 12,
            "avg_wait_time_minutes": 4.5,
            "avg_processing_time_minutes": 3.2,
            "trend_analysis": {"proc_time_slope": "STABLE", "consecutive_cycles_of_increase": 0},
            "trigger_incident": None,
            "system_timestamp": time.time()
        }
    with open(filepath, "r") as f:
        return json.load(f)

def execute_agentic_reasoning(metrics):
    """
    Evaluates pipeline analytics against business logic matrices.
    Returns targeted structures partitioned for user permission roles.
    """
    global CRITICAL_TICKET_START_TIME
    current_time = time.time()
    
    ui_state = {
        "dispatch_mode": "AUTO",
        "severity": "NOMINAL",
        "ai_thought": "",
        "operator_view": {},
        "admin_view": {},
        "timestamp": current_time
    }
    
    dt_wait = metrics["avg_wait_time_minutes"]
    dt_proc = metrics["avg_processing_time_minutes"]
    trend = metrics["trend_analysis"]["proc_time_slope"]
    incident = metrics["trigger_incident"]
    
    # Critical state path with 20 second safety deadline override execution
    if incident == "MEDICAL_EMERGENCY" or dt_wait >= 12.0:
        ui_state["severity"] = "CRITICAL"
        
        if CRITICAL_TICKET_START_TIME is None:
            CRITICAL_TICKET_START_TIME = current_time
            
        elapsed_seconds = current_time - CRITICAL_TICKET_START_TIME
        
        if elapsed_seconds > 20.0:
            ui_state["dispatch_mode"] = "AUTO_EMERGENCY_BYPASS"
            ui_state["ai_thought"] = "Administrative response deadline exceeded. Overriding manual confirmation block to guarantee terminal safety."
            
            ui_state["operator_view"] = {
                "banner": "CRITICAL EMERGENCY OVERRIDE ORDER ACTIVATED",
                "instruction": "AI system has routed medical first responders to current camera vector due to authorization timeout."
            }
            ui_state["admin_view"] = {
                "alert": "SECURITY SYSTEM AUTONOMOUS DISPATCH OVERRIDE",
                "details": "Twenty second window expired without user feedback. Emergency deployment enforced."
            }
        else:
            ui_state["dispatch_mode"] = "MANUAL_PENDING"
            remaining_time = max(0, int(20.0 - elapsed_seconds))
            ui_state["ai_thought"] = f"Severe event registered. Pending admin verification. Escalation lock remains active for {remaining_time}s."
            
            ui_state["operator_view"] = {
                "banner": "PENDING COMMAND TOWER AUTHORIZATION",
                "instruction": "Emergency event detected. Operations parameters escalated to executive terminal. Wait for orders."
            }
            ui_state["admin_view"] = {
                "pop_up_title": "CRITICAL RISK LEVEL DETECTED",
                "description": f"Terminal physical trauma anomaly or severe SLA deterioration observed. Wait time at {dt_wait} mins.",
                "proposed_action": "Authorise immediate deployment of Station A First Aid Unit to current coordinates.",
                "countdown_seconds": remaining_time,
                "action_buttons_enabled": True
            }
        return ui_state

    CRITICAL_TICKET_START_TIME = None

    # Medium severity path tracking chronic processing infrastructure degradation
    if incident == "LUGGAGE_DISPUTE" or (dt_proc > 4.0 and trend == "INCREASING_NON_STOP"):
        ui_state["dispatch_mode"] = "MANUAL"
        ui_state["severity"] = "WARNING"
        ui_state["ai_thought"] = "Desk latency increasing sequentially over last 3 updates. Compounding bottleneck verified."
        
        ui_state["operator_view"] = {
            "banner": "COUNTER SERVICE LATENCY ALERT",
            "instruction": "Processing speeds dropping below nominal baseline. Escalation package routed to line supervisor."
        }
        ui_state["admin_view"] = {
            "pop_up_title": "OPERATIONAL BOTTLENECK ESCALATION",
            "description": f"Desk performance average at {dt_proc} mins with sustained upward delta.",
            "proposed_action": "Freeze check-in assignment cycles for Counter 3, shift arrivals to Counter 6, and deploy Floor Supervisor.",
            "action_buttons_enabled": True
        }
        return ui_state

    # Low severity operations path using standard automated configuration changes
    ui_state["dispatch_mode"] = "AUTO"
    
    if 5.0 <= dt_wait < 12.0 or metrics["current_queue_density"] > 10:
        ui_state["severity"] = "MINIMAL"
        ui_state["ai_thought"] = "Mass density metric expansion observed. Triggering local layout routing updates."
        action_payload = "AUTOMATED COMMAND: Updated dynamic terminal LED boards to open Line 4. Distributed local optimization advice to counter client interfaces."
        
        ui_state["operator_view"] = {
            "banner": "AUTOMATED ADJUSTMENT DISPATCHED",
            "instruction": action_payload
        }
        ui_state["admin_view"] = {
            "log_summary": f"System deployed minor layout changes. Average wait parameters stable at {dt_wait} mins."
        }
    else:
        ui_state["severity"] = "NOMINAL"
        ui_state["ai_thought"] = "All checked parameters matching standard operational profiles."
        ui_state["operator_view"] = {"instruction": "System fully operational. Standard load balances verified."}
        ui_state["admin_view"] = {"log_summary": "Continuous background monitoring active. Balance confirmed."}

    return ui_state

def sync_ui_state(ui_state_data):
    """
    Writes computed state payload to shared disk repository for frontend presentation layers.
    """
    with open("agent_ui_state.json", "w", encoding="utf-8") as f:
        json.dump(ui_state_data, f, ensure_ascii=False, indent=4)

def start_agent_daemon():
    """
    Main background execution routine checking parameters at fixed 1-second ticks.
    """
    print("[INIT] ChokePoint AI Agent Engine processing loops active.")
    while True:
        metrics = load_metrics_data()
        state = execute_agentic_reasoning(metrics)
        sync_ui_state(state)
        time.sleep(1)

if __name__ == "__main__":
    start_agent_daemon()