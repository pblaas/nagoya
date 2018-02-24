# nagoya
Next development iteration of my terraformed kubernetes deploy scripts to produce Cloud Linux config files for boostrapping Kubernetes.

This project has a lot of similarities to project kioto but differs on the following:
* nagoya is based on etcd3
* nagoya is based on Cloud Linux Configs instead of CloudConfig files

### Usage:
```
./nagoya.py --help
usage: nagoya.py [-h] [--corepassword COREPASSWORD] [--username USERNAME]
                 [--projectname PROJECTNAME] [--clustername CLUSTERNAME]
                 [--subnetcidr SUBNETCIDR] [--podcidr PODCIDR]
                 [--managers MANAGERS] [--workers WORKERS]
                 [--managerimageflavor MANAGERIMAGEFLAVOR]
                 [--workerimageflavor WORKERIMAGEFLAVOR]
                 [--glanceimagename GLANCEIMAGENAME] [--dnsserver DNSSERVER]
                 [--cloudprovider CLOUDPROVIDER] [--k8sver K8SVER]
                 [--etcdver ETCDVER] [--flannelver FLANNELVER]
                 [--netoverlay NETOVERLAY] [--authmode AUTHMODE]
                 [--alphafeatures ALPHAFEATURES]
                 keypair floatingip1 floatingip2

positional arguments:
  keypair               Keypair ID
  floatingip1           Floatingip 1 for API calls
  floatingip2           Floatingip 2 for public access to cluster

optional arguments:
  -h, --help            show this help message and exit
  --corepassword COREPASSWORD
                        Password to authenticate with core user
  --username USERNAME   Openstack username - (OS_USERNAME environment
                        variable)
  --projectname PROJECTNAME
                        Openstack project Name - (OS_TENANT_NAME environment
                        variable)
  --clustername CLUSTERNAME
                        Clustername - (k8scluster)
  --subnetcidr SUBNETCIDR
                        Private subnet CIDR - (192.168.3.0/24)
  --podcidr PODCIDR     Pod subnet CIDR - (10.244.0.0/16)
  --managers MANAGERS   Number of k8s managers - (3)
  --workers WORKERS     Number of k8s workers - (0)
  --managerimageflavor MANAGERIMAGEFLAVOR
                        Manager image flavor ID - (2004)
  --workerimageflavor WORKERIMAGEFLAVOR
                        Worker image flavor ID - (2008)
  --glanceimagename GLANCEIMAGENAME
                        Glance image name ID - (Container Linux CoreOS (third-
                        party))
  --dnsserver DNSSERVER
                        DNS server - (8.8.8.8)
  --cloudprovider CLOUDPROVIDER
                        Cloud provider support - (openstack)
  --k8sver K8SVER       Hyperkube version - (v1.8.7_coreos.0)
  --etcdver ETCDVER     ETCD version - (3.3.1)
  --flannelver FLANNELVER
                        Flannel image version - (0.10.0)
  --netoverlay NETOVERLAY
                        Network overlay - (flannel)
  --authmode AUTHMODE   Authorization mode - (AlwaysAllow)
  --alphafeatures ALPHAFEATURES
                        enable alpha feature - (false)
```

#### Features
* HA master K8S setup.
* PKI on ETCD cluster.
* PKI on K8S nodes.
* RBAC authorization mode.
* NodeRestriction admission control.
* OpenStack provider for Storage through Cinder plugin.
* Loadbalancing k8s managers through OpenStack (LBAAS).
* Loadbalancing k8s workers (up to first three) through OpenStack (LBAAS) for ingress.
* Flannel network overlay support.
* Calico network overlay support.
* Private network support.
* All managers nodes are part of etcd3 cluster.

#### Caveats
If you are using this script without my managment container (pblaas/openstack-cli) make sure you set the following environment variables:

export OS_TENANT_ID=$OS_PROJECT_ID
export OS_TENANT_NAME=$OS_PROJECT_NAME


