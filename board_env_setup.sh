#!/bin/bash
sudo -S apt-get update -y << EOF 
orangepi
EOF

# install dependencies
sudo apt-get install -y cmake g++ gcc
sudo apt-get install -y python3-pip python3-dev portaudio19-dev libsndfile1

# install python dependencies
git clone https://Irvingao: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@github.com/Irvingao/takway_base.git
cd takway_base
pip install -v -e .

pip install -r requirements/board_requirements.txt

