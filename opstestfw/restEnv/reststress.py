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
import json
import argparse
import glob
import os
import time


def reststress():
    '''
    workstation python REST client utility sends a json request using the
    RestService object and it reads the REST input from a data file where
    each line consists of URL, method, data and expected http return code
    and issues the rest command and process the return http code comparing
    with expected http code and generate result file in the form of
    reststress_pass_clientid or reststress_fail_clientid at /root/restEnv/
    it also calculates the time taken to complete each iteration and also
    the total time for all of the ierations and writes to result file.

    :param ip: REST server IP running on the switch
    :type ip: string
    :param clientId: Rest client identifier for a given host
    :type clientId: integer
    :param file: REST input data file for the stress test
    :type file: string
    :param iterations: no of loops to repeat the stress test
    :type iterations: integer
    :return: None
    :rtype: None
    '''

    ip = args.ip
    clientId = args.clientId
    file = args.file
    iterations = int(args.iterations)
    returnCode = 0
    dataLength = 0
    testResult = 0
    restDataList = ()
    testPassFileName = "/root/restEnv/reststress_pass_" + clientId
    testFailFileName = "/root/restEnv/reststress_fail_" + clientId
    loopStartTime = 0
    loopEndTime = 0
    firstLoopTime = 0
    finalTime = 0
    restfile = "/root/restEnv/" + file
    initTime = time.time()
    try:

        with open(restfile, 'rb') as f:
            #            inputData = json.load(f)
            inputData = f.read()
            f.close()
        restDataList = inputData.split('\n')
        dataLength = len(restDataList)
    except Exception as e:
        print e
        returnCode = 1
    # before starting the test removing any existing result files
    for afile in glob.iglob("/root/restEnv/reststress_*"):
        print afile
        if os.path.exists(afile):
            os.remove(afile)

    if dataLength < 1:
        returnCode = 1
    print dataLength
    if returnCode == 0:
        rest_handle = RestService.RestService(switch_ip=ip)
        for loop in range(0, iterations):
            if testResult == 1:
                break
            loopStartTime = time.time()
            loopEndTime = 0
            for index in range(0, dataLength):
                restDataElementList = restDataList[index].split('   ')
                listLen = len(restDataElementList)
                if listLen <= 1:
                    print "restdata line is empty .. continuing further..."
                    continue
                url = restDataElementList[0]
                method = restDataElementList[1]
                if method == "POST" or method == "PUT":
                    restData = json.loads(restDataElementList[2])
                    http_expected_code = restDataElementList[3]
                else:
                    http_expected_code = restDataElementList[2]
                if (method == "GET"):
                    result = rest_handle.getResponse(url)
                elif (method == "POST"):
                    result = rest_handle.postResponse(url, restData)
                elif (method == "PUT"):
                    result = rest_handle.putResponse(url, restData)
                elif (method == "DELETE"):
                    restData = ""
                    result = rest_handle.deleteResponse(url, restData)
                restResult = str(result[0])
                if (http_expected_code == restResult):
                    testResult = 0
                else:
                    print "rest stress failed : details as below: "
                    print "URL %s  method %s" % (url, method)
                    print "expected http return code %s" % http_expected_code
                    print "actual return code %s" % restResult
                    print "failed iteration %d" % loop
                    testResult = 1
                    break
                print(str(result[0]))
                print "\n"
                print(str(result[1]))

            loopEndTime = time.time()
            if firstLoopTime == 0:
                firstLoopTime = loopEndTime - loopStartTime
                print "firstLoopTime = %f" % firstLoopTime

        finalTime = time.time()
        totalTime = finalTime - initTime
        print "totalTime = %f" % totalTime
        if testResult == 1:
            filename = testFailFileName
        else:
            filename = testPassFileName
        try:
            with open(filename, 'wb') as f:
                f.write(str(firstLoopTime))
                f.write("\n")
                f.write(str(totalTime))
                f.close()
        except Exception as e:
            print e
        print "rest stress completed"
        return


# Command line argument parser
parser = argparse.ArgumentParser(description='OpenSwitch REST environ test')
parser.add_argument('--ip', help="ip", required=True, dest='ip')
parser.add_argument(
    '--clientId',
    help="clientId",
    required=True,
    dest='clientId')
parser.add_argument('--file', help="file", required=True, dest='file',
                    default=None)
parser.add_argument('--iterations', help="iterations", required=True,
                    dest='iterations', default=1)
args = parser.parse_args()
reststress()
