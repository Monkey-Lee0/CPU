#include<bits/stdc++.h>
#ifdef _WIN32
#include <windows.h>
#include <tchar.h>
#else
#include <dirent.h>
#include <cstring>
#endif
using namespace std;

std::vector<std::string> get_all_hex_files() {
    std::vector<std::string> hex_files;
#ifdef _WIN32
    WIN32_FIND_DATA find_file_data;
    HANDLE hFind = FindFirstFile(_T("*.hex"), &find_file_data);
    if (hFind == INVALID_HANDLE_VALUE) {
        DWORD error = GetLastError();
        if (error != ERROR_FILE_NOT_FOUND) {
            std::cerr << "查找.hex文件失败，错误码: " << error << std::endl;
        }
        return hex_files;
    }
    do {
        if (!(find_file_data.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) {
#ifdef UNICODE
            char filename[MAX_PATH];
            WideCharToMultiByte(CP_ACP, 0, find_file_data.cFileName, -1,
                                filename, MAX_PATH, NULL, NULL);
            hex_files.push_back(std::string(filename));
#else
            hex_files.push_back(std::string(find_file_data.cFileName));
#endif
        }
    } while (FindNextFile(hFind, &find_file_data) != 0);
    DWORD error = GetLastError();
    if (error != ERROR_NO_MORE_FILES) {
        std::cerr << "遍历.hex文件失败，错误码: " << error << std::endl;
    }
    FindClose(hFind);
#else
    DIR* dir = opendir(".");
    if (dir == nullptr) {
        std::cerr << "打开当前目录失败: " << strerror(errno) << std::endl;
        return hex_files;
    }
    struct dirent* entry;
    while ((entry = readdir(dir)) != nullptr) {
        if (entry->d_type != DT_REG) {
            continue;
        }
        std::string filename = entry->d_name;
        size_t dot_pos = filename.find_last_of('.');
        if (dot_pos != std::string::npos && filename.substr(dot_pos) == ".hex") {
            hex_files.push_back(filename);
        }
    }
    closedir(dir);
#endif
    return hex_files;
}

inline char decToHexSingle(const unsigned int dec)
{
    if(dec<10)
        return dec+'0';
    return dec-10+'A';
}
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

void solve_single(ifstream& ifs, ofstream& ofs)
{
    vector<unsigned int> hex;
    unsigned int addr=0;
    char ch[50];
    while(ifs>>ch)
    {
    cout<<addr<<" "<<ch<<endl;
        if(ch[0]=='@')
        {
            int oldAddr=0;
            addr=0;
            const int len=strlen(ch);
            for(int i=1;i<len;i++)
                addr=(addr<<4)+singleHexToDec(ch[i]);
            while(oldAddr!=addr)
                hex.push_back(0), oldAddr++;
            continue;
        }
        hex.push_back((singleHexToDec(ch[0])<<4)|singleHexToDec(ch[1]));
        addr++;
    }
    while(addr%4)
        hex.push_back(0), addr++;
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
        std::vector<std::string> hex_files = get_all_hex_files();
        for(auto str:hex_files)
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
