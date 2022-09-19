#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Project: I2cylib
# Filename: i2tec_home
# Created on: 2022/9/19

import os
from pathlib import Path
from shutil import rmtree


class DirTree(os.PathLike):

    def __init__(self, *root: (os.PathLike, str)):
        self.__root = Path(*root)
        self.name = self.__root.name

    def __str__(self):
        return self.__root.as_posix()

    def __fspath__(self):
        return self.__root.__fspath__()

    def __iter__(self):
        return self.__root.iterdir()

    def __len__(self):
        cnt = 0
        for i in self.__root.iterdir():
            cnt += 1
        return cnt

    def exists(self):
        return self.__root.exists()

    def fixPath(self, is_file=True, touch=False):
        if is_file:
            self.__root.parent.mkdir(parents=True, exist_ok=True)
            if touch:
                self.__root.touch(exist_ok=True)
        else:
            self.__root.mkdir(parents=True, exist_ok=True)

    def isFixed(self):
        return self.__root.parent.exists()

    def touch(self):
        if self.exists():
            return

        self.fixPath(is_file=True, touch=True)

    def isFile(self):
        return self.__root.is_file()

    def isDir(self):
        return self.__root.is_dir()

    def remove(self):
        if self.isDir():
            rmtree(self)
        else:
            os.remove(self)

    def asPosix(self):
        return str(self)

    def parent(self):
        return DirTree(self.__root.parent)

    def toList(self, dir_only=False, file_only=False):
        ret = []
        for ele in self:
            if ele.is_dir():
                if not file_only:
                    ret.append(DirTree(ele))
            else:
                if not dir_only:
                    ret.append(DirTree(ele))
        return ret

    def join(self, *path: (os.PathLike, str)):
        return DirTree(self, *path)


def i2TecHome():
    return DirTree(Path.home(), ".i2tec")


if __name__ == '__main__':
    import time

    root = i2TecHome()
    root.fixPath(False)
    print(root)
    print("root got {} file(dir)s within".format(len(root)))
    print("listing files under it:")
    for i, path in enumerate(root.toList(file_only=True)):
        print("\t{}. \"{}\"".format(i, path))

    file_path = root.join("{}.txt".format(int(time.time())))
    print("creating text file ")
    with open(file_path, "w") as f:
        f.write("test.file.content.{}".format(time.time))
        f.close()

    print("creating dir")
    dir_path = root.join("{}".format(int(time.time())))
    dir_path.fixPath(False)
    print("making random files")
    for i in range(5):
        dir_path.join("{}.txt".format(time.time())).touch()

    print("listing everything under root:")
    for i, path in enumerate(root.toList()):
        print("\t{}. \"{}\"".format(i, path))

    print("listing everything under test dir:")
    for i, path in enumerate(dir_path.toList()):
        print("\t{}. \"{}\"".format(i, path))

    print("removing dir")
    dir_path.remove()

    print("removing test file")
    file_path.remove()

    print("listing everything under root:")
    for i, path in enumerate(root.toList()):
        print("\t{}. \"{}\"".format(i, path))
