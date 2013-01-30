Fakegir: Bring autocompletion to your PyGObject code!
-----------------------------------------------------

fakegir is a tool to build a fake python package of PyGObject modules.

After inserting this package in your editor's python path, you will get
autocompletion for every PyGObject module!

By default the package is saved in ~/.cache/fakegir/. This is the directory you
want to add to your Python PATH.
Of course, you shouldn't put this package in your global PYTHONPATH or your 
PyGObject applications will stop working immediatly ;)

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


Todo
----

Fakegir is still at a very early stage, there's a lot more info that could be 
pulled from gir files and used for autocompletion. For the moment, only classes
and their methods are available, but functions, constants, and docstrings will 
be added soon.
