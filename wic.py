#!/usr/bin/env python

import os
import sys
import json
import subprocess

import googlemaps
from geoip import geolite2


CONFIG_PATH = '{0}/google-dev-api.cfg'.format(os.getenv("HOME"))

with open(CONFIG_PATH) as config_file:
    cfg = json.load(config_file)["Google Developer API"]


def _format_json(dictionary):
    return json.dumps(dictionary, indent=4, sort_keys=True)

def convert_ip_to_coordinates(ip):
    if geolite2.lookup(ip) is None:
        return "Can't locate IP"
    else:
        return geolite2.lookup(ip)

def break_dict(dictionary, index):
    try:
        return dictionary[0]['address_components'][index]['long_name']
    except IndexError:
        return "Out of scope"

def convert_coordinates_to_address(ip, depth):
    # try:
    match = convert_ip_to_coordinates(ip)
    # except AttributeError:"
        # return "Address Can't be located"
    gmaps = googlemaps.Client(key=cfg["Dev API"])

    locations = []
    depth = int(depth)
    for scale in range(8, 0, -1):
        try:
            fetch_location = break_dict(gmaps.reverse_geocode(match.location), scale)
            if fetch_location != "Out of scope":
                if fetch_location.isdigit():
                    continue
                else:
                    locations.append(fetch_location)
            else:
                scale -= 1
        except AttributeError:
            return "Address Can't be located"
    locations = locations[:depth]
    return ("%s, " * len(locations) % tuple(locations))[:-2]

def read_netstat(geo=False):
    active_connections = subprocess.Popen(('netstat', '-atn'), stdout=subprocess.PIPE)
    active_connections_output = subprocess.check_output(('grep', 'ESTABLISHED\|CLOSE_WAIT'), stdin=active_connections.stdout)
    tcp_connections_cut = active_connections_output.split('\n')
    hosts_and_ports = {}
    list_of_hosts = []
    list_of_ips = []
    list_of_ports = []
    for line in tcp_connections_cut:
        if "tcp4" in line:
            single_line = line.split()
            forgien_ip_and_port = single_line[4]
            forgien_ip = str.join('.', (forgien_ip_and_port.split('.')[:4]))
            list_of_ips.append(forgien_ip)
            forgien_port = forgien_ip_and_port.split('.')[4:][0]
            list_of_ports.append(forgien_port)
            hosts_and_ports = dict(zip(list_of_ips, list_of_ports))
    for key, value in hosts_and_ports.iteritems():
        for key in list_of_ips:
            host_dict = {}
            # host_ports = []
            host_dict["Host"] = key
            host_dict["Connections"] = list_of_ips.count(key)
            if not any(host_dict['Host'] == key for host_dict in list_of_hosts):
                list_of_hosts.append(host_dict)
                if geo:
                    host_dict["Geo Location"] = convert_coordinates_to_address(key, 2)
            # host_dict["Ports"] = host_ports
    print _format_json(sorted(list_of_hosts, key=lambda k: k['Connections'], reverse=True))


if __name__ == "__main__":
    read_netstat(geo=True)
    # try:
    #     if int(sys.argv[2]) > 7:
    #         print "Can't zoom in that close..."
    #         sys.argv[2] = 6
    # except IndexError as error:
    #     sys.argv.append(2)
    # print convert_coordinates_to_address(sys.argv[1], sys.argv[2])