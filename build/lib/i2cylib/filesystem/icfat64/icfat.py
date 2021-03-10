# -*- coding: utf-8 -*-
# Author: Icy(enderman1024@foxmail.com)
# OS: ALL
# Name: IC FAT Virtual File System
# Description: A light virtual file system based on FAT
##VERSION: 0.0.4

import os, random, time

class icfat: # ICFAT virtual filesystem API (Version: 0.0.1)
    def __init__(self,filename):
        self.version = b"\x00\x00\x01"
        self.space_total = 0
        self.filename = filename
        self.file = None
        try:
            if os.path.exists(filename) and os.path.isfile(filename):
                pass
            else:
                self.file = open(filename,"wb")
                self.file.close()
                self.file = None
                self.makefs(16)
            self.check()
            self.file = open(self.filename,"r+b")
        except Exception as err:
            raise Exception("error while opening file: " + str(err))
    def _get_free_cluster(self):
        self.load()
        self.file.seek(64+6)
        res = None
        data = None
        for i in range(self.cluster_number-1):
            data = self.file.read(6)
            if data == b"\x00\x00\x00\x00\x00\x00":
                res = i + 1
                break
            else:
                continue
        if data == None:
            raise Exception("no free cluster left")
        return res
    def _bytes_transform(self,data,bytes_length=6):
        if type(data) == type(b"\x00\x00\x00"):
            data = data[::-1]
            res = 0
            n = 0
            for i in data:
                res += i*256**n
                n += 1
        else:
            if data >= 256**bytes_length:
                raise Exception("data to transform out of range (0, "+str(256**bytes_length)+")")
            res = b""
            for i in range(bytes_length-1):
                res += bytes((int(data/256**(bytes_length-1-i)),))
                data = data%256**(bytes_length-1-i)
            res += bytes((data,))
        return res
    def _get_free_tag(self,path_tag_data):
        path_tags = []
        for i in range(int(len(path_tag_data)/32)):
            path_tags.append(path_tag_data[i*32:(i+1)*32])
        offset = None
        for i in range(len(path_tags)):
            if (path_tags[i])[0] == 255:
                offset = i
                break
            else:
                continue
        if offset == None:
            offset = len(path_tags)
        return offset
    def _readalldata(self,path_tag):
        self.load()
        res = b""
        length = path_tag["length"]
        readed = 0
        first_cluster = path_tag["first_cluster"]
        self.file.seek(64+self._bytes_transform(first_cluster)*6)
        next_cluster = self.file.read(6)
        self.file.seek(self.start_pointer+(self._bytes_transform(first_cluster)-1)*self.cluster_length)
        if length < self.cluster_length:
            res += self.file.read(length)
            readed += length
        else:
            res += self.file.read(self.cluster_length)
            readed += self.cluster_length
        while next_cluster != b"\xff\xff\xff\xff\xff\xff":
            self.file.seek(self.start_pointer+(self._bytes_transform(next_cluster)-1)*self.cluster_length)
            if length-readed < self.cluster_length:
                res += self.file.read(length-readed)
                readed += length-readed
            else:
                res += self.file.read(self.cluster_length)
                readed += self.cluster_length
            self.file.seek(64+self._bytes_transform(next_cluster)*6)
            next_cluster = self.file.read(6)
            if next_cluster == b"\x00\x00\x00\x00\x00\x00":
                break
        return res
    def _getfilelist(self,path_tag_data):
        path_tags = []
        for i in range(int(len(path_tag_data)/32)):
            path_tags.append(path_tag_data[i*32:(i+1)*32])
        files = {}
        dirctories = {}
        hided_files = {}
        offset = -1
        for i in path_tags:
            offset += 1
            if i[0] in (255,3):
                continue
            name = i[1:17]
            file_length = self._bytes_transform(i[20:26])
            first_cluster = i[26:32]
            next_tag = i[17:20]
            while next_tag != b"\xff\xff\xff":
                next_tag_data = path_tags[self._bytes_transform(next_tag)]
                name += next_tag_data[1:29]
                next_tag = next_tag_data[29:32]
            name = name.replace(b"\x00",b"")
            name = name.decode()
            if i[0] == 1:
                dirctories.update({name:{
                    "length":file_length,
                    "first_cluster":first_cluster,
                    "tag_offset":offset}})
            elif i[0] == 2:
                files.update({name:{
                    "length":file_length,
                    "first_cluster":first_cluster,
                    "tag_offset":offset}})
            elif i[0] == 4:
                hided_files.update({name:{
                    "length":file_length,
                    "first_cluster":first_cluster,
                    "tag_offset":offset}})
            else:
                raise Exception("unhandled data tag: " + str(i[0]))
        return {"files":files,
                "dirctories":dirctories,
                "hided_files":hided_files}
    def _decode_path(self,path):
        paths = []
        ignore = 0
        name = ""
        for i in path:
            if i == "\"":
                if ignore == 2:
                    ignore = 0
                    continue
                else:
                    ignore = 2
                    continue
            elif i == "'":
                if ignore == 1:
                    ignore = 0
                    continue
                else:
                    if ignore > 1:
                        pass
                    else:
                        ignore = 1
                        continue
            elif i == "/":
                if ignore > 0:
                    pass
                else:
                    paths.append(name)
                    name = ""
                    continue
            name += i
        if name != "":
            paths.append(name)
        return paths
    def _getlength(self):
        seek = self.file.tell()
        self.release()
        res = os.path.getsize(self.filename)
        self.load()
        self.file.seek(seek)
        return res
    def _clear_fat_chain(self,first_cluster):
        self.load()
        cluster = first_cluster
        clusters = []
        while cluster != b"\xff\xff\xff\xff\xff\xff":
            clusters.append(cluster)
            self.file.seek(64+self._bytes_transform(cluster)*6)
            cluster = self.file.read(6)
            if cluster == b"\x00\x00\x00\x00\x00\x00":
                break
        # remove fat chain by step
        for i in clusters:
            self.file.seek(64+self._bytes_transform(i)*6)
            self.file.write(b"\x00\x00\x00\x00\x00\x00")
        self.check()
    def debug(self):
        version_data = list(self.version)
        version = ""
        for i in version_data:
            version += str(i)+"."
        version = version[:-1]
        return {"version":version,
                "uuid":self.uuid,
                "date":self.date,
                "mode":self.mode,
                "space_total":self.space_total,
                "cluster_length":self.cluster_length,
                "cluster_number":self.cluster_number,
                "free_clusters":self.free_clusters,
                "description":self.description}
    def check(self):
        self.load()
        self.file.seek(0)
        try:
            head = self.file.read(5)
            if head != b"ICFAT":
                raise Exception("file is not a ICFAT disk file")
            version = self.file.read(3)
            if version != self.version:
                raise Exception("ICFAT version is " + str(self.version[0]) + "." + str(self.version[1]) + "." + str(self.version[2]) + ", but the file is " + str(version[0]) + "." + str(version[1]) + "." + str(version[2]))
            self.uuid = self.file.read(8)
            data = self.file.read(6)
            self.date = list(data)
            self.file.seek(23)
            data = self.file.read(1)
            if data == b"\x00":
                self.mode = "standard"
            else:
                self.mode = "flexible"
            data = self.file.read(6)
            self.cluster_number = data[0]*256**5+data[1]*256**4+data[2]*256**3+data[3]*256**2+data[4]*256+data[5]
            data = self.file.read(2)
            self.cluster_length = data[0]*256+data[1]
            self.space_total = self.cluster_length*self.cluster_number
            self.start_pointer = self.cluster_number*6+6+64
            self.description = (self.file.read(32).replace(b"\x00",b"")).decode()
            self.free_clusters = 0
            self.file.seek(64+6)
            for i in range(self.cluster_number):
                data = self.file.read(6)
                if data == b"\x00\x00\x00\x00\x00\x00":
                    self.free_clusters += 1
                else:
                    continue
        except Exception as err:
            raise err
    def list(self,path):
        self.load()
        paths = self._decode_path(path)
        # read root path
        self.file.seek(self.start_pointer)
        data = self.file.read(32)
        length = self._bytes_transform(data[20:26])
        head_cluster = data[26:32]
        tag = {"length":length,"first_cluster":head_cluster}
        root_files = self._getfilelist(self._readalldata(tag))
        if paths != []:
            paths.pop(0)
        files = root_files
        # read path by step
        for i in paths:
            if i in files["dirctories"].keys():
                files = self._getfilelist(self._readalldata((files["dirctories"])[i]))
            else:
                raise Exception("path dose not exists")
        return files
    def release(self):
        if self.file != None:
            self.file.close()
            self.file = None
    def load(self):
        if self.file == None:
            self.file = open(self.filename,"r+b")
        else:
            pass
    def makefs(self,cluster_number,description="",cluster_length=512,mode="flexible"): # mode = "flexible", "standard"
        self.release()
        f = open(self.filename,"wb")
        f.close()
        self.load()
        self.file.seek(0)
        # write header (8 bytes)
        self.file.write(b"ICFAT")
        self.file.write(self.version)
        # write uuid (8 bytes)
        self.uuid = b""
        for i in range(8):
            self.uuid += bytes((int(255*random.random()),))
        self.file.write(self.uuid)
        # write date (6 bytes)
        data = time.strftime("%y %m %d %H %M %S").split(" ")
        n = 0
        for i in data:
            data[n] = int(i)
            n += 1
        data = bytes(data)
        self.file.write(data)
        # reserved bytes (1 bytes)
        self.file.write(b"\x00")
        # write flexible tag (1 bytes)
        if mode == "flexible":
            self.file.write(b"\x01")
        else:
            self.file.write(b"\x00")
        # write cluster number (6 bytes)
        data = []
        num = cluster_number
        for i in range(5):
            one_num = int(num/256**(5-i))
            num = num%256**(5-i)
            data.append(one_num)
        data.append(int(num))
        data = bytes(data)
        self.file.write(data)
        # write cluster length (2 bytes)
        data = [int(cluster_length/256),int(cluster_length%256)]
        data = bytes(data)
        self.file.write(data)
        # write description (32 bytes)
        data = description.encode()
        data_len = len(data)
        if data_len > 32:
            raise Exception("description length must <= 32")
        fill = bytes(32-data_len)
        data += fill
        self.file.write(data)
        # write FAT header (6 bytes)
        self.file.write(bytes(6))
        # write FAT table (6*cluster_number bytes)
        for i in range(cluster_number):
            self.file.write(bytes(6))
        # write first cluster (cluster_length bytes)
        self.file.write(bytes(cluster_length))
        # write root path (32 bytes)
        data = b"\x01" + b"\x00"*16 + b"\xff\xff\xff" + b"\x00\x00\x00\x00\x00\x20" + b"\x00\x00\x00\x00\x00\x01"
        start_pointer = cluster_number*6+6+64
        self.file.seek(64+(self._bytes_transform(b"\x00\x00\x00\x00\x00\x01"))*6)
        self.file.write(b"\xff\xff\xff\xff\xff\xff")
        self.file.seek(start_pointer+cluster_length*(self._bytes_transform(b"\x00\x00\x00\x00\x00\x01")-1))
        self.file.write(data)
        if mode == "flexible":
            self.check()
            return
        else:
            pass
        # write clusters
        for i in range(cluster_number-1):
            self.file.write(b"\xff"*cluster_length)
        self.check()
    def mkdir(self,dirname):
        paths = self._decode_path(dirname)
        if paths != []:
            dirname = paths.pop(-1)
        path = "/"
        for i in paths:
            path += i+"/"
        if dirname in self.list(path)["dirctories"].keys():
            raise Exception("path already exists")
        dir = self.open(path+dirname,as_dir=True)
        dir.close()
        self.check()
    def remove(self,filename):
        self.load()
        paths = self._decode_path(filename)
        if paths != []:
            filename = paths.pop(-1)
        path = ""
        for i in paths:
            path += i+"/"
        files = self.list(path)
        if filename in files["files"].keys():
            # get file infos
            length = ((files["files"])[filename])["length"]
            first_cluster = ((files["files"])[filename])["first_cluster"]
            tag_offset = self._bytes_transform(((files["files"])[filename])["tag_offset"],3)
            dirctory = False
        elif filename in files["dirctories"].keys():
            length = ((files["dirctories"])[filename])["length"]
            first_cluster = ((files["dirctories"])[filename])["first_cluster"]
            tag_offset = self._bytes_transform(((files["dirctories"])[filename])["tag_offset"],3)
            dirctory = True
        else:
            raise Exception("target not found")
        if dirctory:
            if filename == "":
                raise Exception("can not remove root path")
            files = self.list(path+filename)
            file_objects = []
            dirctories = []
            for i in files["files"].keys():
                file_objects.append(path+filename+"/"+i)
            for i in files["dirctories"].keys():
                file_objects.append(path+filename+"/"+i)
            # remove sub files in dirctory
            for i in file_objects:
                self.remove(i)
            # remove sub dirctories
            for i in dirctories:
                self.remove(i)
            path_file = self.open(path)
            # locate file tags
            tags_offsets = []
            tags_offsets.append(tag_offset)
            path_file.seek(self._bytes_transform(tag_offset)*32+17)
            tag_offset = path_file.read(3)
            while tag_offset != b"\xff\xff\xff":
                tags_offsets.append(tag_offset)
                path_file.seek(self._bytes_transform(tag_offset)*32+29)
                tag_offset = path_file.read(3)
            # clear fat chain
            self._clear_fat_chain(first_cluster)
            # clear file tags
            for i in tags_offsets:
                path_file.seek(self._bytes_transform(i)*32)
                path_file.write(b"\xff")
            path_file.close()
        else:
            path_file = self.open(path)
            # locate file tags
            tags_offsets = []
            tags_offsets.append(tag_offset)
            path_file.seek(self._bytes_transform(tag_offset)*32+17)
            tag_offset = path_file.read(3)
            while tag_offset != b"\xff\xff\xff":
                tags_offsets.append(tag_offset)
                path_file.seek(self._bytes_transform(tag_offset)*32+29)
                tag_offset = path_file.read(3)
            # clear fat chain
            self._clear_fat_chain(first_cluster)
            # clear file tags
            for i in tags_offsets:
                path_file.seek(self._bytes_transform(i)*32)
                path_file.write(b"\xff")
            path_file.close()
        self.check()
    def open(self,filename,mode="a",as_dir=False):
        file = self.file_object(self,filename,mode,as_dir)
        return file
    class file_object:
        def __init__(self,icfat_class,filename,mode="a",as_dir=False):
            icfat_class.load()
            self.icfat_class = icfat_class
            paths = icfat_class._decode_path(filename)
            self.new_file = False
            self.closed = False
            path = ""
            self.pointer = 0
            self.clusters = []
            try:
                if paths != []:
                    filename = paths.pop(-1)
                for i in paths:
                    path += i+"/"
                self.path = path
                # list target file dirctories
                files = icfat_class.list(path)
                if filename in files["files"].keys():
                    # get file infos
                    self.name = filename
                    self.length = ((files["files"])[filename])["length"]
                    first_cluster = ((files["files"])[filename])["first_cluster"]
                    self.tag_offset = ((files["files"])[filename])["tag_offset"]
                    self.dirctory = False
                elif filename in files["dirctories"].keys():
                    self.name = filename
                    self.length = ((files["dirctories"])[filename])["length"]
                    first_cluster = ((files["dirctories"])[filename])["first_cluster"]
                    self.tag_offset = ((files["dirctories"])[filename])["tag_offset"]
                    self.dirctory = True
                else:
                    self.new_file = True
                    self.name = filename
                    self.length = 0
                    first_cluster = icfat_class._bytes_transform(icfat_class._get_free_cluster(),6)
                    if as_dir:
                        self.dirctory = True
                    else:
                        self.dirctory = False
                self.original_length = self.length
                # get file clusters list
                self.icfat_class.load()
                cluster = first_cluster
                while cluster != b"\xff\xff\xff\xff\xff\xff":
                    self.clusters.append(cluster)
                    self.icfat_class.file.seek(64+self.icfat_class._bytes_transform(cluster)*6)
                    cluster = self.icfat_class.file.read(6)
                    if cluster == b"\x00\x00\x00\x00\x00\x00":
                        break
                    if self.new_file:
                        break
                if "w" in mode:
                    self.length = 0
                    self.clusters = [self.clusters[0]]
                    self.icfat_class._clear_fat_chain(self.clusters[0])
                self._update_fat()
            except Exception as err:
                raise Exception("failed to open file: " + str(err))
        def debug(self):
            print("cluster chain:",self.clusters)
        def _update_fat(self):
            # update FAT table
            cluster = self.clusters[0]
            for i in self.clusters[1:]:
                self.icfat_class.file.seek(64+self.icfat_class._bytes_transform(cluster)*6)
                self.icfat_class.file.write(i)
                cluster = i
            self.icfat_class.file.seek(64+self.icfat_class._bytes_transform(cluster)*6)
            self.icfat_class.file.write(b"\xff\xff\xff\xff\xff\xff")
        def seek(self,offset):
            if self.closed:
                raise Exception("file closed")
            if offset <= self.length and offset >= -self.length-1:
                if offset >= 0:
                    self.pointer = offset
                else:
                    self.pointer = self.length+1+offset
            else:
                raise Exception("file pointer ("+str(offset)+") out of range ("+str(-self.length)+", "+str(self.length)+")")
        def tell(self):
            if self.closed:
                raise Exception("file closed")
            return self.pointer
        def read(self,length=0):
            if self.closed:
                raise Exception("file closed")
            self.icfat_class.load()
            pointer_cluster_num = int(self.pointer/self.icfat_class.cluster_length)
            pointer_cluster = self.clusters[pointer_cluster_num]
            in_cluster_pointer = self.pointer%self.icfat_class.cluster_length
            res = b""
            # locate pointer
            self.icfat_class.file.seek(self.icfat_class.start_pointer+(self.icfat_class._bytes_transform(pointer_cluster)-1)*self.icfat_class.cluster_length+in_cluster_pointer)
            # read file
            if length+self.pointer > self.length or length == 0:
                length = self.length - self.pointer
            left = length
            in_cluster_left = self.icfat_class.cluster_length-in_cluster_pointer
            while left > in_cluster_left:
                res += self.icfat_class.file.read(in_cluster_left)
                self.pointer += in_cluster_left
                in_cluster_pointer = 0
                left -= in_cluster_left
                in_cluster_left = self.icfat_class.cluster_length
                # locate next file cluster
                pointer_cluster_num += 1
                pointer_cluster = self.clusters[pointer_cluster_num]
                self.icfat_class.file.seek(self.icfat_class.start_pointer+(self.icfat_class._bytes_transform(pointer_cluster)-1)*self.icfat_class.cluster_length)
            res += self.icfat_class.file.read(left)
            self.pointer += left
            return res
        def write(self,data):
            if self.closed:
                raise Exception("file closed")
            self.icfat_class.load()
            pointer_cluster_num = int(self.pointer/self.icfat_class.cluster_length)
            if pointer_cluster_num >= len(self.clusters):
                self.clusters.append(self.icfat_class._bytes_transform(self.icfat_class._get_free_cluster(),6))
                self._update_fat()
            pointer_cluster = self.clusters[pointer_cluster_num]
            in_cluster_pointer = self.pointer%self.icfat_class.cluster_length
            # locate pointer
            self.icfat_class.file.seek(self.icfat_class.start_pointer+(self.icfat_class._bytes_transform(pointer_cluster)-1)*self.icfat_class.cluster_length+in_cluster_pointer)
            data_len = len(data)
            in_cluster_left = self.icfat_class.cluster_length-in_cluster_pointer
            left = data_len
            while left > in_cluster_left:
                data_pointer = data_len-left
                self.icfat_class.file.write(data[data_pointer:data_pointer+in_cluster_left])
                in_cluster_pointer = 0
                left -= in_cluster_left
                self.pointer += in_cluster_left
                in_cluster_left = self.icfat_class.cluster_length
                # locate next file cluster
                pointer_cluster_num += 1
                if pointer_cluster_num >= len(self.clusters):
                    self.clusters.append(self.icfat_class._bytes_transform(self.icfat_class._get_free_cluster(),6))
                    self._update_fat()
                pointer_cluster = self.clusters[pointer_cluster_num]
                self.icfat_class.file.seek(self.icfat_class.start_pointer+(self.icfat_class._bytes_transform(pointer_cluster)-1)*self.icfat_class.cluster_length)
            data_pointer = data_len-left
            self.icfat_class.file.write(data[data_pointer:])
            self.pointer += left
            if self.pointer > self.length:
                self.length = self.pointer
            return len(data)
        def close(self):
            if self.closed:
                raise Exception("file closed")
            self.closed = True
            if self.length != self.original_length or self.new_file:
                # update file tag
                dir = self.icfat_class.open(self.path)
                data = dir.read()
                dir.seek(0)
                if self.new_file:
                    self.tag_offset = self.icfat_class._get_free_tag(data)
                    tag_offset = self.tag_offset*32
                    dir.seek(tag_offset)
                    dir.write(b"\x00"*32)
                    dir.seek(tag_offset)
                    if self.dirctory:
                        dir.write(b"\x01")
                    else:
                        dir.write(b'\x02')
                    dir.seek(tag_offset+20)
                    dir.write(self.icfat_class._bytes_transform(self.length,6))
                    dir.write(self.clusters[0])
                    name = self.name.encode()
                    left = len(name)
                    dir.seek(tag_offset+1)
                    if left <= 16:
                        data = name+b'\x00'*(16-left)
                        dir.write(data)
                        dir.write(b"\xff\xff\xff")
                    else:
                        data = name[:16]
                        name = name[16:]
                        dir.write(data)
                        left = len(name)
                        dir.seek(0)
                        next_tag = self.icfat_class._get_free_tag(dir.read())
                        dir.seek(tag_offset+17)
                        dir.write(self.icfat_class._bytes_transform(next_tag,3))
                        tag_offset = next_tag
                        while left > 28:
                            dir.seek(tag_offset*32)
                            dir.write(b"\x00"*32)
                            dir.seek(tag_offset*32)
                            dir.write(b"\x03")
                            data = name[:28]
                            name = name[28:]
                            left = len(name)
                            dir.write(data)
                            dir.seek(0)
                            next_tag = self.icfat_class._get_free_tag(dir.read())
                            dir.seek(tag_offset*32+29)
                            dir.write(self.icfat_class._bytes_transform(next_tag,3))
                            tag_offset = next_tag
                        dir.seek(tag_offset*32)
                        dir.write(b"\x00"*32)
                        dir.seek(tag_offset*32)
                        dir.write(b"\x03")
                        data = name+b"\x00"*(28-left)
                        dir.write(data)
                        dir.write(b"\xff\xff\xff")
                else:
                    dir.seek(self.tag_offset*32+20)
                    dir.write(self.icfat_class._bytes_transform(self.length,6))
                dir.close()
                self.icfat_class.check()
                return
            else:
                return




# examples of using the API


def icfat_test():
    print("\n■ creating a test.blk")
    blk = icfat("test.blk")
    print("\n■ making filesystem")
    blk.makefs(2048,cluster_length=2048,description="测试虚拟盘")
    print("\n■ listing details")
    data = blk.debug()
    for i in data:
        print(i+":\t"+str(data[i]))
    print("\n■ listing root path")
    data = blk.list("/")
    print("[files]")
    for i in data["files"]:
        print(i+":"+str((data["files"])[i]))
    print("[dirctories]")
    for i in data["dirctories"]:
        print(i+":"+str((data["dirctories"])[i]))
    print("\n■ making dirctory: /test")
    blk.mkdir("/test")
    print("\n■ listing root path")
    data = blk.list("/")
    print("[files]")
    for i in data["files"]:
        print(i+":"+str((data["files"])[i]))
    print("[dirctories]")
    for i in data["dirctories"]:
        print(i+":"+str((data["dirctories"])[i]))
    print("\n■ test opening new file in /test and write b\"test\"")
    f = blk.open('/test/super_long_filename_saving_test_and_中文编码测试_coding_test.txt')
    f.write(b'test')
    f.close()
    print("\n■ listing file in /test")
    data = blk.list("/test")
    print("[files]")
    for i in data["files"]:
        print(i+":"+str((data["files"])[i]))
    print("[dirctories]")
    for i in data["dirctories"]:
        print(i+":"+str((data["dirctories"])[i]))
    print("\n■ reading the file we created just now")
    f = blk.open('/test/super_long_filename_saving_test_and_中文编码测试_coding_test.txt')
    print("data: "+f.read().decode())
    print("\n■ creating another 2 files in /test")
    f = blk.open("/test/file2")
    f.close()
    f = blk.open("/test/file3")
    f.close()
    print("\n■ listing file in /test")
    data = blk.list("/test")
    print("[files]")
    for i in data["files"]:
        print(i+":"+str((data["files"])[i]))
    print("[dirctories]")
    for i in data["dirctories"]:
        print(i+":"+str((data["dirctories"])[i]))
    print("\n■ removing the first & second file in /test")
    blk.remove("/test/super_long_filename_saving_test_and_中文编码测试_coding_test.txt")
    blk.remove("/test/file2")
    print("\n■ listing file in /test")
    data = blk.list("/test")
    print("[files]")
    for i in data["files"]:
        print(i+":"+str((data["files"])[i]))
    print("[dirctories]")
    for i in data["dirctories"]:
        print(i+":"+str((data["dirctories"])[i]))
    print("\n■ creating another file 'first' in /test")
    f = blk.open("/test/first")
    f.close()
    print("\n■ listing file in /test")
    data = blk.list("/test")
    print("[files]")
    for i in data["files"]:
        print(i+":"+str((data["files"])[i]))
    print("[dirctories]")
    for i in data["dirctories"]:
        print(i+":"+str((data["dirctories"])[i]))
    print("\n■ listing details")
    data = blk.debug()
    for i in data:
        print(i+":\t"+str(data[i]))
    print("\n■ removing path /test")
    blk.remove("/test")
    print("\n■ listing root path")
    data = blk.list("/")
    print("[files]")
    for i in data["files"]:
        print(i+":"+str((data["files"])[i]))
    print("[dirctories]")
    for i in data["dirctories"]:
        print(i+":"+str((data["dirctories"])[i]))
    print("\n■ listing details")
    data = blk.debug()
    for i in data:
        print(i+":\t"+str(data[i]))

if __name__ == "__main__":
    print("running test")
    icfat_test()