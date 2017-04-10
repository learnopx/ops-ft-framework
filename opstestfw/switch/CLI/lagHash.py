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
#

import opstestfw


def lagHash(**kwargs):

    """
    Library function to configure fallback settings for a LAG working in
    dynamic mode

    :param deviceObj : Device object
    :type  deviceObj : object
    :param lagId     : LAG Identifier
    :type  lagId     : integer
    :param hashType  : l2-src-dst/l3-dsrc-dst hashing algortihms
    :type  hashType  : string

    :return: returnStruct Object
    :returnType: object
    """

    # Params
    lagId = kwargs.get('lagId', None)
    deviceObj = kwargs.get('deviceObj', None)
    hashType = kwargs.get('hashType', 'l3-src-dst')

    # Variables
    overallBuffer = []
    finalReturnCode = 0

    # If deviceObj, lagId, hashType are not present, display an error
    if deviceObj is None or lagId is None:
        opstestfw.LogOutput('error',
                            "Need to pass deviceObj and lagId to use "
                            "this routine")
        returnCls = opstestfw.returnStruct(returnCode=1)
        return returnCls

    # If hashType is different from l2-src-dst and l3-src-dst throw an error
    if hashType != 'l2-src-dst' and hashType != 'l3-src-dst':
        opstestfw.LogOutput('error',
                            "hashType must be l2-src-dst or l3-src-dst")
        returnCls = opstestfw.returnStruct(returnCode=1)
        return returnCls

    # Get into vtyshelll
    returnStructure = deviceObj.VtyshShell(enter=True)
    overallBuffer.append(returnStructure.buffer())
    returnCode = returnStructure.returnCode()
    if returnCode != 0:
        opstestfw.LogOutput('error', "Failed to get vtysh prompt")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = opstestfw.returnStruct(returnCode=returnCode,
                                           buffer=bufferString)
        return returnCls

    # Get into config context
    returnStructure = deviceObj.ConfigVtyShell(enter=True)
    returnCode = returnStructure.returnCode()
    overallBuffer.append(returnStructure.buffer())
    if returnCode != 0:
        opstestfw.LogOutput('error', "Failed to get vtysh config prompt")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = opstestfw.returnStruct(returnCode=returnCode,
                                           buffer=bufferString)
        return returnCls

    # enter LAG configuration context
    command = "interface lag %s" % str(lagId)
    returnDevInt = deviceObj.DeviceInteract(command=command)
    returnCode = returnDevInt['returnCode']
    overallBuffer.append(returnDevInt['buffer'])
    if returnCode != 0:
        opstestfw.LogOutput('error', "Failed to create LAG " + str(lagId)
                            + " on device " + deviceObj.device)
    else:
        opstestfw.LogOutput('debug', "Created LAG " + str(lagId)
                            + " on device " + deviceObj.device)

    # Generate command to query switch
    if hashType == 'l2-src-dst':
        command = "hash l2-src-dst"
    else:
        command = "hash l2-src-dst"

    returnDevInt = deviceObj.DeviceInteract(command=command)
    finalReturnCode = returnDevInt['returnCode']
    overallBuffer.append(returnDevInt['buffer'])
    if finalReturnCode != 0:
        opstestfw.LogOutput('error', "Failed to configure " + hashType
                            + " hashing on interface lag " + str(lagId)
                            + " on device " + deviceObj.device)
    else:
        opstestfw.LogOutput('debug',
                            "Configured l2-src-dst hashing on interface lag "
                            + str(lagId) + " on device " + deviceObj.device)

    # exit LAG configuration context
    command = "exit"
    returnDevInt = deviceObj.DeviceInteract(command=command)
    returnCode = returnDevInt['returnCode']
    overallBuffer.append(returnDevInt['buffer'])
    if returnCode != 0:
        opstestfw.LogOutput('error', "Failed to exit LAG " + str(lagId)
                            + " configuration context")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = opstestfw.returnStruct(returnCode=1, buffer=bufferString)
        return returnCls

    # Get out of  config context
    returnStructure = deviceObj.ConfigVtyShell(enter=False)
    returnCode = returnStructure.returnCode()
    overallBuffer.append(returnStructure.buffer())
    if returnCode != 0:
        opstestfw.LogOutput('error',
                            "Failed to get out of vtysh config context")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = opstestfw.returnStruct(returnCode=returnCode,
                                           buffer=bufferString)
        return returnCls

    # Get out of vtyshell
    returnStructure = deviceObj.VtyshShell(enter=False)
    returnCode = returnStructure.returnCode()
    overallBuffer.append(returnStructure.buffer())
    if returnCode != 0:
        opstestfw.LogOutput('error', "Failed to exit vty shell")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = opstestfw.returnStruct(returnCode=returnCode,
                                           buffer=bufferString)
        return returnCls

    # Compile information to return
    bufferString = ""
    for curLine in overallBuffer:
        bufferString += str(curLine)
    returnCls = opstestfw.returnStruct(returnCode=finalReturnCode,
                                       buffer=bufferString)
    return returnCls
