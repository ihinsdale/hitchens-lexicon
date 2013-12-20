#!/bin/bash
# Simple setup.sh for configuring Ubuntu 12.04 LTS Azure instance

sudo apt-get update
sudo apt-get install screen
sudo apt-get install unzip

# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Install Python dependencies
sudo apt-get install python-setuptools
sudo apt-get install python-pip
sudo apt-get install python-dev

sudo apt-get install python-psycopg2
sudo apt-get install libxml2-dev libxslt-dev
sudo pip install lxml
sudo pip install cssselect

sudo pip install -U numpy
sudo pip install -U pyyaml nltk

# Install the Punkt sentence tokenizer for nltk
python

#import nltk
#nltk.download()
#d
#punkt
#exit()

# Install git
sudo apt-get install -y git

# Clone hitchens-lexicon repo
git clone https://github.com/ihinsdale/hitchens-lexicon.git