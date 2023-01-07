# assuming we're in the CoGhent Git repo
sudo apt install virtualenv
virtualenv env
source env/bin/activate
pip install -r requirements.txt
sudo apt install graphviz
sudo raspi-config nonint do_i2c 0 # make sure I2C is enabled on the board