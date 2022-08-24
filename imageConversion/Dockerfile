FROM pytorch/pytorch:1.6.0-cuda10.1-cudnn7-runtime

RUN apt update && apt install -y wget && apt install -y build-essential python-dev libagg-dev libpotrace-dev pkg-config potrace imagemagick
RUN wget https://www.dropbox.com/s/04suaimdpru76h3/ArtLine_920.pkl

COPY . /workspace/coghent
RUN pip install -r /workspace/coghent/requirements.txt
#VOLUME .:/workspace/coghent_results
ENTRYPOINT ["python"]
CMD ["/workspace/coghent/artlineflow.py"]