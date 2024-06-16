# pip install kafka-python opencv-python faust

""" 
This script handles video frame extraction, sending frames to Kafka for 
processing, receiving processed frames, and reassembling them into an output video.
"""

from roboflow import Roboflow
import cv2
import os
import argparse
import asyncio
import faust
import json
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import numpy as np
from collections import deque # uso una queue per salvare le prev detections (ottimizzata per quello che ci devo fare)

KAFKA_BROKER = 'kafka://localhost:9092'
INPUT_TOPIC = 'raw_frames'
OUTPUT_TOPIC = 'processed_frames'
# GROUP_ID = 'pcb_defect_group'

app = faust.App('pcb-defect-detection', broker=KAFKA_BROKER, value_serializer='raw')    # app name: pcb-defect-detection
input_topic = app.topic(INPUT_TOPIC, value_type=bytes)
output_topic = app.topic(OUTPUT_TOPIC, value_type=bytes)

# MODEL
rf = Roboflow(api_key="Esa6AwYGxOgMqLvAAAWG")
project = rf.workspace().project("pcb-defects")
model = project.version(2).model

threshold = 30
not_found = np.nan
confidence_threshold = 0.7

k = 5       # k is the number of old frames we keep track of
prev = {}
# global prev = deque()

color_map = {
    0: (155, 95, 224),
    1: (22, 164, 216),
    2: (96, 219, 232),
    3: (139, 211, 70),
    4: (239, 223, 72),
    5: (249, 165, 44),
    6: (214, 78, 18)
}

# class Frame(faust.Record):
#     frame_id: int
#     frame: str

# CONSUMER PART
@app.agent(input_topic) # decorator to define async stream processor (faust works in asynchronous manner)
async def process(frames): # frames is the stream: infinite async iterable, consuming messages from a topic/channel
    # consuming the data from the input stream:
    async for frame in frames: # we can think of this as data continuously appended in an unbounded table
        
        # THIS TYPES ARE NOT CORRECT ---> WORK HERE
        print(type(frame))
        image = np.frombuffer(frame, dtype=np.uint8)
        print(type(image))
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        
        # processing the input frame:
        print(type(image))
        processed_image = detect_defects(image)
        _, buffer = cv2.imencode('.jpg', processed_image)
        processed_frame = Frame(frame_id=frame.frame_id, frame=buffer.tobytes().hex())

        # PRODUCER PART
        # publishing the processed frame in the ouput topic
        await output_topic.send(value=processed_frame)


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

def find_closest(pred1, pred2):
    """
    Match bounding boxes from pred1 to pred2 using IoU metric.
    """
    matches = {}
    for i, box1 in enumerate(pred1):
        best_match = None
        best_iou = 0
        for j, box2 in enumerate(pred2):
          if abs(box1['x']-box2['x']) <= threshold and pred1['class_id'] == pred2['class_id']:
            iou = calculate_iou(box1, box2)
            if iou > best_iou:
                best_iou = iou
                best_match = j
        if best_match is None:
            matches[i] = not_found
        else:
          matches[i] = j

    return matches

def predict(frame): # questa la predict "base" per avere tutto più compatto
  return model.predict(frame).json()['predictions']

def detect_defects(frame):
    # frame_str = json.dumps(frame.frame)
    cur = predict(frame)
    v = 1 # da inizializzare a un valore sensato
    if prev:
        m = find_closest(cur,prev)
    else:
        m = {}
    for i in range(len(m)):
        # ricorda che m è un hash map tra gli indici di cur e prev
        if v and m[i] != not_found and prev[m[i]]['confidence'] >= confidence_threshold:
            x = 1/(k+1)*(cur[i]['x']+prev[m[i]]['x'])
            # qua lo sbatti è che dovrei fare il return_closest k volte, da provare (per ora cosi ha senso solo per k = 1)
            y = 1/2*(cur[i]['y']+prev[m[i]]['x'] + v / fps) # v o v/fps?
        else:
            x = cur[i]['x']
            y = cur[i]['y']

        class_id = cur['class_id']
        x0 = int(x - cur['width'] / 2)
        x1 = int(x + cur['width'] / 2)
        y0 = int(y - cur['height'] / 2)
        y1 = int(y + cur['height'] / 2)
        color = color_map.get(class_id, (255, 255, 255))
        cv2.rectangle(frame, (x0, y0), (x1, y1), color, 4)

        # v.update(cur)

    # prev.popleft() # non va la deque bro
    prev.append(cur)
    return frame

def send_video_to_kafka(video_path, kafka_topic, bootstrap_servers='localhost:9092'):
    
    producer = KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    cap = cv2.VideoCapture(video_path)

    # frame_id = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue

        # newframe = Frame(frame_id=frame_id, frame=buffer.tobytes().hex())
        # producer.send(kafka_topic, value=newframe)
        producer.send(kafka_topic, value=buffer)
        # frame_id += 1

    cap.release()
    producer.flush()
    producer.close()

def create_video_from_kafka(kafka_topic, video_path, frame_width, frame_height, fps, bootstrap_servers='localhost:9092'):
    
    consumer = KafkaConsumer(
        kafka_topic,
        bootstrap_servers=bootstrap_servers,
        value_deserializer=lambda v: json.loads(v.decode('utf-8'))
    )

    fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
    out = cv2.VideoWriter(video_path, fourcc, fps, (frame_width, frame_height))

    for message in consumer:
        frame_data = message.value
        frame_id = frame_data['frame_id']
        
        image_hex = frame_data['frame']
        image_bytes = bytes.fromhex(image_hex)

        image = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)

        out.write(image)
        print(f"Processed frame {frame_id}")

    out.release()

if __name__ == '__main__':

    # this is a demo with input video
    parser = argparse.ArgumentParser(description='Process a video for PCB defect detection.')
    parser.add_argument('--input', type=str, required=True, help='Path to the input video file.')
    parser.add_argument('--output', type=str, required=True, help='Path to the output video file.')
    args = parser.parse_args()

    print("Extracting frames from input video...")
    
    video_path = args.input
    cap = cv2.VideoCapture(video_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.release()

    print(f"Extracted frames with width={width} and height={height} at fps={fps}.")

    # send to kafka the frames from the raw video
    send_video_to_kafka(args.input, INPUT_TOPIC)

    print("Starting Faust application...")
    app.main() # Faust

    # take the processed frames from kafka and make the output video
    create_video_from_kafka(OUTPUT_TOPIC, args.output, frame_width=width, frame_height=height, fps=fps)

    print(f"Output video saved to {args.output}")