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
    parser.add_argument('-t', '--value_type', nargs=1, help='Value type normal|abnormal|both', required=True)

    parser.add_argument('-ns', '--normal_start_value', nargs=1, help='Normal data range start value', required=False)
    parser.add_argument('-ne', '--normal_end_value', nargs=1, help='Normal data range end value', required=False)
    parser.add_argument('-nn', '--normal_total_values', nargs=1, help='No. of normal values to generate', required=False)

    parser.add_argument('-as', '--abnormal_start_value', nargs=1, help='Abnormal data range start value',
                        required=False)
    parser.add_argument('-ae', '--abnormal_end_value', nargs=1, help='Abnormal data range end value', required=False)
    parser.add_argument('-an', '--abnormal_total_values', nargs=1, help='No. of abnormal values to generate',
                        required=False)
    parser.add_argument('-no', '--normal_output_file', nargs=1, help='Normal data output file name', required=True)
    parser.add_argument('-ao', '--abnormal_output_file', nargs=1, help='Abnormal data output file name', required=False)

    return parser.parse_args(sys.argv[1:])


def generate_integer_values(start_value, end_value, total_values):
    """Generate integer values based on given range of values"""
    values = list(np.random.randint(low=int(math.floor(float(start_value))),
                                    high=int(math.ceil(float(end_value))),
                                    size=int(total_values)))

    return values


def generate_float_values(start_value, end_value, total_values):
    """Generate float values based on given range of values"""
    values = list(np.random.uniform(low=float(start_value),
                                    high=float(end_value),
                                    size=int(total_values)))

    return values


def generate_both_values():
    """Generate both int and float values based on given range of values"""
    if arguments.value_type[0] == "both":
        normal_int_values = generate_integer_values(
            start_value=arguments.normal_start_value[0], end_value=arguments.normal_end_value[0], total_values=arguments.normal_total_values[0]
        )

        abnormal_int_values = generate_integer_values(
            start_value=arguments.abnormal_start_value[0], end_value=arguments.abnormal_end_value[0], total_values=arguments.abnormal_total_values[0]
        )

        normal_float_values = generate_float_values(
            start_value=arguments.normal_start_value[0], end_value=arguments.normal_end_value[0], total_values=arguments.normal_total_values[0]
        )

        abnormal_float_values = generate_float_values(
            start_value=arguments.abnormal_start_value[0], end_value=arguments.abnormal_end_value[0], total_values=arguments.abnormal_total_values[0]
        )

        normal_values = []
        abnormal_values = []
        for index in range(len(normal_int_values)):
            normal_values.append(str(normal_int_values[index]) + ',' + str(normal_float_values[index]))
        for index in range(len(abnormal_int_values)):
            abnormal_values.append(str(abnormal_int_values[index]) + ',' + str(abnormal_float_values[index]))
        return normal_values, abnormal_values

    elif arguments.value_type[0] == "normal":
        normal_int_values = generate_integer_values(
            arguments.normal_start_value[0], arguments.normal_end_value[0], arguments.normal_total_values[0]
        )

        normal_float_values = generate_float_values(
            arguments.normal_start_value[0], arguments.normal_end_value[0], arguments.normal_total_values[0]
        )

        normal_values = []
        for index in range(len(normal_int_values)):
            normal_values.append(str(normal_int_values[index]) + ',' + str(normal_float_values[index]))
        return normal_values

    elif arguments.value_type[0] == "abnormal":
        abnormal_int_values = generate_integer_values(
            arguments.abnormal_start_value[0], arguments.abnormal_end_value[0], arguments.abnormal_total_values[0]
        )

        abnormal_float_values = generate_float_values(
            arguments.abnormal_start_value[0], arguments.abnormal_end_value[0], arguments.abnormal_total_values[0]
        )

        abnormal_values = []

        for index in range(len(abnormal_int_values)):
            abnormal_values.append(str(abnormal_int_values[index]) + ',' + str(abnormal_float_values[index]))
        return abnormal_values
    else:
        logging.fatal(f'Invalid data type {arguments.value_type[0]} option.')
        sys.exit(0)


def save_data_to_file(generated_normal_values, generated_abnormal_values):
    """Save generated data to file"""
    if arguments.value_type[0] == "both":
        try:
            normal_output_file = open(f'/data/{arguments.normal_output_file[0]}', 'w')
            abnormal_output_file = open(f'/data/{arguments.abnormal_output_file[0]}', 'w')

            for value in generated_normal_values:
                normal_output_file.write(str(value) + "\n")
            normal_output_file.close()

            for value in generated_abnormal_values:
                abnormal_output_file.write(str(value) + "\n")
            abnormal_output_file.close()

            logging.info(f'Data is saved to {arguments.normal_output_file[0]} and {arguments.abnormal_output_file[0]}.')
        except Exception as exception:
            logging.error(f'Error while saving data -> {exception}')

    elif arguments.value_type[0] == "normal":
        try:
            normal_output_file = open(f'/data/{arguments.normal_output_file[0]}', 'w')

            for value in generated_normal_values:
                normal_output_file.write(str(value) + "\n")
            normal_output_file.close()

            logging.info(f'Data is saved to {arguments.normal_output_file[0]}.')
        except Exception as exception:
            logging.error(f'Error while saving data -> {exception}')

    elif arguments.value_type[0] == "abnormal":
        try:
            abnormal_output_file = open(f'/data/{arguments.abnormal_output_file[0]}', 'w')

            for value in generated_abnormal_values:
                abnormal_output_file.write(str(value) + "\n")
            abnormal_output_file.close()

            logging.info(f'Data is saved to {arguments.abnormal_output_file[0]}.')
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
    generated_normal_values, generated_abnormal_values = generate_both_values()

# Save data to file
save_data_to_file(generated_normal_values, generated_abnormal_values)

logging.info('Data is generated and saved successfully.')
