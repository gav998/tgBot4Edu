#!/bin/bashs
systemctl stop tgBot4Edu;
rm /etc/systemd/system/tgBot4Edu;
systemctl disable tgBot4Edu;
systemctl daemon-reload;
systemctl reset-failed;


