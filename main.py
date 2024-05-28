import os
import cv2
import numpy as np
import pandas as pd

video = "videos\inktest.mp4"
video_cropped = video.split(".")[0] + "_cropped.avi"

interval = 0.2

data_folder = "./data"

# 빨간색 범위 (OpenCV에서는 BGR 색상을 사용)
lower_red = np.array([0, 0, 100])
upper_red = np.array([100, 100, 255])

cap = cv2.VideoCapture(video_cropped)

# 프레임당 시간 간격 (단위: 초)
frame_interval = 1 / cap.get(cv2.CAP_PROP_FPS)

# 시간당 면적을 저장할 데이터 프레임 생성
results = []

current_time = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    total_pixels = frame.shape[0] * frame.shape[1]

    # 빨간색 영역 감지
    mask = cv2.inRange(frame, lower_red, upper_red)

    # 빨간색 영역의 픽셀 수 계산
    red_area_pixels = cv2.countNonZero(mask)

    # 시간당 면적을 계산하여 결과에 추가
    results.append([current_time, red_area_pixels, red_area_pixels / total_pixels, total_pixels])

    # 다음 프레임으로 넘어가기 위해 interval초 만큼 프레임 건너뛰기
    cap.set(cv2.CAP_PROP_POS_MSEC, (current_time + interval) * 1000)

    # 다음 프레임의 시간 갱신
    current_time += interval

df = pd.DataFrame(results, columns=["Time (s)", "Red Area (pixels)", "Red Area Ratio", "Total Pixels"])

output_filename = os.path.join(data_folder, os.path.basename(video_cropped).split(".")[0] + ".xlsx")
df.to_excel(output_filename, index=False)

cap.release()

print(f"Red area results saved to {output_filename}")
