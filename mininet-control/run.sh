sudo mn -c

ulimit -n 65535
ulimit -u 65535
sudo sysctl -w fs.file-max=2097152
sudo sysctl -w net.ipv4.ip_local_port_range="1024 65535"

run_experiment() {
    N_PEERS=$1
    SEED=$2

    sudo rm -rf ./tmp
    mkdir -p ./tmp/contact
    mkdir -p ./tmp/scenario

    sudo rm -rf ./results/$N_PEERS/$SEED
    mkdir -p ./results/$N_PEERS/$SEED

    sudo python3 setup.py --n_peers $N_PEERS --seed $SEED >> dump.log 2>&1
}

run_seed_range() {
    N_PEERS=$1
    SEED_MIN=$2
    SEED_MAX=$3

    for i in $(seq $SEED_MIN $SEED_MAX); do
        echo "Running experiment (seed:$i)"
        run_experiment $N_PEERS $i
    done
}

run_seed_range 300 1 9
#run_experiment 300 0