import grpc

import greeting_pb2
import greeting_pb2_grpc


def run():
    with grpc.insecure_channel('localhost:5051') as channel:
        stub = greeting_pb2_grpc.GreeterStub(channel)
        response = stub.greet(greeting_pb2.ClientInput(name='John', greeting="Yo"))
    print("Greeter client received following from server: " + response.message)


run()
