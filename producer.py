from confluent_kafka import Producer
import socket

conf = {'bootstrap.servers': '192.168.176.2:9092',
        'client.id': socket.gethostname()}
# conf = {'bootstrap.servers': 'localhost:9092',
#         'client.id': socket.gethostname()}

producer = Producer(conf)

def acked(err, msg):
    if err is not None:
        print("Failed to deliver message: %s: %s" % (str(msg), str(err)))
    else:
        print("Message produced: %s" % (str(msg)))

print("-------------------------------\n")
producer.produce("todo1-topic", key="key", value="Ejemplo de prueba", callback=acked)

producer.poll(1)