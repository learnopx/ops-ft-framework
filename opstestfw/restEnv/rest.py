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

import urllib
import httplib
import json


def genericREST(method, ip, url, data, debug=False):
    '''
    core method sends a json request using the selected method: method and
    data as the body

    :param method: REST/HTTP method name POST/GET/PUT or DELETE
    :type string: string
    :param ip: REST server ip address
    :type ip: string
    :param url: REST resource url
    :type ip: string
    :param data: data body for the method if any
    :type data: JSON format
    :param debug: flag to display debug statements
    :type debug: boolean
    :return: dictionary containing returnCode and buffer
    :rtype: dictionary
    '''

    if debug:
        debugLabel = "_" + method + "-REST: "
        print ""
        print debugLabel + "ip:          " + str(ip)
        print debugLabel + "url:          " + str(url)
        print debugLabel + "data:         " + str(data)
        print ""

    server_port = 443
    headers = {"Content-type": "application/json", "Accept": "text/plain"}
    json_data = json.dumps(data)

    try:
        conn = httplib.HTTPSConnection(ip, server_port,
                                       key_file="/root/restEnv/server-private.key",
                                       cert_file="/root/restEnv/server.crt")
    except Exception as e:
        print e
        return {"response": e, "data": None}
    try:
        conn.request(method, url, json_data, headers)
        response = conn.getresponse()
        res_data = response.read()
        conn.close()
        return {"response": response, "data": res_data}
    except Exception as e:
        print e
        conn.close()
        return {"response": e, "data": None}


def post(ip, url, data, debug=False):
    '''
    POST method calling genericREST core method

    :param ip: REST server ip address
    :type ip: string
    :param url: REST resource url
    :type url: string
    :param data: data body for the method if any
    :type data: JSON format
    :param debug: flag to display debug statements
    :type debug: boolean
    :return: dictionary containing returnCode and buffer
    :rtype: dictionary
    '''

    return genericREST("POST", ip, url, data, debug)


def put(ip, url, data, debug=False):
    '''
    PUT method calling genericREST core method

    :param ip: REST server ip address
    :type ip: string
    :param url: REST resource url
    :type url: string
    :param data: data body for the method if any
    :type data: JSON format
    :param debug: flag to display debug statements
    :type debug: boolean
    :return: dictionary containing returnCode and buffer
    :rtype: dictionary
    '''

    return genericREST("PUT", ip, url, data, debug)


def delete(ip, url, data, debug=False):
    '''
    DELETE method calling genericREST core method

    :param ip: REST server ip address
    :type ip: string
    :param url: REST resource url
    :type url: string
    :param data: data body for the method if any
    :type data: JSON format
    :param debug: flag to display debug statements
    :type debug: boolean
    :return: dictionary containing returnCode and buffer
    :rtype: dictionary
    '''

    return genericREST("DELETE", ip, url, data, debug)


def get(ip, url, debug=False):
    '''
    GET method calling genericREST core method

    :param ip: REST server ip address
    :type ip: string
    :param url: REST resource url
    :type url: string
    :param debug: flag to display debug statements
    :type debug: boolean
    :return: dictionary containing returnCode and buffer
    :rtype: dictionary
    '''

    return genericREST("GET", ip, url, None, debug)
