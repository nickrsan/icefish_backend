Note that the home for all of the code related to this project is in a
[B-195-M Organization on BitBucket](https://bitbucket.org/b195m/).
This code base is modular and contains subcomponents, some of which will
have their own installation steps. The installers for this
code base will handle most of it automatically, but will link you to
installation documents in those repositories when appropriate.

## Setup
As an introduction, all of the items in this installation are targeted
toward Windows, but everything is developed to be cross-platform in the
event that you should desire running on a Unix-based server. You should
start with a full copy (clone) of this repository in a folder on the
computer you want to serve it from.

### Install Python
This code base relies heavily on Python, so the first step is to download
and install Python. This code is designed to work with Python 3.5 and above,
with the main MOO server running Python 3.6.3 as of this writing. Your best
bet is to try the latest version, then try 3.6.3 if the latest version
doesn't work.

You can [download Python installers from the Python.org website](https://python.org).
While it doesn't matter for this project, the 64-bit version is the recommended
distribution.

### Make a virtual environment for Python
In order to better isolate the python packages we use, we'll make what's
called a virtual environment - this allows different versions of Python
packages to coexist for different projects on the same machine. It also
allows us to control package installation without admin privileges. To
set this up, open a command prompt, and navigate to where you want to
keep the virtual environment. I recommend something like the following:

```
C:
|- Windows
|- Program Files
|- ...
|- Code
     |- virtualenvs
          |- server_virtualenv
     |- icefish_backend
```

In the above tree, you have a Code folder on the C drive that stores code
for the project and has a separate folder for any virtual environments you
create. In that example, it has a virtual environment named `server_virtualenv`.
Each package of code lives in its own folder in the main Code folder.

We'll use the name `server_virtualenv` for our environment here, though
you can choose another name if you prefer.

1. Open a *new* command prompt so we can install Python-based dependencies. The command prompt must be new after the install
so that environment variables updated during the installation are loaded.
2. Navigate to the folder you want to store your virtualenvs in. For example
    `cd C:\Code`
3. Type `python -m venv ./server_virtualenv` to create a virtual
    environment named `server_virtualenv in the current folder.
4. We'll want to use this virtual environment, so type
    `./server_virtualenv/Scripts/activate.bat` and hit enter to run it.
    That command makes the Python interpreter in the virtual environment
    our default for this command line session.

### Install Python-based dependencies
After setting up the virtual environment, we need to install packages.
In that command prompt, navigate to the directory that this code is stored,
the same folder this README file is located inside of, and type:

```
python -m pip install -r requirements.txt
```

That command will download and install all the necessary code for this
project to run.

## Install PostgreSQL
PostgreSQL is the intended database for this codebase. Though the project
uses [Django](https://djangoproject.com), which allows for any SQL-based database
to be the backend, this code has only been tested with PostgreSQL and SQLite,
and SQLite should *not* be used in production environments.

Download and install the [latest 64-bit version of PostgreSQL for Windows](https://www.postgresql.org/).
Most any version of the database should work, but we tested against 10.0,
so using that version or newer is safest.

Postges requires a fair amount of setup. Fortunately, this code will do
a lot of it (filling out the empty database with required tables), but you
will still need to do the following. Everything besides the first step below
can be done relatively easily in PGAdmin, an application that installs
alongside PostgreSQL and can be used for administrative tasks. If you
prefer, you can also use command line utilities, which are often referenced
in documentation.

1. Postgres requires host-based authentication. If you want to connect
to the server, you need to have allowed that server to connect in a text
configuration file. This even applies to connecting to the local database.
Set up host-based authentication to allow the server this code is running
on to connect to your database server. [See their documentation for more
details](https://www.postgresql.org/docs/current/static/auth-pg-hba-conf.html).
2. Create your user account for this project. In the installation, you'll
have created the root user account for managing all of the database. *DO
NOT USE THIS USER ACCOUNT IN THIS CODE*. Instead, log into PGAdmin with that
root user account and create a new user account - remember the username and password - you'll plug them into
a configuration file later.
3. Create a new database in PGAdmin. This is relatively straightforward.
Name it whatever you like, but remember that name.
4. Assign the user account you created full privileges (including ALTER)
 for the database you just created. This can be done from the properties
 pane available via right click on the database in the tree.

### Setting up the application
Now that you have the core dependencies installed, it's time to fill in
the configuration, as it applies to your local environment. Most
configuration is already filled out in settings.py in the folder
icefish_backend, but you should:

1. Make a copy of the file `local_settings_template.py` in the same folder
it's in and rename it to `local_settings.py`*
2. Edit that file with a text editor and fill in the values on each line.
Each line has a Python comment, following the pound/hash sign that indicates
what should be filled in there.

### Install Apache Web Server
Fill in

Clone/download the code
Copy local settings and fill in the values
gunicorn and nginx?

### CTD
See setup information in [seabird_ctd repository](https://bitbucket.org/b195m/seabird_ctd)

Need to install packages in requirements.txt and plug in CTD to computer.

Requires an environment variable to be set, named *SEABIRD_CTD_PORT*
that indicates which COM port the CTD is connected on (eg COM6).

(Maybe) Need to set up and install Erlang and RabbitMQ server and configure ports. As of 10/23/2017 not required, but might be.

## Running CTD Monitoring
To run the script to monitor for CTD data, after setup is complete, simply run
```python
python manage.py monitor_ctd
```

The console window that runs this will remain in an infinite loop monitoring
until the computer shuts down or it is closed.

If you installed RabbitMQ and configured it in the local_settings.py file,
then you can send commands to the CTD while it's sampling. The results
of the command will be printed in the console of the monitoring script you
started in the previous command.

To send a command to the CTD while it's running, use;
```python
python manage.py send_command_to_ctd {command}
```
For example, to get the status output printed in the data reader's console

```python
python manage.py send_command_to_ctd DS
```
