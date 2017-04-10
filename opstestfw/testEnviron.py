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

import os
import sys
import time
import datetime
import json
import pytest
from opstestfw import *
import inspect
import xml.etree.ElementTree
import opstestfw.gbldata
import logging
import glob
import pdb
from commands import *


class testEnviron ():

    """
    This is the base class for any device.
    """
    def __init__(self, **kwargs):

        """
        testEnviron class object is will create the test environment object.

        :param topoDict: Topology dictionary defined in the testcase
        :type topoDict: dictionary

        """
        self.topoDict = kwargs.get('topoDict')
        self.defaultSwitchContext = kwargs.get('defSwitchContext', "linux")

        self.rsvnId = None
        self.topoObj = None
        self.ResultsDirectory = dict()
        self.targetBuild = None
        self.envSetup()
        # Here is where we will stub in the provisionng logic.
        # We should have a topoObj by now
        self.topoObj.CreateDeviceObjects()

        # Check for any docker bringup failures
        if self.rsvnId == 'virtual':
            if self.topoObj.cur_hw_failure:
                LogOutput('error', "cur_hw was not set to 1. "
                                   "Check logs folder : "
                                   + self.ResultsDirectory['resultsDir'])
                self.topoObj.terminate_nodes()
                pytest.fail("cur_hw was not set to 1")
            if self.topoObj.switchd_failure:
                LogOutput('error', "Switchd failed to startup. "
                                   "Check the logs folder : "
                                   + self.ResultsDirectory['resultsDir'])
                self.topoObj.terminate_nodes()
                pytest.fail("Switchd failed to startup")
            if self.topoObj.tuntap_failure:
                self.topoObj.terminate_nodes()
                pytest.fail("Failure adding tuntap interfaces")

        # Provisioning block starts here
        # Provision the physical devices if targetBuild flag is present in
        # the environment
        # self.topoObj.deviceObjGet(device="dut01")
        if self.targetBuild:
            self.targetBuild.strip()
            if self.rsvnId != "virtual" and self.targetBuild != " ":
                try:
                    import rtltestfw
                except ImportError:
                    LogOutput('debug', "RTL environment not available")
                targets = self.topoObj.GetProvisioningTargets()
                targetList = targets.split()
                for target in targetList:
                    if target is not "None":
                        self.topoObj.deviceObjGet(device=target)
                        returnCls = rtltestfw.SwitchProvisioning(TftpImage=self.targetBuild,
                                                                 topoObj=self.topoObj,
                                                                 target=target)
                        returnCode = returnCls.returnCode()
                        if returnCode != 0:
                            LogOutput('error',
                                      "Unable to provision target :: Exiting")
                            exit(1)
                        else:
                            LogOutput('info',
                                      "No targets defined in topo dictionary")

        if self.rsvnId != "virtual":
            LogOutput('info', "Enabling all logical links")
            self.topoObj.LinkModifyStatus(enable=1, allLogical=1)

    def envSetup(self):

        """
        envSetup class method

        This routine does environment setup for the test.

        """
        envRsvnId = os.environ.get('RSVNID', None)
        if envRsvnId is not None:
            self.rsvnId = envRsvnId
        else:
            self.rsvnId = 'virtual'

        envTargetBuild = os.environ.get('TARGETBUILD', None)
        if envTargetBuild is not None:
            self.targetBuild = envTargetBuild

        envResultDir = os.environ.get('RESULTDIR', None)
        if envResultDir is not None:
            self.resultDir = envResultDir
        else:
            self.resultDir = None

        topPktdirname = os.path.dirname(opstestfw.__file__)
        findOutput = getoutput("find " + topPktdirname + " -type d")
        for curdirname in str.split(findOutput, '\n'):
            sys.path.append(curdirname)

        if self.resultDir is None:
            # Means we need to create the results structure
            # currentDir = GetCurrentDirectory()
            ts = time.time()
            timeStamp = datetime.datetime.fromtimestamp(ts).strftime('%Y%b%d'
                                                                     '_%H%M%S')

            if os.path.isdir("/tmp/opsTest-results") is False:
                try:
                    retCode = os.mkdir("/tmp/opsTest-results")
                except:
                    print "Failed to create /tmp/opsTest-results"
            baseResultsDir = "/tmp/opsTest-results"

            filepath = os.path.abspath(inspect.stack()[2][1])
            filename = os.path.splitext(os.path.basename(filepath))[0]

            self.ResultsDirectory['resultsDir'] = baseResultsDir + "/" \
                + filename + "-" + timeStamp + "/"
            gbldata.ResultsDirectory = baseResultsDir + "/"\
                + filename + "-" + timeStamp + "/"
            self.ResultsDirectory['rtlDir'] = baseResultsDir + "/"\
                + filename + "-" + timeStamp + "/RTL/."
        else:
            baseResultsDir = self.resultDir
            self.ResultsDirectory['resultsDir'] = baseResultsDir + "/"
            gbldata.ResultsDirectory = baseResultsDir + "/"
            self.ResultsDirectory['rtlDir'] = baseResultsDir + "/" + "/RTL/"

        self.ResultsDirectory['summaryLog'] = self.ResultsDirectory['resultsDir']\
            + "summary.log"
        self.ResultsDirectory['detailLog'] = self.ResultsDirectory['resultsDir']\
            + "detail.log"

        retCode = ChangeDirectory(baseResultsDir)
        if retCode['returnCode'] == 0 and self.resultDir is None:
            retCode = CreateDirectory(self.ResultsDirectory['resultsDir'])

        if retCode['returnCode'] == 0:
            # Create RTL directory
            if self.rsvnId != "virtual":
                ChangeDirectory(self.ResultsDirectory['resultsDir'])
                retCode = CreateDirectory("RTL/.")
            # Create Files under the result directory structure(summary file)
            retCode = FileCreate(self.ResultsDirectory['resultsDir'],
                                 "summary.log")
            if retCode['returnCode'] != 0:
                LogOutput('error', "File summary.log not created in the "
                          "directory structure")
                exit(1)
            # Create Files under the result directory structure(detail.log)
            retCode = FileCreate(self.ResultsDirectory['resultsDir'],
                                 "detail.log")
            if retCode['returnCode'] != 0:
                LogOutput('error', "File detail.log not created in the "
                          "directory structure")
                exit(1)
        else:
            LogOutput('error',
                      "Result Directory structure not created . Exiting")
            exit(1)

        # Nowsettle on topology
        topologyType = str(self.topoDict.get('topoType', None))
        if self.rsvnId is "virtual":
            # Check to see if we have an RSVNID variable
            envKeys = os.environ.keys()
            for curKey in envKeys:
                if curKey == "RSVNID":
                    tmpRsvn = os.environ['RSVNID']
                    if str.isdigit(tmpRsvn):
                        LogOutput('info', "Detected RSVNID in environment")
                        self.rsvnId = tmpRsvn
                # Get the image to be uploaded on the targets from the
                # environment
                if curKey == "targetBuild":
                    LogOutput('info',
                              "Detected provisioning flag in the environment"
                              " (targetBuild)")
                    self.targetBuild = os.environ['targetBuild']
            # Do TopoDict Check to see if this is physical only
            # If not there, we can run either physical / virtual
            # if set to physical, then only can run physical
            # if set to virtual, then only can run virtual
            if topologyType == "None" or topologyType == "virtual":
                LogOutput('debug', "Topology validation passed")
            else:
                LogOutput('info',
                          "Skipping test due to it being a physical only test")
                time.sleep(2)
                pytest.skip("Skipping test due to it being a physical "
                            "only test")

        else:
            if topologyType == "None" or topologyType == "physical":
                LogOutput('debug', "Topology validation passed")
            else:
                LogOutput('info',
                          "Skipping test due to it being a virtual only test")
                time.sleep(2)
                pytest.skip("Skipping test due to it being a virtual only "
                            "test ")

        LogOutput('info', "", datastamp=True)
        LogOutput('info', "\nPhysical Topology is: " + str(self.rsvnId))
        LogOutput('info', "Test result directory is: " +
                  self.ResultsDirectory['resultsDir'])

        # Read in the Topology
        if self.rsvnId == "virtual":
            self.topoType = "virtual"
            LogOutput('info', "Topology is virtual - creating environment "
                      "specified in the test case topoDict structure")
            # Create a topology object
            self.topoObj = Topology(topoDict=self.topoDict, runEnv=self,
                                    defSwitchContext=self.defaultSwitchContext,
                                    resultsDir=self.ResultsDirectory['resultsDir'])

        elif str.isdigit(self.rsvnId) is True:
            self.topoType = "physical"
            try:
                import rtltestfw
            except ImportError:
                LogOutput('debug', "RTL environment not available")

            # This means we have passed a reservation in
            LogOutput('info', "Topology reservation ID was passed in.  ID = "
                      + str(self.rsvnId) + " querying the topology")
            # Create Topology Object
            self.topoObj = rtltestfw.RTL_Topology(topoDict=self.topoDict,
                                                  topoType="physical",
                                                  rsvnId=self.rsvnId,
                                                  runEnv=self,
                                                  defSwitchContext=self.defaultSwitchContext)

    def topoObjGet(self):

        """
        topoObjGet class method

        This routine returns the topology object

        """
        return(self.topoObj)


class returnStruct():

    """
    returnStruct Class definition

    The returnStruct Class is the return structure that routines will
    use to return status, data, and output back to the calling routine.
    """

    def __init__(self, **kwargs):

        """
        returnStruct init routine definition.  Called on the creation of
        returnStruct.

        :param returnCode :  Return code of the routine.  0 for success
                             1 for failure
        :type returnCode  : integer
        :param buffer     : Buffer of output from the routine
        :type  buffer     : string
        :param data       : data (single piece or dictionary)
        :type  data       : dictionary / integer / string

        """
        self.retCode = kwargs.get('returnCode', None)
        self.return_buffer = kwargs.get('buffer', "")
        self.data = kwargs.get('data', None)
        self.jsonCreate()

    def returnCode(self):

        """
        returnCode method will return the integer returnCode member

        :return: return code integer
        :returnType: integer

        """
        return self.retCode

    def buffer(self):

        """
        buffer method will return the buffer member

        :return: buffer
        :returnType: string

        """
        return self.return_buffer

    def returnJson(self):

        """
        returnJson method will return returnStructure string in JSON
        format.

        :return: JSON string
        :returnType: string

        """
        return self.jsonData

    def dataKeys(self):

        """
        dataKeys method will return the keys of the dictionary data in the
        returnStruct object

        :return: list of keys
        :returnType: list

        """
        return self.data.keys()

    def valueGet(self, **kwargs):

        """
        valueGet method will return value in for the key passed for the data
        dictionary

        :param key : key from a dictionary, if none is past, data is just
                     passed back
        :type: key : index
        :return: data
        :returnType: string / integer / dictionary
        """
        key = kwargs.get('key', None)
        if key is None:
            return self.data
        return self.data[key]

    def retValueString(self):

        """
        retValueString method will return JSON data string

        :return: JSON string
        :returnType: string
        """
        return self.jsonData

    def printValueString(self):

        """
        printValueString method will print returnStruct in JSON string format

        """

        localString = self.retValueString()
        LogOutput('info', localString)

    def jsonCreate(self):

        """
        jsonCreate is in internal function that creates JSON string from
        returnStruct member data

        """

        localDict = dict()
        localDict['returnCode'] = self.retCode
        localDict['buffer'] = self.return_buffer
        localDict['data'] = self.data
        self.jsonData = json.dumps(localDict, indent=3)

# General / Common library routines

def CreateDirectory(dirName):

    """
    Library function to create a directory

    :param arg1 : directory name
    :type  arg1 : string

    :return: dictionary
        data: - Dictionary:
               Keys: DirPath, returnCode
    :returnType: dictionary
    """

    dir = os.path.dirname(dirName)
    retDataStruct = dict()
    if not os.path.exists(dirName):
        os.makedirs(dir)
        if os.path.exists(dir):
            retDataStruct['DirPath'] = os.getcwd()+dirName
            retDataStruct['returnCode'] = 0
        else:
            LogOutput('error', "Result Directory" + dir + "not created")
            retDataStruct['returnCode'] = 1
    else:
        retDataStruct['returnCode'] = 1
    return retDataStruct


def ChangeDirectory(path):

    """
    Library function to change to a directory

    :param arg1 : path
    :type  arg1 : string

    :return: dictionary
        data: - Dictionary:
               Keys: returnCode
    :returnType: dictionary
    """

    retDataStruct = dict()
    try:
        os.chdir(path)
        retDataStruct['returnCode'] = 0
    except:
        retDataStruct['returnCode'] = 1
    return retDataStruct


def GetCurrentDirectory():

    """
    Library function to return current directory

    :return: dictionary or string
        data: - Dictionary:
               Keys: returnCode
    :returnType: dictionary / string
    """
    currentDir = os.getcwd()
    if currentDir is None:
        retStruct = dict()
        retStruct['returnCode'] = 1
        return retStruct
    else:
        return currentDir


def FileCreate(DirPath, fileName):

    """
    Library function to create a new file

    :param arg1 : path
    :type  arg1 : string
    :param arg1 : filename
    :type  arg1 : string

    :return: dictionary
        data: - Dictionary:
               Keys: returnCode
    :returnType: dictionary
    """

    filePath = os.path.join(DirPath, fileName)
    retDataStruct = dict()
    try:
        if not os.path.exists(fileName):
            # Trying to create a new file or open one
            file = open(filePath, 'w')
            retDataStruct['returnCode'] = 0
        else:
            print "File already exists in this path" + DirPath
            retDataStruct['returnCode'] = 0
    except Exception as Err:
        print Err
        raise Exception("FILE NOT CREATED:: " + fileName)
        retDataStruct['returnCode'] = 1
    return retDataStruct


class DeviceLogger(object):

    """
    DeviceLogger Class definition

    This class will create / manage testcase log file structure
    """

    def __init__(self, file):

        """
        DeviceLogger initialization method

        :param arg1 : filename
        :type  arg1 : string

        """
        self.file = file

    def write(self, data):

        """
        write method for DeviceLogger

        :param arg1 : data
        :type  arg1 : string

        """

        # .. filter data however you like
        ts = time.time()
        ts = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
        data = data.strip()

        # Do not log blank spaces
        if data in [' ', '', '\n', '\r', '\r\n']:
            return
        if data:  # non-blank
            # Inspect the stacktrace to get the called module
            # Module trace needs to be dumped to logging module
            # This code will not log unnecessary internal modules
            # (so that log looks clean)
            stackTrace = inspect.stack()
            module = inspect.getmodule(stackTrace[4][0])
            if module is None:
                modulename = module.__name__
                if modulename == "pexpect":
                    modulename = None
                else:
                    self.file.write("++++" + ts + "  " + "Module:"
                                    + "(" + modulename + ")" + "  " + "\n")
            return self.file.write(data + "\n")

    def flush(self):

        """
        flush method for DeviceLogger.  This will flush the file descriptor

        """
        self.file.flush()

    def OpenExpectLog(self, ExpectFileName):

        """
        OpenExpectLog method for DeviceLogger.

        OpenExpectLog function opens a new file to log the expect buffer output

        :param arg1 : ExpectFileName
        :type arg1  : string
        :return:  1 or handle
                  Return 1 in case of error (expect logfile not created),
                  expect file handle in case of success
        :returnType:  handle

        """
        fullFilePath = opstestfw.gbldata.ResultsDirectory + ExpectFileName
        if os.path.isfile(fullFilePath):
            LogOutput('debug', "Filename exists, creating a new indexed file")
            # Now lets see if there are index files that exists
            filebase, fileext = os.path.splitext(fullFilePath)
            fileList = glob.glob(filebase + "*")

            numFiles = len(fileList)
            newFileBase = filebase + "_" + str(numFiles)
            newFileFullPath = newFileBase + fileext
            ExpectFileName = os.path.basename(newFileFullPath)
        retCode = FileCreate(opstestfw.gbldata.ResultsDirectory,
                             ExpectFileName)
        if retCode['returnCode'] == 0:
            # 'full'
            fname = opstestfw.gbldata.ResultsDirectory + "/" + ExpectFileName
            expectLogfile = open(fname, 'w')
            return expectLogfile
        else:
            returnCode = 1
        return returnCode


def LogOutputToFile(path, level, message):

    """
    Library routine to write the logger message to summary and detail file
    based on the level

    :param arg1 : path
    :type  arg1 : string
    :param arg2 : level
    :type  arg2 : string
    :param arg3 : message
    :type  arg3 : string

    """
    intResult = 1
    strSummaryFileName = path + "summary.log"
    strDetailedFileName = path + "detail.log"
    if(os.access(strSummaryFileName, os.W_OK)):
        pass
    else:
        print("either file not exists for %s or no write permission"
              % strSummaryFileName)
        return intResult

    if(os.access(strDetailedFileName, os.W_OK)):
        pass
    else:
        print("either file not exists for %s or no write permission"
              % strDetailedFileName)
        return intResult

    if (level == "debug"):
        writeLogFile(strDetailedFileName, level, message)
    else:
        writeLogFile(strSummaryFileName, level, message)
        writeLogFile(strDetailedFileName, level, message)
    intResult = 0
    return intResult


def writeLogFile(logfile, level, message):

    """
    Library routine to write the logger message to passed file
    based on the level

    :param arg1 : logfile
    :type  arg1 : string
    :param arg2 : level
    :type  arg2 : string
    :param arg3 : message
    :type  arg3 : string

    """

    logger = logging.getLogger()
    formatter = logging.Formatter('%(levelname)-5s - %(asctime)-6s - '
                                  '%(message)s',
                                  '%H:%M:%S')
    fh = logging.FileHandler(logfile)
    if (level == "info"):
        fh.setLevel(logging.INFO)
        logger.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        logger.info(message)
    elif (level == "error"):
        fh.setLevel(logging.ERROR)
        logger.setLevel(logging.ERROR)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        logger.error(message)
    elif (level == "debug"):
        fh.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        logger.debug(message)
    logger.removeHandler(fh)


def LogOutput(dest, message, **kwargs):

    """
    Library routine to write the logger message to stdout along with dest
    log file

    :param arg1 : dest
    :type  arg1 : string
    :param arg2 : message
    :type  arg2 : string
    :param datastamp : True to put date stamp in or False to leave out
    :type  datastamp : boolean

    """

    datestamp = kwargs.get('datastamp', False)
    logType = str(dest)

    if datestamp is True:
        timestring = time.strftime("%m/%d/%y %H:%M:%S", time.localtime())
    else:
        timestring = time.strftime("%H:%M:%S", time.localtime())
        messageSpl = message.split("\n")
        timestampSent = 0
        for msgLine in messageSpl:
            if timestampSent:
                print('%s' % msgLine)
            if logType == 'info' or logType == 'error':
                print("%s %-6s\t%s" % (timestring, logType, msgLine))
    # Logging messages to Log files based on severity
    if logType == 'info':
        message = "%s" % (message)
    else:
        message = "::%s" % (message)
    LogOutputToFile(opstestfw.gbldata.ResultsDirectory, dest, message)


# XML Manipulation Routines
def XmlFileLoad(xmlFile):

    """
    Library routine load an XML file into a local etree

    :param arg1 : xmlFile
    :type  arg1 : string

    :return:  etree representing the XML data
    :returnType: etree
    """
    # check and see if the file exists
    fileExists = os.path.exists(xmlFile)
    if fileExists is False:
        LogOutput('info', "File " + xmlFile + " does not exist.")
        return None

    eTree = xml.etree.ElementTree.parse(xmlFile)
    return eTree


def XmlElementSubElementAppend(parentElement, childElement):

    """
    Library routine append a subelement to an element in an Etree

    :param arg1 : Etree Parent Element
    :type  arg1 : Etree element
    :param arg2 : Etree Child Element
    :type  arg2 : Etree element

    :return:  etree child element
    :returnType: etree element
    """
    mychild = parentElement.append(childElement)
    return mychild


def XmlGetElementsByTag(etree, tag, **kwargs):

    """
    Library routine return data from a tag in an etree

    :param arg1 : Etree
    :type  arg1 : Etree
    :param arg2 : tag
    :type  arg2 : string
    :param allElements : True to return all elements if multiple found,
                         Falue to return first element only
    :type  allElements : boolean

    :return:  etree element
    :returnType: etree element
    """

    allElements = kwargs.get('allElements', False)
    if allElements is False:
        elements = etree.find(tag)
    else:
        elements = etree.findall(tag)
    return elements


def Sleep(**kwargs):

    """
    Library routine to sleep for a tiem and print messaging and countdown
    timer for seconds

    :param message : String of message to print in sleep message
    :type  message : string
    :param seconds : number of seconds to sleep
    :type  seconds : integer

    """

    message = kwargs.get('message')
    seconds = kwargs.get('seconds')

    message = message + " - Pausing for " + str(seconds) + " seconds"
    LogOutput('info', message)
    rangeUpper = seconds + 1
    for i in range(1, rangeUpper):
        time.sleep(1)
        sys.stdout.write("\r")
        printstring = "\t\t%-2d of %-2d" % (i, seconds)
        sys.stdout.write(printstring)
        sys.stdout.flush()

    sys.stdout.write("\r")
    LogOutput('info', "Completed wait for %d seconds" % seconds)
