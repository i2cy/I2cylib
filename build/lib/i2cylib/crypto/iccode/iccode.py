# -*- coding: utf-8 -*-
# Author: Icy(enderman1024@foxmail.com)
# OS: ALL
# Name: Simple Data encoder/decoder
# Description: Encode the data or decode the data with a key
##VERSION: 2.2

class iccode: # Simple Data Encoder/Decoder
    def __init__(self,base_key): # base_key must be bytes
        if len(base_key) <= 1:
            raise Exception("'base_key' length must be greater than 1")
        if type(base_key) != type(b"bytes"):
            try:
                base_key = base_key.encode()
            except Exception as err:
                raise Exception("can not encode \"base_key\"")
        self.base_key = list(base_key)
        self.block_length = len(base_key)
        self.last_bytes = list(b"\x00"*self.block_length)
        self.step = 0
        n = 0
        for i in self.base_key:
            self.base_key[n] = int((base_key[0]+1)*(1+(i**2)/(base_key[-1]+1)))%256
            n += 1
    def reset(self): # reset coder
        self.last_bytes = list(b"\x00"*self.block_length)
        self.step = 0
    def encode(self,data): # encoder
        res = []
        for i in data:
            self.last_bytes.append(i)
            res.append((i+self.last_bytes.pop(0)+self.base_key[self.step%(self.block_length-1)])%256)
            self.step += 1
        return bytes(res)
    def decode(self,data): # decoder
        res = []
        for i in data:
            decoded = (i-self.last_bytes.pop(0)-self.base_key[self.step%(self.block_length-1)])%256
            self.last_bytes.append(decoded)
            res.append(decoded)
            self.step += 1
        return bytes(res)
    def sp_encode(self,data): # simple encoder
        res = []
        for i in data:
            res.append((i+self.base_key[self.step%(self.block_length-1)])%256)
            self.step += 1
        return bytes(res)
    def sp_decode(self,data): # simple decoder
        res = []
        for i in data:
            res.append((i-self.base_key[self.step%(self.block_length-1)])%256)
            self.step += 1
        return bytes(res)
    def debug(self):
        return (self.step,self.last_bytes,self.base_key)
