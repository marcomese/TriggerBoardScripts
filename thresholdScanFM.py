# -*- coding: utf-8 -*-

import sys

if __name__ == '__main__':
    defaultVal     = 0xe1b9563b
    dacCode2Mask   = 0xf801ffff
    dacCodeBit0Pos = 17
    
    argv = sys.argv
    argc = len(sys.argv)

    if argc > 4 or argc < 4:
        print("Uso: thresholdScanFM.py <THRmin> <THRmax> <THRstep>")
        sys.exit(1)

    thrMin  = int(argv[1])
    thrMax  = int(argv[2])
    thrStep = int(argv[3])

    if thrMin > thrMax:
        print("Errore: soglia minima più alta di quella massima!")
        sys.exit(1)

    i = 0

    for thr in range(thrMin,thrMax+thrStep,thrStep):
        i = i + 1

        thrValue = thr << dacCodeBit0Pos
        
        thrReg = (defaultVal & dacCode2Mask) | thrValue
        thrRegStr = f"{thrReg:08x}".upper()
        
        print(f"{i:02d}) THR = {thr} -> 0x00000009 = 0x{thrRegStr}")