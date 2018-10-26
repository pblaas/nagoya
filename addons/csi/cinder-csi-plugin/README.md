To use the cinder-csi-plugin you need to update the csi-secret-cinderplugin.yaml with a base64 encoded string of your cloud.conf which looks like this:

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
```

`cat cloud.conf | base64 -w0`

Paste this into `csi-secret-cinderplugin.yaml` and apply all the yamls.

Next you can apply all the yamls.
`kubectl apply -f .`

This will create a storage class called `csi-sc-cinderplugin` and create a 1Gi volume and attach it to an example nginx service though `nginx.yaml`.

Check your claims with
`kubectl get pvc`

You can also verify if the volume was created on OpenStack with:
`cinder list`
