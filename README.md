# nagoya
Next development iteration of my terraformed kubernetes deploy scripts to produce Container Linux config files and Terraform files for boostrapping Kubernetes on OpenStack.

This project has a lot of similarities to project kioto but differs on the following:
* nagoya is based on etcd3
* nagoya is based on Container Linux Configs instead of CloudConfig files


### Getting Started

To get started with this nagoya script to deploy a high available kubernetes cluster you can follow the following guide lines:
1. Make sure you have loaded the OpenStack environment variables and can talk with the OpenStack API with tools like openstack and nova. You can also use a docker container for this: docker.io/pblaas/openstack-cli:latest.
2. Clone the git project
  * `git clone https://github.com/pblaas/nagoya`
3. Request two new floating ip adresses,
  * `openstack floating ip create floating`
4. Run the nagoya script. When deploying your first cluster you don't have to use all the available flags. The script will prepare the terraform config file and the Ignition files for CoreOS Container Linux.
  * `./nagoya.py "YOURKEYPAIR_NAME" "FIRSTFLOATINGIP" "SECONDFLOATINGIP" --workers 3`
5. Optional verify the result status information if it matches your desired cluster spec. If not to your liking run the command again with additional or altered flags.
6. Instruct terraform to apply the config on OpenStack.
  * `terraform init && terraform plan && terraform apply`
7. Load the generated kubernetes config
  * `sh kubeconfig.sh`
8. You can run a watch command and see when the cluster will come online. This could take a couple of minutes.
  * `watch kubectl get nodes`

You should now have a fully functional kubernetes cluster which is fully compliant with conformance tests. To test conformance you can use a free available service by Heptio: https://scanner.heptio.com/

### Available usage flags:
```
usage: nagoya.py [-h] [--corepassword COREPASSWORD] [--username USERNAME]
                 [--projectname PROJECTNAME] [--clustername CLUSTERNAME]
                 [--subnetcidr SUBNETCIDR] [--podcidr PODCIDR]
                 [--managers MANAGERS] [--workers WORKERS]
                 [--managerimageflavor MANAGERIMAGEFLAVOR]
                 [--workerimageflavor WORKERIMAGEFLAVOR]
                 [--glanceimagename GLANCEIMAGENAME] [--dnsserver DNSSERVER]
                 [--cloudprovider CLOUDPROVIDER] [--k8sver K8SVER]
                 [--etcdver ETCDVER] [--flannelver FLANNELVER]
                 [--netoverlay NETOVERLAY] [--rbac RBAC]
                 [--apidebuglevel APIDEBUGLEVEL] [--proxymode PROXYMODE]
                 [--alphafeatures ALPHAFEATURES]
                 [--availabilityzone AVAILABILITYZONE]
                 [--externalnetid EXTERNALNETID]
                 [--defaultsecuritygroupid DEFAULTSECURITYGROUPID]
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
  --workers WORKERS     Number of k8s workers - (2)
  --managerimageflavor MANAGERIMAGEFLAVOR
                        Manager image flavor ID - (2004)
  --workerimageflavor WORKERIMAGEFLAVOR
                        Worker image flavor ID - (2008)
  --glanceimagename GLANCEIMAGENAME
                        Glance image name ID - (Container Linux CoreOS (third-party))
  --dnsserver DNSSERVER
                        DNS server - (8.8.8.8)
  --cloudprovider CLOUDPROVIDER
                        Cloud provider support - (openstack)
  --k8sver K8SVER       Hyperkube version - (v1.10.5_coreos.0)
  --etcdver ETCDVER     ETCD version - (3.3.9)
  --flannelver FLANNELVER
                        Flannel image version - (0.10.0)
  --netoverlay NETOVERLAY
                        Network overlay - (flannel)
  --rbac RBAC           RBAC mode - (false)
  --apidebuglevel APIDEBUGLEVEL
                        Api DebugLevel - (1)
  --proxymode PROXYMODE
                        Proxymode - (iptables)
  --alphafeatures ALPHAFEATURES
                        enable alpha feature - (false)
  --availabilityzone AVAILABILITYZONE
                        Availability zone - (AMS-EQ1)
  --externalnetid EXTERNALNETID
                        External network id - (f9c73cd5-9e7b-4bfd-89eb-
                        c2f4f584c326)
  --defaultsecuritygroupid DEFAULTSECURITYGROUPID
                        Default Security group id- (c9537380-5f5c-497a-
                        98c3-980b6ba6999e)
```

#### Features
* HA master K8S setup.
* PKI on etcd cluster.
* PKI on K8S nodes.
* RBAC authorization mode support.
* NodeRestriction admission control.
* OpenStack provider for Storage through Cinder plugin.
* OpenStack provider for automatic loadbalancer creation.
* Loadbalancing k8s masters through OpenStack (LBAAS).
* Loadbalancing k8s workers (up to first three) through OpenStack (LBAAS) for ingress.
* Flannel network overlay support.
* Calico network overlay support.
* IPVS proxymode
* Private network support.
* All master nodes are part of etcd3 cluster.

#### Caveats
If you are using this script without my management docker container (pblaas/openstack-cli) make sure you set the following environment variables:

* export OS_TENANT_ID=$OS_PROJECT_ID
* export OS_TENANT_NAME=$OS_PROJECT_NAME

Make sure you have current version of the openstack CLI tool which is used during the deployment by the Python script.
Your environment may use other defaults if not using the OpenStack platform from CloudVPS.com.
