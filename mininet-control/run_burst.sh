# constants
N_PEERS=130
N_CHURN=30
SEED_MIN=0
SEED_MAX=4

# initialization
sudo rm -rf ./results

run_simulation_one_seed() {
    SEED=$1

    echo "Running burst: N_PEERS $N_PEERS N_CHURN $N_CHURN seed $i"

    sudo mn -c > /dev/null 2>&1
    ulimit -n 65535 > /dev/null 2>&1
    ulimit -u 65535 > /dev/null 2>&1
    sudo sysctl -w fs.file-max=2097152 > /dev/null 2>&1
    sudo sysctl -w net.ipv4.ip_local_port_range="1024 65535" > /dev/null 2>&1

    sudo rm -rf ./tmp
    mkdir -p ./tmp/contact
    mkdir -p ./tmp/scenario

    sudo rm -rf ./results/$N_PEERS/$SEED
    mkdir -p ./results/$N_PEERS/$SEED
    
    sudo python3 setup_stability.py --n_peers $N_PEERS --n_churn $N_CHURN --seed $SEED 2>&1
}

run_simulation_all() {
    for i in $(seq $SEED_MIN $SEED_MAX); do
        run_simulation_one_seed $i
    done
}

run_main_ablation() {
    MIN_INTERVAL=$1
    UNIT_INTERVAL=$2
    
    cd abyss_test
    sed -i "s/\(TimerMinInterval  = \)300/\1${MIN_INTERVAL}/" ./abyss_core/and/utils.go
    sed -i "s/\(TimerUnitInterval = \)300/\1${UNIT_INTERVAL}/" ./abyss_core/and/utils.go
    go build -o scenario_run .
    cd ..

    sudo rm -rf ./results

    run_stability_seed_range $N_PEERS 30 0 4
    mkdir ablation/t_min_${MIN_INTERVAL}_unit_${UNIT_INTERVAL}
    cp results/${N_PEERS}/ -r ablation/t_min_${MIN_INTERVAL}_unit_${UNIT_INTERVAL}/
    
    cd abyss_test
    sed -i "s/\(TimerMinInterval  = \)${MIN_INTERVAL}/\1300/" ./abyss_core/and/utils.go
    sed -i "s/\(TimerUnitInterval = \)${UNIT_INTERVAL}/\1300/" ./abyss_core/and/utils.go
    go build -o scenario_run .
    cd ..
}

run_main() {
    cd abyss_test
    ./pkg_load.sh dev
    cd ..

    run_simulation_all()
    mkdir -p burst/dev/
    cp results/${N_PEERS}/ -r burst/dev/
}

run_naive() {
    cd abyss_test
    ./pkg_load.sh dev-eval-naive
    cd ..

    run_simulation_all()
    mkdir -p burst/dev-eval-naive/
    cp results/${N_PEERS}/ -r burst/dev-eval-naive/
}

run_main()