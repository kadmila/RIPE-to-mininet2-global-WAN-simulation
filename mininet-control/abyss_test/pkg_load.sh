rm -rf ./abyss_core
git clone -b $1 https://github.com/kadmila/Abyss-Browser.git
cp -r ./Abyss-Browser/abyss_core ./abyss_core
rm -rf ./Abyss-Browser
rm -rf ./abyss_core/windll
go build -o scenario_run .