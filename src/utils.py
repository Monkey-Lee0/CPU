from assassyn.frontend import *

class ValArray:
    def __init__(self, dtype:DType, size:int, owner):
        self.size = size
        self.dtype = dtype
        self.arr = [RegArray(dtype, 1) for _ in range(size)]
        self.owner = owner

    def __getitem__(self, idx):
        if isinstance(idx, int):
            return self.arr[idx][0]
        if isinstance(idx, Value):
            res = self.arr[0][0]
            for i in range(self.size):
                res = (idx == Bits(32)(i)).select(self.arr[i][0], res)
            return res
        return None

    def __setitem__(self, idx, value):
        if isinstance(idx, int):
            (self.arr[idx] & self.owner)[0] <= value
        elif isinstance(idx, Value):
            for i in range(self.size):
                with Condition(idx == Bits(32)(i)):
                    (self.arr[i] & self.owner)[0] <= value

def popAllPorts(unit:Module):
    for port in unit.ports:
        with Condition(port.valid()):
            port.pop()

def peekWithDefault(port:Port, default:Value):
    return port.peek().optional(default, port.valid())

def checkInside(l:Value, r:Value, i:Value):
    return ((i >= l) & (i < r)) | ((l > r) & ((i >= l) | (i < r)))

def bitsToInt32(b, bit): # b:Bits(bit); sign extend b to Int(32)
    mxVal = Bits(32)(1) << Bits(32)(bit-1)
    bInt = b.bitcast(Int(32))
    return (b < mxVal).select(bInt, bInt - mxVal - mxVal)