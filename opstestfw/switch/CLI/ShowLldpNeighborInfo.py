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


def ShowLldpNeighborInfo(**kwargs):

    """
    This routine shows LLDP neighbor information on a switch

    :param deviceObj : Device object
    :type  deviceObj : object
    :param port      : Device port (optional)
    :type  port      : integer
    :return: returnStruct Object
             portStats - dictionary of ports, each port is a dictionary
                     portKeys - Neighbor_Entries_Deleted,
                                Neighbor_Entries_Dropped
                                Neighbor_Entries
                                Neighbor_Chassis-ID
                                Neighbor_chassisName
                                Neighbor_chassisDescription
                                Neighbor_Management_Address
                                Chassis_Capabilities_Available
                                Neighbor_Port-ID
                                Chassis_Capabilities_Enabled
                                TTL
             globalStats - dictionary of global statistics
                                Total_Neighbor_Entries
                                Total_Neighbor_Entries_Aged-out
                                Total_Neighbor_Entries_Deleted
                                Total_Neighbor_Entries_Dropped
    :returnType: object
    """

    deviceObj = kwargs.get('deviceObj')
    port = kwargs.get('port', None)

    returnDict = dict()
    overallBuffer = []
    returnStructure = deviceObj.VtyshShell()
    returnCode = returnStructure.returnCode()
    overallBuffer.append(returnStructure.buffer())
    if returnCode != 0:
        LogOutput('error', "Failed to get vtysh prompt")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = returnStruct(returnCode=1, buffer=bufferString)
        return returnCls

    # Pass LLDP commands here
    command = "show lldp neighbor-info"
    if port is not None:
        command += " " + str(port)

    LogOutput("info", "Show LLDP command ***" + command)
    # devIntRetStruct = opstestfw.switch.DeviceInteract(connection=connection,
    # command=command)
    devIntRetStruct = deviceObj.DeviceInteract(command=command)
    returnCode = devIntRetStruct.get('returnCode')
    overallBuffer.append(devIntRetStruct.get('buffer'))
    if returnCode != 0:
        LogOutput('error', "Failed to get show lldp neighbor-info command")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = returnStruct(returnCode=returnCode, buffer=bufferString)
        return returnCls
    else:
        rawBuffer = devIntRetStruct.get('buffer')
        bufferSplit = rawBuffer.split("\r\n")
        globalStatsDict = dict()
        portDict = dict()
        if port is not None:
            globalStatsDict['Total_Neighbor_Entries'] = ""
            globalStatsDict['Total_Neighbor_Entries_Deleted'] = ""
            globalStatsDict['Total_Neighbor_Entries_Dropped'] = ""
            globalStatsDict['Total_Neighbor_Entries_Aged-out'] = ""
            for line in bufferSplit:
                portLine = re.match("^Port\s+:\s*(\d{1,2}-\d{1}|\d+)\s*$", line)
                if portLine:
                    curPort = portLine.group(1)
                    portDict[curPort] = dict()
                    continue
                NeighborEntries = re.match(
                    "^Neighbor\s+entries\s+:\s*(\d+)\s*$",
                    line)
                if NeighborEntries:
                    portDict[curPort][
                        'Neighbor_Entries'] = NeighborEntries.group(1)
                    continue
                NeighborEntriesDeleted = re.match(
                    "^Neighbor\s+entries\s+deleted\s+:\s*(\d+)\s*$",
                    line)
                if NeighborEntriesDeleted:
                    portDict[curPort][
                        'Neighbor_Entries_Deleted'] = \
                        NeighborEntriesDeleted.group(1)
                    continue
                NeighborEntriesDropped = re.match(
                    "^Neighbor\s+entries\s+dropped\s+:\s*(\d+)\s*$",
                    line)
                if NeighborEntriesDropped:
                    portDict[curPort][
                        'Neighbor_Entries_Dropped'] = \
                        NeighborEntriesDropped.group(1)
                    continue
                NeighborEntriesAgedOut = re.match(
                    "^Neighbor\s+entries\s+aged-out\s+:\s*(\d+)\s*$",
                    line)
                if NeighborEntriesAgedOut:
                    portDict[curPort][
                        'Neighbor_Entries_Aged-out'] = \
                        NeighborEntriesAgedOut.group(1)
                    continue
                Neighbor_chasisName = re.match(
                    r'Neighbor Chassis-Name\s+:\s*(.*)$',
                    line)
                if Neighbor_chasisName:
                    portDict[curPort][
                        'Neighbor_chassisName'] = Neighbor_chasisName.group(1)
                    continue
                Neighbor_chasisDescrip = re.match(
                    r'Neighbor Chassis-Description\s+:\s*(.*)$',
                    line)
                if Neighbor_chasisDescrip:
                    portDict[curPort][
                        'Neighbor_chassisDescription'] = \
                        Neighbor_chasisDescrip.group(1)
                    continue
                Neighbor_chasisID = re.match(
                    r'Neighbor Chassis-ID :([0-9a-f:]+|\s*)$',
                    line)
                if Neighbor_chasisID:
                    portDict[curPort][
                        'Neighbor_chasisID'] = Neighbor_chasisID.group(1)
                    continue
                Management_address = re.match(
                    r'Neighbor Management-Address\s+:\s*(.*)$',
                    line)
                if Management_address:
                    portDict[curPort][
                        'Neighbor_Management_address'] = Management_address.group(1)
                    continue
                Chassis_CapAvail = re.match(
                    r'Chassis Capabilities Available\s*:\s*(.*)$',
                    line)
                if Chassis_CapAvail:
                    portDict[curPort][
                        'Chassis_Capabilities_Available'] = \
                        Chassis_CapAvail.group(1)
                    continue
                Chassis_CapEnabled = re.match(
                    r'Chassis Capabilities Enabled\s*:\s*(.*)$',
                    line)
                if Chassis_CapEnabled:
                    portDict[curPort][
                        'Chassis_Capabilities_Enabled'] = \
                        Chassis_CapEnabled.group(1)
                    continue
                Neighbor_portID = re.match(
                    r'Neighbor Port-ID\s*:\s*(.*)$',
                    line)
                if Neighbor_portID:
                    portDict[curPort][
                        'Neighbor_portID'] = Neighbor_portID.group(1)
                ttl = re.match(r'TTL :(\d+|\s*)$', line)
                if ttl:
                    portDict[curPort]['TTL'] = ttl.group(1)
            returnDict['globalStats'] = globalStatsDict
            returnDict['portStats'] = portDict
            # returnDict['buffer'] = rawBuffer
            # returnDict['lldpNeighborBuffer'] = rawBuffer
        else:
            # This means we are parsing out output w/out ports
            for line in bufferSplit:
                # Pull out Totals
                totalNeighEntries = re.match(
                    "^Total\s+neighbor\s+entries\s+:\s+(\d+)\s*$",
                    line)
                if totalNeighEntries:
                    globalStatsDict[
                        'Total_Neighbor_Entries'] = totalNeighEntries.group(1)
                    continue
                totalNeighEntriesDeleted = re.match(
                    "^Total\s+neighbor\s+entries\s+deleted\s+:\s+(\d+)\s*$",
                    line)
                if totalNeighEntriesDeleted:
                    globalStatsDict[
                        'Total_Neighbor_Entries_Deleted'] = \
                        totalNeighEntriesDeleted.group(1)
                    continue
                totalNeighEntriesDropped = re.match(
                    "^Total\s+neighbor\s+entries\s+dropped\s+:\s+(\d+)\s*$",
                    line)
                if totalNeighEntriesDropped:
                    globalStatsDict[
                        'Total_Neighbor_Entries_Dropped'] = \
                        totalNeighEntriesDropped.group(1)
                    continue
                totalNeighEntriesAgedOut = re.match(
                    "^Total\s+neighbor\s+entries\s+aged-out\s+:\s+(\d+)\s*$",
                    line)
                if totalNeighEntriesAgedOut:
                    globalStatsDict[
                        'Total_Neighbor_Entries_Aged-out'] = \
                        totalNeighEntriesAgedOut.group(1)
                    continue

                # Now lets go through each line
                blankPortEntry = re.match("^([0-9-]+)\s*$", line)
                if blankPortEntry:
                    curPort = blankPortEntry.group(1)
                    portDict[curPort] = dict()
                    portDict[curPort]['Neighbor_Entries_Deleted'] = ""
                    portDict[curPort]['Neighbor_Entries_Dropped'] = ""
                    portDict[curPort]['Neighbor_Entries'] = ""
                    portDict[curPort]['Neighbor_Chassis-ID'] = ""
                    portDict[curPort]['Neighbor_chassisName'] = ""
                    portDict[curPort]['Neighbor_chassisDescription'] = ""
                    portDict[curPort]['Chassis_Capabilities_Available'] = ""
                    portDict[curPort]['Neighbor_Port-ID'] = ""
                    portDict[curPort]['Chassis_Capabilities_Enabled'] = ""
                    portDict[curPort]['TTL'] = ""
                    continue
                populatedPortEntry = re.match(
                    "^([0-9-]+)\s+([0-9a-f:]+)\s+(\S+)\s+(\d+)\s*$",
                    line)
                if populatedPortEntry:
                    curPort = populatedPortEntry.group(1)
                    portDict[curPort] = dict()
                    portDict[curPort]['Neighbor_Entries_Deleted'] = ""
                    portDict[curPort]['Neighbor_Entries_Dropped'] = ""
                    portDict[curPort]['Neighbor_Entries'] = ""
                    portDict[curPort][
                        'Neighbor_Chassis-ID'] = populatedPortEntry.group(2)
                    portDict[curPort]['Neighbor_chassisName'] = ""
                    portDict[curPort]['Neighbor_chassisDescription'] = ""
                    portDict[curPort]['Chassis_Capabilities_Available'] = ""
                    portDict[curPort]['Chassis_Capabilities_Enabled'] = ""
                    portDict[curPort][
                        'Neighbor_Port-ID'] = populatedPortEntry.group(3)
                    portDict[curPort]['TTL'] = populatedPortEntry.group(4)
            returnDict['globalStats'] = globalStatsDict
            returnDict['portStats'] = portDict
            # returnDict['buffer'] = rawBuffer

    # Exit the vtysh shell
    # returnStructure = opstestfw.switch.CLI.VtyshShell(connection =
    # connection,configOption="unconfig")
    returnStructure = deviceObj.VtyshShell(configOption="unconfig")
    returnCode = returnStructure.returnCode()
    if returnCode != 0:
        LogOutput('error', "Failed to exit vtysh prompt")
        returnCls = returnStruct(returnCode=returnCode,)
        return returnCls

    # Return results
    bufferString = ""
    for curLine in overallBuffer:
        bufferString += str(curLine)
    returnCls = returnStruct(
        returnCode=0,
        buffer=bufferString,
        data=returnDict)
    return returnCls
