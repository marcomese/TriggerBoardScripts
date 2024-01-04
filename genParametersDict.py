# -*- coding: utf-8 -*-
"""
Created on Thu Jun 20 16:43:21 2019

@author: Marco
"""

import re

sp = "[\\s\\t]*"

paramPattern = (f"{sp}Constant{sp}([a-zA-Z0-9_]*){sp}:{sp}"
                f"(std_logic(_vector\((\d+){sp}(downto|to){sp}(\d+)\))?)")

registerPattern = (f"{sp}constant{sp}([a-zA-Z0-9_]*){sp}:{sp}"
                   f"std_logic_vector\(ADDR_LENGHT{sp}-{sp}1{sp}downto{sp}0\)"
                   f"{sp}:={sp}x(\"[a-fA-F0-9]{{8}}\")")

startParametersStr = ("------------------- Slow Control "
                      "------------------------")
endParametersStr = ("---------------------------"
                     "------------------------------")

params = []
names = []
numOfBits = []

parSearch = re.compile(paramPattern,re.IGNORECASE)
regSearch = re.compile(registerPattern,re.IGNORECASE)

with open("register_file.vhd","r") as regVhdlFile:
    registerFileContent = regVhdlFile.read()
    
registers = regSearch.findall(registerFileContent)

with open("regNameRegs.py","w") as regOut:
    regOut.write("# Dizionario generato automaticamente\n"
                  "# Per correggere eventuali errori modificare il file "
                  "genParametersDict.py\n")
    regOut.write("\nregNameRegs = { # \"index\" : \"addr\"\n")
           
    comma = ","
            
    for regName,regAddr in registers:
        if regName == registers[-1][0]:
            comma = "\n}"
        regOut.write(f"\t\"{regName}\" : {regAddr}{comma}\n")

# with open("configCitirocParameters.vhd","r") as vhdFile:
    
#     line = ""
    
#     while line.find(startParametersStr) < 0:
#         line = vhdFile.readline()
    
#     while line.find(endParametersStr) < 0:
#         line = vhdFile.readline()
#         params.append(parSearch.findall(line))

#     for pp in params:
#         if len(pp) > 0:
#             stdT = pp[0][1]
#             firstBit = pp[0][3]
#             lastBit = pp[0][5]
            
#             names.append(pp[0][0])
            
#             if stdT == "std_logic":
#                 numOfBits.append(1)
#             else:
#                 firstBit = int(firstBit)
#                 lastBit = int(lastBit)
#                 numOfBits.append(firstBit-lastBit+1)

# firstReg = 0x09
# lastReg = 0x09
# firstBitCounter = 0
# lastBitCounter = 0
# totBitCounter = 0
# excess = 0


# with open("valNameRegs.py","w") as pyFile:
#     pyFile.write("# Dizionario generato automaticamente\n"
#                   "# Per correggere eventuali errori modificare il file "
#                   "genParametersDict.py\n")
#     pyFile.write("\nvalNameRegs = { # \"index\" : (MSB register, LSB register,"
#             " first bit list, last bit list, nBits)\n")

#     names.reverse()
#     numOfBits.reverse()
    
#     for i,name in enumerate(names):
#         firstBitList = []
#         lastBitList = []

#         if i == 0:
#             lastBitCounter = 0
#             firstBitCounter += numOfBits[i] - 1
#             totBitCounter += numOfBits[i] - 1
#         else:
#             lastBitCounter += numOfBits[i-1]
#             firstBitCounter += numOfBits[i]
#             totBitCounter += numOfBits[i]

#         if int(totBitCounter/32) > 0:
#             totBitCounter -= 32
#             firstReg += 1

#         if lastBitCounter > 31:
#             lastBitCounter -= 32
#             lastReg += 1

#         if firstBitCounter >= 31:
#             excess = firstBitCounter - 32
            
#             if excess >= 0:
#                 firstBitList.append(excess)
#                 firstBitList.append(31)

#                 lastBitList.append(0)
#                 lastBitList.append(lastBitCounter)

#             elif excess < 0:
#                 firstBitList.append(firstBitCounter)

#                 lastBitList.append(lastBitCounter)

#             firstBitCounter = excess

#         else:
#             firstBitList.append(firstBitCounter)
#             lastBitList.append(lastBitCounter)

#         if i == len(names)-1:
#             comma = '\n}'
#         else:
#             comma = ','

#         pyFile.write("\t\"{}\" : ({:#x}, {:#x}, {}, {}, {}){}\n".format(
#                 name.upper(),
#                 firstReg,
#                 lastReg,
#                 firstBitList,
#                 lastBitList,
#                 numOfBits[i],
#                 comma
#                  ))

