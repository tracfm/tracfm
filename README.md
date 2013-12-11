    
TRAC FM 
======= 

This is the public source code for the TracFM site hosted at http://tracfm.org/

It is licensed under the Affero GPL. Public hosting of this code must be accompanied with the publishing of modified sources.

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
