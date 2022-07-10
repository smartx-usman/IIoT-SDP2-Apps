#!/usr/bin/env python3
"""
For generating synthetic data.
Author: Muhammad Usman
Version: 0.2.0
"""

import argparse as ap
import logging
import math
import sys

import numpy as np

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)


def parse_arguments():
    """Read and parse commandline arguments"""
    parser = ap.ArgumentParser(prog='data_generator', usage='%(prog)s [options]', add_help=True)
    parser.add_argument('-d', '--data_type', nargs=1, help='Data type integer|float|both', required=True)
    parser.add_argument('-t', '--value_type', nargs=1, help='Value type normal|abnormal', required=True)
    parser.add_argument('-s', '--start_value', nargs=1, help='Range start value', required=True)
    parser.add_argument('-e', '--end_value', nargs=1, help='Range end value', required=True)
    parser.add_argument('-n', '--total_values', nargs=1, help='No. of values to generate', required=True)
    parser.add_argument('-o', '--output_file', nargs=1, help='Output file name', required=True)

    return parser.parse_args(sys.argv[1:])


def generate_integer_values():
    """Generate integer values based on given range of values"""
    values = list(np.random.randint(low=int(math.floor(float(arguments.start_value[0]))),
                                    high=int(math.ceil(float(arguments.end_value[0]))),
                                    size=int(arguments.total_values[0])))

    return values


def generate_float_values():
    """Generate float values based on given range of values"""
    values = list(np.random.uniform(low=float(arguments.start_value[0]),
                                    high=float(arguments.end_value[0]),
                                    size=int(arguments.total_values[0])).round(4))

    return values


def generate_both_values():
    """Generate both int and float values based on given range of values"""
    int_values = generate_integer_values()
    float_values = generate_float_values()
    values = []
    for index in range(len(int_values)):
        values.append(str(int_values[index]) + ',' + str(float_values[index]))
    return values


def save_data_to_file(generated_values):
    """Save generated data to file"""
    try:
        output_file = open(f'/data/{arguments.output_file[0]}', 'w')

        for value in generated_values:
            output_file.write(str(value) + "\n")
        output_file.close()
    except Exception as exception:
        logging.error(f'Error while saving data -> {exception}')


logging.info(f'Starting data generation.')

# Parse input arguments
arguments = parse_arguments()

# Generate integer data
if arguments.data_type[0] == "integer":
    generated_values = generate_integer_values()

# Generate float data
if arguments.data_type[0] == "float":
    generated_values = generate_float_values()

# Generate both int and float data
if arguments.data_type[0] == "both":
    generated_values = generate_both_values()

# Save data to file
save_data_to_file(generated_values)

logging.info(f'Data is saved to {arguments.output_file[0]}.')
