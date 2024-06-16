# pip install kafka-python opencv-python faust

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
from utilities import send_video_to_kafka, create_video_from_kafka
from faust_app import app
from process_video import detect_defects

KAFKA_BROKER = 'kafka://localhost:9092'
INPUT_TOPIC = 'raw_frames'
OUTPUT_TOPIC = 'processed_frames'
# GROUP_ID = 'pcb_defect_group'

# input_topic = app.topic(INPUT_TOPIC, value_type=bytes)
# output_topic = app.topic(OUTPUT_TOPIC, value_type=bytes)

# MODEL
rf = Roboflow(api_key="Esa6AwYGxOgMqLvAAAWG")
project = rf.workspace().project("pcb-defects")
model = project.version(2).model

threshold = 30
not_found = np.nan
confidence_threshold = 0.7

k = 5       # k is the number of old frames we keep track of
prev = []
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

if __name__ == '__main__':

    # this is a demo with input video
    parser = argparse.ArgumentParser(description='Process a video for PCB defect detection.')
    parser.add_argument('--input', required=True, help='Path to the input video file.')
    parser.add_argument('--output', required=True, help='Path to the output video file.')
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
    print(f"Frames sent to Kafka")
    create_video_from_kafka(INPUT_TOPIC, args.output, frame_width=width, frame_height=height, fps=fps)
    print("Starting Faust application...")
    app.main() # Faust

    print("Faust started")

    # take the processed frames from kafka and make the output video
    create_video_from_kafka(OUTPUT_TOPIC, args.output, frame_width=width, frame_height=height, fps=fps)

    print(f"Output video saved to {args.output}")