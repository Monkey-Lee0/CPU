from assassyn.frontend import *
from assassyn.backend import elaborate
from assassyn import utils
import assassyn
import os
import sys

class Subtractor(Module):
    def __init__(self):
        super().__init__(ports={'sub_a': Port(Int(32)), 'sub_b': Port(Int(32))})

    @module.combinational
    def build(self):
        a, b = self.pop_all_ports(False)
        c = a - b
        log("减法器: {} - {} = {}", a, b, c)

# LeftPath: 创建部分 Bind
class LeftPath(Module):
    def __init__(self):
        super().__init__(ports={'lhs_a': Port(Int(32))})

    @module.combinational
    def build(self, sub: Subtractor):
        lhs_a = self.pop_all_ports(True)
        # 只绑定 sub_a，返回部分 Bind
        return sub.bind(sub_a=lhs_a)

# RightPath: 完成 Bind 并创建 AsyncCall
class RightPath(Module):
    def __init__(self):
        super().__init__(ports={'rhs_b': Port(Int(32))})

    @module.combinational
    def build(self, bound_sub):
        rhs_b = self.pop_all_ports(True)
        # 添加 sub_b 并创建 AsyncCall
        call = bound_sub.async_called(sub_b=rhs_b)
        call.bind.set_fifo_depth(sub_a=2, sub_b=2)

# Driver: 数据分流
class Driver(Module):
    def __init__(self):
        super().__init__(ports={})

    @module.combinational
    def build(self, lhs: LeftPath, rhs: RightPath):
        cnt = RegArray(Int(32), 1)
        (cnt & self)[0] <= cnt[0] + Int(32)(1)

        v = cnt[0] * cnt[0]
        call_lhs = lhs.async_called(lhs_a=v[0:31].bitcast(Int(32)))
        call_lhs.bind.set_fifo_depth(lhs_a=2)

        call_rhs = rhs.async_called(rhs_b=cnt[0])
        call_rhs.bind.set_fifo_depth(rhs_b=2)

if __name__ == "__main__":
    sys = SysBuilder('adder')
    with sys:
        adder = Adder()
        adder.build()

        driver = Driver()
        driver.build(adder)

    print(sys)

    config = assassyn.backend.config(
        verilog=utils.has_verilator(),
        sim_threshold=200,
        idle_threshold=200,
        random=True
    )

    simulator_path, verilator_path = elaborate(sys, **config)

    print(utils.run_simulator(simulator_path))

