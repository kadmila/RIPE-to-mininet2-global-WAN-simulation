#!/bin/bash

# Extract city names from JSON and process each one
jq -r '.[].city' ./info/largest-cities-by-population-2026.json | while read -r city; do
    # Replace spaces with %20
    city_encoded="${city// /%20}"
    
    # Execute the curl command
    #echo $city_encoded
    curl -o "./anchors/${city}.anchors" "https://atlas.ripe.net/api/v2/anchors?search=${city_encoded}"
done

