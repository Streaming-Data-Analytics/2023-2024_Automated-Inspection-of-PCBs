# Automated Inspection of PCBs for Component Compliance and Defect Detection

Optional project of the [Streaming Data Analytics](http://emanueledellavalle.org/teaching/streaming-data-analytics-2023-24/) course provided by [Politecnico di Milano](https://www11.ceda.polimi.it/schedaincarico/schedaincarico/controller/scheda_pubblica/SchedaPublic.do?&evn_default=evento&c_classe=811164&polij_device_category=DESKTOP&__pj0=0&__pj1=d563c55e73c3035baf5b0bab2dda086b).

Student: **[To be assigned]**

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

## Note for Students

* Clone the created repository offline;
* Add your name and surname into the Readme file;
* Make any changes to your repository, according to the specific assignment;
* Add a `requirement.txt` file for code reproducibility and instructions on how to replicate the results;
* Commit your changes to your local repository;
* Push your changes to your online repository.
