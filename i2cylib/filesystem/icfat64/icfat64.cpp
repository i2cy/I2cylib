// -*- coding: utf-8 -*-
// Author: Icy(enderman1024@foxmail.com)
// OS: ALL
// Name: IC FAT Virtual File System (C++ accelerated)
// Description: A light virtual file system based on FAT, v0.0.2

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <fstream>
#include <vector>
#include <string>
#include <unordered_map>
#include <random>
#include <ctime>
#include <cstring>
#include <stdexcept>
#include <iostream>
#include <algorithm>
#include <cstdint>

namespace py = pybind11;

// ==================== Constants ====================

static const std::vector<uint8_t> FAT_END  = {0xFF,0xFF,0xFF,0xFF,0xFF,0xFF};
static const std::vector<uint8_t> FAT_FREE = {0x00,0x00,0x00,0x00,0x00,0x00};
static const std::vector<uint8_t> NEXT_END = {0xFF,0xFF,0xFF};
static const std::vector<uint8_t> VERSION  = {0x00,0x00,0x01};
static const std::vector<uint8_t> MAGIC    = {'I','C','F','A','T'};
static const std::vector<uint8_t> ZERO6    = {0,0,0,0,0,0};
static const std::vector<uint8_t> ZERO32(32, 0);

// ==================== Utility Functions ====================

inline uint64_t b2i(const uint8_t* d, size_t n) {
    uint64_t r=0; for(size_t i=0;i<n;++i) r=(r<<8)|d[i]; return r;
}
inline std::vector<uint8_t> i2b(uint64_t v, size_t n) {
    std::vector<uint8_t> r(n,0);
    for(size_t i=0;i<n;++i){ r[n-1-i]=(uint8_t)(v&0xFF); v>>=8; }
    return r;
}
inline std::vector<uint8_t> bytes2vec(py::handle h) {
    std::string s=py::cast<std::string>(h);
    return std::vector<uint8_t>(s.begin(),s.end());
}
inline std::vector<uint8_t> readn(std::fstream& f, size_t n) {
    std::vector<uint8_t> b(n); f.read((char*)b.data(),n);
    if((size_t)f.gcount()!=n) throw std::runtime_error("unexpected end of file");
    return b;
}
inline void writen(std::fstream& f, const std::vector<uint8_t>& d) {
    f.write((const char*)d.data(), d.size());
}
inline void writez(std::fstream& f, size_t n) {
    std::vector<uint8_t> z(n,0); f.write((const char*)z.data(),n);
}
inline void writef(std::fstream& f, size_t n, uint8_t v) {
    std::vector<uint8_t> z(n,v); f.write((const char*)z.data(),n);
}

std::vector<std::string> decode_path(const std::string& path) {
    std::vector<std::string> paths;
    int ignore=0; std::string name;
    for(char c:path){
        if(c=='"'){ ignore=(ignore==2)?0:2; continue; }
        else if(c=='\''){
            if(ignore==1){ ignore=0; continue; }
            else if(ignore<=1){ ignore=1; continue; }
        }else if(c=='/'){
            if(ignore>0){}
            else{ paths.push_back(name); name.clear(); continue; }
        }
        name+=c;
    }
    if(!name.empty()) paths.push_back(name);
    return paths;
}

// ==================== Structs ====================

struct TagInfo {
    uint64_t length=0;
    std::vector<uint8_t> first_cluster;  // 6 bytes
    uint64_t tag_offset=0;
};

struct DirContent {
    std::unordered_map<std::string,TagInfo> files;
    std::unordered_map<std::string,TagInfo> directories;
    std::unordered_map<std::string,TagInfo> hidden_files;
};

// ==================== IcFAT ====================

class IcFAT {
public:
    class FileObject;

    IcFAT(const std::string& filename);
    ~IcFAT();

    py::dict debug();
    void check();
    py::dict list(const std::string& path);
    void release();
    void load();
    void makefs(uint64_t cluster_number, const std::string& description="",
                uint64_t cluster_length=512, const std::string& mode="flexible");
    void mkdir(const std::string& dirname);
    void remove(const std::string& filename);
    FileObject open(const std::string& filename, const std::string& mode="a", bool as_dir=false);

private:
    friend class FileObject;

    uint64_t _get_free_cluster();
    std::vector<uint8_t> _readalldata(uint64_t length, const std::vector<uint8_t>& first_cluster);
    DirContent _getfilelist(const std::vector<uint8_t>& data);
    uint64_t _get_free_tag(const std::vector<uint8_t>& data);
    void _clear_fat_chain(const std::vector<uint8_t>& first_cluster);

    std::string filename_;
    std::fstream file_;
    bool file_open_=false;

    std::vector<uint8_t> uuid_;     // 8 bytes
    std::vector<uint8_t> date_;     // 6 bytes
    std::string mode_;
    uint64_t cluster_number_=0;
    uint64_t cluster_length_=0;
    uint64_t space_total_=0;
    uint64_t start_pointer_=0;
    std::string description_;
    uint64_t free_clusters_=0;
};

// ==================== FileObject ====================

class IcFAT::FileObject {
public:
    FileObject(IcFAT* parent, const std::string& filename,
               const std::string& mode="a", bool as_dir=false);

    void debug();
    void seek(int64_t offset);
    int64_t tell();
    py::bytes read(uint64_t length=0);
    uint64_t write(const py::bytes& data);
    void close();

private:
    void _update_fat();

    IcFAT* parent_;
    std::string path_;
    std::string name_;
    uint64_t pointer_=0;
    uint64_t length_=0;
    uint64_t original_length_=0;
    std::vector<std::vector<uint8_t>> clusters_;
    std::string mode_;
    bool new_file_=false;
    bool directory_=false;
    bool closed_=false;
    uint64_t tag_offset_=0;
};

// ==================== IcFAT Implementation ====================

IcFAT::IcFAT(const std::string& filename) : filename_(filename) {
    std::ifstream t(filename, std::ios::binary);
    bool exists = t.good(); t.close();
    if(!exists){
        std::ofstream c(filename, std::ios::binary); c.close();
        makefs(16);
        release(); // makefs left the file open, close it first
    }
    file_.open(filename, std::ios::in|std::ios::out|std::ios::binary);
    if(!file_.good()) throw std::runtime_error("error while opening file: "+filename);
    file_open_=true;
    check();
}

IcFAT::~IcFAT() { if(file_open_) file_.close(); }

void IcFAT::release() {
    if(file_open_){ file_.close(); file_open_=false; }
}
void IcFAT::load() {
    if(!file_open_){
        file_.open(filename_, std::ios::in|std::ios::out|std::ios::binary);
        if(!file_.good()) throw std::runtime_error("error while opening file: "+filename_);
        file_open_=true;
    }
}

uint64_t IcFAT::_get_free_cluster() {
    load();
    file_.seekg(64+6);
    for(uint64_t i=0;i<cluster_number_;++i){
        if(readn(file_,6)==FAT_FREE) return i+1;
    }
    throw std::runtime_error("no free cluster left");
}

std::vector<uint8_t> IcFAT::_readalldata(uint64_t length, const std::vector<uint8_t>& first_cluster) {
    load();
    std::vector<uint8_t> res;
    uint64_t readed=0;
    auto cluster=first_cluster;
    while(true){
        uint64_t cn=b2i(cluster.data(),6);
        file_.seekg(start_pointer_+(cn-1)*cluster_length_);
        uint64_t to_read=(length-readed<cluster_length_)?(length-readed):cluster_length_;
        auto chunk=readn(file_,to_read);
        res.insert(res.end(),chunk.begin(),chunk.end());
        readed+=to_read;
        if(readed>=length) break;
        file_.seekg(64+cn*6);
        cluster=readn(file_,6);
        if(cluster==FAT_END||cluster==FAT_FREE) break;
    }
    return res;
}

DirContent IcFAT::_getfilelist(const std::vector<uint8_t>& data) {
    DirContent r;
    size_t n=data.size()/32;
    for(size_t off=0;off<n;++off){
        const uint8_t* tag=data.data()+off*32;
        uint8_t type=tag[0];
        if(type==255||type==3) continue;
        std::vector<uint8_t> name_bytes(tag+1,tag+17);
        auto next_tag=std::vector<uint8_t>(tag+17,tag+20);
        while(next_tag!=NEXT_END){
            uint64_t ni=b2i(next_tag.data(),3);
            if(ni>=n) break;
            const uint8_t* ct=data.data()+ni*32;
            name_bytes.insert(name_bytes.end(),ct+1,ct+29);
            next_tag=std::vector<uint8_t>(ct+29,ct+32);
        }
        name_bytes.erase(std::remove(name_bytes.begin(),name_bytes.end(),0),name_bytes.end());
        std::string name(name_bytes.begin(),name_bytes.end());
        TagInfo info;
        info.length=b2i(tag+20,6);
        info.first_cluster=std::vector<uint8_t>(tag+26,tag+32);
        info.tag_offset=off;
        if(type==1) r.directories[name]=info;
        else if(type==2) r.files[name]=info;
        else if(type==4) r.hidden_files[name]=info;
        else throw std::runtime_error("unhandled data tag: "+std::to_string(type));
    }
    return r;
}

uint64_t IcFAT::_get_free_tag(const std::vector<uint8_t>& data) {
    size_t n=data.size()/32;
    for(size_t i=0;i<n;++i) if(data[i*32]==255) return i;
    return n;
}

void IcFAT::_clear_fat_chain(const std::vector<uint8_t>& first_cluster) {
    load();
    auto cluster=first_cluster;
    std::vector<std::vector<uint8_t>> chain;
    while(cluster!=FAT_END){
        chain.push_back(cluster);
        uint64_t cn=b2i(cluster.data(),6);
        file_.seekg(64+cn*6);
        cluster=readn(file_,6);
        if(cluster==FAT_FREE) break;
    }
    for(auto& c:chain){
        uint64_t cn=b2i(c.data(),6);
        file_.seekp(64+cn*6); writen(file_,FAT_FREE);
    }
    check();
}

py::dict IcFAT::debug() {
    std::string ver;
    for(size_t i=0;i<VERSION.size();++i){ ver+=std::to_string((int)VERSION[i])+"."; }
    ver.pop_back();
    py::dict d;
    d["version"]=ver;
    d["uuid"]=py::bytes((const char*)uuid_.data(),uuid_.size());
    py::list dl;
    for(auto v:date_) dl.append((int)v);
    d["date"]=dl;
    d["mode"]=mode_;
    d["space_total"]=space_total_;
    d["cluster_length"]=cluster_length_;
    d["cluster_number"]=cluster_number_;
    d["free_clusters"]=free_clusters_;
    d["description"]=description_;
    return d;
}

void IcFAT::check() {
    load(); file_.seekg(0);
    auto head=readn(file_,5);
    if(head!=MAGIC) throw std::runtime_error("file is not a ICFAT disk file");
    auto ver=readn(file_,3);
    if(ver!=VERSION){
        throw std::runtime_error("ICFAT version mismatch: expected "+
            std::to_string(VERSION[0])+"."+std::to_string(VERSION[1])+"."+std::to_string(VERSION[2])+
            ", got "+std::to_string(ver[0])+"."+std::to_string(ver[1])+"."+std::to_string(ver[2]));
    }
    uuid_=readn(file_,8);
    date_=readn(file_,6);
    file_.seekg(23);
    auto mb=readn(file_,1); mode_=(mb[0]==0)?"standard":"flexible";
    auto cn=readn(file_,6); cluster_number_=b2i(cn.data(),6);
    auto cl=readn(file_,2); cluster_length_=b2i(cl.data(),2);
    space_total_=cluster_length_*cluster_number_;
    start_pointer_=cluster_number_*6+6+64;
    auto desc=readn(file_,32);
    desc.erase(std::remove(desc.begin(),desc.end(),0),desc.end());
    description_=std::string(desc.begin(),desc.end());
    free_clusters_=0;
    file_.seekg(64+6);
    for(uint64_t i=0;i<cluster_number_;++i){
        if(readn(file_,6)==FAT_FREE) ++free_clusters_;
    }
}

py::dict IcFAT::list(const std::string& path) {
    load();
    auto paths=decode_path(path);
    file_.seekg(start_pointer_);
    auto root_tag=readn(file_,32);
    uint64_t root_len=b2i(root_tag.data()+20,6);
    auto root_fc=std::vector<uint8_t>(root_tag.data()+26,root_tag.data()+32);
    auto root_data=_readalldata(root_len,root_fc);
    auto files=_getfilelist(root_data);
    if(!paths.empty()) paths.erase(paths.begin());
    for(auto& dn:paths){
        auto it=files.directories.find(dn);
        if(it!=files.directories.end()){
            auto dd=_readalldata(it->second.length,it->second.first_cluster);
            files=_getfilelist(dd);
        }else throw std::runtime_error("path dose not exists");
    }
    py::dict r;
    auto mkentry=[&](const auto& m)->py::dict{
        py::dict d;
        for(auto& [k,v]:m){
            py::dict i;
            i["length"]=v.length;
            i["first_cluster"]=py::bytes((const char*)v.first_cluster.data(),6);
            i["tag_offset"]=v.tag_offset;
            d[k.c_str()]=i;
        }
        return d;
    };
    r["files"]=mkentry(files.files);
    r["dirctories"]=mkentry(files.directories);
    r["hided_files"]=mkentry(files.hidden_files);
    return r;
}

void IcFAT::makefs(uint64_t cn, const std::string& desc,
                   uint64_t cl, const std::string& mode) {
    release();
    { std::ofstream t(filename_,std::ios::binary|std::ios::trunc); t.close(); }
    load(); file_.seekp(0);

    // header
    writen(file_,MAGIC);
    writen(file_,VERSION);
    uuid_.clear(); {
        std::random_device rd; std::mt19937 g(rd());
        std::uniform_int_distribution<int> d(0,255);
        for(int i=0;i<8;++i) uuid_.push_back((uint8_t)d(g));
    }
    writen(file_,uuid_);
    {
        std::time_t now=std::time(nullptr); std::tm* tm=std::localtime(&now);
        date_={(uint8_t)(tm->tm_year%100),(uint8_t)(tm->tm_mon+1),
               (uint8_t)tm->tm_mday,(uint8_t)tm->tm_hour,
               (uint8_t)tm->tm_min,(uint8_t)tm->tm_sec};
    }
    writen(file_,date_);
    writen(file_,{0x00}); // reserved
    mode_=mode; writen(file_,{(uint8_t)(mode=="flexible"?0x01:0x00)});
    cluster_number_=cn; writen(file_,i2b(cn,6));
    cluster_length_=cl; writen(file_,i2b(cl,2));
    description_=desc;
    auto db=std::vector<uint8_t>(desc.begin(),desc.end());
    if(db.size()>32) throw std::runtime_error("description length must <= 32");
    db.resize(32,0); writen(file_,db);

    // FAT header + FAT table
    writez(file_,6);
    for(uint64_t i=0;i<cn;++i) writez(file_,6);

    // first cluster data
    writez(file_,cl);

    start_pointer_=cn*6+6+64;
    // FAT[1] = END
    file_.seekp(64+1*6); writen(file_,FAT_END);
    // root tag at start_pointer_
    file_.seekp(start_pointer_);
    std::vector<uint8_t> rt(32,0);
    rt[0]=0x01; // directory
    rt[17]=0xFF;rt[18]=0xFF;rt[19]=0xFF;
    auto lb=i2b(32,6); std::copy(lb.begin(),lb.end(),rt.begin()+20);
    auto cb=i2b(1,6); std::copy(cb.begin(),cb.end(),rt.begin()+26);
    writen(file_,rt);

    if(mode=="flexible"){ check(); return; }
    // standard: fill remaining
    for(uint64_t i=0;i<cn-1;++i) writef(file_,cl,0xFF);
    check();
}

void IcFAT::mkdir(const std::string& dirname) {
    auto paths=decode_path(dirname);
    std::string name;
    if(!paths.empty()){ name=paths.back(); paths.pop_back(); }
    std::string pp="/";
    for(auto& p:paths) pp+=p+"/";
    auto listing=list(pp);
    if(listing["dirctories"].cast<py::dict>().contains(name))
        throw std::runtime_error("path already exists");
    auto d=open(pp+name,"a",true);
    d.close();
    check();
}

void IcFAT::remove(const std::string& filename) {
    load();
    auto paths=decode_path(filename);
    std::string name;
    if(!paths.empty()){ name=paths.back(); paths.pop_back(); }
    std::string pp="/";
    for(auto& p:paths) pp+=p+"/";

    auto listing=list(pp);
    auto fd=listing["files"].cast<py::dict>();
    auto dd=listing["dirctories"].cast<py::dict>();

    std::vector<uint8_t> first_cluster;
    uint64_t tag_offset;
    bool is_dir=false;

    if(fd.contains(name)){
        auto info=fd[name.c_str()].cast<py::dict>();
        first_cluster=bytes2vec(info["first_cluster"]);
        tag_offset=info["tag_offset"].cast<uint64_t>();
    }else if(dd.contains(name)){
        auto info=dd[name.c_str()].cast<py::dict>();
        first_cluster=bytes2vec(info["first_cluster"]);
        tag_offset=info["tag_offset"].cast<uint64_t>();
        is_dir=true;
    }else throw std::runtime_error("target not found");

    if(is_dir){
        if(name.empty()) throw std::runtime_error("can not remove root path");
        auto sl=list(pp+name);
        auto sf=sl["files"].cast<py::dict>();
        auto sd=sl["dirctories"].cast<py::dict>();
        std::vector<std::string> children;
        for(auto& [k,v]:sf) children.push_back(pp+name+"/"+k.cast<std::string>());
        for(auto& [k,v]:sd) children.push_back(pp+name+"/"+k.cast<std::string>());
        for(auto& c:children) remove(c);
    }

    // Open parent directory to clear tags
    auto pf=open(pp);
    auto pdata=pf.read();
    std::string ps=pdata.cast<std::string>();
    std::vector<uint8_t> pv(ps.begin(),ps.end());

    // collect tag offsets (following next_tag chain)
    std::vector<uint64_t> tags;
    tags.push_back(tag_offset);
    uint64_t cur=tag_offset;
    auto nt=std::vector<uint8_t>(pv.begin()+cur*32+17,pv.begin()+cur*32+20);
    while(nt!=NEXT_END){
        uint64_t nidx=b2i(nt.data(),3);
        if(nidx*32+32>pv.size()) break;
        tags.push_back(nidx);
        cur=nidx;
        nt=std::vector<uint8_t>(pv.begin()+cur*32+29,pv.begin()+cur*32+32);
    }

    _clear_fat_chain(first_cluster);

    for(auto off:tags){
        pf.seek(off*32);
        pf.write(py::bytes("\xff",1));
    }
    pf.close();
    check();
}

IcFAT::FileObject IcFAT::open(const std::string& filename, const std::string& mode, bool as_dir) {
    return FileObject(this,filename,mode,as_dir);
}

// ==================== FileObject Implementation ====================

IcFAT::FileObject::FileObject(IcFAT* parent, const std::string& filename,
                               const std::string& mode, bool as_dir)
    : parent_(parent), mode_(mode), directory_(as_dir)
{
    parent_->load();
    auto paths=decode_path(filename);
    if(!paths.empty()){ name_=paths.back(); paths.pop_back(); }
    path_="/";
    for(auto& p:paths) path_+=p+"/";

    auto listing=parent_->list(path_);
    auto fd=listing["files"].cast<py::dict>();
    auto dd=listing["dirctories"].cast<py::dict>();

    std::vector<uint8_t> first_cluster;
    if(fd.contains(name_)){
        auto info=fd[name_.c_str()].cast<py::dict>();
        length_=info["length"].cast<uint64_t>();
        first_cluster=bytes2vec(info["first_cluster"]);
        tag_offset_=info["tag_offset"].cast<uint64_t>();
        directory_=false;
    }else if(dd.contains(name_)){
        auto info=dd[name_.c_str()].cast<py::dict>();
        length_=info["length"].cast<uint64_t>();
        first_cluster=bytes2vec(info["first_cluster"]);
        tag_offset_=info["tag_offset"].cast<uint64_t>();
        directory_=true;
    }else{
        new_file_=true;
        length_=0;
        first_cluster=i2b(parent_->_get_free_cluster(),6);
        directory_=as_dir;
    }
    original_length_=length_;

    // build cluster chain
    parent_->load();
    auto cluster=first_cluster;
    while(cluster!=FAT_END){
        clusters_.push_back(cluster);
        uint64_t cn=b2i(cluster.data(),6);
        parent_->file_.seekg(64+cn*6);
        cluster=readn(parent_->file_,6);
        if(cluster==FAT_FREE) break;
        if(new_file_) break;
    }

    if(mode.find('w')!=std::string::npos){
        length_=0;
        if(!clusters_.empty()){
            auto first=clusters_[0];
            clusters_.clear(); clusters_.push_back(first);
            parent_->_clear_fat_chain(first);
        }
    }
    if(mode.find('a')!=std::string::npos&&!directory_) pointer_=length_;
    _update_fat();
}

void IcFAT::FileObject::debug() {
    std::cout<<"cluster chain: [";
    for(size_t i=0;i<clusters_.size();++i){
        if(i) std::cout<<", ";
        std::cout<<b2i(clusters_[i].data(),6);
    }
    std::cout<<"]"<<std::endl;
}

void IcFAT::FileObject::_update_fat() {
    if(clusters_.empty()) return;
    auto c=clusters_[0];
    for(size_t i=1;i<clusters_.size();++i){
        uint64_t cn=b2i(c.data(),6);
        parent_->file_.seekp(64+cn*6); writen(parent_->file_,clusters_[i]);
        c=clusters_[i];
    }
    uint64_t lcn=b2i(c.data(),6);
    parent_->file_.seekp(64+lcn*6); writen(parent_->file_,FAT_END);
}

void IcFAT::FileObject::seek(int64_t offset) {
    if(closed_) throw std::runtime_error("file closed");
    int64_t mx=(int64_t)length_, mn=-mx-1;
    if(offset>=mn&&offset<=mx){
        pointer_=(offset>=0)?(uint64_t)offset:(uint64_t)(mx+1+offset);
    }else{
        throw std::runtime_error("file pointer ("+std::to_string(offset)+
            ") out of range ("+std::to_string(mn)+", "+std::to_string(mx)+")");
    }
}

int64_t IcFAT::FileObject::tell() {
    if(closed_) throw std::runtime_error("file closed");
    return (int64_t)pointer_;
}

py::bytes IcFAT::FileObject::read(uint64_t length) {
    if(closed_) throw std::runtime_error("file closed");
    parent_->load();
    if(length==0||length+pointer_>length_) length=length_-pointer_;
    if(length==0||clusters_.empty()) return py::bytes("");

    std::vector<uint8_t> res;
    uint64_t left=length;
    uint64_t cidx=pointer_/parent_->cluster_length_;
    uint64_t icp=pointer_%parent_->cluster_length_;

    while(left>0&&cidx<clusters_.size()){
        uint64_t cn=b2i(clusters_[cidx].data(),6);
        uint64_t icl=parent_->cluster_length_-icp;
        uint64_t tr=(left<icl)?left:icl;
        parent_->file_.seekg(parent_->start_pointer_+(cn-1)*parent_->cluster_length_+icp);
        auto chunk=readn(parent_->file_,tr);
        res.insert(res.end(),chunk.begin(),chunk.end());
        pointer_+=tr; left-=tr; icp=0; ++cidx;
    }
    return py::bytes((const char*)res.data(),res.size());
}

uint64_t IcFAT::FileObject::write(const py::bytes& data) {
    if(closed_) throw std::runtime_error("file closed");
    if(mode_.find('r')!=std::string::npos&&mode_.find('a')==std::string::npos&&mode_.find('w')==std::string::npos)
        throw std::runtime_error("read only mode");
    parent_->load();

    std::string ds=data.cast<std::string>();
    const uint8_t* dp=(const uint8_t*)ds.data();
    uint64_t dl=ds.size(), left=dl, off=0;

    while(left>0){
        uint64_t cidx=pointer_/parent_->cluster_length_;
        while(cidx>=clusters_.size()){
            clusters_.push_back(i2b(parent_->_get_free_cluster(),6));
            _update_fat();
        }
        uint64_t cn=b2i(clusters_[cidx].data(),6);
        uint64_t icp=pointer_%parent_->cluster_length_;
        uint64_t icl=parent_->cluster_length_-icp;
        uint64_t tw=(left<icl)?left:icl;
        parent_->file_.seekp(parent_->start_pointer_+(cn-1)*parent_->cluster_length_+icp);
        parent_->file_.write((const char*)(dp+off),tw);
        pointer_+=tw; left-=tw; off+=tw;
    }
    if(pointer_>length_) length_=pointer_;
    return dl;
}

void IcFAT::FileObject::close() {
    if(closed_) throw std::runtime_error("file closed");
    closed_=true;
    if(length_==original_length_&&!new_file_) return;

    auto dir=parent_->open(path_);

    if(new_file_){
        auto dir_data=dir.read();
        std::string dds=dir_data.cast<std::string>();
        std::vector<uint8_t> dv(dds.begin(),dds.end());

        tag_offset_=parent_->_get_free_tag(dv);
        uint64_t tp=tag_offset_*32;
        if(tp+32>dv.size()) dv.resize(tp+32,0);

        // zero out the slot
        std::fill(dv.begin()+tp,dv.begin()+tp+32,0);

        // type, length, first_cluster
        dv[tp]=directory_?0x01:0x02;
        auto lb=i2b(length_,6);
        std::copy(lb.begin(),lb.end(),dv.begin()+tp+20);
        std::copy(clusters_[0].begin(),clusters_[0].end(),dv.begin()+tp+26);

        // name
        auto nb=std::vector<uint8_t>(name_.begin(),name_.end());
        size_t left=nb.size();
        size_t fnl=(left<16)?left:16;
        std::copy(nb.begin(),nb.begin()+fnl,dv.begin()+tp+1);
        for(size_t i=fnl;i<16;++i) dv[tp+1+i]=0;

        if(left<=16){
            dv[tp+17]=0xFF;dv[tp+18]=0xFF;dv[tp+19]=0xFF;
        }else{
            nb.erase(nb.begin(),nb.begin()+16); left=nb.size();
            uint64_t next_tag=parent_->_get_free_tag(dv);
            auto ntb=i2b(next_tag,3);
            std::copy(ntb.begin(),ntb.end(),dv.begin()+tp+17);
            uint64_t ct=next_tag;

            while(left>28){
                uint64_t ctp=ct*32;
                if(ctp+32>dv.size()) dv.resize(ctp+32,0);
                std::fill(dv.begin()+ctp,dv.begin()+ctp+32,0);
                dv[ctp]=0x03;
                std::copy(nb.begin(),nb.begin()+28,dv.begin()+ctp+1);
                nb.erase(nb.begin(),nb.begin()+28); left=nb.size();
                next_tag=parent_->_get_free_tag(dv);
                ntb=i2b(next_tag,3);
                std::copy(ntb.begin(),ntb.end(),dv.begin()+ctp+29);
                ct=next_tag;
            }
            uint64_t ctp=ct*32;
            if(ctp+32>dv.size()) dv.resize(ctp+32,0);
            std::fill(dv.begin()+ctp,dv.begin()+ctp+32,0);
            dv[ctp]=0x03;
            std::copy(nb.begin(),nb.end(),dv.begin()+ctp+1);
            for(size_t i=left;i<28;++i) dv[ctp+1+i]=0;
            dv[ctp+29]=0xFF;dv[ctp+30]=0xFF;dv[ctp+31]=0xFF;
        }

        dir.seek(0);
        dir.write(py::bytes((const char*)dv.data(),dv.size()));
    }else{
        dir.seek((int64_t)(tag_offset_*32+20));
        auto lb=i2b(length_,6);
        dir.write(py::bytes((const char*)lb.data(),6));
    }

    dir.close();
    parent_->check();
}

// ==================== icfat_test ====================

void icfat_test() {
    auto pystr=[](py::handle v)->std::string{return py::repr(v).cast<std::string>();};

    std::cout<<"\n■ creating a test.blk"<<std::endl;
    IcFAT blk("test.blk");
    std::cout<<"\n■ making filesystem"<<std::endl;
    blk.makefs(16384, "test_disk", 32768, "flexible");
    std::cout<<"\n■ listing details"<<std::endl;
    auto data=blk.debug();
    for(auto [k,v]:data) std::cout<<k.cast<std::string>()<<":\t"<<pystr(v)<<std::endl;

    std::cout<<"\n■ listing root path"<<std::endl;
    auto root=blk.list("/");
    std::cout<<"[files]"<<std::endl;
    for(auto [k,v]:root["files"].cast<py::dict>()) std::cout<<k.cast<std::string>()<<":"<<pystr(v)<<std::endl;
    std::cout<<"[dirctories]"<<std::endl;
    for(auto [k,v]:root["dirctories"].cast<py::dict>()) std::cout<<k.cast<std::string>()<<":"<<pystr(v)<<std::endl;

    std::cout<<"\n■ making dirctory: /test"<<std::endl;
    blk.mkdir("/test");

    std::cout<<"\n■ listing root path"<<std::endl;
    root=blk.list("/");
    std::cout<<"[files]"<<std::endl;
    for(auto [k,v]:root["files"].cast<py::dict>()) std::cout<<k.cast<std::string>()<<":"<<pystr(v)<<std::endl;
    std::cout<<"[dirctories]"<<std::endl;
    for(auto [k,v]:root["dirctories"].cast<py::dict>()) std::cout<<k.cast<std::string>()<<":"<<pystr(v)<<std::endl;

    std::cout<<"\n■ test opening new file in /test and write b\"test\""<<std::endl;
    auto f=blk.open("/test/long_filename_and_Chinese_中文_test.txt");
    f.write(py::bytes("test"));
    f.close();

    std::cout<<"\n■ listing file in /test"<<std::endl;
    auto tl=blk.list("/test");
    std::cout<<"[files]"<<std::endl;
    for(auto [k,v]:tl["files"].cast<py::dict>()) std::cout<<k.cast<std::string>()<<":"<<pystr(v)<<std::endl;
    std::cout<<"[dirctories]"<<std::endl;
    for(auto [k,v]:tl["dirctories"].cast<py::dict>()) std::cout<<k.cast<std::string>()<<":"<<pystr(v)<<std::endl;

    std::cout<<"\n■ reading the file we created just now"<<std::endl;
    f=blk.open("/test/long_filename_and_Chinese_中文_test.txt");
    std::cout<<"data: "<<f.read().cast<std::string>()<<std::endl;

    std::cout<<"\n■ creating another 2 files in /test"<<std::endl;
    f=blk.open("/test/file2"); f.close();
    f=blk.open("/test/file3"); f.close();

    std::cout<<"\n■ listing file in /test"<<std::endl;
    tl=blk.list("/test");
    std::cout<<"[files]"<<std::endl;
    for(auto [k,v]:tl["files"].cast<py::dict>()) std::cout<<k.cast<std::string>()<<":"<<pystr(v)<<std::endl;
    std::cout<<"[dirctories]"<<std::endl;
    for(auto [k,v]:tl["dirctories"].cast<py::dict>()) std::cout<<k.cast<std::string>()<<":"<<pystr(v)<<std::endl;

    std::cout<<"\n■ removing the first & second file in /test"<<std::endl;
    blk.remove("/test/long_filename_and_Chinese_中文_test.txt");
    blk.remove("/test/file2");

    std::cout<<"\n■ listing file in /test"<<std::endl;
    tl=blk.list("/test");
    std::cout<<"[files]"<<std::endl;
    for(auto [k,v]:tl["files"].cast<py::dict>()) std::cout<<k.cast<std::string>()<<":"<<pystr(v)<<std::endl;
    std::cout<<"[dirctories]"<<std::endl;
    for(auto [k,v]:tl["dirctories"].cast<py::dict>()) std::cout<<k.cast<std::string>()<<":"<<pystr(v)<<std::endl;

    std::cout<<"\n■ creating another file 'first' in /test"<<std::endl;
    f=blk.open("/test/first"); f.close();

    std::cout<<"\n■ listing file in /test"<<std::endl;
    tl=blk.list("/test");
    std::cout<<"[files]"<<std::endl;
    for(auto [k,v]:tl["files"].cast<py::dict>()) std::cout<<k.cast<std::string>()<<":"<<pystr(v)<<std::endl;
    std::cout<<"[dirctories]"<<std::endl;
    for(auto [k,v]:tl["dirctories"].cast<py::dict>()) std::cout<<k.cast<std::string>()<<":"<<pystr(v)<<std::endl;

    std::cout<<"\n■ listing details"<<std::endl;
    data=blk.debug();
    for(auto [k,v]:data) std::cout<<k.cast<std::string>()<<":\t"<<pystr(v)<<std::endl;

    f=blk.open("/test/first","w");
    f.write(py::bytes("this is the first line\n")); f.close();
    f=blk.open("/test/first","a");
    f.write(py::bytes("this is the second line\n")); f.close();
    f=blk.open("/test/first","r");
    std::cout<<"content in first test file:\n"<<f.read().cast<std::string>()<<std::endl; f.close();

    f=blk.open("/test/first","w");
    f.write(py::bytes("this is the first line\n")); f.close();
    f=blk.open("/test/first","r");
    std::cout<<"content in first test file:\n"<<f.read().cast<std::string>()<<std::endl; f.close();

    std::cout<<"\n■ removing path /test"<<std::endl;
    blk.remove("/test");

    std::cout<<"\n■ listing root path"<<std::endl;
    root=blk.list("/");
    std::cout<<"[files]"<<std::endl;
    for(auto [k,v]:root["files"].cast<py::dict>()) std::cout<<k.cast<std::string>()<<":"<<pystr(v)<<std::endl;
    std::cout<<"[dirctories]"<<std::endl;
    for(auto [k,v]:root["dirctories"].cast<py::dict>()) std::cout<<k.cast<std::string>()<<":"<<pystr(v)<<std::endl;

    std::cout<<"\n■ listing details"<<std::endl;
    data=blk.debug();
    for(auto [k,v]:data) std::cout<<k.cast<std::string>()<<":\t"<<pystr(v)<<std::endl;
}

// ==================== Module ====================

PYBIND11_MODULE(_icfat64, m) {
    m.doc()="ICFAT64 C++ accelerated virtual file system (v0.0.2)";

    py::class_<IcFAT, std::shared_ptr<IcFAT>>(m, "IcFAT")
        .def(py::init<const std::string&>(), py::arg("filename"))
        .def("debug", &IcFAT::debug)
        .def("check", &IcFAT::check)
        .def("list", &IcFAT::list, py::arg("path"))
        .def("release", &IcFAT::release)
        .def("load", &IcFAT::load)
        .def("makefs", &IcFAT::makefs,
             py::arg("cluster_number"),
             py::arg("description")="",
             py::arg("cluster_length")=512,
             py::arg("mode")="flexible")
        .def("mkdir", &IcFAT::mkdir, py::arg("dirname"))
        .def("remove", &IcFAT::remove, py::arg("filename"))
        .def("open", &IcFAT::open,
             py::arg("filename"),
             py::arg("mode")="a",
             py::arg("as_dir")=false,
             py::keep_alive<1,0>());

    py::class_<IcFAT::FileObject>(m, "FileObject")
        .def("debug", &IcFAT::FileObject::debug)
        .def("seek", &IcFAT::FileObject::seek, py::arg("offset"))
        .def("tell", &IcFAT::FileObject::tell)
        .def("read", &IcFAT::FileObject::read, py::arg("length")=0)
        .def("write", &IcFAT::FileObject::write, py::arg("data"))
        .def("close", &IcFAT::FileObject::close);

    m.def("icfat_test", &icfat_test);
}
