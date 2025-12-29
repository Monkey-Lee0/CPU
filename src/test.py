from assassyn.backend import elaborate, config
from assassyn import utils
import assassyn
from regFile import *

import os
from unit import buildSys
from contextlib import contextmanager
from pathlib import Path
from main import run_quietly


class Driver(Module):

    def __init__(self):
        super().__init__(ports={})

    @module.combinational
    def build(self, lhs: Module):
        cnt = RegArray(Bits(32), 1)
        v = cnt[0]
        (cnt & self)[0] <= cnt[0] + Bits(32)(1)
        lhs.async_called(data=v)
        # rhs.async_called(data=v)


class Adder(Downstream):

    def __init__(self):
        super().__init__()

    @downstream.combinational
    def build(self, a: Value, b: Value):
        a = a.optional(Bits(32)(1))
        b = b.optional(Bits(32)(1))
        c = a + b
        log("downstream: {} + {} = {}", a, b, c)


# class RegFileAdder(Module):
#     def __init__(self):
#         super().__init__(ports={
#             'data':Port(Bits(32))
#         })
#
#     @module.combinational
#     def build(self, reg_file: BusyFile):
#         clk = self.data.pop()
#         is_write_phase = (clk < Bits(32)(32))
#         write_addr = Bits(32)(0)
#         write_addr = is_write_phase.select(clk,write_addr)
#         write_value = clk[31:31]
#         reg_file.build(isWrite=is_write_phase,
#                        WriteIndex=write_addr,
#                        WriteValue=write_value)

class RegFileReader(Module):
    def __init__(self):
        super().__init__(ports={
            'data':Port(Bits(32))
        })

    @module.combinational
    def build(self, reg_file: BusyFile):
        clk = self.data.pop()
        # is_read_phase = ((clk > Bits(32)(31)) & (clk < Bits(32)(64)))
        is_read_phase = (clk < Bits(32)(32))
        read_addr = Bits(32)(0)
        read_addr = is_read_phase.select(clk, read_addr)
        a = reg_file.build(isRead=is_read_phase,
                            ReadIndex=read_addr)
        # adder = Adder()
        # adder.build(a, a)


def check_raw(raw):
    cnt = 0
    for i in raw.split('\n'):
        if 'downstream:' in i:
            line_toks = i.split()
            c = line_toks[-1]
            a = line_toks[-3]
            b = line_toks[-5]
            assert int(a) + int(b) == int(c)
            cnt += 1
    assert cnt == 99, f'cnt: {cnt} != 99'


def buildSys():
    sys = SysBuilder('CPU')
    with sys:
        driver = Driver()
        reg_file = BusyFile()
        # adder = RegFileAdder()
        reader = RegFileReader()
        # adder.build(reg_file)
        reader.build(reg_file)
        driver.build(reader)


    return sys

if __name__ == '__main__':
    sys = buildSys()

    print(sys)

    config = assassyn.backend.config(
        verilog=utils.has_verilator(),
        sim_threshold=50,
        idle_threshold=50,
        resource_base=Path(__file__).resolve().parent.parent,
        random=True
    )


    def run_elaborate():
        return elaborate(sys, **config)


    simulator_path, verilator_path = run_quietly(run_elaborate)


    def run_simulator():
        return utils.run_simulator(simulator_path)


    print(run_quietly(run_simulator))
