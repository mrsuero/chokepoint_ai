import cv2
import numpy as np
import time
import json
import os
from ultralytics import YOLO

# =====================================================================
# CONFIGURATION & GLOBAL REGISTRIES
# =====================================================================
# Initialize lightweight YOLOv11 nano model for tracking
MODEL = YOLO("yolov11n.pt")

# ROI Polygons (Assumed 1280x720 frame coordinates)
ZONE_1_QUEUE = np.array([[100, 350], [500, 350], [500, 700], [100, 700]], np.int32)
ZONE_2_COUNTER = np.array([[520, 350], [900, 350], [900, 700], [520, 700]], np.int32)

# Registries to track passenger timestamps
# Structure: { passenger_id: { "enter_z1": ts, "exit_z1": ts, "exit_z2": ts } }
PASSENGER_REGISTRY = {}

# Historical buffers for SLA calculation (stored in minutes)
HISTORICAL_WAIT_TIMES = []
HISTORICAL_PROCESSING_TIMES = []

# Buffer to monitor processing time trend (stores last 3 average processing times)
PROC_TIME_TREND_BUFFER = []

# Accumulation rate metrics
TOTAL_PASSENGERS_ENTERED = 0
SYSTEM_START_TIME = time.time()

# =====================================================================
# HELPER FUNCTIONS
# =====================================================================
def is_inside_zone(point, polygon_zone):
    """
    Checks if a specific coordinate point (x, y) falls inside a predefined ROI polygon.
    """
    return cv2.pointPolygonTest(polygon_zone, point, False) >= 0


def calculate_accumulation_rate(current_time):
    """
    Calculates the passenger accumulation rate per minute.
    Formula: (Total Entered - Total Exited Zone 1) / Elapsed Minutes
    """
    elapsed_minutes = (current_time - SYSTEM_START_TIME) / 60
    total_exited_z1 = len(HISTORICAL_WAIT_TIMES)
    
    if elapsed_minutes > 0:
        return (TOTAL_PASSENGERS_ENTERED - total_exited_z1) / elapsed_minutes
    return 0.0


def analyze_processing_trend(current_avg_proc):
    """
    Analyzes the derivative/direction of processing time over the last 3 monitoring cycles.
    Determines if the bottleneck is compounding or stabilizing.
    """
    global PROC_TIME_TREND_BUFFER
    PROC_TIME_TREND_BUFFER.append(current_avg_proc)
    
    # Keep only the latest 3 cycles for trend analysis
    if len(PROC_TIME_TREND_BUFFER) > 3:
        PROC_TIME_TREND_BUFFER.pop(0)
        
    if len(PROC_TIME_TREND_BUFFER) < 3:
        return "STABLE", 0
        
    # Check for continuous upward trend: cycle_1 < cycle_2 < cycle_3
    if PROC_TIME_TREND_BUFFER[0] < PROC_TIME_TREND_BUFFER[1] < PROC_TIME_TREND_BUFFER[2]:
        return "INCREASING_NON_STOP", 3
        
    return "STABLE", 0


def mock_ocr_weight_sensor():
    """
    Simulates a non-invasive OCR camera reading the digital scale screen.
    Returns excessive weight occasionally to simulate baggage disputes for evaluation.
    """
    # Simulate a scenario where luggage is overweight (e.g., 26.5 kg > 20 kg standard allowance)
    if time.time() % 30 < 5: 
        return 26.5
    return 12.2

# =====================================================================
# TRUCK 1 & 2: CV PROCESSING & MATHEMATICAL METRICS PIPELINE
# =====================================================================
def run_vision_pipeline(video_source="airport_mock.mp4"):
    global TOTAL_PASSENGERS_ENTERED
    cap = cv2.VideoCapture(video_source)
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("[INFO] Video stream ended or failed to load.")
            break
            
        current_time = time.time()
        current_queue_density = 0
        
        # Track people (Class 0) using ByteTrack
        results = MODEL.track(frame, persist=True, classes=[0], tracker="bytetrack.yaml")
        
        # Annotate ROI Zones on monitor
        cv2.polylines(frame, [ZONE_1_QUEUE], True, (0, 255, 0), 2)  # Zone 1: Green Area
        cv2.polylines(frame, [ZONE_2_COUNTER], True, (255, 0, 0), 2) # Zone 2: Blue Area
        
        if results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            ids = results[0].boxes.id.cpu().numpy().astype(int)
            
            for box, pid in zip(boxes, ids):
                # Neo point: Bottom center of bounding box representing foot coordinate
                foot_point = ((box[0] + box[2]) / 2, box[3])
                
                in_z1 = is_inside_zone(foot_point, ZONE_1_QUEUE)
                in_z2 = is_inside_zone(foot_point, ZONE_2_COUNTER)
                
                # Initialize new passenger entry inside the system registry
                if pid not in PASSENGER_REGISTRY:
                    PASSENGER_REGISTRY[pid] = {"enter_z1": None, "exit_z1": None, "exit_z2": None}
                
                # Phase 1: Passenger enters the queue lane (Zone 1)
                if in_z1:
                    current_queue_density += 1
                    if PASSENGER_REGISTRY[pid]["enter_z1"] is None:
                        PASSENGER_REGISTRY[pid]["enter_z1"] = current_time
                        TOTAL_PASSENGERS_ENTERED += 1
                        
                # Phase 2: Passenger leaves the queue (Zone 1) and approaches the desk (Zone 2)
                if in_z2:
                    if PASSENGER_REGISTRY[pid]["exit_z1"] is None:
                        PASSENGER_REGISTRY[pid]["exit_z1"] = current_time
                        # Record completed queue wait time (Simulating 1s real = 30s scaled for demonstration)
                        if PASSENGER_REGISTRY[pid]["enter_z1"] is not None:
                            actual_wait = (PASSENGER_REGISTRY[pid]["exit_z1"] - PASSENGER_REGISTRY[pid]["enter_z1"]) * 30 / 60
                            HISTORICAL_WAIT_TIMES.append(actual_wait)
                            
                # Phase 3: Passenger finishes check-in procedures and leaves the desk (Zone 2)
                if not in_z1 and not in_z2 and PASSENGER_REGISTRY[pid]["exit_z1"] is not None and PASSENGER_REGISTRY[pid]["exit_z2"] is None:
                    PASSENGER_REGISTRY[pid]["exit_z2"] = current_time
                    # Record completed processing desk time (Simulating 1s real = 30s scaled)
                    actual_proc = (PASSENGER_REGISTRY[pid]["exit_z2"] - PASSENGER_REGISTRY[pid]["exit_z1"]) * 30 / 60
                    HISTORICAL_PROCESSING_TIMES.append(actual_proc)

        # Calculate final mathematical SLA averages
        final_avg_wait = np.mean(HISTORICAL_WAIT_TIMES) if HISTORICAL_WAIT_TIMES else 0.0
        final_avg_proc = np.mean(HISTORICAL_PROCESSING_TIMES) if HISTORICAL_PROCESSING_TIMES else 0.0
        
        # Calculate trend analysis and accumulation velocity
        trend_status, trend_cycles = analyze_processing_trend(final_avg_proc)
        accumulation_rate = calculate_accumulation_rate(current_time)
        ocr_weight = mock_ocr_weight_sensor()
        
        # CONTEXT-AWARE DETERMINISTIC LOGIC: Determine baggage dispute without ML training overhead
        detected_incident = None
        if ocr_weight > 20.0 and final_avg_proc > 4.0:
            detected_incident = "LUGGAGE_DISPUTE"
            
        # Hardcode an emergency situation for testing the 20-second timeout mechanism
        if final_avg_wait > 12.0:
            detected_incident = "MEDICAL_EMERGENCY"

        # Construct payload message packet for Trạm 3 (LLM Engine)
        metrics_payload = {
            "current_queue_density": current_queue_density,
            "avg_wait_time_minutes": round(final_avg_wait, 1),
            "avg_processing_time_minutes": round(final_avg_proc, 1),
            "accumulation_rate_per_min": round(accumulation_rate, 2),
            "trend_analysis": {
                "proc_time_slope": trend_status,
                "consecutive_cycles_of_increase": trend_cycles
            },
            "trigger_incident": detected_incident,
            "system_timestamp": current_time
        }
        
        # Export metrics payload payload to shared JSON file
        with open("chokepoint_metrics.json", "w") as f:
            json.dump(metrics_payload, f, indent=4)
            
        # Display annotated feed
        cv2.imshow("ChokePoint AI - Data Pipeline Engine", frame if results[0].boxes.id is None else results[0].plot())
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_vision_pipeline()