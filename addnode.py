#!/usr/bin/env python2.7
"""Kubernetes cluster generator - addnode."""
__author__ = "Patrick Blaas <patrick@kite4fun.nl>"
__license__ = "GPL v3"
__version__ = "0.0.2"
__status__ = "Active"


import argparse
import os
import subprocess
import base64
from jinja2 import Environment, FileSystemLoader

PATH = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_ENVIRONMENT = Environment(
    autoescape=False,
    loader=FileSystemLoader(os.path.join(PATH, '.')),
    trim_blocks=True)


# Testing if environment variables are available.
if not "OS_USERNAME" in os.environ:
    os.environ["OS_USERNAME"] = "Default"
if not "OS_PASSWORD" in os.environ:
    os.environ["OS_PASSWORD"] = "Default"
if not "OS_TENANT_NAME" in os.environ:
    os.environ["OS_TENANT_NAME"] = "Default"
if not "OS_TENANT_ID" in os.environ:
    os.environ["OS_TENANT_ID"] = "Default"
if not "OS_REGION_NAME" in os.environ:
    os.environ["OS_REGION_NAME"] = "Default"
if not "OS_AUTH_URL" in os.environ:
    os.environ["OS_AUTH_URL"] = "Default"

parser = argparse.ArgumentParser()
parser.add_argument("ipaddress", help="node ip address")
parser.add_argument("--workerimageflavor", help="Worker image flavor ID")
parser.add_argument("--username", help="Openstack username - (OS_USERNAME environment variable)", default=os.environ["OS_USERNAME"])
parser.add_argument("--projectname", help="Openstack project Name - (OS_TENANT_NAME environment variable)", default=os.environ["OS_TENANT_NAME"])
parser.add_argument("--k8sver", help="Hyperkube version")
args = parser.parse_args()

cloudconf_template = TEMPLATE_ENVIRONMENT.get_template('k8scloudconf.yaml.tmpl')
opensslmanager_template = TEMPLATE_ENVIRONMENT.get_template('./tls/openssl.cnf.tmpl')
additional_node_template = TEMPLATE_ENVIRONMENT.get_template('additional_node.tf.tmpl')
opensslworker_template = TEMPLATE_ENVIRONMENT.get_template('./tls/openssl-worker.cnf.tmpl')


try:
    #Create node certificates
    def createNodeCert(nodeip, k8srole):
        """Create Node certificates."""
        print("received: " + nodeip)
        if k8srole == "manager":
            openssltemplate = (opensslmanager_template.render(
                floatingip1=args.floatingip1,
                ipaddress=nodeip,
                loadbalancer=(args.subnetcidr).rsplit('.', 1)[0]+".3"
                ))
        else:
            openssltemplate = (opensslworker_template.render(
                ipaddress=nodeip,
                ))

        with open('./tls/openssl.cnf', 'w') as openssl:
            openssl.write(openssltemplate)

        nodeoctet = nodeip.rsplit('.')[3]
        subprocess.call(["openssl", "genrsa", "-out", nodeip +"-k8s-node-key.pem", "2048"], cwd='./tls')
        subprocess.call(["openssl", "req", "-new", "-key", nodeip +"-k8s-node-key.pem", "-out", nodeip +"-k8s-node.csr", "-subj", "/CN=system:node:k8s-"+str(clustername)+"-node"+str(nodeoctet)+"/O=system:nodes", "-config", "openssl.cnf"], cwd='./tls')
        subprocess.call(["openssl", "x509", "-req", "-in", nodeip +"-k8s-node.csr", "-CA", "ca.pem", "-CAkey", "ca-key.pem", "-CAcreateserial", "-out", nodeip+"-k8s-node.pem", "-days", "365", "-extensions", "v3_req", "-extfile", "openssl.cnf"], cwd='./tls')

        # ${i}-etcd-worker.pem
        subprocess.call(["openssl", "genrsa", "-out", nodeip +"-etcd-node-key.pem", "2048"], cwd='./tls')
        subprocess.call(["openssl", "req", "-new", "-key", nodeip +"-etcd-node-key.pem", "-out", nodeip +"-etcd-node.csr", "-subj", "/CN="+nodeip+"-etcd-node", "-config", "openssl.cnf"], cwd='./tls')
        subprocess.call(["openssl", "x509", "-req", "-in", nodeip +"-etcd-node.csr", "-CA", "etcd-ca.pem", "-CAkey", "etcd-ca-key.pem", "-CAcreateserial", "-out", nodeip+"-etcd-node.pem", "-days", "365", "-extensions", "v3_req", "-extfile", "openssl.cnf"], cwd='./tls')

    def configTranspiler(nodeip):
        """Create json file from yaml content."""
        subprocess.call(["./ct", "-files-dir=tls", "-in-file", "node_"+nodeip+".yaml", "-out-file", "node_"+nodeip+".json", "-pretty"])

    buffer = open('./tls/ca.pem', 'rU').read()
    CAPEM = base64.b64encode(buffer)

    buffer = open('./tls/etcd-ca.pem', 'rU').read()
    ETCDCAPEM = base64.b64encode(buffer)

    buffer = open('cloud.conf', 'rU').read()
    cloudconfbase64 = base64.b64encode(buffer)

    if args.ipaddress != "":
        lanip = str(args.ipaddress)
        nodeyaml = str("node_" + lanip.rstrip(' ') + ".yaml")
        with open('cluster.status', 'r') as clusterstat:
            fh = clusterstat.readlines()
            print(lanip)
            etcdendpointsurls = str(fh[0].split("\t")[1])[:-1]
            etcdtoken = str(fh[1].split("\t")[1])[:-1]
            if args.k8sver is None:
                k8sver = str(fh[2].split("\t")[1])[:-1]
            else:
                k8sver = args.k8sver
            clustername = fh[3].split("\t")[1][:-1]
            subnetcidr = str(fh[4].split("\t")[1])[:-1]
            managers = str(fh[6].split("\t")[1])[:-1]
            workers = str(fh[7].split("\t")[1])[:-1]
            managerimageflavor = str(fh[8].split("\t")[1])[:-1]
            if args.workerimageflavor is None:
                workerimageflavor = str(fh[9].split("\t")[1])[:-1]
            else:
                workerimageflavor = args.workerimageflavor
            floatingip1 = str(fh[10].split("\t")[1])[:-1]
            floatingip2 = str(fh[11].split("\t")[1])[:-1]
            dnsserver = str(fh[12].split("\t")[1])[:-1]
            netoverlay = str(fh[13].split("\t")[1])[:-1]
            authmode = str(fh[14].split("\t")[1])[:-1]
            cloudprovider = str(fh[15].split("\t")[1])[:-1]
            podcidr = str(fh[15].split("\t")[1])[:-1]
            flannelver = str(fh[17].split("\t")[1])[:-1]
            keypair = str(fh[20].split("\t")[1])[:-1]
            etcdver = str(fh[18].split("\t")[1])[:-1]
            cryptedPass = str(fh[21].split("\t")[1])[:-1]
            sshkey = str(fh[19].split("\t")[2])[:-1]

            createNodeCert(lanip, "worker")
            buffer = open("./tls/"+ str(lanip)+ "-k8s-node.pem", 'rU').read()
            k8snodebase64 = base64.b64encode(buffer)
            buffer = open('./tls/'+str(lanip)+"-k8s-node-key.pem", 'rU').read()
            k8snodekeybase64 = base64.b64encode(buffer)
            buffer = open('./tls/'+str(lanip)+"-etcd-node.pem", 'rU').read()
            etcdnodebase64 = base64.b64encode(buffer)
            buffer = open('./tls/'+str(lanip)+"-etcd-node-key.pem", 'rU').read()
            etcdnodekeybase64 = base64.b64encode(buffer)

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
                ipaddressgw=subnetcidr.rsplit('.', 1)[0]+".1",
                loadbalancer=subnetcidr.rsplit('.', 1)[0]+".3",
                discoveryid=etcdtoken,
                cryptedPass=cryptedPass,
                sshkey=sshkey,
                cabase64=CAPEM,
                etcdcabase64=ETCDCAPEM,
                k8snodebase64=k8snodebase64,
                k8snodekeybase64=k8snodekeybase64,
                etcdnodebase64=etcdnodebase64,
                etcdnodekeybase64=etcdnodekeybase64,
                cloudconfbase64=cloudconfbase64,
                ))

            with open(nodeyaml, 'w') as worker:
                worker.write(worker_template)

            additional_node = (additional_node_template.render(
                clustername=clustername,
                ipaddress=lanip,
                workerimageflavor=workerimageflavor,
                keypair=keypair,
                subnetcidr=subnetcidr,
                octet=lanip.rsplit('.', 1)[1]
                ))

            with open("k8s.tf", 'a') as k8stf:
                k8stf.write(additional_node)

    configTranspiler(args.ipaddress)

except Exception as e:
    raise
else:
    print("Done")
