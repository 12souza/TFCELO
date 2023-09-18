# TFCELO

This is the bot that powers the TFPugs community.

There are four main python scripts that run the show.

autostuff.py - Handles updating the leaderboard
NFOStats.py -  Listens to the TFC server and reports results on game ends via listening to log commands
TFCELO.py - The main "Bot" that handles pickups and matchmaking
timeout.py - Handles putting people on push-to-talk only, allow runners to timeout people

# Running in Production
`ps aux | grep python` will show all the running scripts
`pkill -9 -f nameofscript.py` will kill the process of the running script

In the `~/TFCELO/` directory...
./autostuff.sh
./nfostats.sh
./TFCELO.sh

# How to run the project locally

You need a token
Token and server info needs to go in variables.json
DB Connection info

Need to install pipenv to leverage the Pipfile / Pipfile.lock for package management.