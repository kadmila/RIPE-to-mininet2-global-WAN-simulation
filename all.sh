#!/bin/bash
gcc -o ./bin/extract -O3 ./utility/extract.c
gcc -o ./bin/ext-reader ./utility/ext-reader.c

get_files() {
    local month=$1
    local day=$2
    
    for ((i=10000; i<=10000; i+=100)); do
        local time="${i:1:4}"
        local date="2026-${month}-${day}"
        local fileName="ping-${date}T${time}.bz2"
        
        echo $fileName
        curl "https://data-store.ripe.net/datasets/atlas-daily-dumps/${date}/${fileName}" | bzip2 -dc | ./bin/extract "./data/extract-ping-${date}T${time}"
    done
}

# Call the function with parameters
get_files "01" "06"