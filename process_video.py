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
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import numpy as np

KAFKA_BROKER = 'kafka://localhost:9092'
INPUT_TOPIC = 'raw_frames'
OUTPUT_TOPIC = 'processed_frames'
GROUP_ID = 'pcb_defect_group'

app = faust.App('pcb-defect-detection', broker=KAFKA_BROKER, value_serializer='raw')
input_topic = app.topic(INPUT_TOPIC, value_type=bytes)
output_topic = app.topic(OUTPUT_TOPIC, value_type=bytes)

rf = Roboflow(api_key="Esa6AwYGxOgMqLvAAAWG")
project = rf.workspace().project("pcb-defects")
model = project.version(2).model

class Frame(faust.Record):
    frame_id: int
    image: bytes

@app.agent(input_topic)
async def process(frames):
    async for frame in frames:
        image = np.frombuffer(frame, dtype=np.uint8).reshape(height, width, 3)
        processed_image = detect_defects(image)
        # processed_frame = Frame(frame_id=frame.frame_id, image=processed_image.tobytes())
        await output_topic.send(value=processed_image.tobytes())

threshold = 30
not_found = np.nan
confidence_threshold = 0.7

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

# uso una queue per salvare le prev detections (ottimizzata per quello che ci devo fare)
from collections import deque
# K is the number of old frames we keep track of
k = 5
prev = deque()

# questa la predict "base" per avere tutto più compatto
def predict(frame):
  return model.predict(frame).json()['predictions']

# loop sul primo indice dei matches:
#   if is not None: hai la prediction, hai la mappa. x_new = (x(i) + prev_i)/2
# questa function deve resistuirmi le prediction

# find closest mappa il bb nella prediction vecchia con quella nuova
# mappa con a sx la prediction vecchia e a dx la prediction nuova (se c'è)
# scorriamo l'indice a dx (sulle pred nuove) e matchi tra vecchia e nuova pred
# hash map che collega quello che serve (dict)
# ora scorriamo le nuove predicition e ognuna la aggreghiamo all'altra: la nuova prediction
# idealmente va aggregata -> abbiamo la media tra nuova e vecchia
# dopo di questo sull'asse y la nuova prediction sarà la composizione della pred
# fatta dal modello y(i) e sulla parte destra ci sarà la stima fatta con l'altro frame
# y_pred(i) + w*t dove w è la velocità stimata e t = 1/fps.
# t lo abbiamo perché è costante (è come scorre)
# possiamo stimare la variazione wt = Delta y
# facciamo la media tra la predizione e il deltay stimato sui due istanti precedenti
# variabile global deltay aggiornata ogni volta scorrendo a t-1
# questo dà le coordinate (x,y) predette dal modello

# serve mettere un po' di if (tipo alla prima prediction non puoi stimare la velocità)
# fatto questo avrò le prediction

# prendo il frame, faccio i magheggi per trovare x0,x1,y0,y1
#     x0 = int(prediction['x'] - prediction['width'] / 2)
#     x1 = int(prediction['x'] + prediction['width'] / 2)
#     y0 = int(prediction['y'] - prediction['height'] / 2)
#     y1 = int(prediction['y'] + prediction['height'] / 2)
# ritornare il frame

# riaggiorno la parte AR: ristimare i parametri
# cambia deltay e salvare il frame appena predetto come previous_frame

# forse: invece di considerare il frame precedente ne considero due precedenti

v = 1 # da inizializzare a un valore sensato

def detect_defects(image):
    # Dummy implementation of defect detection
    # Replace this with actual defect detection logic
    processed_image = image.copy()
    cv2.rectangle(processed_image, (50, 50), (100, 100), (0, 255, 0), 2)
    return processed_image

# qui va capito come unire il tutto 
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
          cur = predict(frame)
          m = find_closest(cur,prev)
          for i in len(m):
            # ricorda che m è un hash map tra gli indici di cur e prev
            if v and m[i] != not_found and prev[i].confience >= confidence_threshold:
              x = 1/(k+1)*(cur[i]['x']+prev[m[i]]['x'])
              # qua lo sbatti è che dovrei fare il return_closest k volte, da provare (per ora cosi ha senso solo per k = 1)
              y = 1/2*(cur[i]['y']+prev[m[i]]['x'] + v / fps)
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

            v.update(cur)
            prev.popleft()
            prev.append(cur)

          processed_frames_topic.send(value = frame)
          output_video.write(frame)

        else:
            break

    cap.release()

def extract_frames(video_path):
    cap = cv2.VideoCapture(video_path)
    frames = []
    frame_id = 0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frames.append((frame_id, frame, width, height))
        frame_id += 1
    cap.release()
    return frames, width, height

def save_video(frames, output_path, fps, width, height):
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    for _, frame in frames:
        out.write(frame)
    out.release()

def send_frames_to_kafka(frames):
    producer = KafkaProducer(bootstrap_servers=KAFKA_BROKER)
    for frame_id, frame, width, height in frames:
        producer.send(INPUT_TOPIC, value=frame)
    producer.flush()
    producer.close()


@app.agent(output_topic)
async def process_output(frames):
    received_frames = []
    async for frame in frames:
        received_frames.append(frame)
        if len(received_frames) == frame_count:
            break
    return received_frames

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process a video for PCB defect detection.')
    parser.add_argument('--input', type=str, required=True, help='Path to the input video file.')
    parser.add_argument('--output', type=str, required=True, help='Path to the output video file.')
    args = parser.parse_args()

    print("Extracting frames from input video...")
    frames, width, height = extract_frames(args.input)
    frame_count = len(frames)
    print(f"Extracted {frame_count} frames with width={width} and height={height}.")

    print("Starting Faust application...")
    app.main()

    processed_frames = app.agents.process_output().get_sync()

    print("Saving processed frames to output video...")
    save_video(processed_frames, args.output, fps=30, width=width, height=height)

    print(f"Output video saved to {args.output}")