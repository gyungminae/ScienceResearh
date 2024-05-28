import cv2

# 비디오 파일 경로
video = "videos\inktest.mp4"
video_cropped = video.split(".")[0] + "_cropped.avi"

# 전역 변수 설정
ref_point = []
cropping = False
click_count = 0
resize_width = 640  # 표시할 창의 너비
resize_height = 480  # 표시할 창의 높이

def click_and_crop(event, x, y, flags, param):
    global ref_point, cropping, click_count, scale_x, scale_y

    if event == cv2.EVENT_LBUTTONDOWN:
        click_count += 1
        ref_point.append((int(x / scale_x), int(y / scale_y)))

        if click_count == 1:
            cropping = True
        elif click_count == 2:
            cropping = False
            cv2.rectangle(frame_display, ref_point[0], ref_point[1], (0, 255, 0), 2)
            cv2.imshow("image", frame_display)

# 비디오 캡처 객체 생성 및 설정
cap = cv2.VideoCapture(video)
cv2.namedWindow("image")
cv2.setMouseCallback("image", click_and_crop)

# 첫 번째 루프: 좌표 설정을 위한 프레임 표시
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # 프레임 크기 조정
    height, width = frame.shape[:2]
    scale_x = resize_width / width
    scale_y = resize_height / height
    frame_display = cv2.resize(frame, (resize_width, resize_height))

    cv2.imshow("image", frame_display)

    key = cv2.waitKey(1) & 0xFF
    if key == ord("q") or (len(ref_point) == 2 and not cropping):
        break

cap.release()
cv2.destroyAllWindows()

# 좌표가 유효한지 확인
if len(ref_point) != 2:
    print("Invalid ROI. Exiting.")
    exit()

x1, y1 = ref_point[0]
x2, y2 = ref_point[1]

# 좌표 정렬
x1, x2 = min(x1, x2), max(x1, x2)
y1, y2 = min(y1, y2), max(y1, y2)

if x1 >= x2 or y1 >= y2:
    print("Invalid ROI dimensions. Exiting.")
    exit()

print(f"ROI set: ({x1}, {y1}) to ({x2}, {y2})")

# 두 번째 루프: 비디오를 다시 읽고, 자른 프레임을 저장
cap = cv2.VideoCapture(video)
fourcc = cv2.VideoWriter_fourcc(*"XVID")
out = cv2.VideoWriter(video_cropped, fourcc, cap.get(cv2.CAP_PROP_FPS), (x2-x1, y2-y1))

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # ROI 영역 잘라내기
    crop_frame = frame[y1:y2, x1:x2]
    out.write(crop_frame)

    # 현재 저장된 비디오의 진행률 계산
    current_frame = cap.get(cv2.CAP_PROP_POS_FRAMES)
    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    progress = int(current_frame / total_frames * 100)

    # 진행률을 한 줄에 출력 (덮어쓰기)
    print(f"\rSaving video: {progress}% complete", end="")

cap.release()
out.release()
cv2.destroyAllWindows()

print(f"\nCropped video saved as {video_cropped}")
