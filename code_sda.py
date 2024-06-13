# !pip3 install roboflow
# !pip install faust
# !pip install opencv-python
# pip install faust
# pip install opencv-python-headless
# pip install aiokafka
# pip install pipreqs

# generate requirements: python3 -m pip freeze > requirements.txt

from roboflow import Roboflow
import cv2
import numpy as np
import faust
from faust import App
import time

app = App('defect-detection', broker='kafka://localhost')

raw_frames_topic = app.topic('raw_frames')
processed_frames_topic = app.topic('processed_frames')

rf = Roboflow(api_key="Esa6AwYGxOgMqLvAAAWG")
project = rf.workspace().project("pcb-defects")
model = project.version(2).model

# Lista per tenere traccia delle previous k annotated detections
prev_detections = []
threshold = 30
not_found = np.nan

# @app.agent(raw_frames_topic)
# async def process_frames(frames):
#     async for frame in frames:
#         processed_frame = detect_defects(frame)
#         await processed_frames_topic.send(value=processed_frame)

@app.agent(raw_frames_topic)
async def process_frames(frames):
    async for frame_bytes in frames:
        frame = np.frombuffer(frame_bytes, dtype=np.uint8)
        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
        processed_frame = detect_defects(frame)
        _, buffer = cv2.imencode('.jpg', processed_frame)
        await processed_frames_topic.send(value=buffer.tobytes())

color_map = {
    0: (155, 95, 224),
    1: (22, 164, 216),
    2: (96, 219, 232),
    3: (139, 211, 70),
    4: (239, 223, 72),
    5: (249, 165, 44),
    6: (214, 78, 18)
}

def calculate_iou(box1, box2):
    """
    Calculate the Intersection over Union (IoU) of two bounding boxes.
    Each box is represented by a dictionary with keys: x, y, width, height.
    """

    x1_min = box1['x'] - box1['width'] / 2
    y1_min = box1['y'] - box1['height'] / 2
    x1_max = box1['x'] + box1['width'] / 2
    y1_max = box1['y'] + box1['height'] / 2

    x2_min = box2['x'] - box2['width'] / 2
    y2_min = box2['y'] - box2['height'] / 2
    x2_max = box2['x'] + box2['width'] / 2
    y2_max = box2['y'] + box2['height'] / 2

    inter_x_min = max(x1_min, x2_min)
    inter_y_min = max(y1_min, y2_min)
    inter_x_max = min(x1_max, x2_max)
    inter_y_max = min(y1_max, y2_max)

    intersection_area = max(0, inter_x_max - inter_x_min) * max(0, inter_y_max - inter_y_min)

    box1_area = box1['width'] * box1['height']
    box2_area = box2['width'] * box2['height']

    iou = intersection_area / float(box1_area + box2_area - intersection_area)
    return iou

def find_closest(pred1, pred2): # Pred2 è model.predict, pred1 è pred vecchia
    """
    Match bounding boxes from pred1 to pred2 using IoU metric.
    """
    matches = {}
    for i, box1 in enumerate(pred1):
        best_match = None
        best_iou = 0
        for j, box2 in enumerate(pred2):
          if abs(box1['x']-box2['x']) <= threshold:
            iou = calculate_iou(box1, box2)
            if iou > best_iou:
                best_iou = iou
                best_match = j
        if best_match is None: 
            matches[i] = not_found

    return matches

def detect_defects(frame, prev_detections):
    predictions = model.predict(frame).json()['predictions']

    for prediction in predictions:
        class_id = prediction['class_id']
        x0 = int(prediction['x'] - prediction['width'] / 2)
        x1 = int(prediction['x'] + prediction['width'] / 2)
        y0 = int(prediction['y'] - prediction['height'] / 2)
        y1 = int(prediction['y'] + prediction['height'] / 2)
        color = color_map.get(class_id, (255, 255, 255))
        cv2.rectangle(frame, (x0, y0), (x1, y1), color, 4)
    
    return frame, prev_detections



async def main():  #  read video and send frames to raw_frames_topic
    video_path = 'SDA_60fps.mp4'
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("Error: Unable to open video file.")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    output_video = cv2.VideoWriter('processed_video.mp4', fourcc, fps, (frame_width, frame_height))

    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            _, buffer = cv2.imencode('.jpg', frame)
            await raw_frames_topic.send(value=buffer.tobytes())
        else:
            break

    cap.release()

@app.agent(processed_frames_topic) # write processed frames to video file
async def write_processed_frames(frames):
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    output_video = cv2.VideoWriter('processed_video.mp4', fourcc, 60.0, (640, 480))

    async for frame_bytes in frames:
        frame = np.frombuffer(frame_bytes, dtype=np.uint8)
        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
        output_video.write(frame)

    output_video.release()
    print("Video processing complete. Processed video saved as 'processed_video.mp4'.")

if __name__ == '__main__':
    app.main()