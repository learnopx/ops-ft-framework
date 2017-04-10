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
import pexpect


def hostIperfServerStart(** kwargs):
    """
    Library function to receive traffic using iperf.

    :param deviceObj : Device object
    :type  deviceObj : object
    :param protocol : UDP or TCP
    :type protocol  : string
    :param interval : Result reporting interval
    :type interval  : integer
    :param port   : server port number
    :type port    : integer

    :return: returnStruct Object
        data: - Dictionary:
               'Client IP': Server IP address
               'Client port': Client port
               'Server IP': Server IP address
               'Server port': Server port
    :returnType: object
    """

    # Params
    deviceObj = kwargs.get('deviceObj', None)
    port = kwargs.get('port', 5001)
    protocol = kwargs.get('protocol', 'TCP')
    interval = kwargs.get('interval', 1)
    # Variables
    bufferString = ''

    # If device is not passed, we need error message
    if deviceObj is None:
        opstestfw.LogOutput('error', "Need to pass device to configure")
        returnJson = opstestfw.returnStruct(returnCode=1)
        return returnJson

    # Verify if iperf is installed on host assuming it is Ubuntu and then
    # install it
    command = 'iperf'
    opstestfw.LogOutput(
        'debug', "Verifying if iperf is installed on device " +
        deviceObj.device)
    deviceObj.expectHndl.sendline(command)
    index = deviceObj.expectHndl.expect(
        ['Usage', '(command not found)|(install)'])
    bufferString += str(deviceObj.expectHndl.before)
    if index == 0:
        # In case iperf is installed
        index = deviceObj.expectHndl.expect(['# ', pexpect.TIMEOUT],
                                            timeout=5)
        bufferString += str(deviceObj.expectHndl.before)
        if index == 1:
            opstestfw.LogOutput(
                'error', "Error while verifying status of iperf on device " +
                deviceObj.device)
            return opstestfw.returnStruct(returnCode=1, buffer=bufferString)
    else:
        # In case iperf is not installed
        index = deviceObj.expectHndl.expect(['# ', pexpect.TIMEOUT],
                                            timeout=5)
        bufferString += str(deviceObj.expectHndl.before)
        if index == 1:
            opstestfw.LogOutput(
                'error', "Error while verifying status of iperf on device " +
                deviceObj.device)
            return opstestfw.returnStruct(returnCode=1, buffer=bufferString)
        opstestfw.LogOutput('debug', "Installing iperf")
        command = 'apt-get install iperf'
        deviceObj.expectHndl.sendline(command)
        index = deviceObj.expectHndl.expect(
            ['# ', pexpect.TIMEOUT], timeout=40)
        bufferString += str(deviceObj.expectHndl.before)
        if index == 1:
            opstestfw.LogOutput(
                'error', "Error while installing iperf on device " +
                deviceObj.device)
            return opstestfw.returnStruct(returnCode=1, buffer=bufferString)
        command = 'iperf'
        deviceObj.expectHndl.sendline(command)
        index = deviceObj.expectHndl.expect(
            ['Usage', '(command not found)|(install)', pexpect.TIMEOUT],
            timeout=5)
        bufferString += str(deviceObj.expectHndl.before)
        if index != 0:
            opstestfw.LogOutput('error', "Could not install iperf correctly")
            index = deviceObj.expectHndl.expect(
                ['# ', pexpect.TIMEOUT], timeout=5)
            bufferString += str(deviceObj.expectHndl.before)
            if index != 0:
                opstestfw.LogOutput('error', "Unknown error on device")
                return opstestfw.returnStruct(returnCode=1,
                                              buffer=bufferString)
            return opstestfw.returnStruct(returnCode=1, buffer=bufferString)
        else:
            index = deviceObj.expectHndl.expect(
                ['# ', pexpect.TIMEOUT], timeout=5)
            bufferString += str(deviceObj.expectHndl.before)
            if index != 0:
                opstestfw.LogOutput('error', "Unknown error on device")
                return opstestfw.returnStruct(returnCode=1,
                                              buffer=bufferString)
        opstestfw.LogOutput('debug', "Successfully installed iperf on device")

    command = 'iperf -s -p ' + str(port)
    command += ' -i ' + str(interval)
    if protocol == 'UDP':
        command += ' -u'

    deviceObj.expectHndl.sendline(command)

    # Compile information to return
    returnCls = opstestfw.returnStruct(returnCode=0, buffer=bufferString)
    return returnCls
