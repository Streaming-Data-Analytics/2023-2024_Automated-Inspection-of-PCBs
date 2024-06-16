# Automated Inspection of PCBs for Component Compliance and Defect Detection

Optional project of the [Streaming Data Analytics](http://emanueledellavalle.org/teaching/streaming-data-analytics-2023-24/) course provided by [Politecnico di Milano](https://www11.ceda.polimi.it/schedaincarico/schedaincarico/controller/scheda_pubblica/SchedaPublic.do?&evn_default=evento&c_classe=811164&polij_device_category=DESKTOP&__pj0=0&__pj1=d563c55e73c3035baf5b0bab2dda086b).

Student: **Ortolani Giulia & Venanzi Alessandro**

## Overview

This project focuses on leveraging image processing techniques and event-driven systems to automate the inspection of Printed Circuit Boards (PCBs) for quality control in manufacturing processes. By analyzing images of PCBs, the system aims to verify the condition of electronic components according to design specifications.

**Components of the solution**:
- Component and Defect Detection Strategies: implementing, using transfer learning from YOLO or other pre-trained Neural Networks, an advanced computer vision solution to identify and verify the presence of each component on the PCB and assess its condition (identifying defects if present).
- Stream Processing Component: Leveraging a Stream Processor (SP) to aggregate detection events, ensuring each component's compliance with the PCB design and reporting defects.

The project will utilize AI frameworks such as Edge Impulse or Roboflow, python libraries, and a stream processor among those illustrated in the course. The project aims to create a highly accurate and efficient system for PCB inspection, reducing the need for manual quality control measures.

**Evaluation Metrics**: \
The project's success will be measured against several key metrics:
- Accuracy and precision in component detection.
- Effectiveness in identifying defective components.
- Throughput and latency in event processing and aggregation.

**Dataset**: \
The system will be tested in controlled scenarios using imagery of PCB obtained [here](https://universe.roboflow.com/uni-4sdfm/pcb-defects).

The expected result is a dockerized application that demos the complete pipeline and analyzes the solution performance against the evaluation metrics. The project will conclude with a detailed discussion of the outcomes, emphasizing the system's potential to revolutionize PCB quality control through automation and precision.

<!-- ## Note for Students

* Clone the created repository offline;
* Add your name and surname into the Readme file;
* Make any changes to your repository, according to the specific assignment;
* Add a `requirement.txt` file for code reproducibility and instructions on how to replicate the results;
* Commit your changes to your local repository;
* Push your changes to your online repository. -->


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
   Here, `-A` stands for Application. So, we want to start the `process_video` application of Faust.
   `-l info` means that I want to print all the logs that are generated.

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

* To list Kafka topics use:
    ```sh
    bin/kafka-topics.sh --list --bootstrap-server localhost:9092 
    ```

### Work environment

* To check that all the versions are compatible:
    ```sh
    pip install --upgrade mode faust asyncio
    ```
