## SETUP
Install Postgres
Configure database settings

### CTD
See setup information in [seabird_ctd package directory](./seabird_ctd)

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

To send a command to the CTD while it's running, use;
```python
python manage.py send_command_to_ctd {command}
```
For example, to get the status output printed in the data reader's console

```python
python manage.py send_command_to_ctd DS
```
