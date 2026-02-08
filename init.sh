mkdir anchors
mkdir bin
mkdir data

apt update
apt upgrade
apt install python3-pip
apt install python3.12-venv

cd utility/anchors-by-city
python3 -m venv .venv
source ./.venv/bin/activate


deactivate