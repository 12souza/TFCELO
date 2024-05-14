# TFCELO

This is the bot that powers the TFPugs community.

There are 2 main python scripts that run the show.

NFOStats.py -  Listens to the TFC server and reports results on game ends via listening to log commands
TFCELO.py - The main "Bot" that handles pickups and matchmaking

# Running in Production
`ps aux | grep python` will show all the running scripts
`pkill -9 -f nameofscript.py` will kill the process of the running script

In the `~/TFCELO/` directory...
./nfostats.sh
./run.sh

# How to run the project locally

You need a token
Token and server info needs to go in variables.json and login.json
DB Connection info

Need to install pipenv to leverage the Pipfile / Pipfile.lock for package management.