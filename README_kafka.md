## Start Kafka
* Start ZooKeeper:

```bash
cd kafka_2.13-3.7.0 
bin/zookeeper-server-start.sh config/zookeeper.properties
```

* Start Kafka server in another terminal:
```bash
cd kafka_2.13-3.7.0 
bin/kafka-server-start.sh config/server.properties
```




## Faust and dependencies 
To install Faust and all the needed dependencies run this code:

`pip install faust`

`pip install opencv-python-headless`

`pip install robinhood-aiokafka`

Check if Faust is installed correctly:

`faust --version`

If it doesn't work you can also try to execute through python:

`python -m faust --version`

Start Zookeper by running this command in the Kafka directory:

`bin/zookeeper-server-start.sh config/zookeeper.properties`

Start Kafka by running this command in the Kafka directory:

`bin/kafka-server-start.sh config/server.properties`

Create Kafka topics (in the Kafka directory):

`bin/kafka-topics.sh --create --topic raw_frames --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1`

`bin/kafka-topics.sh --create --topic processed_frames --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1`

Check that all the versions are compatible:

`pip install --upgrade mode faust asyncio`

Run the script:

`python -m faust -A code_sda worker -l info`
