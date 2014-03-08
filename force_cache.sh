#!/bin/bash

JEDI_PATH=$HOME/.vim/bundle/YouCompleteMe/third_party/jedi

#python fakegir.py
rm -rf $HOME/.cache/jedi

pkgs=""
echo '#/bin/env python' >/tmp/fakeprg.py
for f in ~/.cache/fakegir/gi/repository/*.py; do
    pkgname=`basename $f|cut -d . -f 1`
    pkgs="$pkgs $pkgname"
    echo "from gi.repository import $pkgname" >> /tmp/fakeprg.py
done


for pkgname in $pkgs; do
    echo Forcing cache for $pkgname
    cp /tmp/fakeprg.py /tmp/${pkgname}-fakeprg.py
    compl="w = ${pkgname}."
    echo "$compl"  >> /tmp/${pkgname}-fakeprg.py
    fakeprg_lines=`wc -l /tmp/${pkgname}-fakeprg.py| cut -d ' ' -f 1`
    compl_col=${#compl}

    export PYTHONPATH=$HOME/.cache/fakegir
    pushd $JEDI_PATH
    $JEDI_PATH/sith.py -f run completions /tmp/${pkgname}-fakeprg.py $fakeprg_lines $compl_col
done
