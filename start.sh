#!/bin/bash

if [ -e requirements.txt ]; then
  pip3 install -req requirements.txt
fi

python src/run.py
