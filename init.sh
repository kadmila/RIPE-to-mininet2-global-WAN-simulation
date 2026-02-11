sudo apt update
sudo apt upgrade
sudo apt install python3-pip
sudo apt install python3.12-venv

git clone https://github.com/mininet/mininet
sudo apt-get install mininet

# test installation (optional)
sudo mn --switch ovsbr --test pingall

