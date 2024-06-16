import cv2
from kafka import KafkaProducer, KafkaConsumer

def send_video_to_kafka(video_path, kafka_topic, bootstrap_servers='localhost:9092'):
    
    producer = KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        # value_serializer=lambda v: json.dumps(v).encode('utf-8')
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
        producer.send(kafka_topic, value=buffer.tobytes())
        # frame_id += 1

    cap.release()
    producer.flush()
    producer.close()

def create_video_from_kafka(kafka_topic, video_path, frame_width, frame_height, fps, bootstrap_servers='localhost:9092'):
    
    consumer = KafkaConsumer(
        kafka_topic,
        bootstrap_servers=bootstrap_servers,
        # value_deserializer=lambda v: json.loads(v.decode('utf-8'))
    )

    fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
    out = cv2.VideoWriter(video_path, fourcc, fps, (frame_width, frame_height))

    for message in consumer:
        frame_data = message.value
        frame_id = frame_data['frame_id']
        
        # image_hex = frame_data['frame']
        # image_bytes = bytes.fromhex(image_hex)

        image = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)

        out.write(image)
        # print(f"Processed frame {frame_id}")

    out.release()

