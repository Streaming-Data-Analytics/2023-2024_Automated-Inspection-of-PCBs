from collections import defaultdict, deque
import os
from collections import defaultdict, deque
import cv2
import numpy as np
from roboflow import Roboflow
from inference.models.utils import get_roboflow_model
import supervision as sv

'''
# Questa parte va runnata se introduciamo la prospettiva

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
# import argparse

# def parse_arguments(args = None) -> argparse.Namespace:
#     parser = argparse.ArgumentParser(
#         description="PCB defects"
#     )
#     parser.add_argument(
#         "--model_id",
#         default="pcb-defects/2",
#         help="Roboflow model ID",
#         type=str,
#     )
#     parser.add_argument(
#         "--roboflow_api_key",
#         required=True,
#         help="Roboflow API KEY",
#         type=str,
#     )
#     parser.add_argument(
#         "--source_video_path",
#         required=True,
#         help="Path to the source video file",
#         type=str,
#     )
#     parser.add_argument(
#         "--target_video_path",
#         required=True,
#         help="Path to the target video file (output)",
#         type=str,
#     )
#     parser.add_argument(
#         "--confidence_threshold",
#         default=0.3,
#         help="Confidence threshold for the model",
#         type=float,
#     )
#     parser.add_argument(
#         "--iou_threshold",
#         default=0.7,
#         help="IOU threshold for the model",
#         type=float
#     )

#     return parser.parse_args()

# Salvo le prediction x in un dict:
x_hashmap = {}

def store_x(tracker_id: int, x: float):
    if tracker_id not in x_hashmap:
        x_hashmap[tracker_id] = []
    x_hashmap[tracker_id].append(x)

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

# def predict(frame): # questa la predict "base" per avere tutto più compatto
#   return model.predict(frame).json()['predictions']

class Info:
    def __init__(self, video_info):
        
        self.fps = video_info.fps
        self.byte_track = sv.ByteTrack(frame_rate=self.fps, track_activation_threshold=0.25)
        self.thickness = sv.calculate_optimal_line_thickness(resolution_wh=video_info.resolution_wh)
        self.text_scale = sv.calculate_optimal_text_scale(resolution_wh=video_info.resolution_wh)
        self.bounding_box_annotator = sv.BoundingBoxAnnotator(thickness=self.thickness)
        self.label_annotator = sv.LabelAnnotator(
            text_scale=self.text_scale,
            text_thickness=self.thickness,
            text_position=sv.Position.BOTTOM_CENTER,
        )
        self.trace_annotator = sv.TraceAnnotator(
            thickness=self.thickness,
            trace_length=video_info.fps * 2,
            position=sv.Position.BOTTOM_CENTER,
        )
        self.coordinates = defaultdict(lambda: deque(maxlen=video_info.fps))


def detect_defects(frame):

    # MODEL
    # rf = Roboflow(api_key="Esa6AwYGxOgMqLvAAAWG")
    # project = rf.workspace().project("pcb-defects")
    # model = project.version(2).model
    model = get_roboflow_model(model_id="pcb-defects/2", api_key="Esa6AwYGxOgMqLvAAAWG")


    info = Info(video_info = sv.VideoInfo.from_video_path(video_path='input_video.mp4'))

    results = model.infer(frame)[0]
    detections = sv.Detections.from_inference(results)
    detections = detections[detections.confidence > 0.5]
    
    detections = detections.with_nms(threshold=0.3)
    detections = info.byte_track.update_with_detections(detections=detections)

    points = detections.get_anchors_coordinates(
        anchor=sv.Position.BOTTOM_CENTER
    )
    
    for tracker_id, [x, y] in zip(detections.tracker_id, points):
        coordinates[tracker_id].append(y)
        # qua aggiungo la x per poi calcolare errore!
        store_x(tracker_id,x)
    labels = []


    '''
    # qua potrei addirittura calcolare la velocità, ma non ci interessa
    for tracker_id in detections.tracker_id:
        if len(coordinates[tracker_id]) < video_info.fps / 2:
            labels.append(f"#{tracker_id}")
        else:
            coordinate_start = coordinates[tracker_id][-1]
            coordinate_end = coordinates[tracker_id][0]
            distance = abs(coordinate_start - coordinate_end)
            time = len(coordinates[tracker_id]) / video_info.fps
            speed = distance / time * 3.6
            labels.append(f"#{tracker_id} {int(speed)} km/h")
            '''

    annotated_frame = frame.copy()

    annotated_frame = info.trace_annotator.annotate(
        scene=annotated_frame, detections=detections
    )
    annotated_frame = info.bounding_box_annotator.annotate(
        scene=annotated_frame, detections=detections
    )
    '''
    annotated_frame = label_annotator.annotate(
        scene=annotated_frame, detections=detections, labels=labels
    )'''

    return annotated_frame
