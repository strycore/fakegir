Fakegir: Bring autocompletion to your PyGObject code!
-----------------------------------------------------

fakegir is a tool to build a fake python package of PyGObject modules.

After inserting this package in your editor's python path, you will get
autocompletion for every PyGObject module!

By default the package is saved in ~/.cache/fakegir/. This is the directory you
want to add to your Python PATH.
Of course, you shouldn't put this package in your global PYTHONPATH or your
PyGObject applications will stop working immediatly ;)


Requirements
------------

You'll need python-lxml to parse gir files.

In order to get every required gir file, install the libgirepository1.0-dev package

If you want autocompletion for additional packages, you can find it with apt-file :

    $ apt-file search ".gir" | grep -i unity
    libunity-dev: /usr/share/gir-1.0/Unity-6.0.gir
    libunity-webapps-dev: /usr/share/gir-1.0/UnityWebapps-0.2.gir
    libunity-webapps-dev: /usr/share/gir-1.0/UnityWebappsRepository-0.2.girV
    $ sudo apt-get install libunity-dev


Usage
-----

* python fakegir.py
* Add ~/.cache/fakegir/ to the PYTHONPATH of your favorite editor
* ????
* Profit !

Don't forget to run fakegir when you install new gir files or upgrade your distro.

Vim support
-----------

Vim support is a bit tricky for the moment. There are several options but
these may or may not work with your Vim setup.

For a basic vim setup, you can insert the snippet below to your vimrc:

    if has('python')
    py << EOF
    import os.path
    import sys
    import vim
    sys.path.insert(0, os.path.join(os.path.expanduser('~'), '.cache/fakegir/'))
    EOF

A lot of Vim users use YouCompleteMe for autocompletion which itself uses Jedi
for Python completion. Getting Fakegir to work with a bit trickier. The first
option is to run the provided script `build-jedi-cache.sh`. This script is
from a fork of Fakegir on github I merged back into my branch. I haven't
witnessed this script actually  working with the current version of Jedi but 
I'll leave it here in case someone manages to get something out of it. (Please
make a Pull Request if you do).

The other option which I use is to create a virtualenv and copy the fakegir
gi package into it:

    mkvirtualenv fakegir
    cdvirtualenv
    lib/python*/site-packages
    cp -a ~/.cache/fakegir/gi .

You'll have to activate this virtualenv before editing your GObject program
with vim which makes it a bit more cumbersome but this method is the only one
I could get autocompletion with vim and Jedi. Note that creating a Python3
virtualenv doesn't seem to work and that the first autocompletion can be quite
slow while Jedi is building the cache. (Fakegir modules, while containing no
code at all are very large).
