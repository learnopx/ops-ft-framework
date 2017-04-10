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

from opstestfw import *


def LoopbackInterfaceEnable(**kwargs):

    """
    Library function enable / disable interface

    :param deviceObj : Device object
    :type  deviceObj : object
    :param loopback : loopback-interface number context (optional)
    :type  loopback : integer
    :param addr      : address string for IPv4 or IPv6 address
    :type addr       : string
    :param mask      : subnet mask bit
    :type maks       : int
    :return: returnStruct Object
    :returnType: object
    """
    deviceObj = kwargs.get('deviceObj', None)
    loopback = kwargs.get('loopback', None)
    addr = kwargs.get('addr', None)
    mask = kwargs.get('mask', None)
    ipv6flag = kwargs.get('ipv6flag', False)
    config = kwargs.get('config', None)
    config = kwargs.get('config', None)
    enable = kwargs.get('enable', None)

    # If Device object is not passed, we need to error out
    if deviceObj is None:
        LogOutput('error',
                  "Need to pass switch device object deviceObj to this "
                  "routine")
        returnCls = returnStruct(returnCode=1)
        return returnCls

    paramError = 0
    if loopback is None:
        paramError = 1
    if paramError == 1:
        LogOutput('error',
                  "Need to only pass loopback interface")
        returnCls = returnStruct(returnCode=1)
        return returnCls

    overallBuffer = []
    # Get into vtyshelll
    returnStructure = deviceObj.VtyshShell(enter=True)
    returnCode = returnStructure.returnCode()
    overallBuffer.append(returnStructure.buffer())
    if returnCode != 0:
        LogOutput('error', "Failed to get vtysh prompt")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = returnStruct(returnCode=returnCode, buffer=bufferString)
        return returnCls

    # Get into config context
    returnStructure = deviceObj.ConfigVtyShell(enter=True)
    returnCode = returnStructure.returnCode()
    overallBuffer.append(returnStructure.buffer())
    if returnCode != 0:
        LogOutput('error', "Failed to get vtysh config prompt")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = returnStruct(returnCode=1, buffer=bufferString)
        return returnCls
    command1 = ""
    # Get into the interface context
    if loopback is not None:
        if enable is True:
            command1 += "interface loopback " + str(loopback)
            LogOutput('info', "configuring loopback interface ")
        if enable is False:
            command1 += "no interface loopback " + str(loopback)
        LogOutput('info', "after configuring loopback interface ")
        returnStructure = deviceObj.DeviceInteract(command=command1)
        retCode = returnStructure['returnCode']
        overallBuffer.append(returnStructure['buffer'])
        if retCode != 0:
            LogOutput('error', "command failed ! "
                      + str(loopback))
            bufferString = ""
            for curLine in overallBuffer:
                bufferString += str(curLine)
            returnCls = returnStruct(returnCode=retCode, buffer=bufferString)
            return returnCls

    no_inter_check = command1
    # Need to get into the Interface context
    if addr is not None:
        command = ""
        if config is False:
            command = "no "
        if ipv6flag is False:
            command += "ip "
        else:
            command += "ipv6 "
        command += "address " + str(addr) + "/" + str(mask)
        returnStructure = deviceObj.DeviceInteract(command=command)
        retCode = returnStructure['returnCode']
        overallBuffer.append(returnStructure['buffer'])
        if retCode != 0:
            LogOutput('error', "Failed to assign ip to loopback interface "
                      + str(loopback))
        else:
            LogOutput('debug', "assigned IP to loopback interface "
                      + str(loopback))

    # Get out of the interface context
    if "no" not in no_inter_check:
        command = "exit"
        returnStructure = deviceObj.DeviceInteract(command=command)
        retCode = returnStructure['returnCode']
        overallBuffer.append(returnStructure['buffer'])
        if retCode != 0:
            LogOutput('error', "Failed to exit the interface context")

    # Get out of config context
    returnStructure = deviceObj.ConfigVtyShell(enter=False)
    returnCode = returnStructure.returnCode()
    overallBuffer.append(returnStructure.buffer())
    if returnCode != 0:
        LogOutput('error', "Failed to exit vtysh config prompt")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = returnStruct(returnCode=returnCode, buffer=bufferString)
        return returnCls

    # Get out of vtyshell
    returnStructure = deviceObj.VtyshShell(enter=False)
    returnCode = returnStructure.returnCode()
    overallBuffer.append(returnStructure.buffer())
    if returnCode != 0:
        LogOutput('error', "Failed to exit vtysh prompt")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = returnStruct(returnCode=returnCode, buffer=bufferString)
        return returnCls

    # Return results
    bufferString = ""
    for curLine in overallBuffer:
        bufferString += str(curLine)
    returnCls = returnStruct(returnCode=0, buffer=bufferString)
    return returnCls
