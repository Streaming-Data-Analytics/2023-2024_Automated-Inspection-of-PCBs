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




def iou(box1, box2):
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

    # Calculate the coordinates of the intersection rectangle
    inter_x_min = max(x1_min, x2_min)
    inter_y_min = max(y1_min, y2_min)
    inter_x_max = min(x1_max, x2_max)
    inter_y_max = min(y1_max, y2_max)

    # And compute the area of intersection rectangle
    intersection_area = max(0, inter_x_max - inter_x_min) * max(0, inter_y_max - inter_y_min)

    # Compute the area of both the prediction and the ground-truth rectangles
    box1_area = box1['width'] * box1['height']
    box2_area = box2['width'] * box2['height']

    iou = intersection_area / float(box1_area + box2_area - inter_area)
    return iou




import numpy as np
# Parameters
threshold = 10          # Max horizontal distance to consider the matches
not_found = np.nan      # This means no match

# Pred2 è model.predict, pred1 è pred vecchia
def find_closest(pred1, pred2):
    """
    Match bounding boxes from pred1 to pred2 using IoU metric.
    """
    matches = {}
    for i, box1 in enumerate(pred1):
        best_match = None
        best_iou = 0
        for j, box2 in enumerate(pred2):
          if abs(box1['x']-box2['x']) <= threshold
            iou = calculate_iou(box1, box2)
            if iou > best_iou:
                best_iou = iou
                best_match = j
        if best_match is not None:
            matches[i] = not_found
    return matches




# Lista per tenere traccia delle previous k annotated detections
prev_detections = []

@app.agent(raw_frames_topic)
async def process_frames(frames):
    async for frame in frames:
        processed_frame = detect_defects(frame)
        await processed_frames_topic.send(value=processed_frame)

color_map = {
    0: (155, 95, 224),
    1: (22, 164, 216),
    2: (96, 219, 232),
    3: (139, 211, 70),
    4: (239, 223, 72),
    5: (249, 165, 44),
    6: (214, 78, 18)
}


def detect_defects(frame):

    global prev_detections # mi servono le prev_detections per togliere il blur

    resized_frame = cv2.resize(frame, (1920, 1080))

    predictions = model.predict(resized_frame).json()['predictions']

    for prediction in predictions:

      # confidence va returnata per il type dict
        class_id = prediction['class_id']
        x0 = int(prediction['x'] - prediction['width'] / 2)
        x1 = int(prediction['x'] + prediction['width'] / 2)
        y0 = int(prediction['y'] - prediction['height'] / 2)
        y1 = int(prediction['y'] + prediction['height'] / 2)
        color = color_map.get(class_id, (255, 255, 255))
        cv2.rectangle(frame, (x0, y0), (x1, y1), color, 4)

    return frame




video_path = '/content/gdrive/MyDrive/videos_to_infer/SDA_60fps.mp4'
cap = cv2.VideoCapture('SDA_60fps.mp4')

if not cap.isOpened():
    print("Error: Unable to open video file.")
    exit()

fps = cap.get(cv2.CAP_PROP_FPS)
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))



fourcc = cv2.VideoWriter_fourcc(*'mp4v')
output_video = cv2.VideoWriter('processed_video.mp4', fourcc, fps, (frame_width, frame_height))

fps = int(cap.get(cv2.CAP_PROP_FPS))

while cap.isOpened():

    ret, frame = cap.read()

    if ret:

        processed_frame = detect_defects(frame)

        processed_frames_topic.send(value=processed_frame)
        # cv2_imshow( processed_frame)

        output_video.write(processed_frame)

    else:
      break

cap.release()
output_video.release()

print("Video processing complete. Processed video saved as 'processed_video.mp4'.")