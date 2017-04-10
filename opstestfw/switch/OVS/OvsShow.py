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
import re


def OvsShow(**kwargs):

    """
    Run the ovs-vsctl show command and parse output

    :param deviceObj : Device object
    :type  deviceObj : object

    :return: returnStruct Object
            data: Temp_Sensors:
                  "name": {"max"."temperature". "min"}
                  Bridge
                     "name": {Vlans, Ports}
                        Vlans
                          "name": {admin, id}
                        Ports
                           "name": {Interface, trunk, tag}
                    Open_vSwitch_UUID
                    other_config: {diag_version, number_of_macs, vendor,
                                   base_mac_address, interface_count,
                                   onie_version, part_number,
                                   max_bond_member_count,"Product Name",
                                   platform_name, max_bond_count,
                                   max_interface_speed, device_version,
                                   country_code, label_revision,
                                   serial_number, manufacture_date,
                                   manufacturer}
                    Fans
                      "name": {status, rpm, speed}

    :returnType: object

    """

    deviceObj = kwargs.get('device', None)
    retStruct = dict()
    command = "ovs-vsctl show"

    LogOutput("info", "Doing an OVS show command and parse output***")
    devIntRetStruct = deviceObj.DeviceInteract(command=command)
    retCode = devIntRetStruct.get('returnCode')
    if retCode != 0:
        LogOutput('error', "Failed to get ovs-vsctl show command")
        retString = returnStruct(returnCode=1, data=retStruct)
        return retString

    buffer = devIntRetStruct.get('buffer')
    curBridgeName = ""
    bridgeDict = dict()
    curVlanName = ""
    curPortName = ""

    curFanName = ""
    fanDict = dict()

    # curTempSensor = ""
    tempSensorDict = dict()

    for curLine in buffer.split('\n'):
        # Match the UUID
        testForUUID = re.match("^\s*([0-9a-f-]+)\s*$", curLine)
        if testForUUID:
            retStruct['Open_vSwitch_UUID'] = str(testForUUID.group(1))
            continue

        # Match for bridge information
        testForBridge = re.match("^\s+Bridge\s+(\S+)\s*$", curLine)
        if testForBridge:
            curBridgeName = testForBridge.group(1)
            bridgeDict[curBridgeName] = dict()
            bridgeDict[curBridgeName]['Vlans'] = dict()
            bridgeDict[curBridgeName]['Ports'] = dict()
            continue

        # Vlan Matching
        testForVlan = re.match("\s+VLAN\s+\"(\S+)\"", curLine)
        if testForVlan:
            curVlanName = testForVlan.group(1)
            bridgeDict[curBridgeName]['Vlans'][curVlanName] = dict()
            continue

        # VLAN attributes
        testForVlanAttr = re.match("\s+(id|admin|description?):\s+(\S+)\s*$",
                                   curLine)
        if testForVlanAttr:
            curAttr = testForVlanAttr.group(1)
            bridgeDict[curBridgeName]['Vlans'][curVlanName][curAttr] =\
                testForVlanAttr.group(2)
            continue

        # Port matching underneath bridge
        testForPort = re.match("^\s+Port\s+\"(\S+)\"\s*$", curLine)
        if testForPort:
            curPortName = testForPort.group(1)
            bridgeDict[curBridgeName]['Ports'][curPortName] = dict()
            continue

        # Port Tag Attributes
        testForPortTag = re.match("^\s+tag:\s+(\d+)\s*$", curLine)
        if testForPortTag:
            bridgeDict[curBridgeName]['Ports'][curPortName]['tag'] =\
                testForPortTag.group(1)
            continue

        # Port Trunks Attribute
        testForPortTrunk = re.match("^\s+trunks:\s+\[(.*)\]\s*$", curLine)
        if testForPortTrunk:
            bridgeDict[curBridgeName]['Ports'][curPortName]['trunks'] =\
                testForPortTrunk.group(1)
            continue

        # Port Interface Attribute
        testForPortInterface = re.match("^\s+Interface\s+\"(\S+)\"\s*$",
                                        curLine)
        if testForPortInterface:
            bridgeDict[curBridgeName]['Ports'][curPortName]['Interface'] =\
                testForPortInterface.group(1)
            continue

        # Match for Fan
        testForFan = re.match("^\s+Fan\s+\"(.*)\"", curLine)
        if testForFan:
            curFanName = testForFan.group(1)
            fanDict[curFanName] = dict()
            continue

        testForFanAttr = re.match("^\s+(speed|rpm|status?):\s+(\S+)\s*$",
                                  curLine)
        if testForFanAttr:
            fanDict[curFanName][testForFanAttr.group(1)] =\
                testForFanAttr.group(2)
            continue

        # Match for Temp Sensors
        testForTempSensors = re.match("^\s+Temp_sensor\s+\"(.*)\"", curLine)
        if testForTempSensors:
            curTempSensorName = testForTempSensors.group(1)
            tempSensorDict[curTempSensorName] = dict()
            continue

        testForTempSensorAttr =\
            re.match("^\s+(max|min|temperature?):\s+(\S+)\s*$", curLine)
        if testForTempSensorAttr:
            tempSensorDict[curTempSensorName][testForTempSensorAttr.group(1)] =\
                testForTempSensorAttr.group(2)
            continue

        # Other Config
        testForOther = re.match("^\s+other_config:\s+\{(.*)\}", curLine)
        if testForOther:
            retStruct['other_config'] = dict()
            otherDataString = testForOther.group(1)
            splitArray = otherDataString.split(',')
            for item in splitArray:
                # Split this by =
                # Split out items with quotes
                stringSplitter =\
                    re.match('^\s*\"?(Product Name|base_mac_address|'
                             'device_version|'
                             'diag_version|interface_count|label_revision|'
                             'manufacture_date|max_bond_count|'
                             'max_bond_member_count'
                             '|max_interface_speed|number_of_macs|'
                             'onie_version|'
                             'part_number|platform_name|serial_number'
                             ')\"?=\"(.*)\"\s*$', item)
                if stringSplitter:
                    retStruct['other_config'][stringSplitter.group(1)] =\
                        stringSplitter.group(2)
                    continue

                # Split out other oddball items
                stringSplitter =\
                    re.match('^\s*(country_code|manufacturer|vendor)=(.*)\s*$',
                             item)
                if stringSplitter:
                    retStruct['other_config'][stringSplitter.group(1)] =\
                        stringSplitter.group(2)
                    continue

    # Create mock data
    retStruct['Bridge'] = bridgeDict
    retStruct['Fans'] = fanDict
    retStruct['Temp_Sensors'] = tempSensorDict
    retString = returnStruct(returnCode=0, buffer=buffer, data=retStruct)
    return retString
