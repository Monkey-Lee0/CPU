#include<bits/stdc++.h>
#ifdef _WIN32
#include <windows.h>
#include <tchar.h>
#else
#include <dirent.h>
#include <cstring>
#endif
using namespace std;

const bool pseudo=true;

enum class OP
{
    NONE,ADD,SUB,AND,OR,XOR,SLL,SRL,SRA,SLT,SLTU,ADDI,ANDI,ORI,XORI,SLLI,SRLI,SRAI,SLTI,SLTIU,LB,LBU,LH,LHU,LW,SB,SH,SW,
    BEQ,BGE,BGEU,BLT,BLTU,BNE,JAL,JALR,AUIPC,LUI,EBREAK,ECALL
};
enum class REG
{
    ZERO,RA,SP,GP,TP,T0,T1,T2,S0,S1,A0,A1,A2,A3,A4,A5,A6,A7,S2,S3,S4,S5,S6,S7,S8,S9,S10,S11,T3,T4,T5,T6
};

class instruction
{
public:
    OP op;//name of operation
    int p0;//rd or something else
    int p1;//rs1 or something else
    int p2;//rs2 or something else
    instruction():op(OP::NONE),p0(0),p1(0),p2(0){}
    instruction(const OP op, const int p0, const int p1, const int p2):
        op(op),p0(p0),p1(p1),p2(p2){}
    explicit instruction(const int a):op(static_cast<OP>(a)),p0(0),p1(0),p2(0){}
};
inline unsigned int singleHexToDec(const char s)
{
    if(s>='0'&&s<='9')
        return s-'0';
    if(s>='A'&&s<='F')
        return s-'A'+10;
    if(s>='a'&&s<='f')
        return s-'a'+10;
    return -1;
}
inline string regName(const int id)
{
    static const string res[]={"zero","ra","sp","gp","tp","t0","t1","t2","s0","s1",
    "a0","a1","a2","a3","a4","a5","a6","a7","s2","s3","s4","s5","s6","s7",
    "s8","s9","s10","s11","t3","t4","t5","t6"};
    if(id>=32||id<0)
        return "ukReg-"+to_string(id);
    return res[id];
}
inline string insName(const OP ins)
{
    static const string res[]={"","add","sub","and","or","xor","sll","srl","sra","slt","sltu",
    "addi","andi","ori","xori","slli","srli","srai","slti","sltiu","lb","lbu","lh","lhu",
    "lw","sb","sh","sw","beq","bge","bgeu","blt","bltu","bne","jal","jalr","auipc",
    "lui","ebreak","ecall","c.addi","c.li","c.lui","c.mv","c.add","c.lw","c.sw","c.j",
    "c.jal","c.beqz","c.bnez","c.addi16sp","c.lwsp","c.swsp","c.nop","c.ebreak","c.addi4spn","c.slli","c.srli",
    "c.srai","c.andi","c.sub","c.xor","c.or","c.and","c.jr","c.jalr","mul","mulh","mulhsu","mulhu","div","divu",
    "rem","remu"};
    const auto id=static_cast<int>(ins);
    if(id<0||id>=75)
        return "ukIns-"+to_string(id);
    return res[id];
}
inline ostream& operator<<(ostream& os,const instruction& other)
{
    const string& s=insName(other.op);
    if(pseudo)
    {
        if(s=="beq"&&other.p2==0)
            return os<<"beqz"<<" "<<regName(other.p1)<<" "<<other.p0;
        if(s=="blt"&&other.p2==0)
            return os<<"bltz"<<" "<<regName(other.p1)<<" "<<other.p0;
        if(s=="bge"&&other.p2==0)
            return os<<"bgez"<<" "<<regName(other.p1)<<" "<<other.p0;
        if(s=="bge"&&other.p1==0)
            return os<<"blez"<<" "<<regName(other.p2)<<" "<<other.p0;
        if(s=="bne"&&other.p2==0)
            return os<<"bnez"<<" "<<regName(other.p1)<<" "<<other.p0;
        if(s=="jal"&&other.p0==0)
            return os<<"j"<<" "<<other.p1;
        if(s=="jal"&&other.p0==1)
            return os<<"jal"<<" "<<other.p1;
        if(s=="jalr"&&other.p0==0&&other.p1==1&&other.p2==0)
            return os<<"ret";
        if(s=="jalr"&&other.p0==0&&other.p2==0)
            return os<<"jr"<<" "<<regName(other.p1);
        if(s=="addi"&&other.p0==0&&other.p1==0&&other.p2==0)
            return os<<"nop";
        if(s=="addi"&&other.p1==0)
            return os<<"li"<<" "<<regName(other.p0)<<" "<<other.p2;
        if(s=="addi"&&other.p2==0)
            return os<<"mv"<<" "<<regName(other.p0)<<" "<<regName(other.p1);
        if(s=="sub"&&other.p1==0)
            return os<<"neg"<<" "<<regName(other.p0)<<" "<<regName(other.p2);
        if(s=="xor"&&other.p2==-1)
            return os<<"not"<<" "<<regName(other.p0)<<" "<<regName(other.p1);
    }
    os<<s;
    if(s=="add"||s=="sub"||s=="and"||s=="or"||s=="xor"||s=="sll"||s=="srl"||s=="sra"||s=="slt"||s=="sltu")
        os<<" "<<regName(other.p0)<<" "<<regName(other.p1)<<" "<<regName(other.p2);
    else if(s=="addi"||s=="andi"||s=="ori"||s=="xori"||s=="slli"||s=="srli"||s=="srai"||s=="slti"||s=="sltiu")
        os<<" "<<regName(other.p0)<<" "<<regName(other.p1)<<" "<<other.p2;
    else if(s=="lb"||s=="lbu"||s=="lh"||s=="lhu"||s=="lw")
        os<<" "<<regName(other.p0)<<" "<<other.p2<<"("<<regName(other.p1)<<")";
    else if(s=="sb"||s=="sh"||s=="sw")
        os<<" "<<regName(other.p2)<<" "<<other.p0<<"("<<regName(other.p1)<<")";
    else if(s=="beq"||s=="bge"||s=="bgeu"||s=="blt"||s=="bltu"||s=="bne")
        os<<" "<<regName(other.p1)<<" "<<regName(other.p2)<<" "<<other.p0;
    else if(s=="jal")
        os<<" "<<regName(other.p0)<<" "<<other.p1;
    else if(s=="jalr")
        os<<" "<<regName(other.p0)<<" "<<regName(other.p1)<<" "<<other.p2;
    else if(s=="auipc"||s=="lui")
        os<<" "<<regName(other.p0)<<" "<<other.p1;
    return os;
}

inline char decToHexSingle(const unsigned int dec)
{
    if(dec<10)
        return dec+'0';
    return dec-10+'A';
}
inline string hexize(unsigned int ins)
{
    string res;
    for(int i=0;i<4;i++)
    {
        // if(i)
        //     res.push_back(' ');
        res.push_back(decToHexSingle(ins&15));
        res.push_back(decToHexSingle((ins>>4)&15));
        ins>>=8;
    }
    reverse(res.begin(),res.end());
    return res;
}
inline string binarize(const unsigned int ins)
{
    string res;
    for(int i=31;i>=0;i--)
        res.push_back('0'+((ins>>i)&1));
    return res;
}
struct rule
{
    unsigned int num;
    int l,r,L,R;
    rule(unsigned int a,int b,int c,int d,int e):num(a),l(b),r(c),L(d),R(e){}
    rule(unsigned int a,int b,int c):num(a),l(0),r(31),L(b),R(c){}
};
inline unsigned int mergeBit(vector<rule> rules)
{
    unsigned ans=0;
    for(auto [num,l,r,L,R]:rules)
        if(r-l+1==32)
            ans|=(num<<L);
        else
            ans|=((num>>l)&((1u<<(r-l+1))-1u))<<L;
    return ans;
}
inline unsigned int sext(int val,int bit)
{
    return static_cast<unsigned int>(val<<(32-bit))>>(32-bit);
}
unsigned int coder(const instruction a)
{
    const int op=static_cast<int>(a.op);
    if(op>=1&&op<=10)
    {
        const unsigned int p0=static_cast<unsigned int>(a.p0<<27)>>27,p1=static_cast<unsigned int>(a.p1<<27)>>27,
            p2=static_cast<unsigned int>(a.p2<<27)>>27;
        if(op==1)
            return (0b0110011)|(p0<<7)|(0b000<<12)|(p1<<15)|(p2<<20)|(0b0000000<<25);
        if(op==2)
            return (0b0110011)|(p0<<7)|(0b000<<12)|(p1<<15)|(p2<<20)|(0b0100000<<25);
        if(op==3)
            return (0b0110011)|(p0<<7)|(0b111<<12)|(p1<<15)|(p2<<20)|(0b0000000<<25);
        if(op==4)
            return (0b0110011)|(p0<<7)|(0b110<<12)|(p1<<15)|(p2<<20)|(0b0000000<<25);
        if(op==5)
            return (0b0110011)|(p0<<7)|(0b100<<12)|(p1<<15)|(p2<<20)|(0b0000000<<25);
        if(op==6)
            return (0b0110011)|(p0<<7)|(0b001<<12)|(p1<<15)|(p2<<20)|(0b0000000<<25);
        if(op==7)
            return (0b0110011)|(p0<<7)|(0b101<<12)|(p1<<15)|(p2<<20)|(0b0000000<<25);
        if(op==8)
            return (0b0110011)|(p0<<7)|(0b101<<12)|(p1<<15)|(p2<<20)|(0b0100000<<25);
        if(op==9)
            return (0b0110011)|(p0<<7)|(0b010<<12)|(p1<<15)|(p2<<20)|(0b0000000<<25);
        if(op==10)
            return (0b0110011)|(p0<<7)|(0b011<<12)|(p1<<15)|(p2<<20)|(0b0000000<<25);
    }
    if((op>=11&&op<=14)||(op>=18&&op<=19))
    {
        const unsigned int p0=static_cast<unsigned int>(a.p0<<27)>>27,p1=static_cast<unsigned int>(a.p1<<27)>>27,
            p2=static_cast<unsigned int>(a.p2<<20)>>20;
        if(op==11)
            return (0b0010011)|(p0<<7)|(0b000<<12)|(p1<<15)|(p2<<20);
        if(op==12)
            return (0b0010011)|(p0<<7)|(0b111<<12)|(p1<<15)|(p2<<20);
        if(op==13)
            return (0b0010011)|(p0<<7)|(0b110<<12)|(p1<<15)|(p2<<20);
        if(op==14)
            return (0b0010011)|(p0<<7)|(0b100<<12)|(p1<<15)|(p2<<20);
        if(op==18)
            return (0b0010011)|(p0<<7)|(0b010<<12)|(p1<<15)|(p2<<20);
        if(op==19)
            return (0b0010011)|(p0<<7)|(0b010<<12)|(p1<<15)|(p2<<20);
    }
    if(op>=15&&op<=17)
    {
        const unsigned int p0=static_cast<unsigned int>(a.p0<<27)>>27,p1=static_cast<unsigned int>(a.p1<<27)>>27,
            p2=static_cast<unsigned int>(a.p2<<27)>>27;
        if(op==15)
            return (0b0010011)|(p0<<7)|(0b001<<12)|(p1<<15)|(p2<<20)|(0b0000000<<25);
        if(op==16)
            return (0b0010011)|(p0<<7)|(0b101<<12)|(p1<<15)|(p2<<20)|(0b0000000<<25);
        if(op==17)
            return (0b0010011)|(p0<<7)|(0b101<<12)|(p1<<15)|(p2<<20)|(0b0100000<<25);
    }
    if(op>=20&&op<=24)
    {
        const unsigned int p0=static_cast<unsigned int>(a.p0<<27)>>27,p1=static_cast<unsigned int>(a.p1<<27)>>27,
            p2=static_cast<unsigned int>(a.p2<<20)>>20;
        if(op==20)
            return (0b0000011)|(p0<<7)|(0b000<<12)|(p1<<15)|(p2<<20);
        if(op==21)
            return (0b0000011)|(p0<<7)|(0b100<<12)|(p1<<15)|(p2<<20);
        if(op==22)
            return (0b0000011)|(p0<<7)|(0b001<<12)|(p1<<15)|(p2<<20);
        if(op==23)
            return (0b0000011)|(p0<<7)|(0b101<<12)|(p1<<15)|(p2<<20);
        if(op==24)
            return (0b0000011)|(p0<<7)|(0b010<<12)|(p1<<15)|(p2<<20);
    }
    if(op>=25&&op<=27)
    {
        const unsigned int p0=static_cast<unsigned int>(a.p0<<20)>>20,p1=static_cast<unsigned int>(a.p1<<27)>>27,
            p2=static_cast<unsigned int>(a.p2<<27)>>27;
        const unsigned int p0H=p0>>5,p0L=p0&31;
        if(op==25)
            return (0b0100011)|(p0L<<7)|(0b000<<12)|(p1<<15)|(p2<<20)|(p0H<<25);
        if(op==26)
            return (0b0100011)|(p0L<<7)|(0b001<<12)|(p1<<15)|(p2<<20)|(p0H<<25);
        if(op==27)
            return (0b0100011)|(p0L<<7)|(0b010<<12)|(p1<<15)|(p2<<20)|(p0H<<25);
    }
    if(op>=28&&op<=33)
    {
        const unsigned int p0=static_cast<unsigned int>(a.p0<<19)>>19,p1=static_cast<unsigned int>(a.p1<<27)>>27,
            p2=static_cast<unsigned int>(a.p2<<27)>>27;
        const unsigned int p0H=((p0>>5)&63)|((p0&(1<<12))>>6),p0L=(p0&31)|((p0&(1<<11))>>11);
        if(op==28)
            return (0b1100011)|(p0L<<7)|(0b000<<12)|(p1<<15)|(p2<<20)|(p0H<<25);
        if(op==29)
            return (0b1100011)|(p0L<<7)|(0b101<<12)|(p1<<15)|(p2<<20)|(p0H<<25);
        if(op==30)
            return (0b1100011)|(p0L<<7)|(0b111<<12)|(p1<<15)|(p2<<20)|(p0H<<25);
        if(op==31)
            return (0b1100011)|(p0L<<7)|(0b100<<12)|(p1<<15)|(p2<<20)|(p0H<<25);
        if(op==32)
            return (0b1100011)|(p0L<<7)|(0b110<<12)|(p1<<15)|(p2<<20)|(p0H<<25);
        if(op==33)
            return (0b1100011)|(p0L<<7)|(0b001<<12)|(p1<<15)|(p2<<20)|(p0H<<25);
    }
    if(op==34)
    {
        const unsigned int p0=static_cast<unsigned int>(a.p0<<27)>>27,p1=static_cast<unsigned int>(a.p1<<11)>>11;
        const unsigned int pr=((p1>>12)&255)|((p1&(1<<11))>>3)|(((p1>>1)&1023)<<9)|((p1&(1<<20))>>1);
        return (0b1101111)|(p0<<7)|(pr<<12);
    }
    if(op==35)
    {
        const unsigned int p0=static_cast<unsigned int>(a.p0<<27)>>27,p1=static_cast<unsigned int>(a.p1<<27)>>27,
            p2=static_cast<unsigned int>(a.p2<<20)>>20;
        return (0b1100111)|(p0<<7)|(0b000<<12)|(p1<<15)|(p2<<20);
    }
    if(op>=36&&op<=37)
    {
        const unsigned int p0=static_cast<unsigned int>(a.p0<<27)>>27,p1=static_cast<unsigned int>(a.p1<<12)>>12;
        if(op==36)
            return (0b0010111)|(p0<<7)|(p1<<12);
        if(op==37)
            return (0b0110111)|(p0<<7)|(p1<<12);
    }
    if(op==38)
        return 0b000000000000001110011;
    if(op==39)
        return 0b100000000000001110011;
    if(op==40)
        return mergeBit({
            {0b01,0,1},
            {sext(a.p1,6),0,4,2,6},
            {a.p0,0,4,7,11},
            {sext(a.p1,6),5,5,12,12},
            {0b000,13,15}
        });
    if(op==41)
        return mergeBit({
            {0b01,0,1},
            {sext(a.p1,6),0,4,2,6},
            {a.p0,0,4,7,11},
            {sext(a.p1,6),5,5,12,12},
            {0b010,13,15}
        });
    if(op==42)
        return mergeBit({
            {0b01,0,1},
            {a.p1,0,4,2,6},
            {a.p0,0,4,7,11},
            {a.p1,5,5,12,12},
            {0b011,13,15}
        });
    if(op==43)  
        return mergeBit({
            {0b10,0,1},
            {a.p0,0,4,2,6},
            {a.p2,0,4,7,11},
            {0b1000,12,15}
        });
    if(op==44)
        return mergeBit({
            {0b10,0,1},
            {a.p0,0,4,2,6},
            {a.p2,0,4,7,11},
            {0b1001,12,15}
        });
    if(op==45)
        return mergeBit({
            {0b00,0,1},
            {a.p0,0,2,2,4},
            {sext(a.p2,7),6,6,5,5},
            {sext(a.p2,7),2,2,6,6},
            {a.p1,0,2,7,9},
            {sext(a.p2,7),3,5,10,12},
            {0b010,13,15}
        });
    if(op==46)
        return mergeBit({
            {0b00,0,1},
            {a.p2,0,2,2,4},
            {sext(a.p0,7),6,6,5,5},
            {sext(a.p0,7),2,2,6,6},
            {a.p1,0,2,7,9},
            {sext(a.p0,7),3,5,10,12},
            {0b110,13,15}
        });
    if(op==47)
    {
        auto imm=sext(a.p0,12);
        return mergeBit({
            {0b01,0,1},
            {imm,5,5,2,2},
            {imm,1,3,3,5},
            {imm,7,7,6,6},
            {imm,6,6,7,7},
            {imm,10,10,8,8},
            {imm,8,9,9,10},
            {imm,4,4,11,11},
            {imm,11,11,12,12},
            {0b101,13,15}
        });
    }
    if(op==48)
    {
        auto imm=sext(a.p0,12);
        return mergeBit({
            {0b01,0,1},
            {imm,5,5,2,2},
            {imm,1,3,3,5},
            {imm,7,7,6,6},
            {imm,6,6,7,7},
            {imm,10,10,8,8},
            {imm,8,9,9,10},
            {imm,4,4,11,11},
            {imm,11,11,12,12},
            {0b001,13,15}
        });
    }
    if(op==49)
    {
        auto imm=sext(a.p2,9);
        return mergeBit({
            {0b01,0,1},
            {imm,5,5,2,2},
            {imm,1,2,3,4},
            {imm,6,7,5,6},
            {a.p1,0,2,7,9},
            {imm,3,4,10,11},
            {imm,8,8,12,12},
            {0b110,13,15}
        });
    }
    if(op==50)
    {
        auto imm=sext(a.p2,9);
        return mergeBit({
            {0b01,0,1},
            {imm,5,5,2,2},
            {imm,1,2,3,4},
            {imm,6,7,5,6},
            {a.p1,0,2,7,9},
            {imm,3,4,10,11},
            {imm,8,8,12,12},
            {0b111,13,15},
        });
    }
    if(op==51)
    {
        auto imm=sext(a.p0,10);
        return mergeBit({
            {0b01,0,1},
            {imm,5,5,2,2},
            {imm,7,8,3,4},
            {imm,6,6,5,5},
            {imm,4,4,6,6},
            {0b00010,7,11},
            {imm,9,9,12,12},
            {0b011,13,15}
        });
    }
    if(op==52)
        return mergeBit({
            {0b10,0,1},
            {a.p1,6,7,2,3},
            {a.p1,2,4,4,6},
            {a.p0,0,4,7,11},
            {a.p1,5,5,12,12},
            {0b010,13,15}
        });
    if(op==53)
        return mergeBit({
            {0b10,0,1},
            {a.p2,0,4,2,6},
            {a.p1,6,7,7,8},
            {a.p1,2,5,9,12},
            {0b110,13,15}
        });
    if(op==54)
        return 0b0000000000000001;
    if(op==55)
        return 0b1001000000000010;
    if(op==56)
        return mergeBit({
            {0b00,0,1},
            {a.p0,0,2,2,4},
            {a.p1,3,3,5,5},
            {a.p1,2,2,6,6},
            {a.p1,6,9,7,10},
            {a.p1,4,5,11,12},
            {0b000,13,15}
        });
    if(op==57)
        return mergeBit({
            {0b10,0,1},
            {a.p1,0,4,2,6},
            {a.p0,0,4,7,11},
            {a.p1,5,5,12,12},
            {0b000,13,15}
        });
    if(op==58)
        return mergeBit({
            {0b01,0,1},
            {a.p1,0,4,2,6},
            {a.p0,0,2,7,9},
            {0b00,10,11},
            {a.p1,5,5,12,12},
            {0b100,13,15}
        });
    if(op==59)
        return mergeBit({
            {0b01,0,1},
            {a.p1,0,4,2,6},
            {a.p0,0,2,7,9},
            {0b01,10,11},
            {a.p1,5,5,12,12},
            {0b100,13,15}
        });
    if(op==60)
        return mergeBit({
            {0b01,0,1},
            {a.p1,0,4,2,6},
            {a.p0,0,2,7,9},
            {0b10,10,11},
            {a.p1,5,5,12,12},
            {0b100,13,15}
        });
    if(op==61)
        return mergeBit({
            {0b01,0,1},
            {a.p2,0,2,2,4},
            {0b00,5,6},
            {a.p0,0,2,7,9},
            {0b100011,10,15}
        });
    if(op==62)
        return mergeBit({
            {0b01,0,1},
            {a.p2,0,2,2,4},
            {0b01,5,6},
            {a.p0,0,2,7,9},
            {0b100011,10,15}
        });
    if(op==63)
        return mergeBit({
            {0b01,0,1},
            {a.p2,0,2,2,4},
            {0b10,5,6},
            {a.p0,0,2,7,9},
            {0b100011,10,15}
        });
    if(op==64)
        return mergeBit({
            {0b01,0,1},
            {a.p2,0,2,2,4},
            {0b11,5,6},
            {a.p0,0,2,7,9},
            {0b100011,10,15}
        });
    if(op==65)
        return mergeBit({
            {0b0000010,0,6},
            {a.p1,0,4,7,11},
            {0b1000,12,15}
        });
    if(op==66)
        return mergeBit({
            {0b0000010,0,6},
            {a.p1,0,4,7,11},
            {0b1001,12,15}
        });
    if(op<=74)
    {
        int funct3=0;
        if(op==67)
            funct3=0b000;
        if(op==68)
            funct3=0b001;
        if(op==69)
            funct3=0b010;
        if(op==70)
            funct3=0b011;
        if(op==71)
            funct3=0b100;
        if(op==72)
            funct3=0b101;
        if(op==73)
            funct3=0b110;
        if(op==74)
            funct3=0b111;
        return mergeBit({
            {0b0110011,0,6},
            {a.p0,0,4,7,11},
            {funct3,0,2,12,14},
            {a.p1,0,4,15,19},
            {a.p2,0,4,20,24},
            {0b0000001,25,31}
        });
    }
    return 0;
}

bool isValidChar(char op)
{
    return (op>='a'&&op<='z')||(op>='0'&&op<='9')||(op=='-')||(op=='.');
}

inline string tokenTaker(string& a)
{
    int l=0;
    while(l!=a.size()&&(!isValidChar(a[l])))
        l++;
    int r=l;
    while(r!=a.size()&&isValidChar(a[r]))
        r++;
    auto res=a.substr(l,r-l);
    a=a.substr(r);
    return res;
}

inline int regID(const string& regName)
{
    static const string res[]={"zero","ra","sp","gp","tp","t0","t1","t2","s0","s1",
    "a0","a1","a2","a3","a4","a5","a6","a7","s2","s3","s4","s5","s6","s7",
    "s8","s9","s10","s11","t3","t4","t5","t6"};
    for(int i=0;i<32;i++)
        if(res[i]==regName)
            return i;
    return 32;
}

inline int insID(const string& insName)
{
    static const string res[]={"","add","sub","and","or","xor","sll","srl","sra","slt","sltu",
    "addi","andi","ori","xori","slli","srli","srai","slti","sltiu","lb","lbu","lh","lhu",
    "lw","sb","sh","sw","beq","bge","bgeu","blt","bltu","bne","jal","jalr","auipc",
    "lui","ebreak","ecall","c.addi","c.li","c.lui","c.mv","c.add","c.lw","c.sw","c.j",
    "c.jal","c.beqz","c.bnez","c.addi16sp","c.lwsp","c.swsp","c.nop","c.ebreak","c.addi4spn","c.slli","c.srli",
    "c.srai","c.andi","c.sub","c.xor","c.or","c.and","c.jr","c.jalr","mul","mulh","mulhsu","mulhu","div","divu",
    "rem","remu"};
    for(int i=0;i<75;i++)
        if(res[i]==insName)
            return i;
    return 75;
}

inline instruction strToInstruction(string str)
{
    const string OP_s=tokenTaker(str),s1=tokenTaker(str),s2=tokenTaker(str),s3=tokenTaker(str);
    if(pseudo)
    {
        if(OP_s=="beqz")
            return {static_cast<OP>(28),stoi(s2),regID(s1),0};
        if(OP_s=="bltz")
            return {static_cast<OP>(31),stoi(s2),regID(s1),0};
        if(OP_s=="bgez")
            return {static_cast<OP>(29), stoi(s2),regID(s1),0};
        if(OP_s=="blez")
            return {static_cast<OP>(29), stoi(s2),0,regID(s1)};
        if(OP_s=="bnez")
            return {static_cast<OP>(33), stoi(s2),regID(s1),0};
        if(OP_s=="j")
            return {static_cast<OP>(34), 0,stoi(s1),0};
        if(OP_s=="jal"&&s2.empty())
            return {static_cast<OP>(33), 1,stoi(s1),0};
        if(OP_s=="jr")
            return {static_cast<OP>(35), 0,regID(s1),0};
        if(OP_s=="li")
            return {static_cast<OP>(11), regID(s1),0,stoi(s2)};
        if(OP_s=="mv")
            return {static_cast<OP>(11), regID(s1),regID(s2),0};
        if(OP_s=="neg")
            return {static_cast<OP>(2),regID(s1),0,regID(s2)};
        if(OP_s=="nop")
            return {static_cast<OP>(11), 0,0,0};
        if(OP_s=="not")
            return {static_cast<OP>(14), regID(s1),regID(s2),-1};
        if(OP_s=="ret")
            return {static_cast<OP>(35), 0,1,0};
    }
    int op=insID(OP_s);
    if(op<0||op>=75)
        return {static_cast<OP>(0),0,0,0};
    if(op<=10)
        return {static_cast<OP>(op),regID(s1),regID(s2),regID(s3)};
    if(op<=19)
        return {static_cast<OP>(op),regID(s1),regID(s2),stoi(s3)};
    if(op<=24)
        return {static_cast<OP>(op),regID(s1),regID(s3),stoi(s2)};
    if(op<=27)
        return {static_cast<OP>(op),stoi(s2),regID(s3),regID(s1)};
    if(op<=33)
        return {static_cast<OP>(op),stoi(s3),regID(s1),regID(s2)};
    if(op<=34)
        return {static_cast<OP>(op),regID(s1),stoi(s2),0};
    if(op<=35)
        return {static_cast<OP>(op),regID(s1),regID(s2),stoi(s3)};
    if(op<=37)
        return {static_cast<OP>(op),regID(s1),stoi(s2),0};
    if(op<=39)
        return {static_cast<OP>(op),0,0,0};
    if(op<=42)
        return {static_cast<OP>(op),regID(s1),stoi(s2),0};
    if(op<=44)
        return {static_cast<OP>(op),regID(s1),0,regID(s2)};
    if(op<=45)
        return {static_cast<OP>(op),regID(s1),regID(s3),stoi(s2)};
    if(op<=46)
        return {static_cast<OP>(op),stoi(s2),regID(s3),regID(s1)};
    if(op<=48)
        return {static_cast<OP>(op),stoi(s1),0,0};
    if(op<=50)
        return {static_cast<OP>(op),0,regID(s1),stoi(s2)};
    if(op<=51)
        return {static_cast<OP>(op),stoi(s1),0,0};
    if(op<=52)
        return {static_cast<OP>(op),regID(s1),stoi(s2),0};
    if(op<=53)
        return {static_cast<OP>(op),0,stoi(s2),regID(s1)};
    if(op<=55)
        return {static_cast<OP>(op),0,0,0};
    if(op<=60)
        return {static_cast<OP>(op),regID(s1),stoi(s2),0};
    if(op<=64)
        return {static_cast<OP>(op),regID(s1),0,regID(s2)};
    if(op<=66)
        return {static_cast<OP>(op),0,regID(s1),0};
    if(op<=74)
        return {static_cast<OP>(op),regID(s1),regID(s2),regID(s3)};
    return {static_cast<OP>(op),0,0,0};
}

std::vector<std::string> get_all_ins_files() {
    std::vector<std::string> ins_files;
#ifdef _WIN32
    WIN32_FIND_DATA find_file_data;
    HANDLE hFind = FindFirstFile(_T("*.ins"), &find_file_data);
    if (hFind == INVALID_HANDLE_VALUE) {
        DWORD error = GetLastError();
        if (error != ERROR_FILE_NOT_FOUND) {
            std::cerr << "查找.ins文件失败，错误码: " << error << std::endl;
        }
        return ins_files;
    }
    do {
        if (!(find_file_data.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) {
#ifdef UNICODE
            char filename[MAX_PATH];
            WideCharToMultiByte(CP_ACP, 0, find_file_data.cFileName, -1,
                                filename, MAX_PATH, NULL, NULL);
            ins_files.push_back(std::string(filename));
#else
            ins_files.push_back(std::string(find_file_data.cFileName));
#endif
        }
    } while (FindNextFile(hFind, &find_file_data) != 0);
    DWORD error = GetLastError();
    if (error != ERROR_NO_MORE_FILES) {
        std::cerr << "遍历.ins文件失败，错误码: " << error << std::endl;
    }
    FindClose(hFind);
#else
    DIR* dir = opendir(".");
    if (dir == nullptr) {
        std::cerr << "打开当前目录失败: " << strerror(errno) << std::endl;
        return ins_files;
    }
    struct dirent* entry;
    while ((entry = readdir(dir)) != nullptr) {
        if (entry->d_type != DT_REG) {
            continue;
        }
        std::string filename = entry->d_name;
        size_t dot_pos = filename.find_last_of('.');
        if (dot_pos != std::string::npos && filename.substr(dot_pos) == ".ins") {
            ins_files.push_back(filename);
        }
    }
    closedir(dir);
#endif
    return ins_files;
}

void solve_single(ifstream &ifs,ofstream &ofs)
{
    string input;
    vector<unsigned int> hex;
    while(getline(ifs,input))
    {
        auto p=strToInstruction(input);
        auto result=coder(p);
            if(static_cast<int>(p.op)<=39||static_cast<int>(p.op)>=67)
        {
            hex.push_back(result&255);result>>=8;
            hex.push_back(result&255);result>>=8;
            hex.push_back(result&255);result>>=8;
            hex.push_back(result&255);result>>=8;
        }
        else
        {
            hex.push_back(result&255);result>>=8;
            hex.push_back(result&255);result>>=8;
        }
    }
    while(hex.size()%4)
        hex.push_back(0);
    for(int i=0;i<(int)hex.size();i+=4)
    {
        auto result=hex[i]|(hex[i+1]<<8)|(hex[i+2]<<16)|(hex[i+3]<<24);
        ofs<<hexize(result)<<endl;
    }
}

int main(int argc,char *argv[])
{
	if(argc==3)
	{
        ifstream ifs(argv[1]);
        ofstream ofs(argv[2]);
        solve_single(ifs,ofs);
	}
	else if(argc==1)
	{
        std::vector<std::string> ins_files = get_all_ins_files();
        for(auto str:ins_files)
        {
            string str_data=str;
            str_data.pop_back();
            str_data.pop_back();
            str_data.pop_back();
            str_data+="data";
            ifstream ifs(str);
            ofstream ofs(str_data);
            solve_single(ifs,ofs);
        }
	}
	else
		throw runtime_error("1 or 3 args expected");

    return 0;
}
