echo "To use this utility, make sure you set ICEFISH_INTERPRETER environment variable to match the path to your virtualenvironment's copy of Python"
echo "It's also a good idea to make sure that your mercurial credentials are set so you can pull changes"

hg pull
hg update
%ICEFISH_INTERPRETER% -m pip install -r requirements.txt
%ICEFISH_INTERPRETER% manage.py migrate
net restart MOOWaitress