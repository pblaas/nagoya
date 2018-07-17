#!/usr/bin/env python2.7
"""Kubernetes cluster generator."""

import argparse
import os
import subprocess
import base64
import crypt
import string
import random
from jinja2 import Environment, FileSystemLoader

__author__ = "Patrick Blaas <patrick@kite4fun.nl>"
__license__ = "GPL v3"
__version__ = "0.3.12"
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
parser.add_argument("keypair", help="Keypair ID")
parser.add_argument("floatingip1", help="Floatingip 1 for API calls")
parser.add_argument("floatingip2", help="Floatingip 2 for public access to cluster")
parser.add_argument("--corepassword", help="Password to authenticate with core user")
parser.add_argument("--username", help="Openstack username - (OS_USERNAME environment variable)", default=os.environ["OS_USERNAME"])
parser.add_argument("--projectname", help="Openstack project Name - (OS_TENANT_NAME environment variable)", default=os.environ["OS_TENANT_NAME"])
parser.add_argument("--clustername", help="Clustername - (k8scluster)", default="k8scluster")
parser.add_argument("--subnetcidr", help="Private subnet CIDR - (192.168.3.0/24)", default="192.168.3.0/24")
parser.add_argument("--podcidr", help="Pod subnet CIDR - (10.244.0.0/16)", default="10.244.0.0/16")
parser.add_argument("--managers", help="Number of k8s managers - (3)", type=int, default=3)
parser.add_argument("--workers", help="Number of k8s workers - (2)", type=int, default=2)
parser.add_argument("--managerimageflavor", help="Manager image flavor ID - (2004)", type=int, default=2004)
parser.add_argument("--workerimageflavor", help="Worker image flavor ID - (2008)", type=int, default=2008)
parser.add_argument("--glanceimagename", help="Glance image name ID - (Container Linux CoreOS (third-party))", default="Container Linux CoreOS (third-party)")
parser.add_argument("--dnsserver", help="DNS server - (8.8.8.8)", default="8.8.8.8")
parser.add_argument("--cloudprovider", help="Cloud provider support - (openstack)", default="openstack")
parser.add_argument("--k8sver", help="Hyperkube version - (v1.10.3_coreos.0)", default="v1.10.3_coreos.0")
parser.add_argument("--etcdver", help="ETCD version - (3.3.1)", default="3.3.1")
parser.add_argument("--flannelver", help="Flannel image version - (0.10.0)", default="0.10.0")
parser.add_argument("--netoverlay", help="Network overlay - (flannel)", default="flannel")
parser.add_argument("--rbac", help="RBAC mode - (false)", default="false")
parser.add_argument("--apidebuglevel", help="Api DebugLevel - (1)", type=int, default=1)
parser.add_argument("--proxymode", help="Proxymode - (iptables)", default="iptables")
parser.add_argument("--alphafeatures", help="enable alpha feature - (false)", default="false")
parser.add_argument("--availabilityzone", help="Availability zone - (AMS-EQ1)", default="AMS-EQ1")
parser.add_argument("--externalnetid", help="External network id - (f9c73cd5-9e7b-4bfd-89eb-c2f4f584c326)", default="f9c73cd5-9e7b-4bfd-89eb-c2f4f584c326")
parser.add_argument("--defaultsecuritygroupid", help="Default Security group id- (c9537380-5f5c-497a-98c3-980b6ba6999e)", default="c9537380-5f5c-497a-98c3-980b6ba6999e")
args = parser.parse_args()

template = TEMPLATE_ENVIRONMENT.get_template('k8s.tf.tmpl')
calico_template = TEMPLATE_ENVIRONMENT.get_template('calico.yaml.tmpl')
cloudconf_template = TEMPLATE_ENVIRONMENT.get_template('k8scloudconf.yaml.tmpl')
kubeconfig_template = TEMPLATE_ENVIRONMENT.get_template('kubeconfig.sh.tmpl')
cloudconfig_template = TEMPLATE_ENVIRONMENT.get_template('cloud.conf.tmpl')
clusterstatus_template = TEMPLATE_ENVIRONMENT.get_template('cluster.status.tmpl')
opensslmanager_template = TEMPLATE_ENVIRONMENT.get_template('./tls/openssl.cnf.tmpl')
opensslworker_template = TEMPLATE_ENVIRONMENT.get_template('./tls/openssl-worker.cnf.tmpl')

try:
    # Create CA certificates

    def createCaCert():
        """Create CA certificates."""
        print("CA")
        subprocess.call(["openssl", "genrsa", "-out", "ca-key.pem", "2048"], cwd='./tls')
        subprocess.call(["openssl", "req", "-x509", "-new", "-nodes", "-key", "ca-key.pem", "-days", "10000", "-out", "ca.pem", "-subj", "/CN=k8s-ca"], cwd='./tls')

        print("etcd CA")
        subprocess.call(["openssl", "genrsa", "-out", "etcd-ca-key.pem", "2048"], cwd='./tls')
        subprocess.call(["openssl", "req", "-x509", "-new", "-nodes", "-key", "etcd-ca-key.pem", "-days", "10000", "-out", "etcd-ca.pem", "-subj", "/CN=etcd-k8s-ca"], cwd='./tls')

        print("front-proxy-client CA")
        subprocess.call(["openssl", "genrsa", "-out", "front-proxy-client-ca-key.pem", "2048"], cwd='./tls')
        subprocess.call(["openssl", "req", "-x509", "-new", "-nodes", "-key", "front-proxy-client-ca-key.pem", "-days", "10000", "-out", "front-proxy-client-ca.pem", "-subj", "/CN=front-proxy-client-ca"], cwd='./tls')

    def createSAcert():
        """Create Service Account certificates."""
        print("ServiceAcccount cert")

        openssltemplate = (opensslworker_template.render(
            ipaddress="127.0.0.1"
        ))

        with open('./tls/openssl.cnf', 'w') as openssl:
            openssl.write(openssltemplate)

        print("Service account K8s")
        subprocess.call(["openssl", "genrsa", "-out", "sa-" + (args.clustername) + "-k8s-key.pem", "2048"], cwd='./tls')
        subprocess.call(["openssl", "req", "-new", "-key", "sa-" + (args.clustername) + "-k8s-key.pem", "-out", "sa-" + (args.clustername) + "-k8s-key.csr", "-subj", "/CN=sa:k8s", "-config", "openssl.cnf"], cwd='./tls')
        subprocess.call(["openssl", "x509", "-req", "-in", "sa-" + (args.clustername) + "-k8s-key.csr", "-CA", "ca.pem", "-CAkey", "ca-key.pem", "-CAcreateserial", "-out", "sa-" + (args.clustername) + "-k8s.pem", "-days", "365", "-extensions", "v3_req", "-extfile", "openssl.cnf"], cwd='./tls')

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
        subprocess.call(["openssl", "req", "-new", "-key", nodeip + "-k8s-node-key.pem", "-out", nodeip + "-k8s-node.csr", "-subj", "/CN=system:node:k8s-" + str(args.clustername) + "-node" + str(nodeoctet) + "/O=system:nodes", "-config", "openssl.cnf"], cwd='./tls')
        subprocess.call(["openssl", "x509", "-req", "-in", nodeip + "-k8s-node.csr", "-CA", "ca.pem", "-CAkey", "ca-key.pem", "-CAcreateserial", "-out", nodeip + "-k8s-node.pem", "-days", "365", "-extensions", "v3_req", "-extfile", "openssl.cnf"], cwd='./tls')

        # ${i}-etcd-worker.pem
        subprocess.call(["openssl", "genrsa", "-out", nodeip + "-etcd-node-key.pem", "2048"], cwd='./tls')
        subprocess.call(["openssl", "req", "-new", "-key", nodeip + "-etcd-node-key.pem", "-out", nodeip + "-etcd-node.csr", "-subj", "/CN=" + nodeip + "-etcd-node", "-config", "openssl.cnf"], cwd='./tls')
        subprocess.call(["openssl", "x509", "-req", "-in", nodeip + "-etcd-node.csr", "-CA", "etcd-ca.pem", "-CAkey", "etcd-ca-key.pem", "-CAcreateserial", "-out", nodeip + "-etcd-node.pem", "-days", "365", "-extensions", "v3_req", "-extfile", "openssl.cnf"], cwd='./tls')

    def createClientCert(user):
        """Create Client certificates."""
        print("client: " + user)
        subprocess.call(["openssl", "genrsa", "-out", user + "-key.pem", "2048"], cwd='./tls')
        subprocess.call(["openssl", "req", "-new", "-key", user + "-key.pem", "-out", user + ".csr", "-subj", "/CN=" + user + "/O=system:masters", "-config", "openssl.cnf"], cwd='./tls')
        subprocess.call(["openssl", "x509", "-req", "-in", user + ".csr", "-CA", "ca.pem", "-CAkey", "ca-key.pem", "-CAcreateserial", "-out", user + ".pem", "-days", "365", "-extensions", "v3_req", "-extfile", "openssl.cnf"], cwd='./tls')

    def createFrontProxyCert():
        """Create FrontProxy-Client certificates."""
        openssltemplate = (opensslworker_template.render(
            ipaddress="127.0.0.1"
        ))

        with open('./tls/openssl.cnf', 'w') as openssl:
            openssl.write(openssltemplate)

        subprocess.call(["openssl", "genrsa", "-out", "front-proxy-client-key.pem", "2048"], cwd='./tls')
        subprocess.call(["openssl", "req", "-new", "-key", "front-proxy-client-key.pem", "-out", "front-proxy-client.csr", "-subj", "/CN=front-proxy-client", "-config", "openssl.cnf"], cwd='./tls')
        subprocess.call(["openssl", "x509", "-req", "-in", "front-proxy-client.csr", "-CA", "front-proxy-client-ca.pem", "-CAkey", "front-proxy-client-ca-key.pem", "-CAcreateserial", "-out", "front-proxy-client.pem", "-days", "365", "-extensions", "v3_req", "-extfile", "openssl.cnf"], cwd='./tls')

    def createCalicoObjects():
        """Create Calico cluster objects."""
        openssltemplate = (opensslworker_template.render(
            ipaddress="127.0.0.1"
        ))

        with open('./tls/openssl.cnf', 'w') as openssl:
            openssl.write(openssltemplate)

        print("Service account calico")
        subprocess.call(["openssl", "genrsa", "-out", "sa-" + (args.clustername) + "-calico-key.pem", "2048"], cwd='./tls')
        subprocess.call(["openssl", "req", "-new", "-key", "sa-" + (args.clustername) + "-calico-key.pem", "-out", "sa-" + (args.clustername) + "-calico-key.csr", "-subj", "/CN=sa:calico", "-config", "openssl.cnf"], cwd='./tls')
        subprocess.call(["openssl", "x509", "-req", "-in", "sa-" + (args.clustername) + "-calico-key.csr", "-CA", "etcd-ca.pem", "-CAkey", "etcd-ca-key.pem", "-CAcreateserial", "-out", "sa-" + (args.clustername) + "-calico.pem", "-days", "365", "-extensions", "v3_req", "-extfile", "openssl.cnf"], cwd='./tls')

        buffer_calicosa = open("./tls/sa-" + str(args.clustername) + "-calico.pem", "rU").read()
        etcdsacalicobase64 = base64.b64encode(buffer_calicosa)
        buffercalicosa = open("./tls/sa-" + str(args.clustername) + "-calico-key.pem", "rU").read()
        etcdsacalicokeybase64 = base64.b64encode(buffercalicosa)

        calicoconfig_template = (calico_template.render(
            etcdendpointsurls=iplist.rstrip(','),
            etcdcabase64=ETCDCAPEM,
            etcdsacalicobase64=etcdsacalicobase64,
            etcdsacalicokeybase64=etcdsacalicokeybase64
        ))

        with open('calico.yaml', 'w') as calico:
            calico.write(calicoconfig_template)

    def configTranspiler(nodeip):
        """Create json file from yaml content."""
        subprocess.call(["./ct", "-files-dir=tls", "-in-file", "node_" + nodeip + ".yaml", "-out-file", "node_" + nodeip + ".json"])

    def generatePassword():
        """Generate a random password."""
        randomsalt = ""
        global password
        global cryptedPass
        password = ""
        choices = string.ascii_uppercase + string.digits + string.ascii_lowercase
        for _ in range(0, 12):
            password += random.choice(choices)
        for _ in range(0, 8):
            randomsalt += random.choice(choices)
        cryptedPass = crypt.crypt(password, '$6$%s$' % randomsalt)

    def generateRandomString():
        """Generate a random String."""
        rndstring = ""
        choices = string.ascii_uppercase + string.digits + string.ascii_lowercase
        for _ in range(0, 10):
            rndstring += random.choice(choices)
        return rndstring

    def returnPublicKey():
        """Retrieve rsa-ssh public key from OpenStack."""
        global rsakey
        rsakey = subprocess.check_output(["openstack", "keypair", "show", "--public-key", args.keypair]).strip()
        return rsakey

    def printClusterInfo():
        """Print cluster info."""
        print("-" * 40 + "\n\nCluster Info:")
        print("Core password:\t" + str(password))
        print("Keypair:\t" + str(rsakey))
        print("k8s version:\t" + str(args.k8sver))
        print("ETCD vers:\t" + str(args.etcdver))
        print("Flannel vers:\t" + str(args.flannelver))
        print("Clustername:\t" + str(args.clustername))
        print("Cluster cidr:\t" + str(args.subnetcidr))
        print("Pod Cidr:\t" + str(args.podcidr))
        print("Managers:\t" + str(args.managers))
        print("Workers:\t" + str(args.workers))
        print("Manager flavor:\t" + str(args.managerimageflavor))
        print("Worker flavor:\t" + str(args.workerimageflavor))
        print("Glance imgname:\t" + str(args.glanceimagename))
        print("VIP1:\t\t" + str(args.floatingip1))
        print("VIP2:\t\t" + str(args.floatingip2))
        print("Dnsserver:\t" + str(args.dnsserver))
        print("Net overlay:\t" + str(args.netoverlay))
        print("RBAC mode:\t" + str(args.rbac))
        print("alphafeatures:\t" + str(args.alphafeatures))
        print("apidebuglevel:\t" + str(args.apidebuglevel))
        print("defaultsecgrp:\t" + str(args.defaultsecuritygroupid))
        print("proxymode:\t" + str(args.proxymode))
        print("-" * 40 + "\n")
        print("To start building the cluster: \tterraform init && terraform plan && terraform apply")
        print("To interact with the cluster: \tsh kubeconfig.sh")

        clusterstatusconfig_template = (clusterstatus_template.render(
            etcdendpointsurls=iplist.rstrip(','),
            password=password,
            k8sver=args.k8sver,
            clustername=args.clustername,
            subnetcidr=args.subnetcidr,
            managers=args.managers,
            workers=args.workers,
            managerimageflavor=args.managerimageflavor,
            workerimageflavor=args.workerimageflavor,
            glanceimagename=args.glanceimagename,
            floatingip1=args.floatingip1,
            floatingip2=args.floatingip2,
            dnsserver=args.dnsserver,
            netoverlay=args.netoverlay,
            rbac=args.rbac,
            cloudprovider=args.cloudprovider,
            podcidr=args.podcidr,
            flannelver=args.flannelver,
            etcdver=args.etcdver,
            keypair=args.keypair,
            rsakey=rsakey,
            cryptedpass=cryptedPass,
            availabilityzone=args.availabilityzone,
            externalnetid=args.externalnetid,
            apidebuglevel=args.apidebuglevel,
            defaultsecuritygroupid=args.defaultsecuritygroupid,
            proxymode=args.proxymode
        ))

        with open('cluster.status', 'w') as k8sstat:
            k8sstat.write(clusterstatusconfig_template)

    if args.managers < 3:
        raise Exception('Managers need to be no less then 3.')

    iplist = ""
    for node in range(10, args.managers + 10):
        apiserver = str("https://" + args.subnetcidr.rsplit('.', 1)[0] + "." + str(node) + ":2379,")
        iplist = iplist + apiserver

    initialclusterlist = ""
    for node in range(10, args.managers + 10):
        apiserver = str("infra" + str(node - 10) + "=https://" + args.subnetcidr.rsplit('.', 1)[0] + "." + str(node) + ":2380,")
        initialclusterlist = initialclusterlist + apiserver

    createCaCert()
    # create ServiceAccount certificate
    createSAcert()
    # create FrontProxy certificate for aggregation API
    createFrontProxyCert()
    # Create core user passowrd
    generatePassword()
    returnPublicKey()
    etcdtoken = generateRandomString()

    # Required for Calico yaml
    base64buff = open('./tls/etcd-ca.pem', 'rU').read()
    ETCDCAPEM = base64.b64encode(base64buff)

    cloudconfig_template = (cloudconfig_template.render(
        authurl=os.environ["OS_AUTH_URL"],
        username=args.username,
        password=os.environ["OS_PASSWORD"],
        region=os.environ["OS_REGION_NAME"],
        projectname=args.projectname,
        tenantid=os.environ["OS_TENANT_ID"],
    ))

    with open('cloud.conf', 'w') as cloudconf:
        cloudconf.write(cloudconfig_template)

    k8stemplate = (template.render(
        username=args.username,
        projectname=args.projectname,
        clustername=args.clustername,
        managers=args.managers,
        workers=args.workers,
        subnetcidr=args.subnetcidr,
        podcidr=args.podcidr,
        keypair=args.keypair,
        workerimageflavor=args.workerimageflavor,
        managerimageflavor=args.managerimageflavor,
        glanceimagename=args.glanceimagename,
        floatingip1=args.floatingip1,
        floatingip2=args.floatingip2,
        availabilityzone=args.availabilityzone,
        externalnetid=args.externalnetid,
        defaultsecuritygroupid=args.defaultsecuritygroupid
    ))

    for node in range(10, args.managers + 10):
        lanip = str(args.subnetcidr.rsplit('.', 1)[0] + "." + str(node))
        nodeyaml = str("node_" + lanip.rstrip(' ') + ".yaml")
        createNodeCert(lanip, "manager")

        manager_template = (cloudconf_template.render(
            cryptedPass=cryptedPass,
            sshkey=rsakey,
            apidebuglevel=args.apidebuglevel,
            managers=args.managers,
            workers=args.workers,
            dnsserver=args.dnsserver,
            etcdendpointsurls=iplist.rstrip(','),
            etcdid=(node - 10),
            etcdtoken=etcdtoken,
            initialclusterlist=initialclusterlist.rstrip(','),
            floatingip1=args.floatingip1,
            k8sver=args.k8sver,
            flannelver=args.flannelver,
            etcdver=args.etcdver,
            netoverlay=args.netoverlay,
            cloudprovider=args.cloudprovider,
            rbac=args.rbac,
            clustername=args.clustername,
            subnetcidr=args.subnetcidr,
            podcidr=args.podcidr,
            ipaddress=lanip,
            ipaddressgw=(args.subnetcidr).rsplit('.', 1)[0] + ".1",
            alphafeatures=args.alphafeatures,
            proxymode=args.proxymode
        ))

        with open(nodeyaml, 'w') as controller:
            controller.write(manager_template)

    for node in range(10 + args.managers, args.managers + args.workers + 10):
        lanip = str(args.subnetcidr.rsplit('.', 1)[0] + "." + str(node))
        nodeyaml = str("node_" + lanip.rstrip(' ') + ".yaml")
        createNodeCert(lanip, "worker")

        worker_template = (cloudconf_template.render(
            isworker=1,
            managers=args.managers,
            workers=args.workers,
            cryptedPass=cryptedPass,
            sshkey=rsakey,
            apidebuglevel=args.apidebuglevel,
            dnsserver=args.dnsserver,
            etcdendpointsurls=iplist.rstrip(','),
            etcdid=(node - 10),
            etcdtoken=etcdtoken,
            initialclusterlist=initialclusterlist.rstrip(','),
            floatingip1=args.floatingip1,
            k8sver=args.k8sver,
            etcdver=args.etcdver,
            flannelver=args.flannelver,
            netoverlay=args.netoverlay,
            cloudprovider=args.cloudprovider,
            rbac=args.rbac,
            clustername=args.clustername,
            subnetcidr=args.subnetcidr,
            podcidr=args.podcidr,
            ipaddress=lanip,
            ipaddressgw=(args.subnetcidr).rsplit('.', 1)[0] + ".1",
            loadbalancer=(args.subnetcidr).rsplit('.', 1)[0] + ".3",
            proxymode=args.proxymode
        ))

        with open(nodeyaml, 'w') as worker:
            worker.write(worker_template)

    for node in range(10, args.managers + args.workers + 10):
        lanip = str(args.subnetcidr.rsplit('.', 1)[0] + "." + str(node))
        configTranspiler(lanip)

    createClientCert("admin")
    createCalicoObjects()

    kubeconfig_template = (kubeconfig_template.render(
        floatingip1=args.floatingip1,
        masterhostip=(args.subnetcidr).rsplit('.', 1)[0] + ".10"
    ))

    with open('kubeconfig.sh', 'w') as kubeconfig:
        kubeconfig.write(kubeconfig_template)

    with open('k8s.tf', 'w') as k8s:
        k8s.write(k8stemplate)

except Exception as e:
    raise
else:
    printClusterInfo()
