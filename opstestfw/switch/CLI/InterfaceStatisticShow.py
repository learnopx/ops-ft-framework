# (C) Copyright 2015 Hewlett Packard Enterprise Development LP
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import opstestfw
import re
import pdb


def InterfaceStatisticsShow(**kwargs):
    """
    Library function get statistics for an specific interface

    :param deviceObj : Device object
    :type  deviceObj : object
    :param interface : interface to configure
    :type  interface : integer

    :return: returnStruct Object
                 data:
                   RX: inputPackets,inputErrors,CRC_FCS,bytes,
                       dropped
                   TX: outputPackets,inputError,collision,bytes,dropped

    :returnType: object
    """

    # Params
    deviceObj = kwargs.get('deviceObj', None)
    interface = kwargs.get('interface', None)

    # Variables
    overallBuffer = []
    data = dict()
    bufferString = ""
    command = ""
    returnCode = 0

    # Dictionary initialization
    data['RX'] = []
    data['TX'] = []

    if deviceObj is None:
        opstestfw.LogOutput('error',
                            "Need to pass switch deviceObj to this routine")
        returnCls = opstestfw.returnStruct(returnCode=1)
        return returnCls

    # Get into vtyshelll
    returnStructure = deviceObj.VtyshShell(enter=True)
    returnCode = returnStructure.returnCode()
    overallBuffer.append(returnStructure.buffer())
    if returnCode != 0:
        opstestfw.LogOutput('error', "Failed to get vtysh prompt")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = opstestfw.returnStruct(returnCode=1, buffer=bufferString)
        return returnCls

    # Send Command
    command = "show interface"
    if interface is not None:
        command += " " + str(interface)
    opstestfw.LogOutput('info', "Show interface statistics.*****" + command)
    returnDevInt = deviceObj.DeviceInteract(command=command)
    retCode = returnDevInt['returnCode']
    overallBuffer.append(returnDevInt['buffer'])
    # temporaryBuffer = returnDevInt['buffer']

    if retCode != 0:
        opstestfw.LogOutput('error', "Failed to get information ." + command)

    # Get out of the Shell
    # Get out of vtyshell
    returnStructure = deviceObj.VtyshShell(enter=False)
    returnCode = returnStructure.returnCode()
    overallBuffer.append(returnStructure.buffer())
    if returnCode != 0:
        opstestfw.LogOutput('error', "Failed to exit vtysh prompt")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = opstestfw.returnStruct(returnCode=1, buffer=bufferString)
        return returnCls

    # End Return Command

    # Return The Dict responds

    for curLine in overallBuffer:
        bufferString += str(curLine)
    bufferSplit = bufferString.split("\r\n")

    rx = dict()
    tx = dict()
    # Filling up the dictionaries

    rxTokens = re.findall(
        r'RX\s*\r\n\s*(\d*)\s*input\s*packets\s*(\d*)\s*bytes\s*\r\n\s*' +
        '(\d*)\s*input\s*error\s*(\d*)\s*dropped\s*\r\n\s*(\d*)', bufferString)
    txTokens = re.findall(
        r'TX\s*\r\n\s*(\d*)\s*output\s*packets\s*(\d*)\s*bytes\s*\r\n\s*' +
        '(\d*)\s*input\s*error\s*(\d*)\s*dropped\s*\r\n\s*(\d*)', bufferString)
    if rxTokens:
        rx['inputPackets'] = rxTokens[0][0]
        rx['bytes'] = rxTokens[0][1]
        rx['inputErrors'] = rxTokens[0][2]
        rx['dropped'] = rxTokens[0][3]
        rx['CRC_FCS'] = rxTokens[0][4]
    else:
        returnCode = 1
        opstestfw.LogOutput('error', "Failed to get information ." + command)

    if txTokens:
        tx['outputPackets'] = txTokens[0][0]
        tx['bytes'] = txTokens[0][1]
        tx['inputErrors'] = txTokens[0][2]
        tx['dropped'] = txTokens[0][3]
        tx['collision'] = txTokens[0][4]
    else:
        returnCode = 1
        opstestfw.LogOutput('error', "Failed to get information ." + command)

    data['RX'] = rx
    data['TX'] = tx

    # Return results
    bufferString = ""
    for curLine in overallBuffer:
        bufferString += str(curLine)
    returnCls = opstestfw.returnStruct(
        returnCode=returnCode, buffer=bufferString, data=data)
    return returnCls
