# -*- coding: utf-8 -*-
# Author: Icy(enderman1024@foxmail.com)
# OS: ALL
# Name: Log Writer
# Description: This function is used for recording logs
# Used Librarie(s): time, sys
# Version: 1.3

import time
import sys


class Logger:  # Logger

    def __init__(self, filename=None, line_end="lf",
                 date_format="%Y-%m-%d %H:%M:%S", level="DEBUG", echo=True):
        """
        Universal Python Logger

        :param filename: str (or None), log filename
        :param line_end: str, 'lf' or 'crlf'
        :param date_format: str, time.strftime arguments
        :param level: str (or int), 'DEBUG' - 0, 'INFO' - 1, 'WARNING' - 2, 'ERROR' - 3, 'CRITICAL' - 4
        :param echo: bool, print output in terminal
        """
        self.level = 1
        self.echo = echo
        if level in ("DEBUG", 0):
            self.level = 0
        elif level in ("INFO", 1):
            self.level = 1
        elif level in ("WARNING", 2):
            self.level = 2
        elif level in ("ERROR", 3):
            self.level = 3
        elif level in ("CRITICAL", 4):
            self.level = 4
        else:
            raise Exception("invalid level \"{}\", logger level: DEBUG, INFO, WARNING, ERROR, CRITICAL".format(level))
        try:
            time.strftime(date_format)
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
        if filename is None:
            return
        try:
            log_file = open(filename, "w")
            log_file.close()
        except Exception as err:
            raise Exception("Can't open file: \"" + filename + "\", result: " + str(err))

    def DEBUG(self, msg):
        if self.level > 0:
            return
        infos = "[" + time.strftime(self.date_format) + "] [DBUG] " + msg + self.line_end
        if self.echo:
            sys.stdout.write(infos)
            sys.stdout.flush()
        if self.filename is None:
            return infos
        log_file = open(self.filename, "a")
        log_file.write(infos)
        log_file.close()
        return infos

    def INFO(self, msg):
        if self.level > 1:
            return
        infos = "[" + time.strftime(self.date_format) + "] [INFO] " + msg + self.line_end
        if self.echo:
            sys.stdout.write(infos)
            sys.stdout.flush()
        if self.filename is None:
            return infos
        log_file = open(self.filename, "a")
        log_file.write(infos)
        log_file.close()
        return infos

    def WARNING(self, msg):
        if self.level > 2:
            return
        infos = "[" + time.strftime(self.date_format) + "] [WARN] " + msg + self.line_end
        if self.echo:
            sys.stdout.write(infos)
            sys.stdout.flush()
        if self.filename is None:
            return infos
        log_file = open(self.filename, "a")
        log_file.write(infos)
        log_file.close()
        return infos

    def ERROR(self, msg):
        if self.level > 3:
            return
        infos = "[" + time.strftime(self.date_format) + "] [EROR] " + msg + self.line_end
        if self.echo:
            sys.stdout.write(infos)
            sys.stdout.flush()
        if self.filename is None:
            return infos
        log_file = open(self.filename, "a")
        log_file.write(infos)
        log_file.close()
        return infos

    def CRITICAL(self, msg):
        infos = "[" + time.strftime(self.date_format) + "] [CRIT] " + msg + self.line_end
        if self.echo:
            sys.stdout.write(infos)
            sys.stdout.flush()
        if self.filename is None:
            return infos
        log_file = open(self.filename, "a")
        log_file.write(infos)
        log_file.close()
        return infos


if __name__ == '__main__':
    logger = Logger(level="DEBUG")
    logger = Logger(level="INFO")
    logger = Logger(level="WARNING")
    logger = Logger(level="ERROR")
    logger = Logger(level="CRITICAL")
