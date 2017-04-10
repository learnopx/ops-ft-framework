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
This Class starts packet capturing on workstations and parses the packets
for specific protocol information using tshark
Copies the tshark file to the results directory

PacketCapture init method
:param:device : Device Name
:type:device  : string
:param:interface : workstation interface
:type:interface : string
:param:filename : name of the capture file
:type:filename  : string

Method :: StartCapture
:param:connection deviceObject
:type :connection Object
:param:filter  Tshark filter
:type:filter string

Method :: ParseCapture
:param:connection deviceObject
:type :connection Object

"""

import opstestfw.switch
import opstestfw.host
import opstestfw.gbldata
import re
import collections
from opstestfw import *
import pdb

class PacketCapture():
    returnDict = dict()

    def __init__(self, device, interface, filename):
        self.device = device
        self.filename = filename
        self.CaptureLog = "%s--%s" % (self.device, self.filename)
        self.interface = interface

    # Starts packet capture on workstation:
    def StartCapture(self, **kwargs):
        # Start the tshark process to capture packets on eth1 interface of
        # workstation
        connection = kwargs.get('connection')
        filter = kwargs.get('filter', None)
        LogOutput('info', "Start packet capture on the device->" + self.device)
        if filter is None:
            command = "tshark -l -i %s -V > /tmp/%s &" % (
                self.interface, self.CaptureLog)
            # command = "tshark -l -i wrkston01-eth0 -V > /tmp/%s &"%(self.CaptureLog)
            # command = "tshark -l -i eth1 -F libpcap -V -w /tmp/capture.pcap"
        else:
            # Capture file applying filters
            command = "tshark -l -i %s -V -f %s > /tmp/%s &" % (
                self.interface, filter, self.CaptureLog)

        returnStruct = connection.DeviceInteract(command=command)
        returnCode = returnStruct.get('returnCode')
        buffer = returnStruct.get('buffer')
        if returnCode != 0:
            LogOutput(
                'error',
                "Failed to start capture on the device->" +
                self.device)
            returnCls = opstestfw.returnStruct(
                returnCode=returnCode,
                buffer=buffer)
            return returnCls

    # Parse packets captured on the workstation
    def ParseCapture(self, connection, **kwargs):
        overallBuffer = []
        #Result Dictionary declaration
        returnDictionary = dict() 
        self.FrameDetails = dict()
        #self.FrameDetails = collections.defaultdict(dict)
        #Parse the captured output from the pcap files captured using tshark
        #Kill the tshark processes running on VM
        LogOutput(
            'info',
            "Kill the tshark processes running on the workstation")
        command = "ps -ef | grep tshark | grep -v grep | awk '{print $2}' | xargs kill -9"
        #command = "/usr/bin/killall -w \"tshark\""
        returnDict = connection.DeviceInteract(
            connection=connection, command=command)
        returnCode = returnDict.get('returnCode')
        overallBuffer.append(returnDict['buffer'])
        if returnCode != 0:
            LogOutput(
                'error',
                "Failed to kill tshark processes on the device->" +
                self.device)
            returnCls = opstestfw.returnStruct(
                returnCode=returnCode,
                buffer=overallBuffer)
            return returnCls

        # Download the capture file to local results directory
        # CaptureLog = "%s--%s"%(self.device,self.filename)
        filepath = '/tmp/%s' % (self.CaptureLog)
        localpath = opstestfw.gbldata.ResultsDirectory + self.CaptureLog
        returnCode = connection.FileTransfer(filepath, localpath, "get")
        overallBuffer.append(returnDict['buffer'])
        if returnCode != 0:
            LogOutput(
                'error',
                "Failed to transfer capture file to results directory")
            returnCls = opstestfw.returnStruct(
                returnCode=returnCode,
                buffer=overallBuffer)
            return returnCls

        # Read the capture file to parse for the protocol headers/packets
        fileHandle = open(localpath, "r")
        captureBuffer = fileHandle.read()
        frameCount = 0
        FrameList = re.split(r'Frame \d+:', captureBuffer)
        # FrameList has the capture packet buffer as list
        FrameList = filter(None, FrameList)
        if len(FrameList) != 0:
            for frame in FrameList:
                frameCount = frameCount + 1
                splitFrame = frame.split('\n')
                for line in splitFrame:
                    line = line.strip()

              #<This block needs to replicated for whichever protocol packets need to be parsed>
                    # Regular expressions to parse the tshark output buffer frames
                    # LLDP frame parsing begins here
                    # Protocol
                    Protocol = re.match(
                        r'\[Protocols in frame:\s+([A-Za-z:0-9]+)\]',
                        line)
                    if Protocol:
                        if Protocol not in self.FrameDetails.get(frameCount, {}):
                            self.FrameDetails[frameCount] = dict()
                            VlanNameTLVList = []
                            self.FrameDetails[frameCount][
                                'Protocol'] = Protocol.group(1)
                            LogOutput("info","Protocol detected -->" + self.FrameDetails[frameCount][
                                        'Protocol'])
                    # System Name
                    LldpSystemName = re.match(
                        r'System Name = ([A-Za-z1-9]+)',
                        line)
                    if LldpSystemName:
                        if LldpSystemName not in self.FrameDetails.get(frameCount, {}):
                            self.FrameDetails[frameCount][
                                'LldpSystemName'] = LldpSystemName.group(1)
                    # Port ID:
                    PortID = re.match(r'Port Id: (\d+)', line)
                    if PortID:
                        if PortID not in self.FrameDetails.get(frameCount, {}):
                            self.FrameDetails[frameCount][
                                'PortID'] = PortID.group(1)
                    # Time To Live
                    TimeToLive = re.match(r'Time To Live = (.*)', line)
                    if TimeToLive:
                        if TimeToLive not in self.FrameDetails.get(frameCount, {}):
                            self.FrameDetails[frameCount][
                                'TimeToLive'] = TimeToLive.group(1)
                    # System Description
                    SystemDescription = re.match(
                        r'System Description = (.*)',
                        line)
                    if SystemDescription:
                        if SystemDescription not in self.FrameDetails.get(frameCount, {}):
                            self.FrameDetails[frameCount][
                                'SystemDescription '] = SystemDescription.group(1)
                    # Port Vlan Identifier
                    PortVLanID = re.match(r'Port VLAN Identifier: (.*)', line)
                    if PortVLanID:
                        if PortVLanID not in self.FrameDetails.get(frameCount, {}):
                            self.FrameDetails[frameCount][
                                'PortVLanID'] = PortVLanID.group(1)
                    # Vlan Name
                    VlanName = re.match(r'VLAN Name: (.*)', line)
                    if VlanName:
                            VlanNameTLVList.append(VlanName.group(1))
                            self.FrameDetails[frameCount]['VlanNameTLV'] = VlanNameTLVList
                    # Port Description
                    PortDescr = re.match(r'Port Description = (.*)', line)
                    if PortDescr:
                        if PortDescr not in self.FrameDetails.get(frameCount, {}):
                            self.FrameDetails[frameCount][
                                'PortDescr'] = PortDescr.group(1)
                    # Dump the results in Dictionar(returnDictionary)
                    returnDictionary['LLDPFrames'] = self.FrameDetails
    #<Block ends here ***>>
    #Frame parsing ends

            # Delete the pcap file from workstation in /tmp folder
            filepath = "/tmp/" + self.filename
            command = "rm -f %s" % (filepath)
            returnStruct = connection.DeviceInteract(
                connection=connection, command=command)
            returnCode = returnStruct.get('returnCode')
            overallBuffer.append(returnDict['buffer'])
            if returnCode != 0:
                LogOutput(
                    'error',
                    "Failed to remove capture file from workstation ->" +
                    self.device)
                returnCls = opstestfw.returnStruct(
                    returnCode=returnCode,
                    buffer=overallBuffer)
                return returnCls
            # Return results(makes a json structure of the
            # dictionary(returnDictionary) and return code)
            bufferString = ""
            for curLine in overallBuffer:
                bufferString += str(curLine)
            returnCls = opstestfw.returnStruct(
                returnCode=returnCode,
                buffer=bufferString,
                data=returnDictionary)
            return returnCls
        else:
            LogOutput("info", "No Frames captured *** ")
            returnCls = opstestfw.returnStruct(
                returnCode=returnCode,
                buffer=overallBuffer)
            return returnCls
            # End of method ParseCapture
