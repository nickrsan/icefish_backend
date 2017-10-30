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

[More documentation on venv can be found here](https://docs.python.org/3/library/venv.html) if needed.

### Install Python-based dependencies
After setting up the virtual environment, we need to install packages.
In that command prompt, navigate to the directory that this code is stored,
the same folder this README file is located inside of, and type:

```
python -m pip install -r requirements.txt
```

That command will download and install all the necessary code for this
project to run.

### Install PostgreSQL
PostgreSQL is the intended database for this codebase. Though the project
uses [Django](https://djangoproject.com), which allows for any SQL-based database
to be the backend, this code has only been tested with PostgreSQL and SQLite,
and SQLite should *not* be used in production environments.

Download and install the [latest 64-bit version of PostgreSQL for Windows](https://www.postgresql.org/).
Most any version of the database should work, but we tested against 10.0,
so using that version or newer is safest. You should be able to accept the
defaults while installing, making sure to take note of the username and
password you create during the installation.

Postgres requires a fair amount of setup. Fortunately, this code will do
a lot of it (filling out the empty database with required tables), but you
will still need to do the following. Everything besides the first step below
can be done relatively easily in PGAdmin, an application that installs
alongside PostgreSQL and can be used for administrative tasks. If you
prefer, you can also use command line utilities, which are often referenced
in documentation.

1. If you installed Postgres on a separate server, one of the gotchas is
that Postgres requires host-based authentication (in addition to any required
firewall configuration on each machine). If you want to connect the server with
Postgres to the web server, you need to have allowed the Postgres server to connect in a text
configuration file. You can set up this "host-based authentication" to allow the server this code is running
on to connect to your database server. [See their documentation for more
details](https://www.postgresql.org/docs/current/static/auth-pg-hba-conf.html).
This file can most easily be edited by navigating to `C:\Program Files\PostgreSQL\10\data\`
and right clicking on `pg_hba.conf` and selecting `Edit with Notepad++` if
you have installed Notepad++.
2. Create your user account for this project. In the installation, you'll
have created the root user account for managing all of the database. *DO
NOT USE THIS USER ACCOUNT IN THIS CODE*. Instead, log into PGAdmin with that
root user account and create a new user account - remember the username and password - you'll plug them into
a configuration file later. You can create a new user account by right clicking
on `Login/Group Roles` and selecting `Create`.
    * On the "`General` tab, create a username in the `Name` box. We named it `icefish` in the initial install.
    * On the `Definition` tab, set a password.
    * On the `Privileges` tab, change `Can login?` to `Yes`. Leave the rest
        at their defaults.
3. Create a new database in PGAdmin. This is relatively straightforward.
Name it whatever you like, but remember that name. To do this, right
click on `Databases` in the tree and again, select `Create`.
    * On the `General` tab, give it a name - we called it `icefishdb` in
     the initial install. Leave the Owner as the root user
    (named `postgres` by default). We'll give the new user account the ability
    to operate the database below, but we'll leave ownership with a user
    that's unconnected to the web server so that in the event of a web
    security issue, the data is safer.
    * On the `Security` tab, click the plus sign in the `Privileges` heading.
    Select the new user you just created as the `Grantee`, check the box
    next to `Connect` that pops into the `Privileges` column, but leave
    `With Grant Option` unchecked, and leave `Grantor` as your root user
    account.
    * Click `Save` to create the database.
4. Now connect to the new database by double clicking on it in the tree.
    We need to create a new `Schema` or tablespace, by right clicking
    on the `Schemas` portion of the tree and going to create.
    * Give the schema a name on the `General` tab, again leaving postgres
    as the owner. We've named it `icefish_backend` in the initial install.
    * On the `Security` tab, again add a record and select your new user
    account as the `Grantee`. Give it `ALL` privileges by checking that box,
    but again, do not check `With Grant Option`*
    * On the `Default Privileges` tab, we'll configure the settings for
    new tables that will be created by our application using the new user
    account. This is where we finally give that account the ability to do
    things.
        * On the `Tables` subtab, add a row, select your new user account
        as the Grantee, and again select the `All` option without selecting
        `With Grant Option`. Then, *uncheck* the `Truncate` option.
        Together, these will give the new user the ability to create, modify,
        and delete data - only within this schema.
        * On the `Sequences` tab, again give `All` privileges to your new
        user - no grant option
        * On both the `Functions` and `Types` tabs, give the new user
        the only privilege available for each of those. Once again, do not
        select the `With Grant Option` boxes.
    * Click Save to create the schema and assign the privileges.
5. Now, go back to the properties for your new user account, and we'll
    set up some parameters. Switch to the `Parameters` tab and we'll add
    three new rows:
    ```
    +-------------------------------+----------------+---------------+
    | Name                          | Value          | Database      |
    +-------------------------------+----------------+---------------+
    | client_encoding               | UTF8           | icefishdb     |
    +-------------------------------+----------------+---------------+
    | default_transaction_isolation | read_committed | icefishdb     |
    +-------------------------------+----------------+---------------+
    | timezone                      | UTC            | icefishdb     |
    +-------------------------------+----------------+---------------+
    ```

    Replace icefishdb with whatever you named your database.

### Setting up the application
Now that you have the core dependencies installed, it's time to fill in
the configuration, as it applies to your local environment. Most
configuration is already filled out in settings.py in the folder
subfolder `icefish_backend` of the main `icefish_backend` folder, but you should:

1. Make a copy of the file `local_settings_template.py` in the same folder
it's in and rename it to `local_settings.py`*
2. Edit that file with a text editor and fill in the values on each line.
Each line has a Python comment, following the pound/hash sign that indicates
what should be filled in there.

### Set up the data tables
Now that you've configured the local settings, you can have the application
set up the database. To do this, open a command prompt (if you don't
have the previous one open still) and activate the virtual environment
as you did previously. Then, navigate into the main folder `icefish_backend`
and run the command `python manage.py migrate` - follow any prompts it
gives you. This action will create all of the data tables for the
application and do any additional setup.

### Install Apache Web Server
Fill in
gunicorn and apache?
Backup for Postgres?
Django superuser?
Configure CTD COM Port
Connect to Synology

## Running and Using the Application
### CTD
See setup information in [seabird_ctd repository](https://bitbucket.org/b195m/seabird_ctd)

Need to install packages in requirements.txt and plug in CTD to computer.

Requires an environment variable to be set, named *SEABIRD_CTD_PORT*
that indicates which COM port the CTD is connected on (eg COM6).

(Maybe) Need to set up and install Erlang and RabbitMQ server and configure ports. As of 10/23/2017 not required, but might be.

#### Running CTD Monitoring
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
