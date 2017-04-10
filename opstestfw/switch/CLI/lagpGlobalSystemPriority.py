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


import opstestfw.switch
import opstestfw


def lagpGlobalSystemPriority(**kwargs):

    """
    Function to configure Global LACP system Priority

    :param deviceObj : Device object
    :type  deviceObj : object
    :param systemPriority  : Identification Default is system MAC address,
                             can be changed for another one
    :type  systemPriority  : string
    :param configure : (Optional -Default is True)
                       True to configure,
                       False to unconfigure
    :type  configure : boolean

    :return: returnStruct Object
    :returnType: object
    """

    # Params
    deviceObj = kwargs.get('deviceObj', None)
    systemPriority = kwargs.get('systemPriority', None)
    configure = kwargs.get('configure', True)

    # Variables
    overallBuffer = []
    data = dict()
    bufferString = ""
    command = ""

    # If Device object is not passed, we need to error out
    if deviceObj is None or systemPriority is None:
        opstestfw.LogOutput('error',
                            "Need to pass switch deviceObj and systemPriority"
                            " to this routine")
        returnCls = opstestfw.returnStruct(returnCode=1)
        return returnCls

    # Get into vtysh
    returnStructure = deviceObj.VtyshShell(enter=True)
    returnCode = returnStructure.returnCode()
    overallBuffer.append(returnStructure.buffer())
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
        returnCls = opstestfw.returnStruct(returnCode=1,
                                           buffer=bufferString)
        return returnCls

    # Uconfigure system ID
    if configure is False:
        command = "no "

    # Normal configuration command
    command += ("lacp system-priority " + str(systemPriority))
    returnStructure = deviceObj.DeviceInteract(command=command)
    retCode = returnStructure['returnCode']
    overallBuffer.append(returnStructure['buffer'])
    if retCode != 0:
        opstestfw.LogOutput('error',
                            "Failed to configure LACP system priority: "
                            + str(systemPriority))
    else:
        opstestfw.LogOutput('debug',
                            "LACP system priority configured: "
                            + str(systemPriority))

    # Get out of config context
    returnStructure = deviceObj.ConfigVtyShell(enter=False)
    returnCode = returnStructure.returnCode()
    overallBuffer.append(returnStructure.buffer())
    if returnCode != 0:
        opstestfw.LogOutput('error',
                            "Failed to exit configure terminal prompt")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = opstestfw.retStruct(returnCode=returnCode,
                                        buffer=bufferString)
        return returnCls

    # Get out of vtyshell
    returnStructure = deviceObj.VtyshShell(enter=False)
    returnCode = returnStructure.returnCode()
    overallBuffer.append(returnStructure.buffer())
    if returnCode != 0:
        opstestfw.LogOutput('error', "Failed to exit enable prompt")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = opstestfw.retStruct(returnCode=returnCode,
                                        buffer=bufferString)
        return returnCls

    # Return results
    for curLine in overallBuffer:
        bufferString += str(curLine)
    returnCls = opstestfw.returnStruct(returnCode=0, buffer=bufferString,
                                       data=data)
    return returnCls
