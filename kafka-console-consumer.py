from kafka import KafkaConsumer
import argparse

parser = argparse.ArgumentParser('this is my description')

parser.add_argument('--topic', dest='topic', help='topic', default='deepstream-topic')

args = parser.parse_args()

consumer = KafkaConsumer(args.topic, bootstrap_servers=["localhost:9092"])
print("Connected to the consumer")

print(consumer.topics())

print("Getting messages")
for msg in consumer:
    print(msg.value)
