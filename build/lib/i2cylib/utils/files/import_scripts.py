# -*- coding: utf-8 -*-
# Author: Icy(enderman1024@foxmail.com)
# OS: ALL
# Name: Import Python Module from Scripts
# Description: This function can import a python file from scripts

def import_scripts(scripts): # python scripts importer
    __name__ = "__module__"
    try:
        exec(scripts)
    except Exception:
        raise ImportError(str(Exception))
    del __name__, scripts
    globals().update(locals())
