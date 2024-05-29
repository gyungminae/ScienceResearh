import os
import cv2
import numpy as np
import pandas as pd
import sys


def trim(video, length):
    video_path = "videos/" + video
    video_trimed = "trimmed/" + video.split(".")[0] + ".avi"

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("Error: Could not open video.")
        return

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    display_width = 640
    display_height = 480

    start_time = None
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        resized_frame = cv2.resize(frame, (display_width, display_height))
        cv2.imshow("Video", resized_frame)

        if cv2.waitKey(1) & 0xFF == ord(' '):
            start_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
            break

    if start_time is None:
        print("Start time not set. Exiting.")
        cap.release()
        cv2.destroyAllWindows()
        return

    end_time = start_time + length

    start_frame_index = int(start_time * fps)
    end_frame_index = int(end_time * fps)

    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame_index)

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = cv2.VideoWriter(video_trimed, fourcc, fps, (frame_width, frame_height))

    current_frame = start_frame_index
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret or current_frame >= end_frame_index:
            break

        out.write(frame)

        progress = (current_frame - start_frame_index) / (end_frame_index - start_frame_index) * 100
        sys.stdout.write(f"\rTrimming: {progress:.2f}%")
        sys.stdout.flush()

        current_frame += 1

        if cv2.waitKey(1) & 0xFF == ord(' '):
            cv2.destroyAllWindows()
            break

    cap.release()
    out.release()
    cv2.destroyAllWindows()

    print(f"\nVideo trimmed and saved as {video_trimed}")


def crop(video):
    global ref_point, cropping, click_count, scale_x, scale_y, frame_display

    video_path = "videos/" + video
    video_trimed = "trimmed/" + video.split(".")[0] + ".avi"
    video_cropped = "cropped/" + video.split(".")[0] + ".avi"

    ref_point = []
    cropping = False
    click_count = 0
    resize_width = 640
    resize_height = 480

    cap = cv2.VideoCapture(video_trimed)
    cv2.namedWindow("image")
    cv2.setMouseCallback("image", click_and_crop)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

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

    if len(ref_point) != 2:
        print("Invalid ROI. Exiting.")
        exit()

    x1, y1 = ref_point[0]
    x2, y2 = ref_point[1]
    x1, x2 = min(x1, x2), max(x1, x2)
    y1, y2 = min(y1, y2), max(y1, y2)

    if x1 >= x2 or y1 >= y2:
        print("Invalid ROI dimensions. Exiting.")
        exit()

    print(f"Sellected Coordinate Set: ({x1}, {y1}), ({x2}, {y2})")

    cap = cv2.VideoCapture(video_trimed)
    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    out = cv2.VideoWriter(video_cropped, fourcc, cap.get(cv2.CAP_PROP_FPS), (x2-x1, y2-y1))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        crop_frame = frame[y1:y2, x1:x2]
        out.write(crop_frame)

        current_frame = cap.get(cv2.CAP_PROP_POS_FRAMES)
        total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        progress = int(current_frame / total_frames * 100)

        print(f"\rCropping video: {progress}% complete", end="")

    cap.release()
    out.release()
    cv2.destroyAllWindows()

    print(f"\nCropped video saved as {video_cropped}")


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


def anz(video, interval, ran_s, ran_f):
    video_path = "videos/" + video
    video_trimed = "trimmed/" + video.split(".")[0] + ".avi"
    video_cropped = "cropped/" + video.split(".")[0] + ".avi"

    data_folder = "./data"

    lower_red = np.array(ran_s)
    upper_red = np.array(ran_f)

    cap = cv2.VideoCapture(video_cropped)

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_duration = total_frames / fps

    results = []
    current_time = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        total_pixels = frame.shape[0] * frame.shape[1]

        mask = cv2.inRange(frame, lower_red, upper_red)

        red_area_pixels = cv2.countNonZero(mask)

        results.append([current_time, red_area_pixels, red_area_pixels / total_pixels, total_pixels])

        cap.set(cv2.CAP_PROP_POS_MSEC, (current_time + interval) * 1000)

        current_time += interval

        progress = int((current_time / total_duration) * 100)
        print(f"\rAanalyzing video: {progress}% complete", end="")

    df = pd.DataFrame(results, columns=["Time (s)", "Red Area (pixels)", "Red Area Ratio", "Total Pixels"])

    output_filename = os.path.join(data_folder, os.path.basename(video_path).split(".")[0] + ".xlsx")
    df.to_excel(output_filename, index=False)

    cap.release()

    print(f"\nRed area results saved to {output_filename}")


video = input("video name: ")

trim(video, 60)
crop(video)
anz(video, 0.5, [0, 0, 100], [100, 100, 255])
print("Finished")
