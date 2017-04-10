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

import json
import rest
import urllib2


class RestService(object):

    '''
    This is the main class for Halon FW REST API library.
    '''

    def __init__(self, switch_ip='localhost', user='sdn', password='skyline'):
        """
        RestService init method

        This method will create a RestService object that will contain all
        information to interact with the device

        :param switch_ip: management ip of the switch
        :type switch_ip: string
        :param user: user name
        :type user: string
        :param password: password
        :type password: string

        """

        self.switch_ip = switch_ip
        self.user = user
        self.password = password
        self.url = 'https://' + switch_ip + ':443/rest/v1/system'
        self.token = None
        self.verbose = False

    def setVerbose(self):
        '''
        setVerbose:
        API to set verbosity level for the session.
        No Arguments, sets self.verbose.
        '''
        self.verbose = True

    def clearVerbose(self):
        '''
        clearVerbose:
        API to clear verbosity level for the session.
        No Arguments, clears self.verbose.
        '''
        self.verbose = False

    def setURL(self, url):
        '''
        setURL:
        API to set base URL for the controller.
        No Arguments, sets self.url.
        '''
        self.url = url

    def getResponse(self, reqURL):
        '''
        method calling REST GET request

        :param reqURL: REST resource url
        :type reqURL: string
        :return: dictionary containing returnCode and buffer
        :rtype: dictionary
        '''

        if self.verbose:
            print 'Req URL: ', reqURL
        res = rest.get(self.switch_ip, reqURL, self.verbose)
        if isinstance(res["response"], urllib2.URLError):
            return (555, res.reason)
        else:
            try:
                return (res["response"].status, res["data"])
            except:
                return (res["response"].status, res["response"].reason)

    def postResponse(self, reqURL, data):
        '''
        method calling REST POST request
        :param reqURL: REST resource url
        :type reqURL: string
        :param data: data body for the request
        :type data: JSON format
        :return: dictionary containing returnCode and buffer
        :rtype: dictionary
        '''
        if self.verbose:
            print 'Req URL: ', reqURL
        res = rest.post(self.switch_ip, reqURL, data, self.verbose)
        if isinstance(res, urllib2.URLError):
            return (555, res.reason)
        else:
            try:
                return (res["response"].status, res["data"])
            except:
                return (res["response"].status, res["response"].reason)

    def putResponse(self, reqURL, data):
        '''
        method calling REST PUT request

        :param reqURL: REST resource url
        :type reqURL: string
        :param data: data body for the request
        :type data: JSON format
        :return: dictionary containing returnCode and buffer
        :rtype: dictionary
        '''

        if self.verbose:
            print 'Req URL: ', reqURL
        res = rest.put(self.switch_ip, reqURL, data, self.verbose)
        if isinstance(res, urllib2.URLError):
            return (555, res.reason)
        else:
            try:
                return (res["response"].status, res["data"])
            except:
                return (res["response"].status, res["response"].reason)

    def deleteResponse(self, reqURL, data):
        '''
        method calling REST DELETE request

        :param reqURL: REST resource url
        :type reqURL: string
        :param data: data body for the request
        :type data: JSON format
        :return: dictionary containing returnCode and buffer
        :rtype: dictionary
        '''

        if self.verbose:
            print 'Req URL: ', reqURL
        res = rest.delete(self.switch_ip, reqURL, data, self.verbose)
        if isinstance(res, urllib2.URLError):
            return (555, res.reason)
        else:
            try:
                return (res["response"].status, res["data"])
            except:
                return (res["response"].status, res["response"].reason)
