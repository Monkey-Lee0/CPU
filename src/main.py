from assassyn.backend import elaborate, config
import os
from contextlib import contextmanager
from pathlib import Path

from assassyn import utils
from assassyn.backend import elaborate, config

from unit import buildSys
from inst import RegName, InstName

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

    result = run_quietly(run_simulator)
    for ind, name in reversed(list(enumerate(RegName))):
        result = result.replace(f'${ind}', name)
    for ind, name in reversed(list(enumerate(InstName))):
        result = result.replace(f'%{ind}', name)
    print(result)
