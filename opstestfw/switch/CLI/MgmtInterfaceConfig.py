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

from opstestfw import *
import re
import time


def MgmtInterfaceConfig(**kwargs):

    """
    Library function configure/unconfigure IPv4 / IPv6 address, gateway, nameserver on management interface, 

    :param deviceObj	       : Device object
    :param addr                : IP Address string for IPV4 and IPV6
    :type  addr                : string
    :param mask                : subnet mask bit
    :type mask                 : string:
    :param ipmode	       : ipmode whether static or dhcp
    :type maks		       : string
    :param gateway	       : Gateway Address string for IPV4 and IPV6
    :type gateway              : string
    :param primarynameserver   : True for secondary address, False for not
    :type primarynameserver    : boolean
    :param secondarynameserver : True for secondary address, False for not
    :type secondarynameserver  : boolean
    :param config    : True to configure address
                       False to unconfigure address
                       Defaults to True
    :type config     : boolean
    :return: returnStruct Object
    :returnType: object
    """

    deviceObj = kwargs.get('deviceObj', None)
    addr = kwargs.get('addr', None)
    mask = kwargs.get('mask', None)
    ipmode = kwargs.get('ipmode', 'static')
    gateway = kwargs.get('gateway', None)
    primarynameserver = kwargs.get('primarynameserver', None)
    secondarynameserver = kwargs.get('secondarynameserver', None)
    config = kwargs.get('config', True)

    overallBuffer = []
    # If Device object is not passed, we need to error out
    if deviceObj is None:
        LogOutput('error', "Need to pass switch device object to this routine")
        returnCls = returnStruct(returnCode=1)
        return returnCls

    
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

    # Get into the management interface context
    # if interface is not None:
    command = "interface mgmt"
    returnStructure = deviceObj.DeviceInteract(command=command)
    retCode = returnStructure['returnCode']
    overallBuffer.append(returnStructure['buffer'])
    if retCode != 0:
        LogOutput(
            'error',
            "Failed to enter management interface context for interface ")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = returnStruct(returnCode=1, buffer=bufferString)
        return returnCls

    # Configuring IP address on management interface

    if config is True:

        if ipmode == "static":

            command = "ip static " + str(addr) + "/" + str(mask)
            returnStructure = deviceObj.DeviceInteract(command=command)
            retCode = returnStructure['returnCode']
            overallBuffer.append(returnStructure['buffer'])

            # Configuring gateway address on management interface

            if gateway is not None:
                command = "default-gateway " + str(gateway)
                command += "\r"
            returnStructure = deviceObj.DeviceInteract(command=command)
            retCode = returnStructure['returnCode']
            overallBuffer.append(returnStructure['buffer'])

            if primarynameserver is not None:
                command = ""
                if secondarynameserver is not None:
                    command = "nameserver " + str(
                        primarynameserver) + " " + str(
                        secondarynameserver) + "\r"
                else:
                    command = "nameserver " + str(primarynameserver) + "\r"

            returnStructure = deviceObj.DeviceInteract(command=command)
            retCode = returnStructure['returnCode']
            overallBuffer.append(returnStructure['buffer'])

        else:
            command = "ip dhcp"
            command += "\r"
            returnStructure = deviceObj.DeviceInteract(command=command)
            retCode = returnStructure['returnCode']
            overallBuffer.append(returnStructure['buffer'])

        if retCode != 0:
            LogOutput(
                'error',
                "Failed to configure management interface configs")

    else:
        # Un Configuring gateway address on management interface
        if gateway is not None:
            command = "no default-gateway " + str(gateway)

        returnStructure = deviceObj.DeviceInteract(command=command)
        retCode = returnStructure['returnCode']
        overallBuffer.append(returnStructure['buffer'])

        # Un Configuring name server address on management interface

        if primarynameserver is not None:
            command = ""
            if secondarynameserver is not None:
                command += "no nameserver " + \
                    str(primarynameserver) + " " + str(secondarynameserver)
            else:
                command += "no nameserver " + str(primarynameserver)

            
        returnStructure = deviceObj.DeviceInteract(command=command)
        retCode = returnStructure['returnCode']
        overallBuffer.append(returnStructure['buffer'])

        # Un Configuring IP configs on management interface

        if addr is not None and mask is not None:

            command = "no ip static " + str(addr) + "/" + str(mask)

            
        returnStructure = deviceObj.DeviceInteract(command=command)
        retCode = returnStructure['returnCode']
        overallBuffer.append(returnStructure['buffer'])

        if retCode != 0:

            LogOutput(
                'error',
                "Failed to Unconfigure management interface configs")

    # Get out of the interface context
    command = "exit \r"
    returnStructure = deviceObj.DeviceInteract(command=command)
    retCode = returnStructure['returnCode']
    overallBuffer.append(returnStructure['buffer'])
    if retCode != 0:
        LogOutput('error', "Failed to exit the interface context")

    # Get into config context
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
