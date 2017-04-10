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
import re


def ShowVlan(**kwargs):
    """
    Library function to show the VLANs.

    :param deviceObj : Device object
    :type  deviceObj : object
    :return: returnStruct Object
            buffer
            data keys
                Status - string set to "up" or "down"
                Reserved - string
                Name - string set to the name of the VLAN
                VLAN - string set to the id of the VLAN
                Reason - string
                Ports - list of strings
    :returnType: object
    """
    deviceObj = kwargs.get('deviceObj', None)

    overallBuffer = []
    # If Device object is not passed, we need to error out
    if deviceObj is None:
        opstestfw.LogOutput('error',
                            "Need to pass switch device object deviceObj "
                            "to this routine")
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

    command = "show vlan"

    returnDevInt = deviceObj.DeviceInteract(command=command)
    retCode = returnDevInt['returnCode']
    overallBuffer.append(returnDevInt['buffer'])
    temporaryBuffer = returnDevInt['buffer']
    if retCode != 0:
        opstestfw.LogOutput('error', "Failed to create VLAN." + command)
    else:
        opstestfw.LogOutput('debug', "Created VLAN." + command)

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

    result = []
    opstestfw.LogOutput('debug', "Buffer: " + temporaryBuffer)
    rgx = r'(VLAN|vlan|Vlan)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)'
    keys = re.findall(rgx, temporaryBuffer)

    temporaryBuffer = temporaryBuffer.encode('string-escape')
    opstestfw.LogOutput('debug', "Keys: " + str(keys))
    opstestfw.LogOutput('debug', "Buffer: " + temporaryBuffer)
    if len(keys) == 1:
        keys = keys[0]
        rgx = r'(\d+)\s+(\w+)\s+(\w+)\s+([\w_]+)\s*(\(\w+\))?\s*([0-9\- ,]+)?'
        vlans = \
            re.findall(rgx, temporaryBuffer)

        opstestfw.LogOutput('debug', "Vlans: " + str(vlans))
        for vlan in vlans:
            dictionary = {}
            for key, value in zip(keys, vlan):
                if key == 'Ports':
                    dictionary[key] = value.split(', ')
                else:
                    dictionary[key] = value
            result.append(dictionary)

    # Return results
    bufferString = ""
    for curLine in overallBuffer:
        bufferString += str(curLine)
    returnCls = opstestfw.returnStruct(returnCode=0, buffer=bufferString,
                                       data=result)
    return returnCls
