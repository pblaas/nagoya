#!/usr/bin/env python2.7
"""Kubernetes cluster generator - addnode."""

import argparse
import os
import subprocess
import base64
from jinja2 import Environment, FileSystemLoader

__author__ = "Patrick Blaas <patrick@kite4fun.nl>"
__license__ = "GPL v3"
__version__ = "0.0.7"
__status__ = "Active"

PATH = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_ENVIRONMENT = Environment(
    autoescape=False,
    loader=FileSystemLoader(os.path.join(PATH, '.')),
    trim_blocks=True)

# Testing if environment variables are available.
if "OS_USERNAME" not in os.environ:
    os.environ["OS_USERNAME"] = "Default"
if "OS_PASSWORD" not in os.environ:
    os.environ["OS_PASSWORD"] = "Default"
if "OS_TENANT_NAME" not in os.environ:
    os.environ["OS_TENANT_NAME"] = "Default"
if "OS_TENANT_ID" not in os.environ:
    os.environ["OS_TENANT_ID"] = "Default"
if "OS_REGION_NAME" not in os.environ:
    os.environ["OS_REGION_NAME"] = "Default"
if "OS_AUTH_URL" not in os.environ:
    os.environ["OS_AUTH_URL"] = "Default"

parser = argparse.ArgumentParser()
parser.add_argument("ipaddress", help="node ip address")
parser.add_argument("--workerimageflavor", help="Worker image flavor ID")
parser.add_argument("--glanceimagename", help="Glance image name ID - (Container Linux CoreOS (third-party))", default="Container Linux CoreOS (third-party)")
parser.add_argument("--username", help="Openstack username - (OS_USERNAME environment variable)", default=os.environ["OS_USERNAME"])
parser.add_argument("--projectname", help="Openstack project Name - (OS_TENANT_NAME environment variable)", default=os.environ["OS_TENANT_NAME"])
parser.add_argument("--k8sver", help="Hyperkube version")
args = parser.parse_args()

cloudconf_template = TEMPLATE_ENVIRONMENT.get_template('k8scloudconf.yaml.tmpl')
opensslmanager_template = TEMPLATE_ENVIRONMENT.get_template('./tls/openssl.cnf.tmpl')
additional_node_template = TEMPLATE_ENVIRONMENT.get_template('additional_node.tf.tmpl')
opensslworker_template = TEMPLATE_ENVIRONMENT.get_template('./tls/openssl-worker.cnf.tmpl')

try:
    # Create node certificates
    def createNodeCert(nodeip, k8srole):
        """Create Node certificates."""
        print("received: " + nodeip)
        if k8srole == "manager":
            openssltemplate = (opensslmanager_template.render(
                floatingip1=args.floatingip1,
                ipaddress=nodeip,
                loadbalancer=(args.subnetcidr).rsplit('.', 1)[0] + ".3"
            ))
        else:
            openssltemplate = (opensslworker_template.render(
                ipaddress=nodeip,
            ))

        with open('./tls/openssl.cnf', 'w') as openssl:
            openssl.write(openssltemplate)

        nodeoctet = nodeip.rsplit('.')[3]
        subprocess.call(["openssl", "genrsa", "-out", nodeip + "-k8s-node-key.pem", "2048"], cwd='./tls')
        subprocess.call(["openssl", "req", "-new", "-key", nodeip + "-k8s-node-key.pem", "-out", nodeip + "-k8s-node.csr", "-subj", "/CN=system:node:k8s-" + str(clustername) + "-node" + str(nodeoctet) + "/O=system:nodes", "-config", "openssl.cnf"], cwd='./tls')
        subprocess.call(["openssl", "x509", "-req", "-in", nodeip + "-k8s-node.csr", "-CA", "ca.pem", "-CAkey", "ca-key.pem", "-CAcreateserial", "-out", nodeip + "-k8s-node.pem", "-days", "365", "-extensions", "v3_req", "-extfile", "openssl.cnf"], cwd='./tls')

        # ${i}-etcd-worker.pem
        subprocess.call(["openssl", "genrsa", "-out", nodeip + "-etcd-node-key.pem", "2048"], cwd='./tls')
        subprocess.call(["openssl", "req", "-new", "-key", nodeip + "-etcd-node-key.pem", "-out", nodeip + "-etcd-node.csr", "-subj", "/CN=" + nodeip + "-etcd-node", "-config", "openssl.cnf"], cwd='./tls')
        subprocess.call(["openssl", "x509", "-req", "-in", nodeip + "-etcd-node.csr", "-CA", "etcd-ca.pem", "-CAkey", "etcd-ca-key.pem", "-CAcreateserial", "-out", nodeip + "-etcd-node.pem", "-days", "365", "-extensions", "v3_req", "-extfile", "openssl.cnf"], cwd='./tls')

    def configTranspiler(nodeip):
        """Create json file from yaml content."""
        subprocess.call(["./ct", "-files-dir=tls", "-in-file", "node_" + nodeip + ".yaml", "-out-file", "node_" + nodeip + ".json", "-pretty"])

    base64buffer = open('./tls/etcd-ca.pem', 'rU').read()
    ETCDCAPEM = base64.b64encode(base64buffer)

    if args.ipaddress != "":
        lanip = str(args.ipaddress)
        nodeyaml = str("node_" + lanip.rstrip(' ') + ".yaml")
        with open('cluster.status', 'r') as clusterstat:
            fh = clusterstat.readlines()
            print lanip
            etcdendpointsurls = str(fh[0].split("\t")[1])[:-1]
            if args.k8sver is None:
                k8sver = str(fh[1].split("\t")[1])[:-1]
            else:
                k8sver = args.k8sver
            clustername = fh[2].split("\t")[1][:-1]
            subnetcidr = str(fh[3].split("\t")[1])[:-1]
            managers = str(fh[5].split("\t")[1])[:-1]
            workers = str(fh[6].split("\t")[1])[:-1]
            managerimageflavor = str(fh[7].split("\t")[1])[:-1]
            if args.workerimageflavor is None:
                workerimageflavor = str(fh[8].split("\t")[1])[:-1]
            else:
                workerimageflavor = args.workerimageflavor
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

            createNodeCert(lanip, "worker")
            worker_template = (cloudconf_template.render(
                isworker=1,
                workers=workers,
                dnsserver=dnsserver,
                etcdendpointsurls=etcdendpointsurls,
                floatingip1=floatingip1,
                k8sver=k8sver,
                flannelver=flannelver,
                etcdver=etcdver,
                netoverlay=netoverlay,
                cloudprovider=cloudprovider,
                authmode=authmode,
                clustername=clustername,
                subnetcidr=subnetcidr,
                cidr=podcidr,
                ipaddress=lanip,
                ipaddressgw=subnetcidr.rsplit('.', 1)[0] + ".1",
                loadbalancer=subnetcidr.rsplit('.', 1)[0] + ".3",
                cryptedPass=cryptedPass,
                sshkey=sshkey,
                apidebuglevel=apidebuglevel
            ))

            with open(nodeyaml, 'w') as worker:
                worker.write(worker_template)

            additional_node = (additional_node_template.render(
                clustername=clustername,
                ipaddress=lanip,
                workerimageflavor=workerimageflavor,
                glanceimagename=args.glanceimagename,
                keypair=keypair,
                subnetcidr=subnetcidr,
                octet=lanip.rsplit('.', 1)[1],
                availabilityzone=availabilityzone,
                defaultsecuritygroupid=defaultsecuritygroupid
            ))

            with open("k8s.tf", 'a') as k8stf:
                k8stf.write(additional_node)

    configTranspiler(args.ipaddress)

except Exception as e:
    raise
else:
    print("Done")
