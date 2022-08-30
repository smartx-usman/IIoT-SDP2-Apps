# Example Protobuf and gRPC Application

This application will be extended to implement observability data encoding and transfer from edge nodes to the centralized server.

### Prerequisites
- Python >= 3.8.9

### How to compile protobuf

### How to run this application
1. Start server to respond to client messages
```shell
python3 server.py
```

2. Start client to produce messages
```shell
python3 client.py
```

### Reading material
- [Protocol Buffer Basics: Python](https://developers.google.com/protocol-buffers/docs/pythontutorial)
- [Length-Delimited Protobuf Streams](https://seb-nyberg.medium.com/length-delimited-protobuf-streams-a39ebc4a4565)