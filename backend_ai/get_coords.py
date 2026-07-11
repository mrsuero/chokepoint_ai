'''
python get_coords.py --video "data/7616770422833.mp4"
'''
import cv2
import argparse
import numpy as np

# --- BIẾN TOÀN CỤC ---
points = []
scale_factor = 1.0
img_clean = None
img_display = None


def draw_detailed_grid(img):
    h, w = img.shape[:2]

    # 1. Lưới phụ (Nhỏ)
    minor_spacing = 20
    minor_color = (80, 80, 80)
    for x in range(0, w, minor_spacing):
        cv2.line(img, (x, 0), (x, h), minor_color, 1)
    for y in range(0, h, minor_spacing):
        cv2.line(img, (0, y), (w, y), minor_color, 1)

    # 2. Lưới chính (Lớn)
    major_spacing = 100
    major_color = (200, 200, 200)
    text_color = (255, 255, 255)

    for x in range(0, w, major_spacing):
        cv2.line(img, (x, 0), (x, h), major_color, 1)
        cv2.putText(img, str(x), (x + 5, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, text_color, 1)

    for y in range(0, h, major_spacing):
        cv2.line(img, (0, y), (w, y), major_color, 1)
        if y > 0:
            cv2.putText(img, str(y), (5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, text_color, 1)

    return img


def click_event(event, x, y, flags, params):
    global points, scale_factor, img_clean, img_display

    if event == cv2.EVENT_LBUTTONDOWN:
        if len(points) >= 4:
            print("-> Bạn đã chọn đủ 4 điểm! Nhấn phím bất kỳ để thoát.")
            return

        real_x = int(x * scale_factor)
        real_y = int(y * scale_factor)
        points.append([real_x, real_y])

        img_display = img_clean.copy()
        display_points = [(int(pt[0] / scale_factor), int(pt[1] / scale_factor)) for pt in points]

        for i, pt in enumerate(display_points):
            cv2.circle(img_display, pt, 5, (0, 0, 255), -1)
            cv2.putText(img_display, str(i + 1), (pt[0] + 10, pt[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255),
                        2)
            if i > 0:
                cv2.line(img_display, display_points[i - 1], pt, (0, 255, 0), 2)
            if len(points) == 4 and i == 3:
                cv2.line(img_display, pt, display_points[0], (0, 255, 0), 2)

        cv2.imshow('Cong cu lay toa do Pro', img_display)

        if len(points) == 4:
            print("\n" + "=" * 60)
            print("--- COPY ĐOẠN DƯỚI ĐÂY VÀO FILE yolo_nas_example.py ---")
            print("=" * 60)
            print(f"    SOURCE = np.array([")
            print(f"        [{points[0][0]}, {points[0][1]}],  # Top-Left (1)")
            print(f"        [{points[1][0]}, {points[1][1]}],  # Top-Right (2)")
            print(f"        [{points[2][0]}, {points[2][1]}],  # Bottom-Right (3)")
            print(f"        [{points[3][0]}, {points[3][1]}]   # Bottom-Left (4)")
            print(f"    ])")
            print("=" * 60 + "\n")
            print("-> KHUNG ĐÃ ĐƯỢC VẼ (MÀU XANH LÁ)! Nhấn phím bất kỳ để thoát.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True, help="Path to video file")
    args = parser.parse_args()

    cap = cv2.VideoCapture(args.video)
    ret, frame = cap.read()
    if not ret:
        print("Lỗi: Không đọc được video!")
        exit()

    real_h, real_w = frame.shape[:2]

    TARGET_DISPLAY_WIDTH = 1280
    if real_w > TARGET_DISPLAY_WIDTH:
        scale_factor = real_w / TARGET_DISPLAY_WIDTH
        new_w = TARGET_DISPLAY_WIDTH
        new_h = int(real_h / scale_factor)
        img_base = cv2.resize(frame, (new_w, new_h))
    else:
        scale_factor = 1.0
        img_base = frame.copy()

    img_clean = draw_detailed_grid(img_base)
    img_display = img_clean.copy()

    window_name = 'Cong cu lay toa do Pro'
    cv2.imshow(window_name, img_display)
    cv2.setMouseCallback(window_name, click_event)

    print("\n" + "*" * 50)
    print("=== CÔNG CỤ LẤY TỌA ĐỘ PRO ===")
    print("Click thứ tự: TRÁI-TRÊN (1) -> PHẢI-TRÊN (2) -> PHẢI-DƯỚI (3) -> TRÁI-DƯỚI (4)")
    print("*" * 50 + "\n")

    cv2.waitKey(0)
    cv2.destroyAllWindows()