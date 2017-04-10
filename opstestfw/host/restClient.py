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

"""
This host library provides APIs to run restStress test and to check the status

"""

import opstestfw.switch
import opstestfw.host
import opstestfw.gbldata
from opstestfw import *
import socket


def RestStress(**kwargs):
    """
    restStress Method

    This method used to use host as REST client to issue REST stress request
        :param hostHandle  where the stress command needs to be issued
        :type hostHandle: host object handle
        :param ip: REST server IP running on the switch
        :type ip: string
        :param clientId: Rest client identifier for a given host
        :type clientId: integer
        :param restDataFile: REST input data file for the stress test
        :type restDataFile: string
        :param iterations: no of loops to repeat the stress test
        :type iterations: integer
        :return: returnStruct Object
        :rtype: object
        """
    host = kwargs.get('hostHandle')
    ip = kwargs.get('ip')
    clientId = kwargs.get('clientId', 10)
    restDataFileName = kwargs.get('restDataFile')
    iterations = kwargs.get('iterations', 10)
    returnCode = 0
    try:
        socket.inet_pton(socket.AF_INET, ip)
    except socket.error:
        returnCode = 1
    if returnCode != 1:
        restCmd = "python /root/restEnv/reststress.py --ip=%s --clientId=%d\
                   --file=%s --iterations=%d" % (ip, clientId,
                                                 restDataFileName,
                                                 iterations)
        retDeviceInt = host.DeviceInteract(command=restCmd)
        retCode = retDeviceInt.get('returnCode')
        retBuff = retDeviceInt.get('buffer')
        if retCode != 0:
            opstestfw.LogOutput('error', 'Failed to execute the command : '
                                + restCmd)
            returnCode = 1
        else:
            opstestfw.LogOutput('info',
                                'Successfully executed the command : '
                                + restCmd)

    returnCls = opstestfw.returnStruct(
        returnCode=returnCode,
        buffer=retBuff)
    return returnCls


def RestResultFileChk(**kwargs):
    """
    RestResultFileChk Method

    This method used to check REST stress result in the form of file
        :param hostHandle  where the stress command needs to be issued
        :type hostHandle: host object handle
        :param clientId: Rest client identifier for a given host
        :type clientId: integer
        :param result: check for the result status either pass or fail
        :type result: string
        :return: returnStruct Object
        :rtype: object
        """
    host = kwargs.get('hostHandle')
    clientId = kwargs.get('clientId', 10)
    result = kwargs.get('result', "pass")
    fileName = "reststress_%s_%s" % (result, clientId)
    retDeviceInt = host.FileTransfer("/tmp/" + fileName,
                                     "/root/restEnv/" + fileName, "get")
    return retDeviceInt
