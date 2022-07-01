#!/usr/bin/env python3

import argparse as ap
import logging
import os
import subprocess
import sys
import time

# This is our shell command, executed in subprocess.
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.WARN)


def parse_arguments():
    """Read and parse commandline arguments"""
    parser = ap.ArgumentParser(prog='stress-all', usage='%(prog)s [options]', add_help=True)
    parser.add_argument('-t', '--value_type', nargs=1, help='Data value type normal|abnormal', required=True)
    # parser.add_argument('-s', '--start_value', nargs=1, help='Range start value', required=True)

    return parser.parse_args(sys.argv[1:])


condition = True


def run_normal():
    while 1:
        p = subprocess.Popen("stress --hdd 1 --io 2 --vm 2 --cpu 1 --timeout 300s", stdout=subprocess.PIPE, shell=True)
        logging.info(p.communicate())


def run_abnormal():
    while 1:
        p = subprocess.Popen("stress --hdd 1 --io 2 --vm 2 --cpu 1 --timeout 240s", stdout=subprocess.PIPE, shell=True)
        logging.info(p.communicate())
        logging.error(f'Internal application runtime error.')

        time.sleep(300)


# p = subprocess.run("stress", "--hdd", "2", "--io", "4", "--vm", "6", "--cpu", "4", "--timeout", "120s")


# Parse input arguments
arguments = parse_arguments()

# Generate integer data
if arguments.value_type[0] == "normal":
    run_normal()

# generate float data
if arguments.value_type[0] == "abnormal":
    run_abnormal()
