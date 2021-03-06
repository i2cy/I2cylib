# -*- coding: utf-8 -*-
# Author: Icy(enderman1024@foxmail.com)
# OS: ALL
# Name: Text matcher


def text_match(text1, text2, offset=3):
    offsets = list(range(-offset,1+offset))
    total = len(text1)+len(text2)
    pointer = -1
    offset = 0
    matched = 0
    changed = False
    for i in text1:
        pointer += 1
        if pointer+offset > len(text2)-1:
            break
        if text2[pointer+offset] == i:
            matched += 2
            changed = False
            continue
        else:
            for i2 in offsets:
                if pointer+offset+i2 > len(text2)-1:
                    offset += i2
                    break
                if text2[pointer+offset+i2] == i:
                    if changed:
                        pass
                    else:
                        changed = True
                        matched += 1
                    offset += i2
                    break
                else:
                    continue
    return matched/total
