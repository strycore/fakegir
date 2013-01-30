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
    
Add this to your vimrc for vim support:

    if has('python')
    py << EOF
    import os.path
    import sys
    import vim
    sys.path.insert(0, os.path.join(os.path.expanduser('~'), '.cache/fakegir/'))
    EOF
