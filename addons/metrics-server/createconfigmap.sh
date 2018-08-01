#!/bin/bash
if [ $1 ]; then
kubectl -n kube-system create configmap metricsconfig \
  --from-file=sa-k8s.pem=../../tls/sa-$1-k8s.pem \
  --from-file=sa-k8s-key.pem=../../tls/sa-$1-k8s-key.pem \
  --from-file=kubeconfig=kubeconfig
else
echo Syntax $0 createconfigmap.sh clustername
fi