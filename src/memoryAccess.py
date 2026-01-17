from decoder import *
from predictor import predictor
from utils import ValArray, peekWithDefault, checkInside

def isCInst(inst):
    return (inst & Bits(32)(3)) != Bits(32)(3)

def movePC(pc, inst:Inst, length):
    inst = parseInst(inst)
    pc = (inst.type == Bits(32)(7)).select(
        pc + inst.imm.bitcast(Int(32)), pc)
    pc = (inst.type == Bits(32)(5)).select(
        predictor(pc + inst.imm.bitcast(Int(32)), pc + length)[1], pc)
    pc = ((inst.type != Bits(32)(5)) & (inst.type != Bits(32)(7)) & (inst.id != Bits(32)(35))).select(
        pc + length, pc)
    return pc

class ICache(Module):
    def __init__(self, cacheSize: int, init_file):
        super().__init__(ports={
            'start':Port(Bits(1)),
            'flushTag':Port(Bits(1)),
            'newPC':Port(Bits(32)),
            'newId':Port(Bits(32))
        })
        self.cacheSize = cacheSize
        self.cachePool = ValArray(Bits(32), cacheSize, self)
        self.instPC = ValArray(Bits(32), cacheSize, self)
        self.length = ValArray(Bits(32), cacheSize, self)
        self.sram = SRAM(32, 1<<16, init_file)
        self.l = RegArray(Bits(32), 1)
        self.r = RegArray(Bits(32), 1)
        self.bubble = ValArray(Bits(1), 1, self)

    def push(self, value, pc, length):
        with Condition((value != Bits(32)(0)) & (value != Bits(32)(0xfe000fa3))):
            # log("push {} {} {}", value, pc, length)
            (self.r & self)[0] <= (self.r[0] + Bits(32)(1)) % Bits(32)(self.cacheSize)
            self.cachePool[self.r[0]] = value
            self.instPC[self.r[0]] = pc
            self.length[self.r[0]] = length
        with Condition((value == Bits(32)(0xfe000fa3)) | (parseInst(value).id == Bits(32)(35))):
            self.bubble[0] = Bits(1)(1)

    def clear(self, pos):
        self.cachePool[pos] = Bits(32)(0)
        self.instPC[pos] = Bits(32)(0)
        self.length[pos] = Bits(32)(0)

    def pop(self):
        (self.l & self)[0] <= (self.l[0] + Bits(32)(1)) % Bits(32)(self.cacheSize)
        self.clear(self.l[0])

    def full(self):
        return ((self.r[0] + Bits(32)(1)) % Bits(32)(self.cacheSize) == self.l[0]) | \
            ((self.r[0] + Bits(32)(2)) % Bits(32)(self.cacheSize) == self.l[0])

    @module.combinational
    def build(self, rs, rob, lsb, rf):
        robId = RegArray(Bits(32), 1, [1])
        start = self.start.peek()
        flush = self.flushTag.valid()

        re = ValArray(Bits(1), 1, self)
        pc_cache = ValArray(Bits(32), 1, self)
        leftHalfLast = ValArray(Bits(32), 1, self)

        # combinational logic for pc_cache & re
        re_combinational = start & (~flush) & (~self.full()) & (~self.bubble[0])
        leftHalf = takeBitsRange(self.sram.dout[0], 0, 15)
        rightHalf = takeBitsRange(self.sram.dout[0], 16, 31)
        whole = self.sram.dout[0]
        combined = leftHalfLast[0] | (leftHalf << Bits(32)(16))

        pc_cache_combinational = (pc_cache[0] & Bits(32)(3)).case({
            Bits(32)(0): isCInst(leftHalf).select(movePC(pc_cache[0], leftHalf, Bits(32)(2)),
                                                  movePC(pc_cache[0], whole, Bits(32)(4))),
            Bits(32)(2): isCInst(rightHalf).select(movePC(pc_cache[0], rightHalf, Bits(32)(2)),
                                                   pc_cache[0] + Bits(32)(3)),
            Bits(32)(1): movePC(pc_cache[0] - Bits(32)(3), combined, Bits(32)(4)),
            None: pc_cache[0]
        })
        pc_cache_combinational = re[0].select(pc_cache_combinational, pc_cache[0])

        with Condition(re[0] & (~flush)):
            with Condition((pc_cache[0] & Bits(32)(3)) == Bits(32)(0)):
                with Condition(isCInst(leftHalf)):
                    self.push(leftHalf, pc_cache[0], Bits(32)(2))
                with Condition(~isCInst(leftHalf)):
                    self.push(whole, pc_cache[0], Bits(32)(4))
            with Condition((pc_cache[0] & Bits(32)(3)) == Bits(32)(2)):
                with Condition(isCInst(rightHalf)):
                    self.push(rightHalf, pc_cache[0], Bits(32)(2))
                with Condition(~isCInst(rightHalf)):
                    leftHalfLast[0] = rightHalf
            with Condition((pc_cache[0] & Bits(32)(3)) == Bits(32)(1)):
                self.push(combined, pc_cache[0] - Bits(32)(3), Bits(32)(4))

        self.sram.build(Bits(1)(0), re_combinational, pc_cache_combinational >> Bits(32)(2), Bits(32)(0))
        with Condition(~flush):
            pc_cache[0] = pc_cache_combinational
            re[0] = re_combinational

        with (Condition(start)):
            # flush
            with Condition(flush):
                self.flushTag.pop()
                newPC = self.newPC.pop()
                newId = self.newId.pop()

                pc_cache[0] = newPC
                re[0] = Bits(1)(0)
                (robId & self)[0] <= newId + Bits(32)(1)

                (self.l & self)[0] <= Bits(32)(0)
                (self.r & self)[0] <= Bits(32)(0)

                for i in range(self.cacheSize):
                    self.clear(i)

                self.bubble[0] = Bits(1)(0)

            with Condition(~flush):
                valid_rs = ~rs.full()
                valid_lsb = ~lsb.full()
                valid_rob = ~rob.full()
                valid_self = self.l[0] != self.r[0]
                valid = valid_rs & valid_lsb & valid_rob & valid_self

                # issue
                with Condition(valid):
                    inst = self.cachePool[self.l[0]]
                    pc = self.instPC[self.l[0]]
                    length = self.length[self.l[0]]
                    self.pop()
                    (robId & self)[0] <= robId[0] + Bits(32)(1)

                    # issue into rs
                    res = parseInst(inst)
                    log("issue {} {} {}", robId[0], inst, pc)
                    res.print()

                    with Condition((res.id != Bits(32)(34)) & (res.id != Bits(32)(36)) & (res.id != Bits(32)(37))):
                        rs.inst_type.push(res.type)
                        rs.id.push(res.id)
                        rs.rd.push(res.rd)
                        rs.rs1.push(res.rs1)
                        rs.rs2.push(res.rs2)
                        rs.imm.push(res.imm)
                        rs.newId.push(robId[0])

                    # issue into rob
                    rob.type.push(res.type)
                    rob.id.push(res.id)
                    rob.rd.push(res.rd)
                    rob.newId.push(robId[0])
                    rob.val.push(res.id.case({
                        Bits(32)(34): pc + length,
                        Bits(32)(35): pc + length,
                        Bits(32)(36): pc + res.imm,
                        Bits(32)(37): res.imm,
                        None: Bits(32)(0)
                    }))
                    # (branch prediction)
                    branch, _, otherPC = predictor(pc + res.imm.bitcast(Int(32)), pc + length)
                    rob.expectV.push((res.type == Bits(32)(5)).select(branch.zext(Bits(32)), Bits(32)(0)))
                    rob.otherPC.push((res.type == Bits(32)(5)).select(otherPC, Bits(32)(0)))

                    # issue into rf
                    # with Condition((res.type == Bits(32)(1)) | (res.type == Bits(32)(2)) | (res.type == Bits(32)(3)) |
                    #                (res.type == Bits(32)(6)) | (res.type == Bits(32)(7))):
                    #     rf.buildDependence(res.rd, robId[0])

                    # issue into lsb
                    with Condition((res.id >= Bits(32)(20)) & (Bits(32)(27) >= res.id)):
                        lsb.newId_ic.push(robId[0])
                        lsb.inst_id.push(res.id)

        rs.async_called()
        rob.async_called()

class DCache(Module):
    def __init__(self, cacheSize, init_file):
        super().__init__(ports={
            'newAddr':Port(Bits(32)),
            'wdata':Port(Bits(32)),
            'newType':Port(Bits(1)) # sb-25 ; sh-26 ; sw-27
        })
        self.cacheSize = cacheSize
        self.sram = SRAM(32, 1<<16, init_file)
        self.itemAddr = ValArray(Bits(32), cacheSize, self)
        self.itemValue = ValArray(Bits(32), cacheSize, self)
        self.itemStatus = ValArray(Bits(1), cacheSize, self) # 0-request not sent; 1-value prepared
        self.l = RegArray(Bits(32), 1)
        self.r = RegArray(Bits(32), 1)

    def full(self):
        return (self.r[0] + Bits(32)(1)) % Bits(32)(self.cacheSize) == self.l[0]

    def empty(self):
        return self.l[0] == self.r[0]

    def push(self, newAddr, newValue, prepared):
        (self.r & self)[0] <= (self.r[0] + Bits(32)(1)) % Bits(32)(self.cacheSize)
        self.itemAddr[self.r[0]] = newAddr
        self.itemValue[self.r[0]] = newValue
        self.itemStatus[self.r[0]] = prepared

    def pop(self):
        (self.l & self)[0] <= (self.l[0] + Bits(32)(1)) % Bits(32)(self.cacheSize)
        self.itemAddr[self.l[0]] = Bits(32)(0)
        self.itemValue[self.l[0]] = Bits(32)(0)
        self.itemStatus[self.l[0]] = Bits(1)(0)

    def getItem(self, myAddr):
        hasItem = Bits(1)(0)
        itemStatus = Bits(1)(0)
        value = Bits(32)(0)
        for i in range(self.cacheSize):
            hit = (myAddr == self.itemAddr[i]) & checkInside(self.l[0], self.r[0], Bits(32)(i))
            hasItem = hasItem | hit
            itemStatus = itemStatus | hit.select(self.itemStatus[i], Bits(1)(0))
            value = hit.select(self.itemValue[i], value)

        return hasItem, itemStatus, value

    @module.combinational
    def build(self):
        # write when full, top priority
        we = self.full()
        addr_we = self.itemAddr[self.l[0]]
        wdata = self.itemValue[self.l[0]]
        lastAddr = RegArray(Bits(32), 1)

        with Condition(self.full()):
            self.pop()

        # request old read, second top priority
        re_old = Bits(1)(0)
        addr_re_old = Bits(32)(0)
        for i in range(self.cacheSize):
            inside = checkInside(self.l[0], self.r[0], Bits(32)(i))
            addr_re_old = ((~re_old) & (~self.itemStatus[i]) & inside).select(
                self.itemAddr[i], addr_re_old)
            re_old = re_old | ((~self.itemStatus[i]) & inside)
        re_old = re_old & (~we)

        # request new read, last top priority
        newAddr = peekWithDefault(self.newAddr, Bits(32)(0))
        newData = peekWithDefault(self.wdata, Bits(32)(0))
        newType = peekWithDefault(self.newType, Bits(1)(0)) # read-0 ; write-1 (sb, sh both need to read before write)
        hasItem = (~self.newAddr.valid()) | self.getItem(newAddr)[0]
        re_new = (~we) & (~re_old) & (~hasItem) & (~newType)
        addr_re_new = newAddr
        with Condition(self.newAddr.valid()):
            self.newAddr.pop()
            self.wdata.pop()
            self.newType.pop()
            # log('hillo {} {} {} {} {}', newAddr, newType, newData, hasItem, re_new)
            with Condition(~hasItem):
                self.push(newAddr, newData, newType)
            with Condition(hasItem & newType):
                for i in range(self.cacheSize):
                    with Condition((self.itemAddr[i] == newAddr) & self.itemStatus[i]):
                        self.itemValue[i] = newData

        addr_dram = we.select(addr_we, re_old.select(addr_re_old, re_new.select(addr_re_new, Bits(32)(0))))
        re = re_old | re_new
        self.sram.build(we, re, addr_dram, wdata)
        (lastAddr & self)[0] <= addr_dram

        # self.log()

        for i in range(self.cacheSize):
            with Condition((self.itemAddr[i] == lastAddr[0]) & (~self.itemStatus[i]) &
                           checkInside(self.l[0], self.r[0], Bits(32)(i))):
                self.itemStatus[i] = Bits(1)(1)
                self.itemValue[i] = self.sram.dout[0]


    def log(self):
        log('-'*50)
        log('range: {} {}', self.l[0], self.r[0])
        for i in range(self.cacheSize):
            log('{} {} {}', self.itemAddr[i], self.itemValue[i], self.itemStatus[i])
        log('-'*50)