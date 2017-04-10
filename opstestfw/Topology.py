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
#
import os
import xml.dom.minidom
from mininet.net import *
from mininet.topo import *
from mininet.node import *
from mininet.link import *
from mininet.cli import *
from mininet.log import *
from mininet.util import *
from subprocess import *
from subprocess import *
from opsvsi.docker import *
from opsvsi.opsvsitest import *
from subprocess import *
import xml.etree.ElementTree as ET
import re
import select
import opstestfw
import shutil
from opstestfw import gbldata
import time
import pexpect

try:
    import rtltestfw
except ImportError:
    pass

class FTOpsVsiHost(OpsVsiHost):

    def __init__(self, name, **kwargs):
        kwargs['nodetype'] = "OpsVsiHost"
        print ""
        host_image_dict = kwargs.pop('HostImageDict')
        #image = kwargs.pop('HostImage')
        image = host_image_dict[name]
        opstestfw.LogOutput('info', name + " docker image: " + image)
        super(OpsVsiHost, self).__init__(name, image, **kwargs)

class Topology (OpsVsiTest):

    """
    Topology  Class definition

    This Class defines openswitch topology by taking inputs from the topology
    dictionary defined in the test scripts
    Inherits the base class OpsVsiTest

    """

    def __init__(self, **kwargs):
        """
        Topology  init method

        This method generates the Topology object that contains topology
        information extracted from LogicalTopology.xml .
        LogicalTopology.xml is built from the topology dictionary as described
        in the test scripts .
        This library enables mapping of logical topologies to docker 
        containers physical devices (switches & hosts)

        :param topoDict : topology dictionary defined in the test case
        :type topology: dictionary
        :param runEnv: reference object to testEnviron.py
        :type runEnv:  Object

        """

        self.topoDict = kwargs.get('topoDict', None)
        self.runEnv = kwargs.get('runEnv', None)
        self.defaultSwitchContext = kwargs.get('defSwitchContext', "linux")
        self.hostimage = 'openswitch/ubuntutest:latest'
        self.topoType = 'virtual'
        # Initialize Structures
        self.LOGICAL_TOPOLOGY = ""
        self.TOPOLOGY = ""
        self.tuntap_failure = False
        self.switchd_failure = False
        self.cur_hw_failure = False

        self.topo = dict()
        self.deviceObj = dict()
        self.id = str(os.getpid())
        self.testdir = kwargs.get('resultsDir', None)
        envVsiDebug = os.environ.get('VSIDEBUG', None)
        if envVsiDebug is None:
            self.setLogLevel('info')
        else:
            self.setLogLevel('debug')
        self.hostmounts = []
        self.switchmounts = []
        # Initialize Structures
        self.LOGICAL_TOPOLOGY = ""
        self.TOPOLOGY = ""
        self.mininetGlobal = ""
        self.inbandIndex = 0
        self.LogicalTopologyCreate()
        self.VirtualXMLCreate()
        self.setHostImageOpts(self.hostimage)
        self.setupNet()
        self.TopologyXMLWrite()

    def getHostOpts(self):
        opts = self.getNodeOpts()
        opts.update({'mounts': self.hostmounts})
        opts.update({'HostImage': self.hostimage})
        opts.update({'HostImageDict': self.topo_wrkston_image_dict})
        return opts

    def setupNet(self, **kwargs):
        """

        This method defines the Mininet object and populates it
        by using inputs from logical topology defined in testcase

        """

        # Define Mininet object so we can populate it.
        self.mntopo = mininet.topo.Topo(
            hopts=self.getHostOpts(),
            sopts=self.getSwitchOpts())

        logicalTopo = dict()
        for curDev in str.split(self.topoDevices):
            logicalTopo[curDev] = dict()
            logicalTopo[curDev]['attributes'] = dict()
            logicalTopo[curDev]['links'] = dict()

        # Create a local dictionary around the devices in topoFilters
        for curFilter in str.split(self.topoFilters, ','):
            (cDev, cAttr, cVal) = str.split(curFilter, ':')
            logicalTopo[cDev]['attributes'][cAttr] = cVal

        for curDev in logicalTopo.keys():
            # Grag attributes for each device
            devAttrs = logicalTopo[curDev]['attributes']
            devCategory = devAttrs['system-category']
            if devCategory == "switch":
                opstestfw.LogOutput('debug', "Added Switch Device: " + curDev)
                self.mntopo.addSwitch(curDev)
            elif devCategory == "workstation":
                opstestfw.LogOutput(
                    'debug',
                    "Added Workstation Device: " +
                    curDev)
                self.mntopo.addHost(curDev)

        dockerLinks = dict()
        if self.topoLinks != "":
            # The dockerLinks is a local dictionary to identify what links have
            # topoLinkFilters associated with them

            for curLink in str.split(self.topoLinks, ','):
                #print "looking at link " + curLink
                (link, dev1, dev2) = str.split(curLink, ':')
                linkFilterMatch = 0
                if self.topoLinkFilter != "":
                    tmpLinkDict = dict()
                    for curLinkFilter in str.split(self.topoLinkFilter, ','):
                        #print "examing linkfilter " + curLinkFilter
                        (lfLink, lfDev, lfIntTag, lfInt) =\
                            str.split(curLinkFilter, ':')
                        if lfLink.strip(' ') == link:
                            #print "linkfilter for " + link
                            linkFilterMatch = 1
                            # break
                            if 'dev1' in tmpLinkDict:
                                tmpLinkDict['dev2'] = lfDev
                                tmpLinkDict['dev2Port'] = lfInt
                            else:
                                tmpLinkDict['dev1'] = lfDev
                                tmpLinkDict['dev1Port'] = lfInt

                if linkFilterMatch == 0:
                    # No link filters detected, we will just add the link
                    linkKey = self.mntopo.addLink(dev1, dev2, key=link)
                else:
                    # We are seeing a link filter, lets see if interface is
                    # eth0
                    if lfInt == "eth0":
                        intIndex = "eth0"
                        opstestfw.LogOutput('info', "Virtual out of band "
                                            "test.  Out of band link "
                                            "internal to Docker.")
                        dockerLinks[link] = dict()
                        dockerLinks[link]['mininetLink'] = False
                        dockerLinks[link]['node1'] = dev1
                        dockerLinks[link]['node2'] = dev2
                        dockerLinks[link]['port1'] = "eth0"
                        dockerLinks[link]['port2'] = "eth0"
                    else:
                        # Means we have a numeric port
                        #print "tmpLinkDict"
                        #print tmpLinkDict
                        if 'dev1' in tmpLinkDict and 'dev2' in tmpLinkDict:
                            dev1Port = tmpLinkDict['dev1Port']
                            dev2Port = tmpLinkDict['dev2Port']
                            dockerLinks[link] = dict()
                            dockerLinks[link]['mininetLink'] = True
                            dockerLinks[link]['node1'] = dev1
                            dockerLinks[link]['node2'] = dev2
                            dockerLinks[link]['port1'] = int(dev1Port)
                            dockerLinks[link]['port2'] = int(dev2Port)
                            linkKey = self.mntopo.addLink(dev1, dev2, key=link,
                                                          port1=int(dev1Port),
                                                          port2=int(dev2Port))
                        else:
                            dev1Port = tmpLinkDict['dev1Port']
                            dockerLinks[link] = dict()
                            dockerLinks[link]['mininetLink'] = True
                            dockerLinks[link]['node1'] = dev1
                            dockerLinks[link]['port1'] = int(dev1Port)
                            linkKey = self.mntopo.addLink(dev1, dev2, key=link,
                                                          port1=int(dev1Port))
                # Add to Link Logical Topology
                logicalTopo[dev1]['links'][link] = dev2
                logicalTopo[dev2]['links'][link] = dev1
                # print logicalTopo

        # Configure MiniNet
        self.net = mininet.net.Mininet(topo=self.mntopo,
                                       switch=VsiOpenSwitch,
                                       host=FTOpsVsiHost,
                                       link=OpsVsiLink,
                                       controller=None,
                                       build=True)

        # Check for docker bringup failures and update the flags
        for switch in self.net.switches:
            if isinstance(switch, VsiOpenSwitch):
                if switch.cur_hw_failed:
                    self.cur_hw_failure = True
                elif switch.switchd_failed:
                    self.switchd_failure = True
                if self.switchd_failure or self.cur_hw_failure:
                    break

        print ""
        # Now we need to query what we have.... to put in the topology
        # We will not formally have mapping, so we will create the mapping
        # array here.
        switches = self.net.switches
        for curSwitch in switches:
            xmlAddRet = self.VirtualXMLDeviceAdd(
                name=str(curSwitch.container_name))
            logDevRe = re.match("^\d+_(\S+)", curSwitch.container_name)
            if logDevRe:
                logicalDevice = logDevRe.group(1)
                self.topo[logicalDevice] = curSwitch.container_name
                self.topo[curSwitch.container_name] = logicalDevice

        hosts = self.net.hosts
        # hosts
        for curHost in hosts:
            xmlAddRet =\
                self.VirtualXMLDeviceAdd(name=str(curHost.container_name))
            logDevRe = re.match("^\d+_(\S+)", curHost.container_name)
            if logDevRe:
                logicalDevice = logDevRe.group(1)
                self.topo[logicalDevice] = curHost.container_name
                self.topo[curHost.container_name] = logicalDevice

        # Query Links and update the XML
        topoLinkMininet = self.mntopo.iterLinks(withKeys=True, withInfo=True)
        for curLink in topoLinkMininet:
            # print curLink
            linkName = curLink[2]
            linkFilter = 0
            if linkName in dockerLinks:
                linkFilter = 1
            # print "current link = " + str(curLink)
            linkInfo = curLink[3]
            # print linkInfo
            node1 = linkInfo['node1']
            node1Obj = self.searchNetNodes(self.topo[node1])
            node1port = linkInfo['port1']
            node1IntStruct = node1Obj.intfList()
            if linkFilter == 1:
                # Look for node1 in the dockerLink
                linkFilterInfo = dockerLinks[linkName]
                linkNode1 = linkFilterInfo.get('node1', None)
                linkNode2 = linkFilterInfo.get('node2', None)
                if node1 == linkNode1:
                    linkPort1 = linkFilterInfo.get('port1', None)
                    # Find the index of the port and replace it.
                    for curIndex in range(0, len(node1IntStruct)):
                        if str(node1IntStruct[curIndex]) == str(linkPort1):
                            node1port = curIndex
                            break
                elif node1 == linkNode2:
                    linkPort2 = linkFilterInfo.get('port2', None)
                    # Find the index of the port and replace it.
                    for curIndex in range(0, len(node1IntStruct)):
                        if str(node1IntStruct[curIndex]) == str(linkPort2):
                            node1port = curIndex
                            break

            node2 = linkInfo['node2']
            node2Obj = self.searchNetNodes(self.topo[node2])
            node2port = linkInfo['port2']
            # print node2port
            node2IntStruct = node2Obj.intfList()
            #print node2IntStruct
            if linkFilter == 1:
                # Look for node1 in the dockerLink
                linkFilterInfo = dockerLinks[linkName]
                linkNode1 = linkFilterInfo.get('node1', None)
                linkNode2 = linkFilterInfo.get('node2', None)
                if node2 == linkNode1:
                    linkPort1 = linkFilterInfo.get('port1', None)
                    # Find the index of the port and replace it.
                    for curIndex in range(0, len(node2IntStruct)):
                        # print curIndex
                        if str(node2IntStruct[curIndex]) == str(linkPort1):
                            node2port = curIndex
                            break
                elif node2 == linkNode2:
                    linkPort2 = linkFilterInfo.get('port2', None)
                    # Find the index of the port and replace it.
                    for curIndex in range(0, len(node2IntStruct)):
                        if str(node2IntStruct[curIndex]) == str(linkPort2):
                            node2port = curIndex
                            break
            # Add link to Topology XML
            retStruct =\
                self.VirtualXMLLinkAdd(link=linkName,
                                       device1=self.topo[node1],
                                       device1Port=node1IntStruct[node1port],
                                       device2=self.topo[node2],
                                       device2Port=node2IntStruct[node2port])
            #opstestfw.LogOutput('info', "Link info\n"+self.topo[node1]
            #                    +" "+str(node1IntStruct[node1Index])
            #                    + " "+self.topo[node2] + " "+str(node2IntStruct[node2Index]))
            self.topo[linkName] = linkName

        # Now lets look for docker links since they will not be part of mininet
        for curLink in dockerLinks.keys():
            linkName = curLink
            if dockerLinks[curLink]['mininetLink'] is True:
                # if this is a link we created in mininet, then continue
                continue
            node1 = dockerLinks[curLink]['node1']
            port1 = dockerLinks[curLink]['port1']
            node2 = dockerLinks[curLink]['node2']
            port2 = dockerLinks[curLink]['port2']
            # Add link to Topology XML
            retStruct =\
                self.VirtualXMLLinkAdd(link=linkName,
                                       device1=self.topo[node1],
                                       device1Port=port1,
                                       device2=self.topo[node2],
                                       device2Port=port2)
            self.topo[linkName] = linkName

        # topology mapping
        opstestfw.LogOutput('info', "========================================"
                            "=============================")
        opstestfw.LogOutput('info', "Topology Mapping")
        for curDev in str.split(self.topoDevices):
            #outstring = curDev + "  =  " + self.topo[curDev]
            outstring = "%-12s" % curDev + " =\t%-12s"\
                        % self.topo[curDev]
            opstestfw.LogOutput('info', outstring)

        if self.topoLinks != "":
            # Resolve the links
            for curLink in str.split(self.topoLinks, ','):
                (link, dev1, dev2) = str.split(curLink, ':')
                dev1LportStruct = self.InterfaceGetByDeviceLink(
                    device=self.topo[dev1], link=link)
                if dev1LportStruct.returnCode() != 0:
                    opstestfw.LogOutput(
                        'error',
                        "Unable to obtain link information for " +
                        link +
                        " for " +
                        dev1)
                    continue
                dev1Lport = dev1LportStruct.valueGet()
                dev2LportStruct = self.InterfaceGetByDeviceLink(
                    device=self.topo[dev2], link=link)
                if dev2LportStruct.returnCode() != 0:
                    # Unable to obtain link information
                    opstestfw.LogOutput(
                        'error',
                        "Unable to obtain link information for " +
                        link +
                        " for " +
                        dev2)
                    continue
                dev2Lport = dev2LportStruct.valueGet()
                outstring = "%-12s" % link + " =\t" + self.topo[dev1] + ":"\
                    + str(dev1Lport) + " <===> " + self.topo[dev2] + ":"\
                    + str(dev2Lport)
                opstestfw.LogOutput('info', outstring)
        opstestfw.LogOutput('info', "======================================="
                            "==============================")
        self.net.start()
        # Tuntap failure check
        for switch in self.net.switches:
            if isinstance(switch, VsiOpenSwitch) and switch.tuntap_failed:
                self.tuntap_failure = True
                switch.get_syslog_on_failure()
                break

    def VirtualLinkModifyStatus(self, **kwargs):
        """
        This method identifies Link information from the topology dictionary
        and modifies its state
        :param link: Link whose state needs to be modified
        :type link : string

        :param status : Link status
        :type status :  string

        """

        link = kwargs.get('link', None)
        status = kwargs.get('status', 'down')
        # Find out who the link belongs to - can do this with the logical
        # topology
        xpath = "./link[@name='" + str(link) + "']"
        linkNameElement = opstestfw.XmlGetElementsByTag(
            self.LOGICAL_TOPOLOGY, xpath)

        linkAttrs = linkNameElement.attrib
        device1 = linkAttrs['device1']
        device2 = linkAttrs['device2']

        self.net.configLinkStatus(device1, device2, status)
        retCls = opstestfw.returnStruct(returnCode=0)
        return retCls

    # Restart Switch
    def RestartSwitch(self, **kwargs):
        """
        This method restarts the virtual switch
        :param switch : Virtual Switch object
        :type  switch : Object

        """
        switch = kwargs.get('switch', None)
        opstestfw.LogOutput('info', "Restarting Virtual Switch: " + switch)
        switches = self.mininetGlobal.net.switches

        for curSwitch in switches:
            if switch == curSwitch.container_name:
                switchObj = curSwitch
                # print switchObj
                break

        mylogicalDev = self.topo[switch]

        # cleanup the old container
        switchObj.terminate()

        # Clean up old directory
        mydir = switchObj.testdir + "/" + mylogicalDev
        shutil.rmtree(mydir)

        # We actually really need to add the switch again in order to get
        # everything properly setup to as it was before.
        self.net.addSwitch(
            mylogicalDev,
            testid=str(self.id),
            testdir=str(self.testdir))

        # Now search for links in the logical topology that are in respect to
        # this dev and add them.
        for curLink in str.split(self.topoLinks, ','):
            (link, dev1, dev2) = str.split(curLink, ':')
            if dev1 == mylogicalDev or dev2 == mylogicalDev:
                # add the link
                opstestfw.LogOutput(
                    'debug',
                    "Creating Link " +
                    link +
                    " between " +
                    dev1 +
                    " & " +
                    dev2)
                self.net.addLink(dev1, dev2)

        return None

    def searchNetNodes(self, name):
        """
        Routine to search for Net Node
        :param:name : docker container name
        :type :name : string

        """
        switches = self.net.switches
        hosts = self.net.hosts

        for curSwitch in switches:
            if curSwitch.container_name == name:
                return(curSwitch)

        for curHost in hosts:
            if curHost.container_name == name:
                return(curHost)

        return(None)

    def terminate_nodes(self):
        """
        This routine deletes docker container instances

        """

        envKeepContainers = os.environ.get('VSIKEEPENV', None)
        if envKeepContainers is not None or envKeepContainers == 1:
            return

        # gather up all nodes
        # Close file desc
        for curDev in str.split(self.topoDevices):
            devObj = self.deviceObjGet(device=curDev)
            devObj.expectHndl.close()
        self.shell = 1
        self.net.stop()
        self.setLogLevel('output')
        switch_list = self.net.switches
        host_list = self.net.hosts
        for curHost in host_list:
            opstestfw.LogOutput('debug', "terminating " + str(curHost))
            curHost.terminate()
            curHost.cleanup()

        for curSwitch in switch_list:
            opstestfw.LogOutput('debug', "terminating " + str(curSwitch))
            curSwitch.terminate()

    def VirtualXMLCreate(self):
        """
        Virtual TOPOLOGY XML Routines
        Create virtual topology XML file from topology
        Base Topology Tag
        create reservation header w/ id = virtual

        """
        self.TOPOLOGY = ET.Element("topology", attrib={'version': "1.0"})

        # Reservation Tag
        reservationTag = ET.SubElement(self.TOPOLOGY, 'reservation')
        reservationIdTag = ET.SubElement(reservationTag, 'id').text = "virtual"
        reservationUserTag = ET.SubElement(reservationTag, 'user')
        reservationServerTag = ET.SubElement(reservationTag, 'server')

    def VirtualXMLDeviceAdd(self, **kwargs):
        """
        This routine populates devices to the XML files using device
        attributes from the topology dictinary

        """

        name = kwargs.get('name')
        vendor = kwargs.get('vendor', "hp")
        platform = kwargs.get('platform', None)
        category = kwargs.get('category', "switch")
        macAddress = kwargs.get('macAddress', None)
        os = kwargs.get('os', None)
        partNumber = kwargs.get('partNumber', None)
        serialNumber = kwargs.get('serialNumber', None)
        productCode = kwargs.get('productCode', None)
        status = kwargs.get('status', "ok")
        pod = kwargs.get('pod', "virtual")

        # device tag block
        deviceTag = ET.SubElement(self.TOPOLOGY, 'device')
        if name is None:
            retCls = opstestfw.returnStruct(returnCode=1)
            return retCls

        deviceNameTag = ET.SubElement(deviceTag, 'name').text = name

        # Create System area
        systemTag = ET.SubElement(deviceTag, 'system')

        # System Area
        # Name
        systemNameTag = ET.SubElement(systemTag, "name").text = name

        # Vendor
        systemVendorTag = ET.SubElement(systemTag, "vendor").text = vendor

        # Platform
        if platform is None:
            systemPlatformTag = ET.SubElement(systemTag, "platform")
        else:
            systemPlatformTag = ET.SubElement(
                systemTag,
                "platform").text = platform

        systemPlatformTag = ET.SubElement(
            systemTag,
            "category").text = category

        # macAddress
        if macAddress is None:
            systemPlatformTag = ET.SubElement(systemTag, "macAddress")
        else:
            systemPlatformTag = ET.SubElement(
                systemTag,
                "macAddress").text = macAddress

        # os
        if os is None:
            systemPlatformTag = ET.SubElement(systemTag, "os")
        else:
            systemPlatformTag = ET.SubElement(systemTag, "os").text = os

        # partNumber
        if partNumber is None:
            systemPlatformTag = ET.SubElement(systemTag, "partNumber")
        else:
            systemPlatformTag = ET.SubElement(
                systemTag,
                "partNumber").text = partNumber

        # serialNumber
        if serialNumber is None:
            systemPlatformTag = ET.SubElement(systemTag, "serialNumber")
        else:
            systemPlatformTag = ET.SubElement(
                systemTag,
                "serialNumber").text = serialNumber

        # productCode
        if serialNumber is None:
            systemPlatformTag = ET.SubElement(systemTag, "productCode")
        else:
            systemPlatformTag = ET.SubElement(
                systemTag,
                "productCode").text = productCode

        # status
        systemPlatformTag = ET.SubElement(systemTag, "status").text = status

        # pod
        systemPlatformTag = ET.SubElement(systemTag, "pod").text = pod

        # Add connection Area
        connectionTag = ET.SubElement(deviceTag, 'connection')

        # name
        connectionNameTag = ET.SubElement(connectionTag, "name").text = name

        connectionConsoleTag = ET.SubElement(
            connectionTag,
            "category").text = "console"
        connectionManagementTag = ET.SubElement(
            connectionTag,
            "type").text = "management"
        connectionIPTag = ET.SubElement(connectionTag, "ipAddr")
        connectionPortTag = ET.SubElement(connectionTag, "port")
        connectionProtocolTag = ET.SubElement(
            connectionTag,
            "protocol").text = "docker"
        connectionPriorityTag = ET.SubElement(
            connectionTag, "priority").text = "0"

        retCls = opstestfw.returnStruct(returnCode=0)
        return retCls

    def VirtualXMLLinkAdd(self, **kwargs):
        """
        This routine adds link attributes to XML file
        """
        device1 = kwargs.get("device1")
        device2 = kwargs.get("device2")
        link = kwargs.get("link")
        device1Port = kwargs.get("device1Port")
        device2Port = kwargs.get("device2Port")

        # Search for device1 to create interface block and link block
        xpath = ".//device[name='" + device1 + "']"
        device1Element = opstestfw.XmlGetElementsByTag(
            self.TOPOLOGY,
            ".//device[name='" + device1 + "']")

        # create device 1 interface block
        dev1InterfaceTag = ET.SubElement(device1Element, "interface")
        interfaceName = ET.SubElement(
            dev1InterfaceTag,
            "name").text = str(
            device1Port)
        staticName = ET.SubElement(
            dev1InterfaceTag,
            "staticName").text = str(
            device1Port)

        # Dummied up values for now
        intId = ET.SubElement(dev1InterfaceTag, "id")
        rate = ET.SubElement(
            dev1InterfaceTag,
            "rate").text = "Ethernet-Auto-Negotiate"
        rate = ET.SubElement(dev1InterfaceTag, "rate").text = "Ethernet-10Mb"
        rate = ET.SubElement(dev1InterfaceTag, "rate").text = "Ethernet-100Mb"
        rate = ET.SubElement(dev1InterfaceTag, "rate").text = "Ethernet-1Gb"
        chassis = ET.SubElement(dev1InterfaceTag, "chassis")
        chassisPort = ET.SubElement(dev1InterfaceTag, "chassisPort")
        type = ET.SubElement(dev1InterfaceTag, "type").text = "auto"
        mode = ET.SubElement(dev1InterfaceTag, "mode").text = "100/1000T"
        module = ET.SubElement(dev1InterfaceTag, "module")
        poe = ET.SubElement(dev1InterfaceTag, "poe")
        slot = ET.SubElement(dev1InterfaceTag, "slot")
        systemPod = ET.SubElement(
            dev1InterfaceTag,
            "system-pod").text = "virtual"

        # create device 1 link block
        dev1LinkTag = ET.SubElement(device1Element, "link")
        linkName = ET.SubElement(dev1LinkTag, "name").text = link
        id = ET.SubElement(dev1LinkTag, "id")
        rate = ET.SubElement(dev1LinkTag, "rate").text = "Ethernet-1Gb"
        remoteDev1 = ET.SubElement(dev1LinkTag, "remoteDevice").text = device2
        remoteInterface1 = ET.SubElement(
            dev1LinkTag,
            "remoteInterface").text = str(
            device2Port)
        localInteface1 = ET.SubElement(
            dev1LinkTag,
            "localInterface").text = str(
            device1Port)
        type = ET.SubElement(dev1LinkTag, "type").text = "auto"
        asicVersion = ET.SubElement(dev1LinkTag, "asicVersion")

        # Search for device1 to create interface block and link block
        xpath = ".//device[name='" + device2 + "']"
        device2Element = opstestfw.XmlGetElementsByTag(self.TOPOLOGY, xpath)

        # create device 1 interface block
        dev2InterfaceTag = ET.SubElement(device2Element, "interface")
        interfaceName = ET.SubElement(
            dev2InterfaceTag,
            "name").text = str(
            device2Port)
        staticName = ET.SubElement(
            dev2InterfaceTag,
            "staticName").text = str(
            device2Port)

        # Dummied up values for now
        intId = ET.SubElement(dev2InterfaceTag, "id")
        rate = ET.SubElement(
            dev2InterfaceTag,
            "rate").text = "Ethernet-Auto-Negotiate"
        rate = ET.SubElement(dev2InterfaceTag, "rate").text = "Ethernet-10Mb"
        rate = ET.SubElement(dev2InterfaceTag, "rate").text = "Ethernet-100Mb"
        rate = ET.SubElement(dev2InterfaceTag, "rate").text = "Ethernet-1Gb"
        chassis = ET.SubElement(dev2InterfaceTag, "chassis")
        chassisPort = ET.SubElement(dev2InterfaceTag, "chassisPort")
        type = ET.SubElement(dev2InterfaceTag, "type").text = "auto"
        mode = ET.SubElement(dev2InterfaceTag, "mode").text = "100/1000T"
        module = ET.SubElement(dev2InterfaceTag, "module")
        poe = ET.SubElement(dev2InterfaceTag, "poe")
        slot = ET.SubElement(dev2InterfaceTag, "slot")
        systemPod = ET.SubElement(
            dev2InterfaceTag,
            "system-pod").text = "virtual"

        # create device 1 link block
        dev2LinkTag = ET.SubElement(device2Element, "link")
        linkName = ET.SubElement(dev2LinkTag, "name").text = link
        id = ET.SubElement(dev2LinkTag, "id")
        rate = ET.SubElement(dev2LinkTag, "rate").text = "Ethernet-1Gb"
        remoteDev2 = ET.SubElement(dev2LinkTag, "remoteDevice").text = device1
        remoteInterface2 = ET.SubElement(
            dev2LinkTag,
            "remoteInterface").text = str(
            device1Port)
        localInteface2 = ET.SubElement(
            dev2LinkTag,
            "localInterface").text = str(
            device2Port)
        type = ET.SubElement(dev2LinkTag, "type").text = "auto"
        asicVersion = ET.SubElement(dev2LinkTag, "asicVersion")

        retCls = opstestfw.returnStruct(returnCode=0)
        return retCls

    def InterfaceGetByDeviceLink(self, **kwargs):
        """
        This method gets the real interfaces attached to a link
        :param device: Device whose link needs to be determined
        :type device:  string
        :param link: Device link
        :type link: string

        """
        device = kwargs.get('device', None)
        link = kwargs.get('link', None)

        xpath = ".//device[name='" + str(device) + \
            "']/link[name='" + str(link) + "']/localInterface"
        retStruct = opstestfw.XmlGetElementsByTag(self.TOPOLOGY, xpath)
        retCls = opstestfw.returnStruct(returnCode=0, data=retStruct.text)
        return retCls

    def Links(self, **kwargs):
        """
        This method makes a list of links associated with a device
        :param device : Device name
        :type  device : string

        """
        device = kwargs.get('device', None)

        xpath = ".//link"
        linksList = []
        linkElements = opstestfw.XmlGetElementsByTag(
            self.LOGICAL_TOPOLOGY, xpath, allElements=True)
        # print linkElements
        for curElement in linkElements:
            linkName = curElement.attrib['name']
            device1 = curElement.attrib['device1']
            device2 = curElement.attrib['device2']
            if device == device1 or device == device2:
                linksList.append(linkName)
        return linksList

    # Get the provisioning targets (Physical devices)
    def GetProvisioningTargets(self):
        """
        This routine returns the provisioning target switches as defined
        in the topology dictionaryi(topotarget) (only for physical switches)

        """
        self.LOGICAL_TOPOLOGY = ET.Element("topology", attrib={'version': "3"})
        # Get target if there
        self.targets = str(self.topoDict.get('topoTarget', None))
        return self.targets

    # Logical Topology Create
    def LogicalTopologyCreate(self):
        """
        This routine creates Logical topologies taking the topology dictionary
        described in the test case as an input

        """
        self.LOGICAL_TOPOLOGY = ET.Element("topology", attrib={'version': "3"})

        # Get target if there
        self.targets = str(self.topoDict.get('topoTarget', None))
        # self.topoLinks = str(self.topoDict.get)
        # create the links
        self.topoLinkFilter = ""

        if "topoLinks" in self.topoDict:
            mytopoLinks = str(self.topoDict['topoLinks'])
            self.topoLinks = re.sub('\s+', '', mytopoLinks)
            for curLink in str.split(self.topoLinks, ','):
                (link, dev1, dev2) = str.split(curLink, ':')
                linkTag = ET.SubElement(self.LOGICAL_TOPOLOGY,
                                        'link',
                                        attrib={'name': link, 'device1': dev1,
                                                'device2': dev2,
                                                'rate': "any"})

            # now search for topoLinkFilter in the dictionary
            if "topoLinkFilter" in self.topoDict:
                self.topoLinkFilter = str(self.topoDict['topoLinkFilter'])
        else:
            self.topoLinks = ""
        # Create TopoDevices
        self.topoDevices = str(self.topoDict['topoDevices'])
        for curDev in str.split(self.topoDevices):
            # Search for device in target
            curDevTarget = "false"
            for curTarget in str.split(self.targets):
                if curTarget == curDev:
                    curDevTarget = "true"
                    break

            deviceTag = ET.SubElement(
                self.LOGICAL_TOPOLOGY,
                'device',
                attrib={'name': curDev,
                        'target': curDevTarget,
                        'group': "NULL"})

        mytopoFilters = str(self.topoDict['topoFilters'])
        self.topoFilters = re.sub('\s+', '', mytopoFilters)
        for curFilter in str.split(self.topoFilters, ','):
            # print curFilter
            (cDev, cAttr, cVal) = str.split(curFilter, ':')
            # Search for the tag in logical topology
            xpath = ".//device[@name='" + cDev + "']"
            deviceTag = opstestfw.XmlGetElementsByTag(
                self.LOGICAL_TOPOLOGY, xpath)
            if deviceTag is not None and cAttr != "docker-image":
                attributeTag = ET.SubElement(
                    deviceTag,
                    'attribute',
                    attrib={'name': cAttr,
                            'value': cVal})
            if cAttr == "docker-image":
                self.hostimage = cVal
                attributeTag = ET.SubElement(
                    deviceTag,
                    'attribute',
                    attrib={'name': cAttr,
                            'value': cVal})

        # Now parse through topoLinkFilter statements
        if self.topoLinkFilter != "":
            for curTopoLinkFilter in str.split(self.topoLinkFilter, ','):
                # print curTopoLinkFilter
                (cLink, cDev, cFType, CAttr) = str.split(
                    curTopoLinkFilter, ':')
                # Search for Device in logical Topology
                xpath = ".//device[@name='" + cDev + "']"
                deviceTag = opstestfw.XmlGetElementsByTag(
                    self.LOGICAL_TOPOLOGY, xpath)
                if deviceTag is not None:
                    # Create new subElement for port
                    portTag = ET.SubElement(
                        deviceTag,
                        'port',
                        attrib={'link': cLink})
                    # Create Attribute tag now
                    attributeTag = ET.SubElement(
                        portTag,
                        'attribute',
                        attrib={'name': 'portName',
                                'value': CAttr})

        # Need to inspect ETREE to see if profile is specific.  If not, lets
        # assume auto-ubuntu-12-04 for workstations
        self.topo_wrkston_image_dict = dict()
        xpath = ".//device/attribute[@value='workstation']/.."
        #xpath = ".//device"
        wrkstonDevsTag = opstestfw.XmlGetElementsByTag(
            self.LOGICAL_TOPOLOGY, xpath, allElements=True)
        for curTag in wrkstonDevsTag:
            #print curTag
            wrkston_name = curTag.get('name')
            # Default to default image
            self.topo_wrkston_image_dict[wrkston_name] = "openswitch/ubuntutest:latest"
            # =" + wrkston_name
            attribute_list = curTag.findall('attribute')
            # print "attrList "
            # print attribute_list
            found_profile = 0
            found_docker = 0
            for curAttr in attribute_list:
                # print "curAttr"
                attrName = curAttr.get('name')
                # print attrName
                if attrName == "system-profile":
                    found_profile = 1
                    opstestfw.LogOutput(
                        'debug',
                        "Found system-profile attribute stated for device "
                        "- not assuming auto-ubuntu-12-04")
                if attrName == "docker-image":
                    found_docker = 1
                    found_profile = 1
                    opstestfw.LogOutput('debug',
                                        "Found docker-image attribute. "
                                        "Adding CentOS profile")
                    attrValue = curAttr.get('value')
                    self.topo_wrkston_image_dict[wrkston_name] = attrValue
            if found_profile == 0:
                # Need to add subelements
                opstestfw.LogOutput(
                    'debug',
                    "No system-profile attribute, default auto-ubuntu-12-04")
                deviceTag = ET.SubElement(
                    curTag,
                    'attribute',
                    attrib={
                        'name': "system-profile",
                        'value': "auto-ubuntu-12-04"})
            if found_docker == 1:
                opstestfw.LogOutput('debug',
                                    "Found docker image, need to boot centos")
                deviceTag = ET.SubElement(
                    curTag,
                    'attribute',
                    attrib={
                        'name': "system-profile",
                        'value': "CentOS"})

        dumpString = ET.tostring(self.LOGICAL_TOPOLOGY)

        # Write the topology out
        myxml = xml.dom.minidom.parseString(dumpString)
        pretty_xml_as_string = myxml.toprettyxml()
        topoFileName = self.runEnv.ResultsDirectory[
            'resultsDir'] + "/logicalTopology.xml"
        topologyXMLFile = open(topoFileName, 'w+')
        topologyXMLFile.write(pretty_xml_as_string)
        topologyXMLFile.close()

    # Logical device attributes
    def LogicalDeviceAttrsGet(self, **kwargs):
        """
        Topology LogicalDeviceAttributesGet method

        This method will query to logical topology for device attributes
        associated with the device passed

        :param device: logical device name
        :type device: string
        :return: dictionary

        """

        deviceName = kwargs.get('device', None)
        xpath = ".//device[@name=" + deviceName + "]"
        #xpath = ".//device"
        deviceTag = opstestfw.XmlGetElementsByTag(
            self.LOGICAL_TOPOLOGY, xpath, allElements=True)

        attribute_list = deviceTag.findall('attribute')
        retDict = dict()

        for curAttr in attribute_list:
            attrName = curAttr.get('name')
            attrValue = curAttr.get('value')
            retDict[attrName] = attrValue
        return retDict

    # Routine to go and create device objects and establish connections
    def CreateDeviceObjects(self):
        """
        This routine creates device objects and establishes connections

        """
        # Look to the logical topology to
        xpathString = ".//device"
        deviceEtreeElements = opstestfw.XmlGetElementsByTag(
            self.LOGICAL_TOPOLOGY, xpathString, allElements=True)

        if deviceEtreeElements is None:
            opstestfw.LogOutput(
                'error',
                "Did not find devices to spawn off device connections")
            return None

        for curEtree in deviceEtreeElements:
            deviceName = curEtree.get('name')
            attribute_list = curEtree.iter('attribute')

            for curAttr in attribute_list:
                # print "curAttr"
                attrName = curAttr.get('name')
                # print attrName
                if attrName == "system-category":
                    categoryValue = curAttr.get('value')

                    if categoryValue == "switch":
                        # Do logic to spawn switch off
                        opstestfw.LogOutput(
                            'info',
                            "Connecting to switch " +
                            deviceName +
                            " (" +
                            self.topo[
                                deviceName] +
                            ")")
                        switchObj = self.LaunchSwitch(
                            device=self.topo[deviceName])
                        self.deviceObj[deviceName] = switchObj
                        deviceLinks = self.Links(device=deviceName)
                        # Populate Link dictionary for each device str
                        switchObj.linkPortMapping = dict()
                        # Populate the name of the switch devices in the
                        # topology
                        switchObj.topo = dict()

                        for curLink in deviceLinks:
                            portStruct = self.InterfaceGetByDeviceLink(
                                link=self.topo[curLink],
                                device=self.topo[deviceName])
                            port = portStruct.valueGet()
                            switchObj.linkPortMapping[curLink] = port

                        # Set up default Context
                        switchObj.setDefaultContext(context=self.defaultSwitchContext)

                    if categoryValue == "workstation":
                        # Do logic to spawn host off
                        opstestfw.LogOutput(
                            'info',
                            "Connecting to host " +
                            deviceName +
                            " (" +
                            self.topo[
                                deviceName] +
                            ")")
                        hostObj = self.LaunchHost(device=self.topo[deviceName])
                        self.deviceObj[deviceName] = hostObj

                        deviceLinks = self.Links(device=deviceName)
                        # Populate Link dictionary for each device str
                        hostObj.linkPortMapping = dict()
                        for curLink in deviceLinks:
                            portStruct = self.InterfaceGetByDeviceLink(
                                link=self.topo[curLink],
                                device=self.topo[deviceName])
                            port = portStruct.valueGet()
                            hostObj.linkPortMapping[curLink] = port

    def deviceObjGet(self, **kwargs):
        """
        This routine returns the device object
        :param device: Device name
        :type device: string
        """

        device = kwargs.get('device', None)
        return(self.deviceObj[device])

    def LaunchSwitch(self, **kwargs):
        """
        This routine launches the VSwitch.py class for the applicable topology
        :param device: Device name
        :type device: string
        :param noConnect:
        :type noConnect : Boolean to flag not actually connecting to the
                          device
        """

        device = kwargs.get('device')
        noConnect = kwargs.get('noConnect', False)
        switchObj = opstestfw.VSwitch(
            topology=self,
            device=device,
            noConnect=noConnect)
        return switchObj

    def LaunchHost(self, **kwargs):
        """
        This routine launches the VHost.py class for the applicable topology
        :param:device: Host name
        :type :device: string

        """
        device = kwargs.get('device')
        hostObj = opstestfw.VHost(topology=self, device=device)
        return hostObj

    def inbandSwitchConnectGet(self, **kwargs):
        """
        This routine establishes an inband connection to the switch device
        using SSH
        :param srcObj: Object of the device from which to connect
        :type  srcObj: Object
        :param targetObj : Switch object
        :type targetObj : object
        :param address : Ip address of switch
        :type address : string
        :param user: ssh user ID
        :type user : string
        :param sshArgs: ssh parameters
        :type sshArgs: string
        :param sshPassword : ssh user name password
        :type sshPassword  : string

        Return :
          -New switch connection object
          -Non zero return code in case of failure to so ssh

        """
        deviceConnFrom = kwargs.get('srcObj', None)
        deviceConnTo = kwargs.get('targetObj', None)
        targetAddress = kwargs.get('address', None)
        targetUser = kwargs.get('user', "root")
        sshArgs = kwargs.get('args', "-o StrictHostkeyChecking=no")
        sshPassword = kwargs.get('sshPassword', None)

        # Create the new how object and then connect.
        newHostObj = self.LaunchHost(device=deviceConnFrom.device,
                                     factoryDefaultCheck=False,
                                     sshCon=True)
        newSwitchObj = self.LaunchSwitch(noConnect=True)
        newSwitchObj.expectHndl = newHostObj.expectHndl
        newSwitchObj.deviceContext = "linux"
        bailflag = 0
        returnCode = 0
        sshCommand = "ssh " + sshArgs + " " + \
            targetUser + "@" + str(targetAddress)
        if sshPassword is not None:
            # In case of non root user password needs to be passed
            connectionBuffer = []
            self.expectList = ['[A-Za-z0-9]+#',
                               '[\[\]A-Za-z0-9@~\s]+#',
                               'ssh_exchange_identification: Connection closed by remote host',
                               '\(config\)#',
                               '\(config-\S+\)#\s*$',
                               '.*password:',
                               'Permission denied .*:',
                               pexpect.EOF,
                               pexpect.TIMEOUT]

            newSwitchObj.expectHndl.send(sshCommand)
            newSwitchObj.expectHndl.send('\r')
            sshRetCode = 0
            while bailflag == 0:
                index = newSwitchObj.expectHndl.expect(self.expectList,
                                                       timeout=30)
                if index == 0 or index == 1:
                    opstestfw.LogOutput("debug", "Prompt received")
                    connectionBuffer.append(newSwitchObj.expectHndl.before)
                    bailflag = 1
                elif index == 2 :
                    opstestfw.LogOutput("debug", "Prompt received")
                    connectionBuffer.append(newSwitchObj.expectHndl.before)
                    sshRetCode = 1591
                elif index == 5:
                    opstestfw.LogOutput("debug", "Sending password")
                    newSwitchObj.expectHndl.send(sshPassword)
                    newSwitchObj.expectHndl.send('\n')
                    connectionBuffer.append(newSwitchObj.expectHndl.before)
                elif index == 7:
                    # Got EOF
                    opstestfw.LogOutput('error', "Telnet to switch failed")
                    return None
                elif index == 8:
                    # Got a Timeout
                    opstestfw.LogOutput('error', "Connection timed out")
                    return None
                else:
                    connectionBuffer.append(newSwitchObj.expectHndl.before)
            # Append on buffer after
            connectionBuffer.append(newSwitchObj.expectHndl.after)
            newSwitchObj.expectHndl.expect(['$'], timeout=2)
            self.santString = ""
            for curLine in connectionBuffer:
                self.santString += str(curLine)
            # Do an error check on the new inband connection
            if sshRetCode == 0:
               opstestfw.LogOutput('debug', "Doing error check at DUT")
               errCheckRetStr = newSwitchObj.ErrorCheckCLI(buffer=self.santString)
               returnCode = errCheckRetStr['returnCode']
               sshRetCode = returnCode
        else:
            sshReturn = newHostObj.DeviceInteract(command=sshCommand)
            sshRetCode = sshReturn.get('returnCode')
            # sshBuffer = sshReturn.get('buffer')

        if sshRetCode != 0:
            opstestfw.LogOutput(
                'error',
                "ssh connection to " + str(
                    targetAddress) + " failed")
            return sshRetCode
        else:
            opstestfw.LogOutput(
                'debug',
                "ssh connection to " + str(
                    targetAddress) + " succeeded")

        # Now lets stash this away for future retrieval
        pseudoDeviceName = self.topo.get(
            deviceConnTo.device) + "-ssh-" + str(
            self.inbandIndex)
        self.inbandIndex += 1
        self.deviceObj[pseudoDeviceName] = newSwitchObj
        return newSwitchObj

    def deviceObjList(self):
        return self.deviceObj.keys()

    # Write out Topology File Physical
    def TopologyXMLWrite(self):
        """

        This routine writes the physical topology xml file to
        results directory corresponding to a particular test run.

        """
        dumpString = ET.tostring(self.TOPOLOGY)
        # print "topologyDump" + str(dumpString)
        myxml = xml.dom.minidom.parseString(dumpString)
        pretty_xml_as_string = myxml.toprettyxml()
        topoFileName = self.runEnv.ResultsDirectory[
            'resultsDir'] + "/physicalTopology.xml"
        topologyXMLFile = open(topoFileName, 'w+')

        topologyXMLFile.write(pretty_xml_as_string)
        topologyXMLFile.close()
