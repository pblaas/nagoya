clean:
	rm -f *.txt config.env *.tf kubeconfig.sh cloud.conf *.yaml cluster.status
	rm -rvf cloudinit_generator
	rm -f tls/*.pem tls/*.cnf tls/*.csr tls/*.srl *.json
