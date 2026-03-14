sudo mn -c

ulimit -n 65535
ulimit -u 65535
sudo sysctl -w fs.file-max=2097152
sudo sysctl -w net.ipv4.ip_local_port_range="1024 65535"

run_stability_experiment() {
    N_PEERS=$1
    N_CHURN=$2
    SEED=$3

    sudo rm -rf ./tmp
    mkdir -p ./tmp/contact
    mkdir -p ./tmp/scenario

    sudo rm -rf ./results/$N_PEERS/$SEED
    mkdir -p ./results/$N_PEERS/$SEED

    sudo python3 setup_stability.py --n_peers $N_PEERS --n_churn $N_CHURN --seed $SEED
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

run_one_unit() {
    MIN_INTERVAL=$1
    UNIT_INTERVAL=$2
    
    cd abyss_test
    sed -i "s/\(TimerMinInterval  = \)100/\1${MIN_INTERVAL}/" ./abyss_core/and/utils.go
    sed -i "s/\(TimerUnitInterval = \)300/\1${UNIT_INTERVAL}/" ./abyss_core/and/utils.go
    go build -o scenario_run .
    cd ..

    sudo rm -rf ./results

    run_stability_seed_range 110 10 0 3
    mkdir ablation/t_min_${MIN_INTERVAL}_unit_${UNIT_INTERVAL}
    cp results/110/ -r ablation/t_min_${MIN_INTERVAL}_unit_${UNIT_INTERVAL}/
    
    cd abyss_test
    sed -i "s/\(TimerMinInterval  = \)${MIN_INTERVAL}/\1100/" ./abyss_core/and/utils.go
    sed -i "s/\(TimerUnitInterval = \)${UNIT_INTERVAL}/\1300/" ./abyss_core/and/utils.go
    go build -o scenario_run .
    cd ..
}

rm -rf results
mkdir results

# run_one_unit 100 100
# run_one_unit 100 200
# run_one_unit 100 300
# run_one_unit 100 400

run_one_unit 50 400
run_one_unit 100 400
run_one_unit 200 400
run_one_unit 400 400

#run_stability_experiment 101 1 0