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
import re


def lacpAggregatesShow(** kwargs):

    """
    Library function to display settings configured on 1 or several LAGs

    :param deviceObj : Device object
    :type  deviceObj : object
    :param lagId     : LAG identifier
    :type  lagId     : integer

    :return: returnStruct Object
             data
                Keys: LAG numeric identifier
                Values:
                      interfaces:   - List of interfaces part of LAG
                      lacpFastFlag: - True for fast heartbeat,
                                      False for slow heartbeat
                      fallbackFlag: - True when enabled, False otherwise
                      hashType:     - l2-src-dst/l3-src-dst depending on
                                      configured settings on LAG
                      lacpMode:     - LAG configured mode: off for static and
                                      active/passive for dynamic
    :returnType: object
    """

    # Params
    lagId = kwargs.get('lagId', None)
    deviceObj = kwargs.get('deviceObj', None)

    # Variables
    overallBuffer = []
    retStruct = dict()
    helperLagId = ''
    finalReturnCode = 0
    results = ''
    counter = 0

    # If device is not passed, we need error message
    if deviceObj is None:
        opstestfw.LogOutput('error',
                            "Need to pass deviceObj to use this routine")
        returnCls = opstestfw.returnStruct(returnCode=1)
        return returnCls

    # Get into vtyshelll
    returnStructure = deviceObj.VtyshShell(enter=True)
    overallBuffer.append(returnStructure.buffer())
    returnCode = returnStructure.returnCode()
    if returnCode != 0:
        opstestfw.LogOutput('error', "Failed to get vtysh prompt")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = opstestfw.returnStruct(returnCode=returnCode,
                                           buffer=bufferString)
        return returnCls

    # Create command to query switch
    command = 'show lacp aggregates'
    if lagId is not None:
        command += ' lag' + str(lagId)
    returnDevInt = deviceObj.DeviceInteract(command=command)
    finalReturnCode = returnDevInt['returnCode']
    overallBuffer.append(returnDevInt['buffer'])
    if finalReturnCode != 0:
        opstestfw.LogOutput('error',
                            "Could not obtain LACP aggregates information")

    # Get out of vtyshell
    returnStructure = deviceObj.VtyshShell(enter=False)
    returnCode = returnStructure.returnCode()
    overallBuffer.append(returnStructure.buffer())
    if returnCode != 0:
        opstestfw.LogOutput('error', "Failed to exit vty shell")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = opstestfw.returnStruct(returnCode=returnCode,
                                           buffer=bufferString)
        return returnCls

    if finalReturnCode == 0:
        # ######TEMPORARY###
        # consume output for results
        buffer2 = ''
        while True:
            result = deviceObj.expectHndl.expect(['# ', pexpect.TIMEOUT],
                                                 timeout=5)
            buffer2 += str(deviceObj.expectHndl.before)
            if result == 1:
                break
        overallBuffer.append(buffer2)
        # ###END OF TEMPORARY

        # Parse information for desired results
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)

        results = bufferString.split('\r\n')
        for i in results:
            if counter == 0:
                # LAG id match
                result = re.search('Aggregate-name[ ]+: lag([0-9])+', i)
                if result is None:
                    continue
                helperLagId = str(result.group(1))
                retStruct[helperLagId] = dict()
                counter += 1
                continue
            if counter == 1:
                # Match for interfaces
                result = re.search('Aggregated-interfaces[ ]+:[ ]?([ ][a-zA-Z0-9 \-]*)',
                                   i)
                if result is None:
                    opstestfw.LogOutput('error',
                                        "Error while obtaining LACP aggregates"
                                        " interfaces information on line:\n"
                                        + i)
                    returnCls = opstestfw.returnStruct(returnCode=1,
                                                       buffer=bufferString)
                    return returnCls
                retStruct[helperLagId]['interfaces'] = []
                for k in re.split(' ', result.group(1)):
                    if k != '':
                        retStruct[helperLagId]['interfaces'].append(k)
                counter += 1
                continue
            if counter == 2:
                # Match for Heartbeat speed
                result = re.search('Heartbeat rate[ ]+: (slow|fast)', i)
                if result is None:
                    opstestfw.LogOutput('error',
                                        "Error while obtaining LACP "
                                        "aggregates heartbeat information "
                                        "on line:\n" + i)
                    returnCls = opstestfw.returnStruct(returnCode=1,
                                                       buffer=bufferString)
                    return returnCls
                if result.group(1) == 'fast':
                    retStruct[helperLagId]['lacpFastFlag'] = True
                else:
                    retStruct[helperLagId]['lacpFastFlag'] = False
                counter += 1
                continue
            if counter == 3:
                # Match for fallback settings
                result = re.search('Fallback[ ]+: (true|false)', i)
                if result is None:
                    opstestfw.LogOutput('error',
                                        "Error while obtaining LACP "
                                        "aggregates fallback information "
                                        "on line:\n" + i)
                    returnCls = opstestfw.returnStruct(returnCode=1,
                                                       buffer=bufferString)
                    return returnCls
                if result.group(1) == 'true':
                    retStruct[helperLagId]['fallbackFlag'] = True
                else:
                    retStruct[helperLagId]['fallbackFlag'] = False
                counter += 1
                continue
            if counter == 4:
                # Match for Hashing algorithm
                result = re.search('Hash[ ]+: (l2-src-dst|l3-src-dst)', i)
                if result is None:
                    opstestfw.LogOutput('error',
                                        "Error while obtaining LACP "
                                        "aggregates hash information on "
                                        "line:\n" + i)
                    returnCls = opstestfw.returnStruct(returnCode=1,
                                                       buffer=bufferString)
                    return returnCls
                retStruct[helperLagId]['hashType'] = result.group(1)
                counter += 1
                continue
            if counter == 5:
                # Match for LAG mode
                result = re.search('Aggregate mode[ ]+: (off|passive|active)',
                                   i)
                if result is None:
                    opstestfw.LogOutput('error',
                                        "Error while obtaining LACP "
                                        "aggregates hash information on "
                                        "line:\n" + i)
                    returnCls = opstestfw.returnStruct(returnCode=1,
                                                       buffer=bufferString)
                    return returnCls
                retStruct[helperLagId]['lacpMode'] = result.group(1)
                counter = 0
                continue

    # Compile information to return
    bufferString = ""
    for curLin in overallBuffer:
        bufferString += str(curLin)
    returnCls = opstestfw.returnStruct(returnCode=finalReturnCode,
                                       buffer=bufferString, data=retStruct)
    return returnCls
