#!/usr/bin/env python2.7
"""PKI renweal tool."""

import argparse
import os
import io
import os.path
import sys
import subprocess
import base64
import crypt
import string
import random
from sets import Set
from jinja2 import Environment, FileSystemLoader

__author__ = "Patrick Blaas <patrick@kite4fun.nl>"
__license__ = "GPL v3"
__version__ = "0.0.1"
__status__ = "Active"

PATH = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_ENVIRONMENT = Environment(
    autoescape=False,
    loader=FileSystemLoader(os.path.join(PATH, '.')),
    trim_blocks=True)

remotecrtlist = ["./remote-etcd-ca.pem", "./remote-etcd-client-crt.pem", "./remote-etcd-client-key.pem"]
for x in remotecrtlist:
    if (not os.path.isfile(x)) and (not os.access(x, os.R_OK)):
        print "Either the file(" + x + ") is missing or not readable. Unable to continue."
        sys.exit(1)

with open('cluster.status', 'r') as clusterstat:
    fh = clusterstat.readlines()
    etcdendpointsurls = str(fh[0].split("\t")[1])[:-1]
    k8sver = str(fh[1].split("\t")[1])[:-1]
    clustername = fh[2].split("\t")[1][:-1]
    subnetcidr = str(fh[3].split("\t")[1])[:-1]
    managers = str(fh[5].split("\t")[1])[:-1]
    workers = str(fh[6].split("\t")[1])[:-1]
    managerimageflavor = str(fh[7].split("\t")[1])[:-1]
    workerimageflavor = str(fh[8].split("\t")[1])[:-1]
    floatingip1 = str(fh[9].split("\t")[1])[:-1]
    floatingip2 = str(fh[10].split("\t")[1])[:-1]
    dnsserver = str(fh[11].split("\t")[1])[:-1]
    netoverlay = str(fh[12].split("\t")[1])[:-1]
    authmode = str(fh[13].split("\t")[1])[:-1]
    cloudprovider = str(fh[14].split("\t")[1])[:-1]
    podcidr = str(fh[15].split("\t")[1])[:-1]
    flannelver = str(fh[16].split("\t")[1])[:-1]
    keypair = str(fh[19].split("\t")[1])[:-1]
    etcdver = str(fh[17].split("\t")[1])[:-1]
    cryptedPass = str(fh[20].split("\t")[1])[:-1]
    sshkey = str(fh[18].split("\t")[2])[:-1]
    availabilityzone = str(fh[21].split("\t")[2])[:-1]
    apidebuglevel = str(fh[23].split("\t")[1])[:-1]
    defaultsecuritygroupid = str(fh[24].split("\t")[1])[:-1]
    proxymode = str(fh[25].split("\t")[1])[:-1]
    clusterid = str(fh[26].split("\t")[1])[:-1]
    remoteetcd = str(fh[27].split("\t")[1])[:-1]

    cidr = subnetcidr.split('/')[1]
    net = subnetcidr.strip(".0/" + cidr)
    iplist = subprocess.Popen("ls ./tls | grep " + net, shell=True, stdout=subprocess.PIPE)
    ipset = Set([])
    while True:
        line = iplist.stdout.readline()
        if line != '':
            # os.write(1, line)
            ip = (line.rsplit("-")[:-1][0])
            ipset.add(ip)
        else:
            break
    # print(ipset)
    totalnodes = (len(ipset))
    totalworkers = totalnodes - managers


