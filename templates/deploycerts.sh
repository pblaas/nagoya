#!/bin/bash

#example usage
#/home/core/deploycerts.sh 192.168.3.10 2doJPTFgnYMy k8scluster https://83.96.176.30:2379 deploy

if [ ! $5 ]; then
  echo Invalid syntax.
  exit 1 
fi

nodeip=$1
clusterid=$2
clustername=$3
remoteetcd=$4
action=$5

declare -a pkilist
pkilist=($nodeip"-k8s-kube-cm.pem"
         $nodeip"-k8s-kube-cm-key.pem"
         $nodeip"-k8s-kube-proxy-key.pem"
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
         "front-proxy-client-ca-key.pem"
         )
for i in "${pkilist[@]}"; do 
  ETCDCTL_API=3  /bin/etcdctl --endpoints=$remoteetcd --cacert=/etc/kubernetes/ssl/remote-etcd-ca.pem --cert=/etc/kubernetes/ssl/remote-etcd-client-crt.pem --key=/etc/kubernetes/ssl/remote-etcd-client-key.pem \
  --print-value-only=true get ${clusterid}_${i} > /etc/kubernetes/ssl/$i
done

