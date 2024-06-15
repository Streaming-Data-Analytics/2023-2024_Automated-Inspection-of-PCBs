# pip install opencv-python numpy
# pip install cv2
# pip install os

import cv2
import os
import numpy as np

image_folder = 'images'
images = [img for img in os.listdir(image_folder) if img.endswith(".png") or img.endswith(".jpg")]

images.sort()

def create_sliding_frames(images, image_folder, frame_width, frame_height, slide_speed, band_height):
    frames = []
    total_height = len(images) * (frame_height + band_height) - band_height

    # Create a blank canvas large enough to hold all images stacked vertically with bands
    canvas = np.zeros((total_height, frame_width, 3), dtype=np.uint8)

    # Place each image on the canvas with a black band between each
    for idx, image_name in enumerate(images):
        image_path = os.path.join(image_folder, image_name)
        image = cv2.imread(image_path)
        image = cv2.resize(image, (frame_width, frame_height))
        y_start = idx * (frame_height + band_height)
        y_end = y_start + frame_height
        canvas[y_start:y_end, :] = image
        if idx < len(images) - 1:
            canvas[y_end:y_end + band_height, :] = (0, 0, 0)  # Black band

    # Create sliding frames
    for shift in range(0, total_height - frame_height + 1, slide_speed):
        frame = canvas[shift:shift + frame_height, :]
        frames.append(frame)
    
    return frames

def create_video(frames, output_path, fps):
    height, width, layers = frames[0].shape
    size = (width, height)

    # Use 'mp4v' codec for MP4 format
    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, size)

    for frame in frames:
        out.write(frame)
    out.release()

# Parameters
frame_width = 440
frame_height = 550
band_height = 100  # Height of the black band between images
slide_speed = 4  # Pixels to slide per frame
fps = 30
output_path = 'input_video.mp4'

# Create frames with vertical sliding effect
frames = create_sliding_frames(images, image_folder, frame_width, frame_height, slide_speed, band_height)
# Create v
# Create video
create_video(frames, output_path, fps)

