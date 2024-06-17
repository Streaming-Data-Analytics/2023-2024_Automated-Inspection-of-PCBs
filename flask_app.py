from flask import Flask, Response, render_template
import cv2
import numpy as np
from kafka import KafkaConsumer

app = Flask(__name__)

consumer = KafkaConsumer(
    'processed_frames',
    bootstrap_servers='localhost:9092',
    # value_deserializer=lambda x: np.frombuffer(x, dtype=np.uint8)
)

@app.route('/')
def index():
    return render_template('index.html')

def get_frame():
    for message in consumer:
        frame_bytes = message.value
        frame = np.frombuffer(frame_bytes, dtype=np.uint8)
        frame = frame.reshape((550, 440, 3))

        if frame is not None:
            frame_jpeg = cv2.imencode('.jpg', frame)[1].tobytes()

            yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame_jpeg + b'\r\n\r\n')
        else:
            print("Error decoding frame")

@app.route('/video_feed')
def video_feed():
    return Response(get_frame(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True)
