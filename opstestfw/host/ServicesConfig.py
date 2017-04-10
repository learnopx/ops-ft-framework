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


def ServicesConfig(** kwargs):
    """
    Library function to start/stop/restart services on Ubuntu workstations

    :param deviceObj : Device object
    :type  deviceObj : object
    :param service : Server service (dhcpd/tftp/radiusd)
    :type service  : string
    :param action : service action (start/stop/restart)
    :type action  : string

    :return: returnStruct Object
    :returnType: object
    """

    # Params
    deviceObj = kwargs.get('deviceObj', None)
    service = kwargs.get('service', None)
    action = kwargs.get('action', 'start')
    # Variables
    overallBuffer = []
    bufferString = ''
    returnCode = 0

    # If device is not passed, we need error message
    if deviceObj is None:
        opstestfw.LogOutput('error', "Need to pass device object")
        returnJson = opstestfw.returnStruct(returnCode=1)
        return returnJson

    # Move files on workstation to destination path
    # For DHCP service on Ubuntu workstations
    if service == "dhcpd":
        server_service = "isc-dhcp-server"
    elif service == "freeradius":
    # freeradius service on Ubuntu workstation
        server_service = "freeradius"
    elif service == "tftp" :
    #tftpd service for ubuntu
        server_service = "tftpd-hpa"
    command = "service %s %s" % (server_service, action)

    returnStruct = deviceObj.DeviceInteract(command=command)
    returnCode = returnStruct.get('returnCode')
    buffer = returnStruct.get('buffer')
    overallBuffer.append(buffer)
    if returnCode != 0:
        opstestfw.LogOutput(
            'error', "Failed to %s service %s on %s->" %
            (action, service, deviceObj.device))
        returnCls = opstestfw.returnStruct(
            returnCode=returnCode,
            buffer=buffer)
        return returnCls
    else:
        opstestfw.LogOutput(
            'info', "%s service %s , get the pid" %
            (action, service))
        command = "pgrep " + service
        returnStruct = deviceObj.DeviceInteract(command=command)
        returnCode = returnStruct.get('returnCode')
        buffer = returnStruct.get('buffer')

    # Configure service
    command = "pgrep " + service
    returnStruct = deviceObj.DeviceInteract(command=command)
    returnCode = returnStruct.get('returnCode')
    buffer = returnStruct.get('buffer')
    overallBuffer.append(buffer)
    if returnCode != 0 and service != "stop":
        opstestfw.LogOutput(
            'error', "service %s on %s :: %s->" %
            (service, deviceObj.device, action))
        returnCls = opstestfw.returnStruct(
            returnCode=returnCode,
            buffer=buffer)
        return returnCls
    else:
        opstestfw.LogOutput('info', "Service %s -> %s->" % (service, action))

    for curLine in overallBuffer:
        bufferString += str(curLine)
    # Compile information to return
    returnCls = opstestfw.returnStruct(returnCode=0, buffer=bufferString)
    return returnCls


def GetServicePID(**kwargs):
    """
    Library function to get the PID of a server service

    :param deviceObj : Device object
    :type  deviceObj : object
    :param service :  service(freeradius/dhcpd/tftp)
    :type service  : string

    :return: returnStruct Object
        data: - Dictionary:
               'pid': PID of the service running
    :returnType: object
    """

    service = kwargs.get('service', None)
    deviceObj = kwargs.get('deviceObj', None)
    returnDict = dict()
    returnCode = 0
    # Confirm service pid
    command = "pgrep " + str(service)
    returnStruct = deviceObj.DeviceInteract(command=command)
    returnCode = returnStruct.get('returnCode')
    buffer = returnStruct.get('buffer')
    if returnCode != 0:
        opstestfw.LogOutput(
            'error', "pid for service %s : service not running" %
            (service))
        returnCls = opstestfw.returnStruct(
            returnCode=returnCode,
            data=returnDict,
            buffer=buffer)
    else:
        splitBuffer = buffer.split("\r\n")
        for line in splitBuffer:
            line = line.strip()
            pidMatch = re.match(r'(\d+)', line)
            if pidMatch:
                returnDict['pid'] = pidMatch.group(1)
                opstestfw.LogOutput(
                    'info', "%s service pid :: %s" %
                    (service, returnDict['pid']))

    # Compile information to return
    returnCls = opstestfw.returnStruct(
        returnCode=returnCode,
        data=returnDict,
        buffer=buffer)
    return returnCls
