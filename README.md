    
TRAC FM 
======= 

This is the source code for the TracFM site hosted at http://tracfm.org/ as of April 1st 2013.


Getting Started
-------------------

```bash
% virtualenv env
% source env/bin/activate
% pip install -r pip-freeze.txt
% cd tracfm
% python manage.py syncdb
% python manage.py migrate
% python manage.py runserver
```
