import struct

import grpc

import greeting_pb2 as pb
import greeting_pb2_grpc


def run():
    with grpc.insecure_channel('localhost:5051') as channel:
        stub = greeting_pb2_grpc.GreeterStub(channel)
        response = stub.greet(pb.ClientInput(name='User', greeting="Hej"))
    print("Greeter client received following from server: " + response.message)


def write_to_file():
    # Write two users to the same protobuf file
    # Put a length delimiter in front of each message
    with open('output.user.ld', 'wb') as f:
        pb_users = [
            pb.ClientInput(name='User A', greeting='Hi'),
            pb.ClientInput(name='User B', greeting='Hello'),
        ]
        for pb_user in pb_users:
            # serialize the message to a bytes array
            s = pb_user.SerializeToString()

            # retrieve message length as a bytes block
            len_bytes = struct.pack('>L', len(s))

            # write message length + serialized message
            f.write(len_bytes + s)


def read_from_file():
    pb_users = []

    with open('output.user.ld', 'rb') as f:
        while True:
            # read 4 bytes (32-bit int)
            msg_len_bytes = f.read(4)

            # no bytes => EOF
            if len(msg_len_bytes) == 0:
                return

                # retrieve length prefix
            # struct.unpack always returns a tuple, even if there is only one element
            msg_len = struct.unpack('>L', msg_len_bytes)[0]

            # read message as a byte string
            proto_str = f.read(msg_len)

            # de-serialize bytes into a protobuf message
            pb_user = pb.ClientInput()
            pb_user.ParseFromString(proto_str)
            print(pb_user.name)
            # pb_users.append(pb_user)


write_to_file()
read_from_file()
run()
#
