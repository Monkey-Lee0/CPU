from assassyn.frontend import *

def predictor(branch1PC:Value, branch2PC:Value):
    branch = branch1PC < branch2PC
    return branch, branch.select(branch1PC, branch2PC), branch.select(branch2PC, branch1PC)