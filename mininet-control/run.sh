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

run_stability_experiment() {
    N_PEERS=$1
    N_CHURN=$2
    SEED=$3

    sudo rm -rf ./tmp
    mkdir -p ./tmp/contact
    mkdir -p ./tmp/scenario

    sudo rm -rf ./results/$N_PEERS/$SEED
    mkdir -p ./results/$N_PEERS/$SEED

    sudo python3 setup_stability.py --n_peers $N_PEERS --n_churn $N_CHURN --seed $SEED >> dump.log 2>&1
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

run_stability_seed_range() {
    N_PEERS=$1
    N_CHURN=$2
    SEED_MIN=$3
    SEED_MAX=$4

    for i in $(seq $SEED_MIN $SEED_MAX); do
        echo "Running experiment (seed:$i)"
        run_stability_experiment $N_PEERS $N_CHURN $i
    done
}

# run_seed_range 300 0 9
# run_experiment 10 0

run_stability_experiment 101 1 0