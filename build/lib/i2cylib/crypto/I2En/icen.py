#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: Icy(enderman1024@foxmail.com)
# OS: ALL
# Name: Simple File encoder/decoder
##VERSION: 3.1


import os
import sys
import time
from i2cylib.crypto.iccode import Iccode
from tqdm import tqdm


def action_bar(prt, maxlen):  # Action bar generator
    bar = "[" + "#" * int(prt * maxlen) + " " * (maxlen - int(prt * maxlen)) + "]"
    return bar


def round(data, num):  # float rounder
    data = str(data)
    n = 0
    for i in data:
        if i == ".":
            break
        else:
            n += 1
    try:
        data = data[:n + num]
    except:
        data = data
    return data


def get_args():  # read command shell's argument(s)
    opts = sys.argv[1:]
    argv = ""
    res = {}
    for i in opts:
        if len(argv) > 0 and "-" != i[0]:
            res.update({argv: i})
            argv = ""
        if "-" == i[0]:
            argv = i
            res.update({argv: ""})
    return res


def trf_time(data):  # Time transformer
    time_data = data
    hour = int(time_data / 3600)
    time_data = time_data - hour * 3600
    mins = int(time_data / 60)
    time_data = time_data - mins * 60
    sec = time_data
    return (hour, mins, sec)


def usage():
    print("""IcCode File Encrypter (by Icy)

Usage: icen.py -f <Target_File> -d/-e -k <Key> -t <File_to_Save>

Options:
 -h --help                           - display this page
 -f --file <File_Path>               - target file to be encode
                                       or decoder
 -d --decode                         - decode mode
 -e --encode                         - encode mode(default)
 -l --level                          - fingerprint level (3 default, >=1)
 -k --key <Key>                      - the key which is used for
                                       enctypter to encrypt
 -t --to <File_Path>                 - file to save to(default: %filename%.enc)

Example:
 $ icen.py -f "test.jpg" -e -k "test" -t "res.jpg"
""")
    sys.exit(1)


def main():
    global FILE, ENCODE, KEY, TO
    FILE = None
    ENCODE = True
    KEY = None
    TO = None
    level = 3
    opts = get_args()
    try:
        if opts == {}:
            print("IcCode File Encrypter (by Icy)")
            MODE = input("mode select(\"e\"--encode, \"d\"--decode): ")
            if MODE == "e":
                ENCODE = True
            elif MODE == "d":
                ENCODE = False
            else:
                print("please input correct words")
                sys.exit(1)

            FILE = input("target file path: ")

            if not os.path.exists(FILE):
                print("Can not find file \"" + FILE + "\"")
                sys.exit(1)

            TO = input("encripted(decripted) file path: ")

            KEY = input("key: ")
            level = input("fingerprint level(>=1): ")

        for i in opts:
            if i in ("-h", "--help"):
                usage()
            elif i in ("-f", "--file"):
                FILE = opts[i]
                if not os.path.exists(FILE):
                    print("Can not find file \"" + FILE + "\"")
                    sys.exit(1)
            elif i in ("-e", "--encode"):
                ENCODE = True
            elif i in ("-d", "--decode"):
                ENCODE = False
            elif i in ("-k", "--key"):
                KEY = opts[i]
            elif i in ("-t", "--to"):
                TO = opts[i]
            elif i in ("-l", "--level"):
                level = opts[i]
            else:
                print("Unhandled option: \"" + i + "\", try \"-h\" for help")
                sys.exit(1)
        try:
            level = int(level)
            if level < 1:
                raise Exception()
        except Exception:
            print("finger print level must be int type and bigger than 0")

        if KEY is None:
            KEY = input("key:")

        if FILE is None:
            print("syntax error, please check your command")
            sys.exit(1)

        if TO is None or not len(TO):
            if ENCODE:
                TO = FILE + ".enc"
            else:
                TO = FILE
                if len(TO) > 4 and TO[-4:] == ".enc":
                    TO = TO[:-4]
                else:
                    TO += ".dec"
        print("File Name  : " + FILE)
        if ENCODE:
            mode = "Encode"
        else:
            mode = "Decode"
        print("MODE       : " + mode)
        print("Level      : " + str(level))
        print("Destination: " + TO)
        print("Key        : " + KEY)
        file_a = open(FILE, "rb")
        try:
            file_to = open(TO, "wb")
        except Exception as err:
            print("Failed to open file: \"" + TO + "\", result: " + str(err))
            return
        lt = time.time()
        st = lt
        file_size = os.path.getsize(FILE)
        doed = 0
        coder = Iccode(KEY, fingerprint_level=level)
        ui = ""
        pbar = tqdm(total=file_size, unit="B", leave=True, unit_scale=True)
        while True:
            data = file_a.read(2048)
            #print(len(data))
            doed = len(data)
            if ENCODE:
                data = coder.encode(data)
            else:
                data = coder.decode(data)
            if len(data) == 0:
                break
            try:
                file_to.write(data)
            except Exception as err:
                print("Failed to write data to file: \"" + TO + "\", result: " + str(err))
                sys.exit(1)

            pbar.update(doed)

        file_a.close()
        file_to.close()
    except KeyboardInterrupt:
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
