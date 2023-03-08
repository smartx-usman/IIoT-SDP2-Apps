import http.server
import logging
import os
import random
import socketserver
import string

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

PORT = 8000
DIRECTORY = "/files"


def create_file(filename, size_in_bytes):
    if not os.path.exists(filename):
        # Generate random content for the file
        content = ''.join(random.choices(string.ascii_letters + string.digits, k=size_in_bytes))

        # Write the content to the file
        with open(filename, 'w') as f:
            f.write(content)

        logging.info(f"File {filename} created with size {size_in_bytes} bytes")
    else:
        logging.info(f"File {filename} already exists")


# Example usage: create a file "dummy.txt" with 10 KB of random content

create_file(f"{DIRECTORY}/file-tiny.txt", 10000)
create_file(f"{DIRECTORY}/file-small.txt", 1000000)
create_file(f"{DIRECTORY}/file-large.txt", 100000000)


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)


with socketserver.ThreadingTCPServer(('0.0.0.0', PORT), Handler) as httpd:
    logging.info(f"Serving files at http://127.0.0.1:{PORT}{DIRECTORY}")
    httpd.serve_forever()
