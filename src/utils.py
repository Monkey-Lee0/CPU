from assassyn.frontend import *

class ValWithOwner:
    def __init__(self, arr:Array, owner):
        self.arr = arr
        self.owner = owner

    def __le__(self, other):
        (self.arr & self.owner)[0] <= other

    def get(self):
        return self.arr[0]

class ValArray:
    def __init__(self, dtype:DType, size:int, owner):
        self.arr = [RegArray(dtype, 1) for _ in range(size)]
        self.owner = owner

    def __getitem__(self, idx):
        return ValWithOwner(self.arr[idx], self.owner)
