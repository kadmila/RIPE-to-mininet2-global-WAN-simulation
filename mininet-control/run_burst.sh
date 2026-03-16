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
    
    sudo python3 setup_burst.py --n_peers $N_PEERS --n_churn $N_CHURN --seed $SEED > /dev/null 2>&1
}

run_simulation_all() {
    for i in $(seq $SEED_MIN $SEED_MAX); do
        run_simulation_one_seed $i
    done
}

run_ablation() {
    TARGET=$1
    MIN_INTERVAL=$2
    UNIT_INTERVAL=$3

    cd abyss_test
    ./pkg_load.sh $TARGET
    cd ..
    
    cd abyss_test
    sed -i "s/\(TimerMinInterval  = \)300/\1${MIN_INTERVAL}/" ./abyss_core/and/utils.go
    sed -i "s/\(TimerUnitInterval = \)300/\1${UNIT_INTERVAL}/" ./abyss_core/and/utils.go
    go build -o scenario_run .
    cd ..

    run_simulation_all
    mkdir -p ablation/${TARGET}/t_min_${MIN_INTERVAL}_unit_${UNIT_INTERVAL}/
    cp results/${N_PEERS}/ -r ablation/${TARGET}/t_min_${MIN_INTERVAL}_unit_${UNIT_INTERVAL}/
}

run_main() {
    cd abyss_test
    ./pkg_load.sh dev
    cd ..

    run_simulation_all
    mkdir -p burst/dev/
    cp results/${N_PEERS}/ -r burst/dev/
}

run_naive() {
    cd abyss_test
    ./pkg_load.sh dev-eval-naive
    cd ..

    run_simulation_all
    mkdir -p burst/dev-eval-naive/
    cp results/${N_PEERS}/ -r burst/dev-eval-naive/
}

run_trickle() {
    cd abyss_test
    ./pkg_load.sh dev-eval-trickle
    cd ..

    run_simulation_all
    mkdir -p burst/dev-eval-trickle/
    cp results/${N_PEERS}/ -r burst/dev-eval-trickle/
}

# run_trickle

run_ablation dev-v2 0 300
run_ablation dev-v2 200 300
run_ablation dev-v2 400 300
run_ablation dev-v2 600 300

run_ablation dev-v2 300 100
run_ablation dev-v2 300 300
run_ablation dev-v2 300 500
run_ablation dev-v2 300 700