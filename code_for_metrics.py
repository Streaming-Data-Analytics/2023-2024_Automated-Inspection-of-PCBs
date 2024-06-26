!pip install roboflow
!pip install opencv-python
!pip install inference
!pip install supervision

import os
from collections import defaultdict, deque
import cv2
import numpy as np
from roboflow import Roboflow
from inference.models.utils import get_roboflow_model
import supervision as sv
import pandas as pd

'''
# Questa parte va runnata se si introduce la prospettiva

class ViewTransformer:
    def __init__(self, source: np.ndarray, target: np.ndarray) -> None:
        source = source.astype(np.float32)
        target = target.astype(np.float32)
        self.m = cv2.getPerspectiveTransform(source, target)

    def transform_points(self, points: np.ndarray) -> np.ndarray:
        if points.size == 0:
            return points

        reshaped_points = points.reshape(-1, 1, 2).astype(np.float32)
        transformed_points = cv2.perspectiveTransform(reshaped_points, self.m)
        return transformed_points.reshape(-1, 2)
'''

# Qua lasciamo la possibiità di passare da terminale key, model, paths e thresholds (non funziona da colab e jupyter però)

import argparse

def parse_arguments(args = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PCB defects"
    )
    parser.add_argument(
        "--model_id",
        default="pcb-defects/2",
        help="Roboflow model ID",
        type=str,
    )
    parser.add_argument(
        "--roboflow_api_key",
        required=True,
        help="Roboflow API KEY",
        type=str,
    )
    parser.add_argument(
        "--source_video_path",
        required=True,
        help="Path to the source video file",
        type=str,
    )
    parser.add_argument(
        "--target_video_path",
        required=True,
        help="Path to the target video file (output)",
        type=str,
    )
    parser.add_argument(
        "--confidence_threshold",
        default=0.3,
        help="Confidence threshold for the model",
        type=float,
    )
    parser.add_argument(
        "--iou_threshold",
        default=0.7,
        help="IOU threshold for the model",
        type=float
    )

    return parser.parse_args()

# Salvo le prediction x in un dict:
x_hashmap = {}

def store_x(tracker_id: int, x: float):
    if tracker_id not in x_hashmap:
        x_hashmap[tracker_id] = []
    x_hashmap[tracker_id].append(x)

y_hashmap = {}

def store_y(tracker_id: int, y: float):
    if tracker_id not in y_hashmap:
        y_hashmap[tracker_id] = []
    y_hashmap[tracker_id].append(y)

s_list = []

def store_s(s: float):
    s_list.append(s)

if __name__ == "__main__":

    # args = parse_arguments()
    # api_key = args.roboflow_api_key
    api_key = "Esa6AwYGxOgMqLvAAAWG"
    api_key = os.environ.get("ROBOFLOW_API_KEY", api_key)
    if api_key is None:
        raise ValueError(
            "Roboflow API key is missing. Please provide it as an argument or set the "
            "ROBOFLOW_API_KEY environment variable."
        )
    # args.roboflow_api_key = api_key
    # video_info = sv.VideoInfo.from_video_path(video_path=args.source_video_path)
    # model = get_roboflow_model(model_id=args.model_id, api_key=args.roboflow_api_key)

    video_info = sv.VideoInfo.from_video_path(video_path="input_video.mp4")
    model = get_roboflow_model(model_id="pcb-defects/2", api_key="Esa6AwYGxOgMqLvAAAWG")

    #byte_track = sv.ByteTrack(
    #    frame_rate=video_info.fps, track_thresh=args.confidence_threshold
    #)
    byte_track = sv.ByteTrack(
        frame_rate=video_info.fps, track_activation_threshold=0.25
    )

    thickness = sv.calculate_optimal_line_thickness(
        resolution_wh=video_info.resolution_wh
    )
    text_scale = sv.calculate_optimal_text_scale(resolution_wh=video_info.resolution_wh)
    bounding_box_annotator = sv.BoundingBoxAnnotator(thickness=thickness)
    label_annotator = sv.LabelAnnotator(
        text_scale=text_scale,
        text_thickness=thickness,
        text_position=sv.Position.BOTTOM_CENTER,
    )
    trace_annotator = sv.TraceAnnotator(
        thickness=thickness,
        trace_length=video_info.fps * 2,
        position=sv.Position.BOTTOM_CENTER,
    )

    # frame_generator = sv.get_video_frames_generator(source_path=args.source_video_path)
    frame_generator = sv.get_video_frames_generator(source_path="input_video.mp4")

    # qua commento perchè non serve la prospettiva
    # polygon_zone = sv.PolygonZone(polygon=SOURCE)
    # view_transformer = ViewTransformer(source=SOURCE, target=TARGET)

    # uso una hash map + deque
    coordinates = defaultdict(lambda: deque(maxlen=video_info.fps))

    # with sv.VideoSink(args.target_video_path, video_info) as sink:
    with sv.VideoSink("output.mp4", video_info) as sink:
        for frame in frame_generator:
            results = model.infer(frame)[0]
            detections = sv.Detections.from_inference(results)
            detections = detections[detections.confidence > 0.5]
            # detections = detections[polygon_zone.trigger(detections)]
            detections = detections.with_nms(threshold=0.3)
            detections = byte_track.update_with_detections(detections=detections)

            points = detections.get_anchors_coordinates(
                anchor=sv.Position.BOTTOM_CENTER
            )
            # points = view_transformer.transform_points(points=points).astype(int)

            for tracker_id, [x, y] in zip(detections.tracker_id, points):
                coordinates[tracker_id].append(y)
                store_x(tracker_id,x)
                store_y(tracker_id,y)


            for tracker_id in detections.tracker_id:
                if len(coordinates[tracker_id]) >= video_info.fps / 2:
                    coordinate_start = coordinates[tracker_id][-1]
                    coordinate_end = coordinates[tracker_id][0]
                    distance = abs(coordinate_start - coordinate_end)
                    time = len(coordinates[tracker_id]) / video_info.fps
                    speed = distance / time
                    store_s(speed)

            annotated_frame = frame.copy()

            annotated_frame = trace_annotator.annotate(
                scene=annotated_frame, detections=detections
            )
            annotated_frame = bounding_box_annotator.annotate(
                scene=annotated_frame, detections=detections
            )

            sink.write_frame(annotated_frame)

x_new = {}
for k in x_hashmap.keys():
  if len(x_hashmap[k]) > 10:
    x_new[k] = x_hashmap[k]

from matplotlib import pyplot as plt
import seaborn as sns
from seaborn import objects as so

res = [ x-np.median(x_new[k]) for k in x_new.keys() for x in x_new[k] ]
so.Plot(res).add(so.Bar(), so.Hist())

estimated_speed = np.mean(s_list)
estimated_delta_y = np.round(estimated_speed / video_info.fps)

y_new = {}
for k in y_hashmap.keys():
  if len(y_hashmap[k]) > 10:
    y_new[k] = (pd.Series(y_hashmap[k]).diff().dropna()).tolist()

err = estimated_delta_y + [ y for k in y_new.keys() for y in y_new[k] ]
