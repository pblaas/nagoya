kubectl -n kube-system create configmap metricsconfig \
  --from-file=sa-k8s.pem=../../tls/sa-calico-k8s.pem \
  --from-file=sa-k8s-key.pem=../../tls/sa-calico-k8s-key.pem \
  --from-file=kubeconfig=kubeconfig
