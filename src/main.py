from assassyn.frontend import *
from assassyn.backend import elaborate, config
from assassyn import utils
import assassyn

import os
from unit import buildSys
from contextlib import contextmanager
from pathlib import Path

# 先定义上下文管理器，用于临时抑制输出
@contextmanager
def _suppress_output():
    """内部辅助上下文管理器：临时屏蔽标准输出和标准错误"""
    # 保存原始的 stdout 和 stderr，用于后续恢复
    import sys
    original_stdout = sys.stdout
    original_stderr = sys.stderr

    try:
        # 打开系统空设备（自动适配 Windows/nul 和 Linux/Mac/dev/null）
        with open(os.devnull, 'w') as null_device:
            # 重定向标准输出和错误到空设备
            sys.stdout = null_device
            sys.stderr = null_device
            yield  # 执行被包裹的代码块
    finally:
        # 无论是否发生异常，都恢复原始输出流
        sys.stdout = original_stdout
        sys.stderr = original_stderr

def run_quietly(func, *args, **kwargs):
    """
    静默运行目标函数的封装函数
    :param func: 待静默运行的目标函数
    :param args: 目标函数的位置参数
    :param kwargs: 目标函数的关键字参数
    :return: 目标函数 func 的执行返回值
    """
    # 使用上下文管理器包裹目标函数的执行，实现静默运行
    with _suppress_output():
        # 传递参数并执行目标函数，保存返回值
        result = func(*args, **kwargs)
    # 返回目标函数的执行结果
    return result

if __name__ == "__main__":

    sys = buildSys()

    print(sys)

    config = assassyn.backend.config(
        verilog=utils.has_verilator(),
        sim_threshold=20,
        idle_threshold=20,
        resource_base=Path(__file__).resolve().parent.parent,
        random=True
    )

    def run_elaborate():
        return elaborate(sys, **config)

    simulator_path, verilator_path = run_quietly(run_elaborate)

    def run_simulator():
        return utils.run_simulator(simulator_path)

    print(run_quietly(run_simulator))

