# nagoya
Next development iteration of my terraformed kubernetes deploy scripts to produce Container Linux config files and Terraform files for boostrapping Kubernetes on OpenStack.

This project has a lot of similarities to project kioto but differs on the following:
* nagoya is based on etcd3
* nagoya is based on Container Linux Configs instead of CloudConfig files


### Getting Started

To get started with this nagoya script to deploy a high available kubernetes cluster you can follow the following guide lines:
* Make sure you have loaded the OpenStack environment variables and can talk with the OpenStack API with tools like openstack and nova. You can also use a docker container for this: docker.io/pblaas/openstack-cli:latest.
* Request two new floating ip adresses,
** `openstack floating ip create floating`
* Run the nagoya script. When deploying your first cluster you don't have to use all the available flags. The script will prepare the terraform config file and the Ignition files for CoreOS Container Linux.
** `./nagoya.py "YOURKEYPAIR_NAME" "FIRSTFLOATINGIP" "SECONDFLOATINGIP" --workers 3`
* Optional verify the result status information if it matches your desired cluster spec. If not to your liking run the command again with additional or altered flags.
* Instruct terraform to apply the config on OpenStack. You should add this as a onliner to make sure the snat permissions are properly set and the OS has connectivity to the internet and bootstrap properly.
** `terraform init && terraform plan && terraform apply && sh snat_acl.sh`
* Load the generated kubernetes config
** `sh kubeconfig.sh`
* You can run a watch comment and see when the cluster will come online. This could take a couple of minutes.
** `watch kubectl get nodes`

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
                 [--apidebuglevel APIDEBUGLEVEL]
                 [--alphafeatures ALPHAFEATURES]
                 [--availabilityzone AVAILABILITYZONE]
                 [--externalnetid EXTERNALNETID]
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
                        Glance image name ID - (Container Linux CoreOS (third-party))
  --dnsserver DNSSERVER
                        DNS server - (8.8.8.8)
  --cloudprovider CLOUDPROVIDER
                        Cloud provider support - (openstack)
  --k8sver K8SVER       Hyperkube version - (v1.9.6_coreos.0)
  --etcdver ETCDVER     ETCD version - (3.3.1)
  --flannelver FLANNELVER
                        Flannel image version - (0.10.0)
  --netoverlay NETOVERLAY
                        Network overlay - (flannel)
  --rbac RBAC           RBAC mode - (false)
  --apidebuglevel APIDEBUGLEVEL
                        Api DebugLevel - (1)
  --alphafeatures ALPHAFEATURES
                        enable alpha feature - (false)
  --availabilityzone AVAILABILITYZONE
                        Availability zone - (AMS-EQ1)
  --externalnetid EXTERNALNETID
                        External network id - (f9c73cd5-9e7b-4bfd-89eb-
                        c2f4f584c326)
```

#### Features
* HA manager K8S setup.
* PKI on etcd cluster.
* PKI on K8S nodes.
* RBAC authorization mode support.
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

* export OS_TENANT_ID=$OS_PROJECT_ID
* export OS_TENANT_NAME=$OS_PROJECT_NAME

Make sure you have current version of the openstack CLI tool which is used during the deployment by the Python script.

You're environment may use other defaults. Please let me know if you need to change anything to make this work on your end, not being on cloudvps.com so I can update the scripts and define this in provided params.

