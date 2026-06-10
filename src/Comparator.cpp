#include <iostream>
#include "NBT_explorer.hpp"
#include <sstream>
#include <string>
#include <vector>
#include <windows.h>
class File_Data{
    public:
        std::string World_Name;
        long long ticks;
        long long lastplayed;
        int Data_Version;
    public:
        File_Data(std::string w,long long t,long long l,int d){
            World_Name = w;
            ticks = t;
            lastplayed = l;
            Data_Version = d;
        }
        bool comparator(std::string s1 , std::string s2){
            return s1==s2;
        }
        bool comparator(int s1 , int s2){
            return s1==s2;
        }
        bool comparator(long long s1, long long s2){
            return s1==s2;
        }

};
bool compare_string(std::string s1 , std::string s2);
bool compare_integer(std::string s1 , std::string s2);
std::tuple<std::string,long long,long long,int>string_processor(const std::string &s);
int main(int argc, char* argv[]){
    if(argc!=3){
        std::cout<<"Can't access the string";
    }
    auto command1 = argv[1];
    auto command2 = argv[2];
    auto[worldname,ticks,lastplayed,dataversion] = string_processor(command1);//PASS THE OUTPUT OF MAIN
    File_Data local(worldname,ticks,lastplayed,dataversion);
    auto[worldname2,ticks2,lastplayed2,dataversion2] = string_processor(command2);
    File_Data Server(worldname2,ticks2,lastplayed2,dataversion2);

    if(!local.comparator(local.World_Name,Server.World_Name)){
        // std::cout<<"The world Names are different";
        std::cout<<"-1";
        return -1;} //NEED TO REPLACE
    else{
        if(local.comparator(local.ticks,Server.ticks)&&local.comparator(local.lastplayed,Server.lastplayed)&&local.comparator(local.Data_Version,Server.Data_Version)){
           std::cout<<"-1"; //NO REPLACEMENT NEEDED
        }
        else if(local.ticks>Server.ticks){ //LOCAL WORLD IS AHEAD
            std::cout<<"1";
        }
        else if(local.ticks<Server.ticks){ //Server World is ahead
            std::cout<<"0";
        }
    }
    return 0;
    
}
std::tuple<std::string,long long,long long,int>string_processor(const std::string &s){
    std::stringstream ss(s);
    std::string token;
    std::vector<std::string> extractedvalue;

    while (std::getline(ss, token, ',')) {
        extractedvalue.push_back(token);
    }
    if(extractedvalue.size()==4){
        std::string worldName=extractedvalue[0];
        long long ticks = std::stoll(extractedvalue[1]);
        long long lastPlayed = std::stoll(extractedvalue[2]);
        int DataVersion = std::stoi(extractedvalue[3]);
        return {worldName,ticks,lastPlayed,DataVersion};
}
return {"NOT FOUND",0,0,0};
}
bool compare_string(std::string s1 , std::string s2){
    return s1==s2;
}
bool compare_integer(int i1 , int i2 ){
    return i1==i2;

}