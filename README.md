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

In order to get every required gir file, install the libgirepository1.0-dev package
You'll also need python-lxml

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

