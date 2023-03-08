import concurrent.futures
import logging
import os
import time
import datetime

import requests

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

server_url = os.getenv('FILE_SERVER_URL')
server_port = os.getenv('FILE_SERVER_PORT')
seasonality = os.getenv('SEASONALITY')
total_requests = int(os.getenv('TOTAL_REQUESTS'))

while True:
    urls = []
    current_time = datetime.datetime.now()

    if seasonality:
        if 9 <= current_time.hour < 18:
            total_requests = 80
        elif (6 <= current_time.hour < 9) or (18 <= current_time.hour < 21):
            total_requests = 15
        else:
            total_requests = 5

    logging.info(f"Total concurrent requests: {total_requests}")

    for request in range(total_requests):
        if request % 3 == 0:
            urls.append(f"http://{server_url}:{server_port}/file-tiny.txt")
        elif request % 3 == 1:
            urls.append(f"http://{server_url}:{server_port}/file-small.txt")
        else:
            urls.append(f"http://{server_url}:{server_port}/file-large.txt")

    #logging.info(urls)


    def get_file(url):
        logging.info(f"Downloading file {url}...")
        try:
            response = requests.get(url)
            if response.status_code == 200:
                filename = url.split('/')[-1]
                with open(filename, 'wb') as f:
                    f.write(response.content)
                logging.info(f"File saved as {filename}")
            else:
                logging.warning(f"File {url} not found on server")
        except Exception as e:
            logging.error(f"Error downloading file {url}: {e}")


    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(get_file, urls)

    time.sleep(60)
