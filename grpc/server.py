from concurrent import futures

import grpc
import greeting_pb2 as pb
import greeting_pb2_grpc


class Greeter(greeting_pb2_grpc.GreeterServicer):
    def greet(self, request, context):
        print("Got request " + str(request))
        return pb.ServerOutput(message='{0} {1}!'.format(request.greeting, request.name))


def start_server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    greeting_pb2_grpc.add_GreeterServicer_to_server(Greeter(), server)
    server.add_insecure_port('[::]:5051')
    print("gRPC starting")
    server.start()
    server.wait_for_termination()


start_server()
