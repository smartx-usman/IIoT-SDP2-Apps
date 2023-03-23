import logging
import subprocess
import sys
import time


class Stress:
    hdd = '0'
    io = '0'
    vm = '0'
    cpu = '1'
    vm_bytes = '0'
    stress_timeout = '0s'
    idle_timeout = '0'
    stress_initial_delay = '0'
    stress = 'false'

    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

    def __init__(self, cpu, vm, vm_bytes, io, hdd, stress_timeout, idle_timeout, stress_initial_delay):
        self.cpu = cpu
        self.vm = vm
        self.vm_bytes = vm_bytes
        self.io = io
        self.hdd = hdd
        self.stress_timeout = stress_timeout
        self.idle_timeout = idle_timeout
        self.stress_initial_delay = stress_initial_delay

    def stress_task(self):
        time.sleep(self.stress_initial_delay)
        command = "stress"

        if int(self.vm) <= 0 and int(self.cpu) <= 0 and int(self.hdd) <= 0 and int(self.io) <= 0:
            logging.error('Invalid stress options provided. Application is exiting.')
            sys.exit()
        else:
            command = command + " --cpu " + str(self.cpu) if int(self.cpu) >= 1 else command
            command = command + " --vm " + str(self.vm) + " --vm-bytes " + str(self.vm_bytes) if int(
                self.vm) >= 1 else command
            command = command + " --hdd " + str(self.hdd) if int(self.hdd) >= 1 else command
            command = command + " --io " + str(self.io) if int(self.io) >= 1 else command
            command = command + " --timeout " + str(self.stress_timeout)

        while True:
            logging.info('Stress test Started.')
            logging.info(f'Stress command: [{command}].')

            process = subprocess.Popen(
                [command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                universal_newlines=True)
            stdout, stderr = process.communicate()
            #print(stdout)
            logging.info('Stress test Ended.')
            time.sleep(self.idle_timeout)
