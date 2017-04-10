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


def Dot1qEncapsulation(**kwargs):

    """
    Library function enable / disable interface

    :param deviceObj : Device object
    :type  deviceObj : object
    :param subInterface : sub-interface number context (optional)
    :type  subInterface : integer
    :param dot1q      : enables dot1q encapsulation
    :type dot1q       : bool
    :param vlan      : vlan id
    :type vlan       : int
    :return: returnStruct Object
    :returnType: object
    """
    deviceObj = kwargs.get('deviceObj', None)
    subInterface = kwargs.get('subInterface', None)
    dot1q = kwargs.get('dot1q', None)
    vlan = kwargs.get('vlan', None)

    # If Device object is not passed, we need to error out
    if deviceObj is None:
        LogOutput('error',
                  "Need to pass switch device object deviceObj to this "
                  "routine")
        returnCls = returnStruct(returnCode=1)
        return returnCls

    paramError = 0
    if subInterface is None:
        paramError = 1
    if paramError == 1:
        LogOutput('error',
                  "Need to only pass sub-interface")
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

    # Get into the interface context
    if subInterface is not None:
        command = "interface " + str(subInterface)
        LogOutput('info', "configuring sub-interface ")
    LogOutput('info', "after configuring sub-interface ")
    returnStructure = deviceObj.DeviceInteract(command=command)
    retCode = returnStructure['returnCode']
    overallBuffer.append(returnStructure['buffer'])
    if retCode != 0:
        LogOutput('error', "Failed to enter loopback interface context "
                  + str(loopback))
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = retStruct(returnCode=retCode, buffer=bufferString)
        return returnCls

    # Need to get into the Interface context
    if dot1q is True:
        if vlan is not None:
            command = "encapsulation dot1Q " + str(vlan)
            returnStructure = deviceObj.DeviceInteract(command=command)
            retCode = returnStructure['returnCode']
            overallBuffer.append(returnStructure['buffer'])
            if retCode != 0:
                LogOutput('error', "Failed to enable encapsulation dto1q vlan "
                          + str(vlan))
            else:
                LogOutput('debug', "enabled dot1q encapsulation ")
    else:
        command = "no encapsulation dot1Q " + str(vlan)
        returnStructure = deviceObj.DeviceInteract(command=command)
        retCode = returnStructure['returnCode']
        overallBuffer.append(returnStructure['buffer'])
        if retCode != 0:
            LogOutput('error', "Failed to enable encapsulation dto1q vlan "
                      + str(vlan))
        else:
            LogOutput('debug', "enabled dot1q encapsulation ")

    # Get out of the interface context
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
        returnCls = retStruct(returnCode=returnCode, buffer=bufferString)
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
        returnCls = retStruct(returnCode=returnCode, buffer=bufferString)
        return returnCls

    # Return results
    bufferString = ""
    for curLine in overallBuffer:
        bufferString += str(curLine)
    returnCls = returnStruct(returnCode=0, buffer=bufferString)
    return returnCls
