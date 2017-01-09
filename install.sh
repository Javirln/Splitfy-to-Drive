#!/bin/bash


Download_install () {

    echo "Downloading and installing pip..."

    mkdir $(pwd)/temp
    cd temp
    curl -O https://bootstrap.pypa.io/get-pip.py
    sudo python get-pip.py
    pip install -U pip
    pip install virtualenv
    cd ..
    rm -rf temp/
    $(which virtualenv) env
    source env/bin/activate
    python --version
    pip3 install SIP
    pip3 install PyQt5
    pip3 install -r requirements.txt

    echo "All dependencies have been successfully installed"
}

echo "Checking python version..."

if [ "$(whereis python)" != "" ];
then
    $(python --version)

    Download_install

else
    echo "Python is not installed..."
    echo "Downloading and installing Python..."

    curl -O "https://www.python.org/ftp/python/3.6.0/Python-3.6.0.tar.xz"
    tar -xf Python-3.5.1.tgz
    cd Python-3.5.1
    ./configure
    make
    sudo make install

    Download_install
fi

