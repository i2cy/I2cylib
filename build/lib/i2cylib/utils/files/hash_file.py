# -*- coding: utf-8 -*-
# Author: Icy(enderman1024@foxmail.com)
# OS: ALL
# Name: File Hash Reader
# Description: This function can the file's sha3-512 value
# Used Librarie(s): hashlib
##VERSION: 1.1

import hashlib

def hash_file(file_path):
    filex = open(file_path,"rb")
    hashs = hashlib.sha512()
    while True:
        data = filex.read(1024)
        if len(data) == 0:
            break
        hashs.update(data)
    return hashs.hexdigest()
