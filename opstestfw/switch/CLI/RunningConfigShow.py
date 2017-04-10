#!/usr/bin/python

# (c) Copyright 2015 Hewlett Packard Enterprise Development LP
#
# GNU Zebra is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2, or (at your option) any
# later version.
#
# GNU Zebra is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GNU Zebra; see the file COPYING.  If not, write to the Free
# Software Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.

from opstestfw import *
from opstestfw.switch.CLI import *
from opstestfw.switch.OVS import *

IPV4_STATIC_ROUTE = "ipv4_static_route"
IPV6_STATIC_ROUTE = "ipv6_static_route"


def if_config_in_running_config(**kwargs):

    """
    Library function to checks whether a given configuration exists
    in the "show running-config" output or not. If the configuration
    exists in the "show running-config", then this function returns 'True'
    otherwise this function will return 'False'.

    :param deviceObj : Device object
    :type  deviceObj : object
    :param configtype : Configuration type that the user wants to tests
                        in the "show running-config" output. This should
                        be a string. The configtype can be only one of
                        the following string:-
                        IPv4 static route configuration: "ipv4_static_route"
                        IPv6 static route configuration: "ipv6_static_route"
    :type configtype: string
    :param route     : Route which is of the format "Prefix/Masklen"
    :type  route     : string
    :param nexthop   : Nexthop which is of the format "IP/IPv6 address" or
                       "Port number"
    :type nexthop    : string
    :param distance  : Administration distance of the route
    :type distance   : string
    :returnType: Boolean
    """

    deviceObj = kwargs.get('deviceObj', None)
    configtype = kwargs.get('configtype', None)
    running_config_string = ''

    # If Device object is not passed, we need to error out and return 'False'
    if deviceObj is None:
        opstestfw.LogOutput('error',
                            "Need to pass switch device object deviceObj "
                            "to this routine")
        return False

    # If config type is not passed, we need to error out and return 'False'
    if configtype is None:
        opstestfw.LogOutput('error',
                            "Need to pass the config type to this routine")
        return False

    # If the config type is either IPV4_STATIC_ROUTE or IPV6_STATIC_ROUTE:,
    # then read the route, nexthop and distance from the arguments
    if configtype is IPV4_STATIC_ROUTE or configtype is IPV6_STATIC_ROUTE:

        route = kwargs.get('route', None)
        nexthop = kwargs.get('nexthop', None)
        distance = kwargs.get('distance', None)

        # If route is not passed, we need to error out and return 'False'
        if route is None:
            opstestfw.LogOutput('error',
                                "Need to pass the route if looking for static "
                                "route in running config")
            return False

        # If nexthop is not passed, we need to error out and return 'False'
        if nexthop is None:
            opstestfw.LogOutput('error',
                                "Need to pass the nexthop if looking for "
                                "static route in running config")
            return False

        # Form the IPv4/IPV6 configuration string. This will be checked in the
        # the output of "show running-config"
        if configtype is IPV4_STATIC_ROUTE:

            # Check if the distance needs to be added into the configuration
            # string
            if distance is None:
                running_config_string = 'ip route ' + route + ' ' + nexthop
            else:
                running_config_string = 'ip route ' + route + ' ' + \
                                        nexthop + ' ' + distance
        else:
            # Check if the distance needs to be added into the configuration
            # string
            if distance is None:
                running_config_string = 'ipv6 route ' + route + ' ' + nexthop
            else:
                running_config_string = 'ipv6 route ' + route + ' ' + \
                                        nexthop + ' ' + distance

    # Get into vtyshelll
    returnStructure = deviceObj.VtyshShell(enter=True)
    returnCode = returnStructure.returnCode()
    if returnCode != 0:
        opstestfw.LogOutput('error', "Failed to get vtysh prompt")
        return False

    # The command in whose output we need to check the presence of
    # configuration
    command = "show running-config"

    # Execute the command in the vtyshell
    returnDevInt = deviceObj.DeviceInteract(command=command)
    retCode = returnDevInt['returnCode']
    show_running_config = returnDevInt['buffer']
    if retCode != 0:
        opstestfw.LogOutput('error', "No running config on the device"
                            + command)
    else:
        opstestfw.LogOutput('debug', "Found running config on the device"
                            + command)

    # Get out of vtyshell
    returnStructure = deviceObj.VtyshShell(enter=False)
    returnCode = returnStructure.returnCode()
    if returnCode != 0:
        opstestfw.LogOutput('error', "Failed to exit vtysh prompt")
        return False

    # Split the output of "show running-config" into lines
    show_running_config_lines = show_running_config.split('\n')

    # Walk through all the lines of "show running-config" and check if the
    # configuration exists in one of the lines
    for line in show_running_config_lines:

        # If the configuration exists in the "show running-config" output,
        # then return 'True'
        if running_config_string in line:
            return True

    # If the configuration does not exists in the "show running-config" output,
    # then return 'False'
    return False


def verify_route_and_nexthop_in_show_running_config(**kwargs):
    """
    Library function tests whether a static route with "prefix/mask-length",
    next-hop and administration distance exists in the command
    "show running-config". If such a static route configuration does not exists
    in the output of "show running-config" output, then this function fails the
    test case by calling assert().

    :param deviceObj : Device object
    :type  deviceObj : object
    :param if_ipv4   : If the route passed is IPv4 or IPv6 route. If
                       the route passed in IPv4, then if_ipv4 should
                       be 'True' otherwise it should be 'False'
    :type  if_ipv4   : boolean
    :param route     : route is of the format "prefix/mask-length"
    :type  route     : string
    :param nexthop   : Nexthop which is of the format "IP/IPv6 address" or
                       "Port number"
    :type nexthop    : string
    :param distance  : Administration distance of the route
    :type distance   : string
    """

    deviceObj = kwargs.get('deviceObj', None)
    if_ipv4 = kwargs.get('if_ipv4', None)
    route = kwargs.get('route', None)
    nexthop = kwargs.get('nexthop', None)
    distance = kwargs.get('distance', None)

    if distance is None:
        LogOutput('info', "\nCheck presence in running-config static route "
                  + route + "and next-hop " + nexthop)
    else:
        LogOutput('info', "\nCheck presence in running-config static route " 
                   + route + "and next-hop " + nexthop + " and distance " 
                   + distance)

    # If the route is a IPv4 route call if_config_in_running_config() with
    # IPV4_STATIC_ROUTE else call if_config_in_running_config() with
    # IPV6_STATIC_ROUTE
    if if_ipv4 is True:
        assert if_config_in_running_config(deviceObj=deviceObj,
                                           configtype=IPV4_STATIC_ROUTE,
                                           route=route,
                                           nexthop=nexthop,
                                           distance=distance)
    else:
        assert if_config_in_running_config(deviceObj=deviceObj,
                                           configtype=IPV6_STATIC_ROUTE,
                                           route=route,
                                           nexthop=nexthop,
                                           distance=distance)


def verify_route_and_nexthop_not_in_show_running_config(**kwargs):
    """
    Library function tests whether a static route with "prefix/mask-length",
    next-hop and administration distance does not exists in the command
    "show running-config". If such a static route configuration exists in the
    output of "show running-config" output, then this function fails the
    test case by calling assert().

    :param deviceObj : Device object
    :type  deviceObj : object
    :param if_ipv4   : If the route passed is IPv4 or IPv6 route. If
                       the route passed in IPv4, then if_ipv4 should
                       be 'True' otherwise it should be 'False'
    :type  if_ipv4   : boolean
    :param route     : route is of the format "prefix/mask-length"
    :type  route     : string
    :param nexthop   : Nexthop which is of the format "IP/IPv6 address" or
                       "Port number"
    :type nexthop    : string
    :param distance  : Administration distance of the route
    :type distance   : string
    """
    deviceObj = kwargs.get('deviceObj', None)
    if_ipv4 = kwargs.get('if_ipv4', None)
    route = kwargs.get('route', None)
    nexthop = kwargs.get('nexthop', None)
    distance = kwargs.get('distance', None)

    if distance is None:
        LogOutput('info', "\nCheck absence in running-config static route "
                  + route + "and next-hop " + nexthop)
    else:
        LogOutput('info', "\nCheck absence in running-config static route "
                  + route + "and next-hop " + nexthop + " and distance "
                  + distance)

    # If the route is a IPv4 route call if_config_in_running_config() with
    # IPV4_STATIC_ROUTE else call if_config_in_running_config() with
    # IPV6_STATIC_ROUTE
    if if_ipv4 is True:
        assert not if_config_in_running_config(deviceObj=deviceObj,
                                               configtype=IPV4_STATIC_ROUTE,
                                               route=route,
                                               nexthop=nexthop,
                                               distance=distance)
    else:
        assert not if_config_in_running_config(deviceObj=deviceObj,
                                               configtype=IPV6_STATIC_ROUTE,
                                               route=route,
                                               nexthop=nexthop,
                                               distance=distance)
