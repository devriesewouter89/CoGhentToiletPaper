# CoGhentToiletPaper

## Project

## installation

Start with a **64-bit** raspberry pi OS as Git lfs needs 64 bits

	tip: enable SSH & setup headless wifi via raspberry pi Imager and CTRL+SHIFT+X

Install GIT-lfs:
```bash
wget -c https://github.com/git-lfs/git-lfs/releases/download/v3.2.0/git-lfs-linux-arm64-v3.2.0.tar.gz -O - | tar -xvzf -
cd git-lfs-3.2.0
sudo ./install.sh
```

clone the repo with submodules and lfs:
```bash
git clone --recurse-submodules https://github.com/devriesewouter89/CoGhentToiletPaper/
cd CoGhentToiletPaper
git lfs pull
```

##

in directory dBPathFinder:
copy `.env.template` to `.env` and adapt to your needs.

[//]: # ()
[//]: # (**optional:** Want to run docker containers? install docker:)

[//]: # (```bash)

[//]: # (curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh)

[//]: # (sudo groupadd docker)

[//]: # (sudo usermod -aG docker ${USER})

[//]: # (sudo reboot)

[//]: # (```)

[//]: # ()
[//]: # ()
[//]: # ()
[//]: # ()
[//]: # (### image conversion)

[//]: # ()
[//]: # (multiple approaches:)

[//]: # (1. docker)

[//]: # (2. jupyter notebook)

[//]: # (3. directly via python scripts)

[//]: # ()
[//]: # ()
[//]: # (#### docker )

[//]: # ()
[//]: # (if CUDA cores available:)

[//]: # (```bash)

[//]: # (docker build -f Dockerfile.GPU -t imageconversion .)

[//]: # (```)

[//]: # ()
[//]: # (else )

[//]: # ()
[//]: # (```bash)

[//]: # (docker build -f Dockerfile.CPU -t imageconversion .)

[//]: # (```)

[//]: # ()
[//]: # (to run with the example folders: )

[//]: # (```bash)

[//]: # (docker run --name imgconv --mount type=bind,source="$&#40;pwd&#41;"/input,target=/coghent_input --mount type=bind,source="$&#40;pwd&#41;"/output/lineart,target=/workspace/coghent_vectors --mount type=bind,source="$&#40;pwd&#41;"/output/vectors,target=/workspace/coghent_lineart imageconversion)

[//]: # ()
[//]: # (```)

[//]: # ()
[//]: # (and then to start it:)

[//]: # (```bash)

[//]: # (docker start -a imgconv)

[//]: # (```)

## Nice to haves

### a web ui

perhaps in flutter? to check the state of the statemachine