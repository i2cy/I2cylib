# -*- coding: utf-8 -*-
# Author: Icy(enderman1024@foxmail.com)
# OS: ALL
# Name: Time Transformer
# Description: Transform the second(s) time to "**:**:**"

def trf_time(data): # Time transformer
    time_data = data
    hour = int(time_data/3600)
    time_data = time_data - hour*3600
    mins = int(time_data/60)
    time_data = time_data - mins*60
    sec = time_data
    return (hour, mins, sec)
