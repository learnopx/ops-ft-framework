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
import pexpect
import opstestfw
import re


def hostIperfClientStop(** kwargs):
    """
    Library function to generate traffic using iperf.

    :param deviceObj : Device object
    :type  deviceObj : object

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

    #Variable initialization
    retBuffer = ''

    # If device is not passed, we need error message
    if deviceObj is None:
        opstestfw.LogOutput('error', "Need to pass device to configure")
        returnStruct = opstestfw.returnStruct(returnCode=1)
        return returnStruct

    deviceObj.expectHndl.expect(['# ', pexpect.TIMEOUT], timeout=1)
    retBuffer = deviceObj.expectHndl.before

    ips_and_ports = re.search(
        'local (.*) port (\d+) connected with (.*) port (\d+)',
        deviceObj.expectHndl.before)

    traffic_data = re.findall('sec  ([.\d]+ .*?)  ([.\d]+ .+)\r',
                              deviceObj.expectHndl.before)

    # If client fails result is None and returnList == []
    server_ip = None
    server_port = None
    client_ip = None
    client_port = None

    if ips_and_ports is not None:
        server_ip = ips_and_ports.group(1)
        server_port = ips_and_ports.group(2)
        client_ip = ips_and_ports.group(3)
        client_port = ips_and_ports.group(4)

    data_dict = {}

    data_dict['Server IP'] = server_ip
    data_dict['Server port'] = server_port
    data_dict['Client IP'] = client_ip
    data_dict['Client port'] = client_port
    data_dict['Traffic data'] = traffic_data

    command = '\003'
    deviceObj.expectHndl.send(command)
    deviceObj.expectHndl.expect('#')
    retBuffer += deviceObj.expectHndl.before

    # Compile information to return
    returnCls = opstestfw.returnStruct(returnCode=0,
                                       buffer=retBuffer,
                                       data=data_dict)
    return returnCls
