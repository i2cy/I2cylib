#!/usr/bin/python3
# dependency: smartctl
# OS: linux
# author: i2cy(i2cy@outlook.com)
# description: get a hard drive disk's temperature through 'smartctl'
#              command and analize its S.M.A.R.T. infomation for temperature value


import os
import sys


def getHDDTemp(device): # hard drive temperature reader
    if not os.path.exists(device):
        raise Exception("device does not exists")
    pipe = os.popen("smartctl -A -f old "+device)
    data = pipe.read().split("\n")
    res = 0
    temp = []
    for i in data:
        temp = i.split(" ")
        if temp[0] == "194":
            n = 0
            for i2 in temp:
                if i2 == '':
                    continue
                else:
                    n += 1
                if n == 10:
                    res = int(i2)
    return res





def main():
    device = sys.argv[1]
    print("HDD temperature of device \""+device+"\" is "+str(getHDDTemp(device))+"C")





if __name__ == "__main__":
    main()
