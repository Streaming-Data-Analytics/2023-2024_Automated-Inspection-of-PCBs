import faust
import numpy as np
import cv2
from process_video import detect_defects
from roboflow import Roboflow
import asyncio

KAFKA_BROKER = 'kafka://localhost:9092'
INPUT_TOPIC = 'raw_frames'
OUTPUT_TOPIC = 'processed_frames'

app = faust.App('pcb-defect-detection', broker=KAFKA_BROKER, value_serializer='raw')    # app name: pcb-defect-detection

input_topic = app.topic(INPUT_TOPIC, value_type=bytes)
output_topic = app.topic(OUTPUT_TOPIC, value_type=bytes)

# CONSUMER PART
@app.agent(input_topic) # decorator to define async stream processor (faust works in asynchronous manner)
async def process(frames): # frames is the stream: infinite async iterable, consuming messages from a topic/channel
    # consuming the data from the input stream:
    print('Faust started')

    async for frame in frames: # we can think of this as data continuously appended in an unbounded table
    
        frame = np.frombuffer(frame, dtype=np.uint8)
        frame = frame.reshape((440, 550, 3))
        
        # processing the input frame:
        processed_image = await detect_defects_async(frame)

        # _, buffer = cv2.imencode('.jpg', processed_image)
        # processed_frame = Frame(frame_id=frame.frame_id, frame=buffer.tobytes().hex())

        # PRODUCER PART
        # publishing the processed frame in the ouput topic
        await output_topic.send(value=processed_image.tobytes())

async def detect_defects_async(frame):
    await asyncio.sleep(3)  
    return detect_defects(frame)

if __name__ == '__main__':
    app.main()