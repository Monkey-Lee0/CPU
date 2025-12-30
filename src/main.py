from assassyn.backend import elaborate, config
import os
from contextlib import contextmanager
from pathlib import Path

from assassyn import utils
from assassyn.backend import elaborate, config

from unit import buildSys

@contextmanager
def _suppress_output():
    import sys
    original_stdout = sys.stdout
    original_stderr = sys.stderr

    try:
        with open(os.devnull, 'w') as null_device:
            sys.stdout = null_device
            sys.stderr = null_device
            yield
    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr

def run_quietly(func, *args, **kwargs):
    with _suppress_output():
        result = func(*args, **kwargs)
    return result

numToReg = {
  '$0': 'zero',
  '$1': 'ra',
  '$2': 'sp',
  '$3': 'gp',
  '$4': 'tp',
  '$5': 't0',
  '$6': 't1',
  '$7': 't2',
  '$8': 's0',
  '$9': 's1',
  '$10': 'a0',
  '$11': 'a1',
  '$12': 'a2',
  '$13': 'a3',
  '$14': 'a4',
  '$15': 'a5',
  '$16': 'a6',
  '$17': 'a7',
  '$18': 's2',
  '$19': 's3',
  '$20': 's4',
  '$21': 's5',
  '$22': 's6',
  '$23': 's7',
  '$24': 's8',
  '$25': 's9',
  '$26': 's10',
  '$27': 's11',
  '$28': 't3',
  '$29': 't4',
  '$30': 't5',
  '$31': 't6'
}

if __name__ == "__main__":

    sys = buildSys()
    print(sys)

    config = config(
        verilog=utils.has_verilator(),
        sim_threshold=500,
        idle_threshold=200,
        resource_base=Path(__file__).resolve().parent.parent,
        random=True
    )

    def run_elaborate():
        return elaborate(sys, **config)

    simulator_path, verilator_path = run_quietly(run_elaborate)

    def run_simulator():
        return utils.run_simulator(simulator_path)

    print(run_quietly(run_simulator).replace('$0', numToReg['$0'])
    .replace('$1', numToReg['$1'])
    .replace('$2', numToReg['$2'])
    .replace('$3', numToReg['$3'])
    .replace('$4', numToReg['$4'])
    .replace('$5', numToReg['$5'])
    .replace('$6', numToReg['$6'])
    .replace('$7', numToReg['$7'])
    .replace('$8', numToReg['$8'])
    .replace('$9', numToReg['$9'])
    .replace('$10', numToReg['$10'])
    .replace('$11', numToReg['$11'])
    .replace('$12', numToReg['$12'])
    .replace('$13', numToReg['$13'])
    .replace('$14', numToReg['$14'])
    .replace('$15', numToReg['$15'])
    .replace('$16', numToReg['$16'])
    .replace('$17', numToReg['$17'])
    .replace('$18', numToReg['$18'])
    .replace('$19', numToReg['$19'])
    .replace('$20', numToReg['$20'])
    .replace('$21', numToReg['$21'])
    .replace('$22', numToReg['$22'])
    .replace('$23', numToReg['$23'])
    .replace('$24', numToReg['$24'])
    .replace('$25', numToReg['$25'])
    .replace('$26', numToReg['$26'])
    .replace('$27', numToReg['$27'])
    .replace('$28', numToReg['$28'])
    .replace('$29', numToReg['$29'])
    .replace('$30', numToReg['$30'])
    .replace('$31', numToReg['$31']))

