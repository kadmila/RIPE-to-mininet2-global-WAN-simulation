mkdir anchors
mkdir bin
mkdir data

sudo apt update
sudo apt upgrade
sudo apt install python3-pip
sudo apt install python3.12-venv

git clone https://github.com/mininet/mininet
cd mininet/

./util/install.sh -a

# test installation (optional)
sudo mn --switch ovsbr --test pingall
cd..

cd source/
