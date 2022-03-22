sudo apt-get install libcblas-dev;
python3 -m pip install -r requirements.txt;
chmod +x ./main.py;
sudo cp ./tgBot4Edu.service /etc/systemd/system/tgBot4Edu.service;
sudo systemctl daemon-reload;
sudo systemctl enable tgBot4Edu.service;
sudo systemctl start tgBot4Edu.service;
sudo systemctl status tgBot4Edu;