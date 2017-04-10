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

from opstestfw import *


def GetLinuxInterfaceIp(**kwargs):

    """
    Library function to get the IP address on an eth0 interface

    :param deviceObj : Device object
    :type  deviceObj : object

    :return: returnStruct Object
    :returnType: object
    """

    deviceObj = kwargs.get('deviceObj', None)
    returnCode = 0
    ipAddr = None
    overallBuffer = []
    # If Device object is not passed, we need to error out
    if deviceObj is None:
        LogOutput('error', "Pass switch/wrkstn device object to this routine")
        returnCls = returnStruct(returnCode=1)
        return returnCls

    # Get the interface ip
    command = "ifconfig eth0 | grep 'inet addr'"
    returnStructure = deviceObj.DeviceInteract(command=command)
    retCode = returnStructure['returnCode']
    buf = returnStructure['buffer']

    overallBuffer.append(buf)
    if retCode != 0:
        LogOutput(
            'error',
            "Failed to ifconfig on eth0 interface for the device")
        returnCode = 1
    else:
        LogOutput(
            'info',
            "Success to ifconfig on eth0 interface for the device")
        print buf
        if buf.find("inet addr:") != -1:
            inetAddr = buf.split('\n')
            listSize = len(inetAddr)
            for i in range(0, listSize-1):
                if inetAddr[i].find("inet addr:") != -1:
                    ipAddrList = inetAddr[i].split(' ')
                    ipAddrItem = ipAddrList[11].split(':')
                    if len(ipAddrItem) > 1:
                        ipAddr = ipAddrItem[1]
                    else:
                        ipAddr = ""
                else:
                    ipAddr = ""
        else:
            ipAddr = ""

    bufferString = ""
    for curLine in overallBuffer:
        bufferString += str(curLine)
    returnCls = returnStruct(
        returnCode=returnCode,
        data=ipAddr,
        buffer=bufferString)
    return returnCls
