import producer_server


def run_kafka_server():
    
    input_file = "/home/workspace/police-department-calls-for-service.json"

    # TODO fill in blanks
    producer = producer_server.ProducerServer(
        input_file=input_file,
        topic="crime.police-event",
        bootstrap_servers="localhost:9092",
        client_id="crime.broker"
    )

    return producer


def feed():
    producer = run_kafka_server()
    producer.generate_data()


if __name__ == "__main__":
    feed()
