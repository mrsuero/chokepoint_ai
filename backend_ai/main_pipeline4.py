import cv2
import numpy as np
import time
import json
import os
from collections import deque
from ultralytics import YOLO

# Global model initialization
try:
    MODEL = YOLO("yolo11n.pt")
    print(f"[DEBUG] YOLO model loaded successfully: {MODEL}")
except Exception as e:
    print(f"[ERROR] Failed to load YOLO model: {e}")
    MODEL = None

# Runtime tracking data structures
PASSENGER_REGISTRY = {}          # pid -> {"first_seen", "last_seen"} - không còn phụ thuộc zone
HISTORICAL_DWELL_TIMES = []      # thời gian hiện diện (phút) của từng người đã rời khỏi khung hình
PROC_TIME_TREND_BUFFER = []

# Statistical initial states
TOTAL_PASSENGERS_ENTERED = 0
SYSTEM_START_TIME = time.time()

# Target data paths directly inside the Frontend public repository
OUTPUT_PATH = os.path.join("..", "frontend_ui", "public", "chokepoint_metrics.json")
FRAME_OUTPUT_PATH = os.path.join("..", "frontend_ui", "public", "current_frame3.jpg")

LUGGAGE_LABELS = {"backpack", "handbag", "suitcase"}
LUGGAGE_STATIONARY_THRESHOLD_MINUTES = 10
LUGGAGE_MOVEMENT_TOLERANCE_PX = 15

LUGGAGE_TRACKER = {}

# === PHÁT HIỆN ẨU ĐẢ / ĐÁNH NHAU (thay cho logic chia zone cũ) ===
# Không dùng pose model riêng, chỉ dùng bounding box người từ YOLO tracker có sẵn.
# LƯU Ý QUAN TRỌNG: khi 1 người tung cú đấm, THÂN NGƯỜI hầu như đứng yên - chỉ
# có tay vươn ra - nên nếu chỉ đo vận tốc TÂM bbox thì gần như không phát hiện
# được cú đấm (đây là lý do bản trước đó bị bỏ sót cảnh đấm bốc). Thay vào đó:
#   1) Đo khoảng cách CẠNH-VỚI-CẠNH giữa 2 bbox (không phải tâm-với-tâm) để
#      biết 2 người có đang trong tầm với/đá của nhau hay không - chính xác
#      hơn nhiều so với khoảng cách tâm khi 2 người đứng đối mặt tầm sải tay.
#   2) Đo mức "phình/co" của bbox (width, height) qua từng frame. Khi tay/chân
#      vươn ra đấm/đá, bbox người sẽ phình rộng đột ngột dù tâm không đổi -
#      đây là tín hiệu tốt hơn nhiều để bắt cử động chi so với tâm bbox.
#   3) Kết hợp cả 2 tín hiệu trên, xác nhận qua nhiều frame liên tiếp để giảm
#      báo nhầm khi chỉ là nhiễu detection thoáng qua.
ALTERCATION_EDGE_GAP_PX = 40           # 2 bbox được coi là "trong tầm với nhau" nếu khoảng cách cạnh-với-cạnh dưới ngưỡng này
ALTERCATION_MOTION_PX = 14             # biến động (tâm di chuyển HOẶC kích thước bbox thay đổi) mỗi frame để coi là "cử động mạnh"
ALTERCATION_FRAME_WINDOW = 20          # số frame gần nhất dùng để xác nhận, giảm false positive tức thời
ALTERCATION_CONFIRM_RATIO = 0.4        # tỉ lệ frame "nghi vấn" trong window để xác nhận là ẩu đả thật

PERSON_MOTION_TRACKER = {}             # pid -> {"prev_center", "prev_size": (w, h), "motion_history": deque}
ALTERCATION_FRAME_BUFFER = deque(maxlen=ALTERCATION_FRAME_WINDOW)


def box_edge_gap(box_a, box_b):
    """
    Khoảng cách cạnh-với-cạnh giữa 2 bounding box (x1, y1, x2, y2).
    Trả về 0 nếu 2 box chồng lấn nhau (đang chạm/gần như chạm).
    """
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    gap_x = max(0.0, max(ax1, bx1) - min(ax2, bx2))
    gap_y = max(0.0, max(ay1, by1) - min(ay2, by2))

    return (gap_x ** 2 + gap_y ** 2) ** 0.5


def calculate_accumulation_rate(current_time):
    """
    Calculates the linear passenger inflow accumulation delta per minute.
    """
    elapsed_minutes = (current_time - SYSTEM_START_TIME) / 60
    total_exited = len(HISTORICAL_DWELL_TIMES)
    if elapsed_minutes > 0:
        return (TOTAL_PASSENGERS_ENTERED - total_exited) / elapsed_minutes
    return 0.0


def analyze_processing_trend(current_avg_dwell):
    """
    Tracks historical data derivatives over 3 data steps to verify monotonic expansion.
    """
    global PROC_TIME_TREND_BUFFER
    PROC_TIME_TREND_BUFFER.append(current_avg_dwell)
    if len(PROC_TIME_TREND_BUFFER) > 3:
        PROC_TIME_TREND_BUFFER.pop(0)
    if len(PROC_TIME_TREND_BUFFER) < 3:
        return "STABLE", 0
    if PROC_TIME_TREND_BUFFER[0] < PROC_TIME_TREND_BUFFER[1] < PROC_TIME_TREND_BUFFER[2]:
        return "INCREASING_NON_STOP", 3
    return "STABLE", 0


def update_person_motion(pid, center, box):
    """
    Cập nhật lịch sử chuyển động của 1 người, trả về điểm "motion_score" trung
    bình gần đây (px/frame). motion_score lấy giá trị LỚN HƠN giữa:
      - vận tốc tâm bbox (bắt cử động toàn thân: bước tới, né, ngã...)
      - biến động kích thước bbox (bắt cử động chi: vươn tay đấm, đá...)
    vì một cú đấm thường không di chuyển tâm thân nhiều nhưng làm bbox phình
    rộng đột ngột khi tay vươn ra khỏi khung thân.
    """
    width = box[2] - box[0]
    height = box[3] - box[1]

    state = PERSON_MOTION_TRACKER.get(pid)
    if state is None:
        state = {
            "prev_center": center,
            "prev_size": (width, height),
            "motion_history": deque(maxlen=5),
        }
        PERSON_MOTION_TRACKER[pid] = state
        return 0.0

    prev_center = state["prev_center"]
    prev_width, prev_height = state["prev_size"]

    center_velocity = ((center[0] - prev_center[0]) ** 2 + (center[1] - prev_center[1]) ** 2) ** 0.5
    size_change = abs(width - prev_width) + abs(height - prev_height)
    motion_score = max(center_velocity, size_change)

    state["motion_history"].append(motion_score)
    state["prev_center"] = center
    state["prev_size"] = (width, height)

    return sum(state["motion_history"]) / len(state["motion_history"])


def detect_altercation_candidate(persons_this_frame):
    """
    persons_this_frame: list of (pid, center, box) cho tất cả người phát hiện được trong frame hiện tại.
    Trả về True nếu có ít nhất 1 cặp người vừa trong tầm với nhau (khoảng cách
    cạnh-với-cạnh, không phải tâm-với-tâm) VỪA có cử động mạnh/đột ngột đồng
    thời (thân hoặc chi) - dấu hiệu nghi vấn xô xát/đấm nhau.
    """
    motion_scores = {pid: update_person_motion(pid, center, box) for pid, center, box in persons_this_frame}

    for i in range(len(persons_this_frame)):
        pid_a, _, box_a = persons_this_frame[i]
        for j in range(i + 1, len(persons_this_frame)):
            pid_b, _, box_b = persons_this_frame[j]

            if box_edge_gap(box_a, box_b) > ALTERCATION_EDGE_GAP_PX:
                continue

            if motion_scores[pid_a] >= ALTERCATION_MOTION_PX and motion_scores[pid_b] >= ALTERCATION_MOTION_PX:
                return True

    return False


def draw_altercation_overlay(frame, person_count, altercation_confirmed):
    cv2.rectangle(frame, (20, 20), (380, 78), (15, 23, 42), -1)
    cv2.rectangle(frame, (20, 20), (380, 78), (71, 85, 105), 1)
    cv2.putText(frame, "CHOKEPOINT AI - LIVE ANALYTICS", (32, 43), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (226, 232, 240), 2)
    cv2.putText(frame, f"PAX IN FRAME: {person_count}", (32, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (148, 163, 184), 1)

    if altercation_confirmed:
        cv2.rectangle(frame, (0, 0), (frame.shape[1] - 1, frame.shape[0] - 1), (0, 0, 255), 6)
        cv2.putText(frame, "!!! SUSPECTED PHYSICAL ALTERCATION !!!", (32, 105),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)


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
        simulated_dwell = 4.5 + (elapsed * 0.05)

        trend_status = "STABLE"
        trend_cycles = 0
        if elapsed > 30:
            trend_status = "INCREASING_NON_STOP"
            trend_cycles = 3

        detected_incident = None
        if elapsed > 20 and elapsed <= 35:
            detected_incident = "SUSPECTED_PHYSICAL_ALTERCATION"
        elif simulated_dwell >= 12.0:
            detected_incident = "MEDICAL_EMERGENCY"

        metrics_payload = {
            "current_queue_density": max(0, current_queue_density),
            "avg_wait_time_minutes": round(simulated_dwell, 1),
            "avg_processing_time_minutes": round(simulated_dwell * 0.6, 1),
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


def run_vision_pipeline(video_source="video3.mp4"):
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
    print(f"[DEBUG] Video opened successfully: {frame_width}x{frame_height}")

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            # Tự động lặp lại video từ đầu khi chạy hết file để tiện Demo
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        current_time = time.time()
        persons_this_frame = []      # list (pid, center, box) - toàn bộ khung hình, không chia zone
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
                label_name = results[0].names.get(int(class_id), str(class_id))

                if label_name in LUGGAGE_LABELS:
                    tracker_state = LUGGAGE_TRACKER.get(pid)
                    if tracker_state is None:
                        tracker_state = {
                            "first_seen": current_time,
                            "stationary_since": current_time,
                            "last_center": center_point,
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

                    LUGGAGE_TRACKER[pid] = tracker_state

                    stationary_duration = current_time - tracker_state["stationary_since"] if tracker_state["stationary_since"] else 0
                    if stationary_duration >= LUGGAGE_STATIONARY_THRESHOLD_MINUTES * 60:
                        zone_1_luggage_count += 1

                if label_name != "person":
                    continue

                persons_this_frame.append((pid, center_point, tuple(box)))

                if pid not in PASSENGER_REGISTRY:
                    PASSENGER_REGISTRY[pid] = {"first_seen": current_time, "last_seen": current_time}
                    TOTAL_PASSENGERS_ENTERED += 1
                else:
                    PASSENGER_REGISTRY[pid]["last_seen"] = current_time

        # Người không còn xuất hiện gần đây -> coi như đã rời khung hình, chốt thời gian hiện diện của họ
        STALE_TIMEOUT_SECONDS = 3.0
        active_ids_this_frame = {pid for pid, _, _ in persons_this_frame}
        for pid in list(PASSENGER_REGISTRY.keys()):
            record = PASSENGER_REGISTRY[pid]
            if pid not in active_ids_this_frame and (current_time - record["last_seen"]) > STALE_TIMEOUT_SECONDS:
                dwell_minutes = (record["last_seen"] - record["first_seen"]) / 60
                HISTORICAL_DWELL_TIMES.append(dwell_minutes)
                del PASSENGER_REGISTRY[pid]
                PERSON_MOTION_TRACKER.pop(pid, None)

        # --- Phát hiện ẩu đả / đấm nhau (thay cho logic chia zone) ---
        altercation_candidate = detect_altercation_candidate(persons_this_frame)
        ALTERCATION_FRAME_BUFFER.append(altercation_candidate)
        altercation_confirmed = (
            len(ALTERCATION_FRAME_BUFFER) == ALTERCATION_FRAME_BUFFER.maxlen
            and (sum(ALTERCATION_FRAME_BUFFER) / len(ALTERCATION_FRAME_BUFFER)) >= ALTERCATION_CONFIRM_RATIO
        )

        current_queue_density = len(persons_this_frame)
        active_wait_minutes = [
            (current_time - record["first_seen"]) / 60 for record in PASSENGER_REGISTRY.values()
        ]
        final_avg_wait = float(np.mean(active_wait_minutes)) if active_wait_minutes else 0.0
        final_avg_dwell = float(np.mean(HISTORICAL_DWELL_TIMES)) if HISTORICAL_DWELL_TIMES else 0.0

        trend_status, trend_cycles = analyze_processing_trend(final_avg_dwell)
        accumulation_rate = calculate_accumulation_rate(current_time)

        detected_incident = None
        if altercation_confirmed:
            detected_incident = "SUSPECTED_PHYSICAL_ALTERCATION"
        elif final_avg_wait > 12.0:
            detected_incident = "MEDICAL_EMERGENCY"

        metrics_payload = {
            "current_queue_density": current_queue_density,
            "avg_wait_time_minutes": round(final_avg_wait, 1),
            "avg_processing_time_minutes": round(final_avg_dwell, 1),
            "accumulation_rate_per_min": round(accumulation_rate, 2),
            "luggage_stationary_threshold_minutes": LUGGAGE_STATIONARY_THRESHOLD_MINUTES,
            "luggage_stationary_count": zone_1_luggage_count,
            "altercation_detected": altercation_confirmed,
            "trend_analysis": {
                "proc_time_slope": trend_status,
                "consecutive_cycles_of_increase": trend_cycles
            },
            "trigger_incident": detected_incident,
            "system_timestamp": current_time
        }

        with open(OUTPUT_PATH, "w") as f:
            json.dump(metrics_payload, f, indent=4)

        render_frame = results[0].plot()
        draw_altercation_overlay(render_frame, current_queue_density, altercation_confirmed)

        cv2.imwrite(FRAME_OUTPUT_PATH, render_frame)

        cv2.imshow("ChokePoint AI - Core Pipeline Terminal", render_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_vision_pipeline()