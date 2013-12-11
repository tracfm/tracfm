from subprocess import call
import sys

def exe(command):
    print command
    if call(command, shell=True):
        print "Bootstrap failed, exiting."
        sys.exit()

exe("echo 'drop database tracfm; create database tracfm;' | python manage.py dbshell")
exe("python manage.py dbshell < ../dump.sql")
exe("python manage.py syncdb --noinput")
# exe("python manage.py dbshell < ../migrate_quickblocks.sql")

# exe("python manage.py migrate guardian --fake")
# exe("python manage.py migrate reversion --fake")

#apps = ["locations", "simple_locations", "polls"]

# fake the first migration
#for app in apps:
#    exe("python manage.py migrate %s 0001 --fake" % app)

# rock the second one
# for app in apps:
#    exe("python manage.py migrate %s" % app)
