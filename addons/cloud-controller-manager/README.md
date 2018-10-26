Cloud-controller-manager is replacing the in-tree Openstack intergration.
You can use this to allocate VIPS through the LBAAS loadbalancer to your kubernetes service objects.

To utilize the CCM you need to create a config map from a file which looks like this:

`cloud.conf`
```
[Global]
region=AMS
username=LOGINNAME
password=YOURPASSWORD
auth-url="https://identity.openstack.cloudvps.com/v3"
tenant-name="YOUR-PROJECT-ID"
tenant-id=YOUR-TENANT_ID
domain-name=Default

[LoadBalancer]
subnet-id=PROEJCT-SUBNET-ID-HERE
floating-network-id=FLOATING-NETWORK-ID_HERE

[BlockStorage]
bs-version=v2

[Networking]
public-network-name=net-public
ipv6-support-disabled=false
```

Create a cloud-config configMap like this:
`kubectl -n kube-system create configmap cloud-config --from-file=cloud-config=cloud.conf`

Next install the RBAC elements and the cloud controller manager manifests.

```
kubectl apply -f cloud-controller-manager-role-bindings.yaml
kubectl apply -f cloud-controller-manager-roles.yaml
kubectl apply -f ccm.yaml
```

Ensure the cloud-controller-manager pods are running.
`kubectl -n kube-system get pods`

