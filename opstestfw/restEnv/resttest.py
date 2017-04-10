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


import RestService
import pprint
import json
import argparse


def resttest():
    '''
    workstation python REST client utility sends a json request using the
    RestService object and prints the output on the host console

    :param ip: REST server ip address
    :type ip: string
    :param url: REST resource url
    :type url: string
    :param method: REST/HTTP method name POST/GET/PUT or DELETE
    :type method: string
    :param data: data body for the method if any
    :type data: JSON string
    :return: None
    :rtype: None
    '''

    ip = args.ip
    url = args.url
    method = args.method
    inputData = args.inputData
    expectedData = args.expectedData
    rest_handle = RestService.RestService(switch_ip=ip)
    if method == "POST" or method == "PUT":
        with open('/root/restEnv/restdata', 'rb') as f:
            inputData = json.load(f)

    if (method == "GET"):
        result = rest_handle.getResponse(url)
    elif (method == "POST"):
        result = rest_handle.postResponse(url, inputData)
    elif (method == "PUT"):
        result = rest_handle.putResponse(url, inputData)
    elif (method == "DELETE"):
        result = rest_handle.deleteResponse(url, inputData)
    print(str(result[0]))
    print "\n"
    print(str(result[1]))
# Command line argument parser
parser = argparse.ArgumentParser(description='OpenSwitch REST environ test')
parser.add_argument('--ip', help="ip", required=True, dest='ip')
parser.add_argument('--url', help="url", required=True, dest='url',
                    default=None)
parser.add_argument('--method', help="method GET/POST", required=True,
                    dest='method', default=None)
parser.add_argument('--inputData', help="JSON input data", required=False,
                    dest='inputData', default=None)
parser.add_argument('--expectedData', help="JSON output data", required=False,
                                           dest='expectedData', default=None)
args = parser.parse_args()
resttest()
