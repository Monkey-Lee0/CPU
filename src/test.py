from assassyn.backend import elaborate, config
from assassyn import utils
import assassyn
from memoryAccess import *

import os
from unit import buildSys
from contextlib import contextmanager
from pathlib import Path
from main import run_quietly


class Driver(Module):

    def __init__(self):
        super().__init__(ports={})

    @module.combinational
    def build(self, dCache):
        cnt = RegArray(Bits(32), 1)
        (cnt & self)[0] <= cnt[0] + Bits(32)(1)
        with Condition(cnt[0] == Bits(32)(1)):
            dCache.newAddr.push(Bits(32)(1))
            dCache.newType.push(Bits(1)(1))
            dCache.wdata.push(Bits(32)(505))
        with Condition(cnt[0] == Bits(32)(2)):
            dCache.newAddr.push(Bits(32)(2))
            dCache.newType.push(Bits(1)(1))
            dCache.wdata.push(Bits(32)(808))
        with Condition(cnt[0] == Bits(32)(3)):
            dCache.newAddr.push(Bits(32)(3))
            dCache.newType.push(Bits(1)(1))
            dCache.wdata.push(Bits(32)(1040))
        with Condition(cnt[0] == Bits(32)(4)):
            dCache.newAddr.push(Bits(32)(4))
            dCache.newType.push(Bits(1)(1))
            dCache.wdata.push(Bits(32)(1808))
        with Condition(cnt[0] == Bits(32)(5)):
            dCache.newAddr.push(Bits(32)(5))
            dCache.newType.push(Bits(1)(1))
            dCache.wdata.push(Bits(32)(59808))
        with Condition(cnt[0] == Bits(32)(6)):
            dCache.newAddr.push(Bits(32)(6))
            dCache.newType.push(Bits(1)(1))
            dCache.wdata.push(Bits(32)(114514))
        with Condition(cnt[0] == Bits(32)(7)):
            dCache.newAddr.push(Bits(32)(7))
            dCache.newType.push(Bits(1)(1))
            dCache.wdata.push(Bits(32)(109020102))
        with Condition(cnt[0] == Bits(32)(8)):
            dCache.newAddr.push(Bits(32)(8))
            dCache.newType.push(Bits(1)(1))
            dCache.wdata.push(Bits(32)(50020))
        with Condition(cnt[0] == Bits(32)(12)):
            dCache.newAddr.push(Bits(32)(5))
            dCache.newType.push(Bits(1)(0))
            dCache.wdata.push(Bits(32)(0))
        with Condition(cnt[0] == Bits(32)(70)):
            hasItem, itemStatus, value = dCache.getItem(Bits(32)(2))
            log("{} {} {}", hasItem, itemStatus, value)
        dCache.async_called()



def buildSys():
    sys = SysBuilder('CPU')
    with sys:
        driver = Driver()
        dCache = DCache(4, 'workload/'+testcase)
        driver.build(dCache)
        dCache.build()

    return sys

if __name__ == '__main__':
    sys = buildSys()

    print(sys)

    config = assassyn.backend.config(
        verilog=utils.has_verilator(),
        sim_threshold=100,
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
