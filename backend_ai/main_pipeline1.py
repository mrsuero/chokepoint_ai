import cv2
import numpy as np
import time
import json
import os
from ultralytics import YOLO

# Global model initialization
try:
    MODEL = YOLO("yolo11n.pt")
    print(f"[DEBUG] YOLO model loaded successfully: {MODEL}")
except Exception as e:
    print(f"[ERROR] Failed to load YOLO model: {e}")
    MODEL = None

# Runtime tracking data structures
PASSENGER_REGISTRY = {}
HISTORICAL_WAIT_TIMES = []
HISTORICAL_PROCESSING_TIMES = []
PROC_TIME_TREND_BUFFER = []

# Statistical initial states
TOTAL_PASSENGERS_ENTERED = 0
SYSTEM_START_TIME = time.time()

# Target data paths directly inside the Frontend public repository
OUTPUT_PATH = os.path.join("..", "frontend_ui", "public", "chokepoint_metrics1.json")
FRAME_OUTPUT_PATH = os.path.join("..", "frontend_ui", "public", "current_frame1.jpg")

# === TOẠ ĐỘ ZONE (đã calibrate thực tế bằng get_coords.py) ===
ZONE_1_SOURCE = np.array([
    [198, 246],  # Top-Left (1)
    [610, 249],  # Top-Right (2)
    [612, 349],  # Bottom-Right (3)
    [154, 337]   # Bottom-Left (4)
], np.int32)  # Zone 1 - khu vực xếp hàng chờ để vô làm thủ tục

ZONE_2_SOURCE = np.array([
    [357, 257],  # Top-Left (1)
    [358, 206],  # Top-Right (2)
    [756, 203],  # Bottom-Right (3)
    [740, 253]   # Bottom-Left (4)
], np.int32)  # Zone 2 - khu vực làm thủ tục tại quầy

LUGGAGE_LABELS = {"backpack", "handbag", "suitcase"}
LUGGAGE_STATIONARY_THRESHOLD_MINUTES = 10
LUGGAGE_MOVEMENT_TOLERANCE_PX = 15

LUGGAGE_TRACKER = {}

def get_dynamic_zones(frame_width, frame_height):
    """
    Cả 2 zone đều lấy trực tiếp từ toạ độ đã calibrate bằng get_coords.py.
    """
    zone_1 = ZONE_1_SOURCE
    zone_2 = ZONE_2_SOURCE

    # Đường ranh giới ảo minh hoạ (lấy trung bình toạ độ x của zone_2 làm mốc)
    divider_x = int(np.mean(zone_2[:, 0]))

    return zone_1, zone_2, divider_x

def is_inside_zone(point, polygon_zone):
    """
    Evaluates point polygon inclusion test to check if coordinate matches target ROI.
    """
    return cv2.pointPolygonTest(polygon_zone, point, False) >= 0


def draw_zone_labels(frame, zone_1, zone_2, zone_1_count, zone_2_count):
    zone_1_min = zone_1.min(axis=0)
    zone_2_min = zone_2.min(axis=0)

    cv2.putText(frame, "ZONE 1: WAITING AREA", (int(zone_1_min[0]), max(25, int(zone_1_min[1]) - 10)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)
    cv2.putText(frame, f"PAX: {zone_1_count}", (int(zone_1_min[0]), max(50, int(zone_1_min[1]) + 15)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)

    cv2.putText(frame, "ZONE 2: CHECK-IN AREA", (int(zone_2_min[0]), max(25, int(zone_2_min[1]) - 10)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 0, 0), 2)
    cv2.putText(frame, f"PAX: {zone_2_count}", (int(zone_2_min[0]), max(50, int(zone_2_min[1]) + 15)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 0, 0), 2)

    cv2.rectangle(frame, (20, 20), (360, 78), (15, 23, 42), -1)
    cv2.rectangle(frame, (20, 20), (360, 78), (71, 85, 105), 1)
    cv2.putText(frame, "ZONE TRACKING LEGEND", (32, 43), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (226, 232, 240), 2)
    cv2.putText(frame, "GREEN = WAITING AREA | BLUE = CHECK-IN AREA", (32, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (148, 163, 184), 1)

def calculate_accumulation_rate(current_time):
    """
    Calculates the linear passenger inflow accumulation delta per minute.
    """
    elapsed_minutes = (current_time - SYSTEM_START_TIME) / 60
    total_exited_z1 = len(HISTORICAL_WAIT_TIMES)
    if elapsed_minutes > 0:
        return (TOTAL_PASSENGERS_ENTERED - total_exited_z1) / elapsed_minutes
    return 0.0

def analyze_processing_trend(current_avg_proc):
    """
    Tracks historical data derivatives over 3 data steps to verify monotonic expansion.
    """
    global PROC_TIME_TREND_BUFFER
    PROC_TIME_TREND_BUFFER.append(current_avg_proc)
    if len(PROC_TIME_TREND_BUFFER) > 3:
        PROC_TIME_TREND_BUFFER.pop(0)
    if len(PROC_TIME_TREND_BUFFER) < 3:
        return "STABLE", 0
    if PROC_TIME_TREND_BUFFER[0] < PROC_TIME_TREND_BUFFER[1] < PROC_TIME_TREND_BUFFER[2]:
        return "INCREASING_NON_STOP", 3
    return "STABLE", 0

def run_simulation_loop():
    """
    Fallback loop executing mathematical generation if no source video asset is found.
    Generates dummy frames to ensure the frontend image stream works properly.
    """
    print("[SYSTEM NOTICE] Entering dynamic vision simulation mode due to missing video source asset.")
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    # Create a base dark canvas for web preview fallback simulation
    sim_frame = np.zeros((540, 960, 3), dtype=np.uint8)

    while True:
        current_time = time.time()
        elapsed = current_time - SYSTEM_START_TIME

        current_queue_density = 8 + int(np.sin(elapsed / 10) * 4)
        simulated_wait = 4.5 + (elapsed * 0.05)
        simulated_proc = 2.5 + (elapsed * 0.02)

        trend_status = "STABLE"
        trend_cycles = 0
        if elapsed > 30:
            trend_status = "INCREASING_NON_STOP"
            trend_cycles = 3

        detected_incident = None
        if simulated_wait >= 12.0:
            detected_incident = "MEDICAL_EMERGENCY"
        elif elapsed > 20 and elapsed <= 35:
            detected_incident = "SUSPECTED_LUGGAGE_DISPUTE"

        metrics_payload = {
            "current_queue_density": max(0, current_queue_density),
            "avg_wait_time_minutes": round(simulated_wait, 1),
            "avg_processing_time_minutes": round(simulated_proc, 1),
            "accumulation_rate_per_min": round(0.5 + (current_queue_density * 0.1), 2),
            "trend_analysis": {
                "proc_time_slope": trend_status,
                "consecutive_cycles_of_increase": trend_cycles
            },
            "trigger_incident": detected_incident,
            "system_timestamp": current_time
        }

        with open(OUTPUT_PATH, "w") as f:
            json.dump(metrics_payload, f, indent=4)

        # Draw dynamic canvas details for web display testing
        frame_copy = sim_frame.copy()
        cv2.putText(frame_copy, f"SIMULATION FEED RUNNING - TIME: {int(elapsed)}s", (50, 200),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 200), 2)
        cv2.putText(frame_copy, f"DENSITY TARGET: {current_queue_density} PAX", (50, 260),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        if detected_incident:
            cv2.putText(frame_copy, f"ALERT: {detected_incident}", (50, 320),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        cv2.imwrite(FRAME_OUTPUT_PATH, frame_copy)
        time.sleep(1)

def run_vision_pipeline(video_source="video1.mp4"):
    global TOTAL_PASSENGERS_ENTERED

    # Cơ chế tự động quét thông minh: Check thư mục hiện tại trước, nếu không thấy thì check thư mục cha
    original_source = video_source
    if not os.path.exists(video_source):
        fallback_path = os.path.join("..", video_source)
        if os.path.exists(fallback_path):
            video_source = fallback_path

    print(f"[DEBUG] Working directory: {os.getcwd()}")
    print(f"[DEBUG] Original video_source arg: {original_source}")
    print(f"[DEBUG] Resolved video_source path: {os.path.abspath(video_source)}")
    print(f"[DEBUG] Video exists check: {os.path.exists(video_source)}")
    print(f"[DEBUG] MODEL is None: {MODEL is None}")

    if not os.path.exists(video_source) or MODEL is None:
        if not os.path.exists(video_source):
            print(f"[SYSTEM NOTICE] Fatal: Video asset not found at '{os.path.abspath(video_source)}'. Launching Simulation Mode.")
        if MODEL is None:
            print("[SYSTEM NOTICE] Fatal: YOLO model failed to load (see [ERROR] above). Launching Simulation Mode.")
        run_simulation_loop()
        return

    cap = cv2.VideoCapture(video_source)
    if not cap.isOpened():
        print(f"[SYSTEM NOTICE] Fatal: cv2.VideoCapture could not open '{video_source}' (codec/format issue?). Launching Simulation Mode.")
        run_simulation_loop()
        return

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    zone_1, zone_2, divider_x = get_dynamic_zones(frame_width, frame_height)

    print(f"[DEBUG] Video opened successfully: {frame_width}x{frame_height}")

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            # Tự động lặp lại video từ đầu khi chạy hết file để tiện Demo
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        current_time = time.time()
        current_queue_density = 0
        zone_1_people_count = 0
        zone_2_people_count = 0
        zone_1_luggage_count = 0
        results = MODEL.track(
            frame,
            persist=True,
            classes=[0, 24, 26, 28],
            tracker="bytetrack.yaml",
            conf=0.15,      # Hạ ngưỡng confidence (mặc định 0.25) để bắt cả người bị che/ở xa
            iou=0.5,        # Ngưỡng NMS - giữ được người đứng sát nhau, tránh gộp box
            imgsz=960       # Tăng độ phân giải inference (mặc định 640) để không mất chi tiết người nhỏ
        )

        if results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            ids = results[0].boxes.id.cpu().numpy().astype(int)
            class_ids = results[0].boxes.cls.cpu().numpy().astype(int)

            for box, pid, class_id in zip(boxes, ids, class_ids):
                center_point = (int((box[0] + box[2]) / 2), int((box[1] + box[3]) / 2))
                foot_point = (int((box[0] + box[2]) / 2), int(box[3]))
                label_name = results[0].names.get(int(class_id), str(class_id))
                in_z1 = is_inside_zone(foot_point, zone_1)
                in_z2 = is_inside_zone(foot_point, zone_2)

                if label_name in LUGGAGE_LABELS:
                    tracker_state = LUGGAGE_TRACKER.get(pid)
                    if tracker_state is None:
                        tracker_state = {
                            "first_seen": current_time,
                            "stationary_since": current_time,
                            "last_center": center_point,
                            "in_zone_1": in_z1,
                        }
                    else:
                        last_center = tracker_state["last_center"]
                        movement_delta = abs(center_point[0] - last_center[0]) + abs(center_point[1] - last_center[1])
                        if movement_delta <= LUGGAGE_MOVEMENT_TOLERANCE_PX:
                            if tracker_state["stationary_since"] is None:
                                tracker_state["stationary_since"] = current_time
                        else:
                            tracker_state["stationary_since"] = current_time

                        tracker_state["last_center"] = center_point
                        tracker_state["in_zone_1"] = in_z1

                    LUGGAGE_TRACKER[pid] = tracker_state

                    stationary_duration = current_time - tracker_state["stationary_since"] if tracker_state["stationary_since"] else 0
                    if in_z1 and stationary_duration >= LUGGAGE_STATIONARY_THRESHOLD_MINUTES * 60:
                        zone_1_luggage_count += 1

                if label_name != "person":
                    continue

                if pid not in PASSENGER_REGISTRY:
                    PASSENGER_REGISTRY[pid] = {"enter_z1": None, "exit_z1": None, "exit_z2": None}

                if in_z1:
                    current_queue_density += 1
                    zone_1_people_count += 1
                    if PASSENGER_REGISTRY[pid]["enter_z1"] is None:
                        PASSENGER_REGISTRY[pid]["enter_z1"] = current_time
                        TOTAL_PASSENGERS_ENTERED += 1

                if in_z2:
                    zone_2_people_count += 1
                    if PASSENGER_REGISTRY[pid]["exit_z1"] is None:
                        PASSENGER_REGISTRY[pid]["exit_z1"] = current_time
                        if PASSENGER_REGISTRY[pid]["enter_z1"] is not None:
                            actual_wait = (PASSENGER_REGISTRY[pid]["exit_z1"] - PASSENGER_REGISTRY[pid]["enter_z1"]) * 30 / 60
                            HISTORICAL_WAIT_TIMES.append(actual_wait)

                if not in_z1 and not in_z2 and PASSENGER_REGISTRY[pid]["exit_z1"] is not None and PASSENGER_REGISTRY[pid]["exit_z2"] is None:
                    PASSENGER_REGISTRY[pid]["exit_z2"] = current_time
                    actual_proc = (PASSENGER_REGISTRY[pid]["exit_z2"] - PASSENGER_REGISTRY[pid]["exit_z1"]) * 30 / 60
                    HISTORICAL_PROCESSING_TIMES.append(actual_proc)

        final_avg_wait = np.mean(HISTORICAL_WAIT_TIMES) if HISTORICAL_WAIT_TIMES else 0.0
        final_avg_proc = np.mean(HISTORICAL_PROCESSING_TIMES) if HISTORICAL_PROCESSING_TIMES else 0.0

        trend_status, trend_cycles = analyze_processing_trend(final_avg_proc)
        accumulation_rate = calculate_accumulation_rate(current_time)

        detected_incident = None
        if zone_1_luggage_count > 0 and final_avg_proc > 4.0 and zone_1_people_count > 0:
            detected_incident = "SUSPECTED_LUGGAGE_DISPUTE"
        elif final_avg_wait > 12.0:
            detected_incident = "MEDICAL_EMERGENCY"

        metrics_payload = {
            "current_queue_density": current_queue_density,
            "avg_wait_time_minutes": round(final_avg_wait, 1),
            "avg_processing_time_minutes": round(final_avg_proc, 1),
            "accumulation_rate_per_min": round(accumulation_rate, 2),
            "luggage_stationary_threshold_minutes": LUGGAGE_STATIONARY_THRESHOLD_MINUTES,
            "zone_analysis": {
                "zone_1_name": "WAITING_AREA",
                "zone_2_name": "CHECK_IN_AREA",
                "zone_1_people_count": zone_1_people_count,
                "zone_2_people_count": zone_2_people_count,
                "zone_1_luggage_count": zone_1_luggage_count,
            },
            "trend_analysis": {
                "proc_time_slope": trend_status,
                "consecutive_cycles_of_increase": trend_cycles
            },
            "trigger_incident": detected_incident,
            "system_timestamp": current_time
        }

        if zone_1_luggage_count > 0 and final_avg_proc > 4.0 and zone_1_people_count > 0:
            metrics_payload["trigger_incident"] = "SUSPECTED_LUGGAGE_DISPUTE"

        with open(OUTPUT_PATH, "w") as f:
            json.dump(metrics_payload, f, indent=4)

        render_frame = results[0].plot()
        cv2.polylines(render_frame, [zone_1], True, (0, 255, 0), 2)
        cv2.polylines(render_frame, [zone_2], True, (255, 0, 0), 2)
        draw_zone_labels(render_frame, zone_1, zone_2, zone_1_people_count, zone_2_people_count)

        cv2.imwrite(FRAME_OUTPUT_PATH, render_frame)

        cv2.imshow("ChokePoint AI - Core Pipeline Terminal", render_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_vision_pipeline()