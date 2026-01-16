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
    "lui","ebreak","ecall"};
    const auto id=static_cast<int>(ins);
    if(id<0||id>=40)
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

unsigned int coder(const instruction a)
{
    const unsigned int op=static_cast<int>(a.op);
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
    return 0;
}

bool isValidChar(char op)
{
    return (op>='a'&&op<='z')||(op>='0'&&op<='9')||(op=='-');
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
    "lui","ebreak","ecall"};
    for(int i=0;i<40;i++)
        if(res[i]==insName)
            return i;
    return 40;
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
    if(op<0||op>=40)
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
    return {static_cast<OP>(op),0,0,0};
}

std::vector<std::string> get_all_ins_files() {
    std::vector<std::string> ins_files;

#ifdef _WIN32
    // Windows 平台实现
    WIN32_FIND_DATA find_file_data;
    HANDLE hFind = FindFirstFile(_T("*.ins"), &find_file_data);

    // 检查查找是否成功
    if (hFind == INVALID_HANDLE_VALUE) {
        // 没有找到任何.ins文件时，GetLastError()会返回ERROR_FILE_NOT_FOUND
        DWORD error = GetLastError();
        if (error != ERROR_FILE_NOT_FOUND) {
            std::cerr << "查找.ins文件失败，错误码: " << error << std::endl;
        }
        return ins_files;
    }

    // 遍历所有匹配的文件
    do {
        // 排除目录（只保留文件）
        if (!(find_file_data.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) {
            // 将TCHAR转换为std::string
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

    // 检查遍历结束的原因（是否是正常遍历完成）
    DWORD error = GetLastError();
    if (error != ERROR_NO_MORE_FILES) {
        std::cerr << "遍历.ins文件失败，错误码: " << error << std::endl;
    }

    // 关闭查找句柄
    FindClose(hFind);

#else
    // Linux/macOS 平台实现
    DIR* dir = opendir(".");  // 打开当前目录
    if (dir == nullptr) {
        std::cerr << "打开当前目录失败: " << strerror(errno) << std::endl;
        return ins_files;
    }

    struct dirent* entry;
    // 遍历目录中的每个条目
    while ((entry = readdir(dir)) != nullptr) {
        // 跳过目录（只处理文件）
        if (entry->d_type != DT_REG) {
            continue;
        }

        // 获取文件名并检查后缀是否为.ins
        std::string filename = entry->d_name;
        size_t dot_pos = filename.find_last_of('.');
        if (dot_pos != std::string::npos && filename.substr(dot_pos) == ".ins") {
            ins_files.push_back(filename);
        }
    }

    closedir(dir);  // 关闭目录
#endif

    return ins_files;
}

int main(int argc,char *argv[])
{
	if(argc==3)
	{
        ifstream ifs(argv[1]);
        ofstream ofs(argv[2]);
        string input;
        string result;
        while(getline(ifs,input))
        {
            ofs<<hexize(coder(strToInstruction(input)))<<endl;
        }
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
            string input;
            string result;
            while(getline(ifs,input))
            {
                ofs<<hexize(coder(strToInstruction(input)))<<endl;
            }
        }
	}
	else
		throw runtime_error("1 or 3 args expected");


    return 0;
}
