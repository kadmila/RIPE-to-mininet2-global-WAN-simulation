ulimit -n 65535
ulimit -u 65535
sudo sysctl -w fs.file-max=2097152
sudo sysctl -w net.ipv4.ip_local_port_range="1024 65535"

sudo python3 main.py --n_client=14 --server_region=ny --server_bandwidth=2500