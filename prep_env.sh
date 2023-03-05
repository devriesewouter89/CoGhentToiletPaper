# assuming we're in the CoGhent Git repo
#sudo apt install virtualenv
#virtualenv env
#source env/bin/activate
#pip install -r requirements.txt
sudo apt install graphviz libcairo2-dev pkg-config python3-dev libopencv-* python3-picamera2
sudo raspi-config nonint do_i2c 0 # make sure I2C is enabled on the board
curl -sSL https://install.python-poetry.org | python3 -
poetry install
poetry shell
python -m pip install https://cdn.evilmadscientist.com/dl/ad/public/AxiDraw_API.zip