# SaltwaterRoom 
SaltwaterRoom is a simple sandbox based on docker. It supports x86_64, MIPS, ARM file format, can identify the behavior of mining, worms, DDos of malware.
## Getting Started
### Prerequisites
* linux system(test on ubuntu 16.04)
* python2.7
* docker and some images
```bash
docker pull ubuntu:latest
docker pull npmccallum/debian-mips:jessie
docker pull ioft/armhf-ubuntu:latest
```
* qemu-user
```bash
apt-get update && apt-get install -y --no-install-recommends qemu-user-static binfmt-support
update-binfmts --enable qemu-arm
update-binfmts --display qemu-arm
update-binfmts --enable qemu-mips
update-binfmts --display qemu-mips
sudo chmod a+x /usr/bin/qemu-*
```
* python requirements
```bash
pip install -r requirements
```
## Running
help information
```bash
python saltwaterroom.py -h
```
example
```bash
python saltwaterroom.py juno
```
The default monitoring time is 30 minutes, you can press ctrl-c to close at any time, the program will automatically delete the container.
![](http://m.qpic.cn/psb?/V11VYTq22xVeJ6/B7vRs7pzHi5IG*kRCHxUZJKzseH3GfDhiy7DnI59R.s!/b/dEkBAAAAAAAA&bo=sgL4AAAAAAADB2o!&rf=viewer_4)
## TodoList
* support for x86
* add data storage
* optimize monitoring performance
