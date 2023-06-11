import pika
import grpc
import protos.mafia_pb2 as mafia_pb2
import protos.mafia_pb2_grpc as mafia_pb2_grpc


# код вдохновлен https://www.rabbitmq.com/tutorials/tutorial-six-python.html и моей домашкой по РС)))

class RabbitClient(object):
    def __init__(self, name, room_name):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='0.0.0.0', port=5672))
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange=f'{room_name}_{name}', exchange_type='fanout')
        self.result = self.channel.queue_declare(queue=f'{room_name}_{name}')
        self.callback_queue = self.result.method.queue
        self.channel.queue_bind(exchange=f'{room_name}_{name}', queue=self.callback_queue)
        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)

    def on_response(self, ch, method, props, body):
        print(body.decode(encoding='UTF-8', errors='replace'))

    def close(self):
        try:
            self.channel.close()
            self.connection.close()
        except:
            pass


class RabbitServer(object):
    def __init__(self, host='0.0.0.0'):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host, port=5672))
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange='rabbit_server', exchange_type='fanout')
        self.result = self.channel.queue_declare(queue='rabbit_server')
        self.callback_queue = self.result.method.queue
        self.channel.queue_bind(exchange='rabbit_server', queue=self.callback_queue)
        self.grpc_channel = grpc.insecure_channel('server:8080')
        self.stub = mafia_pb2_grpc.SoaMafiaServerStub(self.grpc_channel)

    def on_response(self, ch, method, props, body):
        name = props.headers['name']
        room_name = props.headers['room_name']
        time = props.headers['time']
        if time == 'day':
            response = self.stub.AlivePlayers(mafia_pb2.Room(room_name=room_name)).players
        else:
            response = self.stub.MafiaPlayers(mafia_pb2.Room(room_name=room_name)).players
        for value in response:
            if value == name:
                continue
            self.channel.queue_declare(f'{room_name}_{value}')
            self.channel.basic_publish(f'{room_name}_{value}', routing_key='rpc_queue', body=body)

    def close(self):
        try:
            self.grpc_channel.close()
            self.channel.close()
            self.connection.close()
        except:
            pass


def main():
    server = RabbitServer('rabbitmq')
    server.channel.basic_consume(
        queue=server.callback_queue,
        on_message_callback=server.on_response,
        auto_ack=True)
    server.channel.start_consuming()


if __name__ == '__main__':
    main()
