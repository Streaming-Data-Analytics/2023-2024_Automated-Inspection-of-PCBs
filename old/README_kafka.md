# Automated Inspection of PCBs

## Overview

This project aims to detect defects in Printed Circuit Board (PCB) components by analyzing video footage. The process involves several steps, including video frame extraction, defect detection using a Python function, and reassembling the processed frames into an output video. Apache Kafka is used for managing the data stream, with Faust as the stream processing library.

## Table of Contents

- [Requirements](#requirements)
- [Architecture](#architecture)
- [Features](#feaures)
- [Installation](#installation)
- [Usage](#usage)
- [Utilities](#utilities)


## Requirements

- Python 3.7+
- Faust (`streaming-faust`)
- Kafka

The complete list of requirements is contained in `requirements.txt`.

## Architecture

1. **Video Input:** The input video is divided into individual frames.
2. **Kafka Topic (Input):** The raw frames are sent to a Kafka topic for processing.
3. **Defect Detection:** Each frame is processed using a Python function to detect defects and generate bounding boxes for missing parts.
4. **Kafka Topic (Output):** The processed frames with defect annotations are sent to another Kafka topic.
5. **Video Output:** The processed frames are reassembled into a final output video.

The processing pipeline utilizes Apache Kafka for message streaming and Faust for stream processing. The project is designed to handle high-throughput video streams efficiently.

## Features

   * Frame-by-Frame Processing: The video is processed one frame at a time to ensure accurate defect detection.
   * Bounding Box Detection: The system highlights missing or defective components with bounding boxes.
   * Kafka Integration: Uses Kafka topics to manage the input and output video frames.
   * Faust Stream Processing: Leverages Faust to process video frames in real-time.
   * Output Video Generation: Combines processed frames into a final output video.


## Installation

### Kafka Setup

1. Download and install Kafka from [Kafka Downloads](https://kafka.apache.org/downloads).


### Python Dependencies

1. Clone the repository:
   ```sh
   git clone git@github.com:Streaming-Data-Analytics/2023-2024_Automated-Inspection-of-PCBs.git
   ```

2. Install the required Python packages:
   ```sh
   pip install -r requirements.txt
   ```


## Usage

### Running the Application

1. **Start Kafka:**
   In the Kafka directory, open a new terminal and start Zookeper:
   ```sh
   bin/zookeeper-server-start.sh config/zookeeper.properties
   ```
   In the Kafka directory, open a new terminal and start Kafka:
   ```sh
   bin/kafka-server-start.sh config/server.properties
   ```

2. **Create Topics:**
In the Kafka directory, open a new terminal and create two topics:
    ```sh
    bin/kafka-topics.sh --create --topic raw_frames --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
    bin/kafka-topics.sh --create --topic processed_frames --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
    ```

3. **Faust Worker:**
    In the main directory, start the Faust worker to process the frames:
   ```sh
   faust -A process_video worker -l info
   ```

4. **Process Video:**
   Run the script to start processing the video:
   ```sh
   python3 process_video.py --input input_video.mp4 --output output_video.mp4
   ```

### Command-Line Options

- `--input`: Path to the input video file.
- `--output`: Path to the output video file.

<!-- ## Configuration

Modify `config.py` to adjust Kafka topics, server settings, and other parameters.

```python
KAFKA_BROKER = 'localhost:9092'
INPUT_TOPIC = 'raw_frames'
OUTPUT_TOPIC = 'processed_frames'
GROUP_ID = 'pcb_defect_group'
``` -->

## Utilities

### Faust and dependencies 
* To install Faust and all the needed dependencies run this code:
    ```sh
    pip install streaming-faust
    pip install opencv-python-headless
    pip install robinhood-aiokafka
    ```

* To check if Faust is installed correctly:
    ```sh
    faust --version
    ```

    If it doesn't work you can also try to execute through python, either via
    ```sh
    python -m faust --version
    ```
    or
    ```sh
    python3 -m faust --version
    ```

### Kafka
* Remember to start Zookeper by running this command in the Kafka directory:
    ```sh
    bin/zookeeper-server-start.sh config/zookeeper.properties
    ```

    and to start Kafka by running this command, in the Kafka directory as well:
    ```sh
    bin/kafka-server-start.sh config/server.properties
    ```

* Remember to create the Kafka topics (in the Kafka directory):
    ```sh
    bin/kafka-topics.sh --create --topic raw_frames --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

    bin/kafka-topics.sh --create --topic processed_frames --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
    ```

### Work environment

* To check that all the versions are compatible:
    ```sh
    pip install --upgrade mode faust asyncio
    ```
