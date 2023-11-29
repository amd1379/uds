#!/bin/bash

# just for debian base distributions

cwd=$(pwd)

### get secret
echo "Enter a secret key to increase the security of communication between the bot and the server:"
echo "(secret key must be same for both bot and server!)"
read -p "(Default value: @123%): " secret
if [[ -z "$secret" ]]; then
  secret="@123%"
fi
### add block list
#cd /usr/local/x-ui/bin
#wget https://github.com/bootmortis/iran-hosted-domains/releases/latest/download/iran.dat
#wget https://github.com/v2fly/domain-list-community/releases/latest/download/dlc.dat
###

apt update

apt install python3 -y
apt install pip -y
pip install datetime
pip install flask
pip install waitress

# remove oldFiles

systemctl disable user-detail-server
systemctl stop user-detail-server
rm -rfv /usr/local/user-detail-server
rm -fv /etc/systemd/system/user-detail-server.service

mkdir /usr/local/user-detail-server -v
# mkdir /usr/local/user-detail-server/templates -v
# mkdir /usr/local/user-detail-server/static -v
cd /usr/local/user-detail-server

wget https://raw.githubusercontent.com/ahmady2001/UserDetailServer/master/UserDetailServer.py -O UserDetailServer.py

#### make config.ini
cat << EOF > config.ini
[API]
secret = $secret
EOF
echo "Configuration saved to config.txt"

# cd /usr/local/user-detail-server/templates

# wget https://raw.githubusercontent.com/ahmady2001/UserDetailServer/master/templates/index.html -O index.html

# cd /usr/local/user-detail-server/static

# wget https://raw.githubusercontent.com/ahmady2001/UserDetailServer/master/static/style.min.css -O style.min.css
# wget https://raw.githubusercontent.com/ahmady2001/UserDetailServer/master/static/script.min.js -O script.min.js
# wget https://raw.githubusercontent.com/ahmady2001/UserDetailServer/master/static/chart.min.js -O chart.min.js
# wget https://raw.githubusercontent.com/ahmady2001/UserDetailServer/master/static/Sora-VariableFont_wght.ttf -O Sora-VariableFont_wght.ttf

cd /etc/systemd/system

wget https://raw.githubusercontent.com/ahmady2001/UserDetailServer/master/user-detail-server.service -O user-detail-server.service

systemctl enable user-detail-server
systemctl start user-detail-server

cd $cwd
rm install.sh -v
