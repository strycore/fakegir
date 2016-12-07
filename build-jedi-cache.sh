#!/bin/bash

PYTHON_EXECUTABLE=python

TEMPDIR=

_help() {
    cat <<EOF
Usage: $0 [options...]

Options:
    -3      Use python3 instead of python as a Python interpreter
    -p INTERPRETER
            Specify custom Python interpreter path
    -h      Show this help message
    -k      Keep (do not remove) temporary files on exit
EOF
}

_clean_up_tempdir() {
    if [ "$TEMPDIR" ]; then
        [ ! -d $TEMPDIR ] || rm -r $TEMPDIR \
            || echo "Cannot remove temporary directory: $TEMPDIR" >&2
    fi
}

_do_clean_up_tempdir=true

while getopts '3p:hk' arg; do
    case "$arg" in
        3) PYTHON_EXECUTABLE=python3;;
        p) PYTHON_EXECUTABLE="$OPTARG";;
        h) _help; exit 0;;
        k) _do_clean_up_tempdir=false;;
        *) _help >&2; exit 127;;
    esac
done

$_do_clean_up_tempdir && trap _clean_up_tempdir 0

shift $(( $OPTIND - 1 ))

# if $PYTHON_EXECUTABLE does not contain slashes,
# then use /usr/bin/env in shebang line
# otherwise, try getting the absolute path and use it instead
if [ "$(expr "$PYTHON_EXECUTABLE" : '.*/')" -eq 0 ]; then
    # also, find the real 'env'
    _env=
    for _p in /bin/env /usr/bin/env; do
        if [ -x "$_p" ]; then
            _env=$_p
            break
        fi
    done
    [ "$_env" ] || { echo "Could not find 'env' executable" >&2; exit 4; }

    SHEBANG="#!$_env $PYTHON_EXECUTABLE"
else
    SHEBANG="#!$(realpath "$PYTHON_EXECUTABLE")"
fi

VIM_PLUGINS_DIR="$HOME/.vim/bundle"
if [ ! -d $VIM_PLUGINS_DIR ]; then
    VIM_PLUGINS_DIR="$HOME/.vim/plugged"
fi
if [ ! -d $VIM_PLUGINS_DIR ]; then
    echo "Unable to find vim plugins directory"
    exit 2
fi

JEDI_PATH=

for _p in \
    $VIM_PLUGINS_DIR/YouCompleteMe/third_party/ycmd/third_party/jedi \
    $VIM_PLUGINS_DIR/YouCompleteMe/third_party/ycmd/third_party/JediHTTP/vendor/jedi
do
    if [ -d "$_p" ]; then
        JEDI_PATH=$_p
        break
    fi
done

[ "$JEDI_PATH" ] || { echo "Unable to find Jedi directory"; exit 3; }

#python fakegir.py
rm -rf $HOME/.cache/jedi

TEMPDIR=`mktemp -d /tmp/fakegirXXXXXXXXXX`
echo "Temporary modules will be created in: $TEMPDIR" >&2

pkgs=""
echo "$SHEBANG" > $TEMPDIR/fakeprg.py
for f in ~/.cache/fakegir/gi/repository/*.py; do
    pkgname=`basename $f | cut -d . -f 1`
    pkgs="$pkgs $pkgname"
    echo "from gi.repository import $pkgname" >> $TEMPDIR/fakeprg.py
done


for pkgname in $pkgs; do
    echo Forcing cache for $pkgname
    cp $TEMPDIR/fakeprg.py $TEMPDIR/${pkgname}-fakeprg.py
    compl="w = ${pkgname}."
    echo "$compl"  >> $TEMPDIR/${pkgname}-fakeprg.py
    fakeprg_lines=`wc -l $TEMPDIR/${pkgname}-fakeprg.py| cut -d ' ' -f 1`
    compl_col=${#compl}

    export PYTHONPATH=$HOME/.cache/fakegir
    pushd $JEDI_PATH
    $PYTHON_EXECUTABLE $JEDI_PATH/sith.py \
        -f run completions $TEMPDIR/${pkgname}-fakeprg.py $fakeprg_lines $compl_col
done
