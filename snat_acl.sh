for i in `openstack port list|grep 100.64|awk '{ print $2 }'`; do  openstack port set --security-group allow-all $i; done
