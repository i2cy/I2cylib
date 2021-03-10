# -*- coding: utf-8 -*-
# Author: Icy(enderman1024@foxmail.com)
# OS: ALL
# Name: Log Writer
# Description: This function is used for recording logs
# Used Librarie(s): time, sys
# Version: 1.3

import time
import sys


class logger: # Logger
    def __init__(self, filename=None, line_end="lf",
                 date_format="%Y-%m-%d %H:%M:%S", level="DEBUG", echo=True):
        self.level = 1
        self.echo = echo
        if level == "DEBUG":
            self.level = 0
        elif level == "INFO":
            self.level = 1
        elif level == "WARNING":
            self.level = 2
        elif level == "ERROR":
            self.level = 3
        elif level == "CRITICAL":
            self.level = 4
        else:
            raise Exception("logger level: DEBUG, INFO, WARNING, ERROR, CRITICAL")
        try:
            temp = time.strftime(date_format)
            del temp
        except Exception as err:
            raise Exception("Failed to set date formant, result: " + str(err))
        self.date_format = date_format
        if line_end == "lf":
            self.line_end = "\n"
        elif line_end == "crlf":
            self.line_end = "\r\n"
        else:
            raise Exception("Unknow line end character(s): \"" + line_end + "\"")
        self.filename = filename
        if filename == None:
            return
        try:
            log_file = open(filename,"w")
            log_file.close()
        except Exception as err:
            raise Exception("Can't open file: \"" + filename + "\", result: " + str(err))
    def DEBUG(self,msg):
        if self.level > 0:
            return
        infos = "["+ time.strftime(self.date_format) +"] [DBUG] " + msg + self.line_end
        if self.echo:
            sys.stdout.write(infos)
            sys.stdout.flush()
        if self.filename == None:
            return
        log_file = open(self.filename,"a")
        log_file.write(infos)
        log_file.close()
        return infos
    def INFO(self,msg):
        if self.level > 1:
            return
        infos = "["+ time.strftime(self.date_format) +"] [INFO] " + msg + self.line_end
        if self.echo:
            sys.stdout.write(infos)
            sys.stdout.flush()
        if self.filename == None:
            return
        log_file = open(self.filename,"a")
        log_file.write(infos)
        log_file.close()
        return infos
    def WARNING(self,msg):
        if self.level > 2:
            return
        infos = "["+ time.strftime(self.date_format) +"] [WARN] " + msg + self.line_end
        if self.echo:
            sys.stdout.write(infos)
            sys.stdout.flush()
        if self.filename == None:
            return
        log_file = open(self.filename,"a")
        log_file.write(infos)
        log_file.close()
        return infos
    def ERROR(self,msg):
        if self.level > 3:
            return
        infos = "["+ time.strftime(self.date_format) +"] [EROR] " + msg + self.line_end
        if self.echo:
            sys.stdout.write(infos)
            sys.stdout.flush()
        if self.filename == None:
            return
        log_file = open(self.filename,"a")
        log_file.write(infos)
        log_file.close()
        return infos
    def CRITICAL(self,msg):
        infos = "["+ time.strftime(self.date_format) +"] [CRIT] " + msg + self.line_end
        if self.echo:
            sys.stdout.write(infos)
            sys.stdout.flush()
        if self.filename == None:
            return
        log_file = open(self.filename,"a")
        log_file.write(infos)
        log_file.close()
        return infos
