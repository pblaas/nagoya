#!/bin/bash

#example usage
#/home/core/deploycerts.sh 192.168.3.10 2doJPTFgnYMy k8scluster https://83.96.176.30:2379 deploy master

if [ ! $5 ]; then
  echo Invalid syntax.
  exit 1 
fi

nodeip=$1
clusterid=$2
clustername=$3
remoteetcd=$4
action=$5
role=$6

declare -a pkilist

if [ "${role}" == "master"]; then
  pkilist=($nodeip"-etcd-node-key.pem"
           $nodeip"-etcd-node.pem"
           $nodeip"-k8s-kube-cm.pem"
           $nodeip"-k8s-kube-cm-key.pem"
           $nodeip"-k8s-kube-proxy-key.pem"
           $nodeip"-k8s-kube-proxy.pem"
           $nodeip"-k8s-kube-scheduler-key.pem"
           $nodeip"-k8s-kube-scheduler.pem"
           $nodeip"-k8s-kubelet-client-key.pem"
           $nodeip"-k8s-kubelet-client.pem"
           $nodeip"-k8s-node-key.pem"
           $nodeip"-k8s-node.pem"
           "sa-"$clustername"-k8s-key.pem"
           "sa-"$clustername"-k8s.pem"
           "front-proxy-client.pem"
           "front-proxy-client-key.pem"
           "front-proxy-client-ca.pem"
           "ca.pem"
           "etcd-ca.pem"
          )
else
  pkilist=($nodeip"-etcd-node-key.pem"
           $nodeip"-etcd-node.pem"
           $nodeip"-k8s-kube-proxy-key.pem"
           $nodeip"-k8s-kube-proxy.pem"
           $nodeip"-k8s-node-key.pem"
           $nodeip"-k8s-node.pem"
           "ca.pem"
           "etcd-ca.pem"
          )
fi

for i in "${pkilist[@]}"; do
  #check if key is available on the etcd datastore. Only overwrite with new value if we can find it.
  testkey=$(ETCDCTL_API=3 /bin/etcdctl --endpoints=${remoteetcd} --cacert=/etc/kubernetes/ssl/remote-etcd-ca.pem --cert=/etc/kubernetes/ssl/remote-etcd-client-crt.pem --key=/etc/kubernetes/ssl/remote-etcd-client-key.pem get --keys-only ${clusterid}_${i})
  #echo testkey: $testkey
  if [ "${testkey}" == "${clusterid}_${i}" ]; then
    ETCDCTL_API=3  /bin/etcdctl --endpoints=${remoteetcd} --cacert=/etc/kubernetes/ssl/remote-etcd-ca.pem --cert=/etc/kubernetes/ssl/remote-etcd-client-crt.pem --key=/etc/kubernetes/ssl/remote-etcd-client-key.pem    --print-value-only=true get ${clusterid}_${i} > /etc/kubernetes/ssl/$i
    if [[ "${testkey}" =~ "etcd" ]]; then
      ETCDCTL_API=3  /bin/etcdctl --endpoints=${remoteetcd} --cacert=/etc/kubernetes/ssl/remote-etcd-ca.pem --cert=/etc/kubernetes/ssl/remote-etcd-client-crt.pem --key=/etc/kubernetes/ssl/remote-etcd-client-key.pem    --print-value-only=true get ${clusterid}_${i} > /etc/ssl/certs/$i
    fi
  fi

done

