import logging
import os

import numpy as np
import pandas as pd
import requests

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

workload_type = os.environ['WORKLOAD_TYPE']
logging.info(f'Workload type is {workload_type}')


def cpu_intensive():
    while True:
        np.random.seed(0)
        monte_carlo_simulation(1000)
    logging.info("CPU intensive workload completed")


def monte_carlo_simulation(n):
    simulations = []
    for _ in range(n):
        prices = [100]
        for _ in range(100):
            prices.append(prices[-1] * np.exp(np.random.normal(0, 0.01)))
        simulations.append(prices)
    return simulations


def memory_intensive():
    data = []
    while True:
        data.append(pd.DataFrame(np.random.rand(1000, 1000)))
    logging.info("Memory intensive workload completed")


def disk_intensive():
    while True:
        with open('tempfile', 'wb') as f:
            f.write(os.urandom(10 ** 6))
        if os.path.exists('tempfile'):
            os.remove('tempfile')
    logging.info("Disk intensive workload completed")


def network_intensive():
    data = os.urandom(10 ** 6)
    while True:
        requests.post('http://example.com', data=data)
    logging.info("Network intensive workload completed")


def main():
    if workload_type == 'cpu-burner':
        cpu_intensive()
    elif workload_type == 'memory-burner':
        memory_intensive()
    elif workload_type == 'disk-burner':
        disk_intensive()
    elif workload_type == 'network-burner':
        network_intensive()
    else:
        logging.ERROR(f"Invalid workload type: {workload_type}")
        exit(1)


if __name__ == '__main__':
    main()
