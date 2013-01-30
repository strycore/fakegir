#!/bin/bash

python fakegir.py
cd ~/.cache/fakegir/gi/repository/
for file in $(ls *.py); do
    echo "Checking $file"
    python $file
done
