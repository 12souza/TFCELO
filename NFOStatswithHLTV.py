'''from rHLDS import Console

# Default port 27015
srv = Console(host='coach.hltv.nfoservers.com', port = 27020, password='asdfcoach')

srv.connect()

srv.execute('stoprecording')

srv.disconnect()'''

import socket
from ftplib import FTP
import os
import zlib
import zipfile
import discord
from discord.ext import commands
import json
from rHLDS import Console
from zipfile import ZipFile

client = commands.Bot(command_prefix="!")
UDP_IP_ADDRESS = "0.0.0.0"
UDP_PORT_NO = 6789
MIN_DEMO_FILE_SIZE = 100000  # TODO: Find average HLTV round filesize and use that instead
serverSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
serverSock.bind((UDP_IP_ADDRESS, UDP_PORT_NO))
with open('login.json') as f:
    logins = json.load(f)
with open('variables.json') as f:
    v = json.load(f)
with open('kills.json') as f:
    kills = json.load(f)
with open('damage.json') as f:
    damage = json.load(f)
with open('flagstats.json') as f:
    flagstats = json.load(f)

srv = Console(host='coach.hltv.nfoservers.com', port=27020, password='asdfcoach')
srv2 = Console(host='coachcent.hltv.nfoservers.com', port=27020, password='asdfcoach')

@client.event
async def on_ready():
    print("connected")
    #channel = await client.fetch_channel(860987432329019413)#1000847501194174675
    pChannel = await client.fetch_channel(v['pID'])#836633689248104518
    user = await client.fetch_user(118900492607684614)
    #await pChannel.send("test")
    bRecording = 0
    while True:
        
        #await pChannel.send("!stats EAST")
        data, addr = serverSock.recvfrom(1024)
        #if("killed" in str(data)):
        print(str(data))
        #L 12/31/2022 - 11:21:34: [MATCH RESULT] DRAW at <0> EAST
        
        # THIS IS WHERE THE HLTV MANAGE WILL START THE HLTV
        # ADDED TAG INTO RESTARTGAME.AMXX (NOT UPLOADED YET)
        # WORKED ON LOCAL SERVER
        if("[STARTHLTV]" in str(data)):
            string = str(data)
            begin = string.find('<') + 2
            end = string.find('>') - 6
            region = string[begin:end]
            print(region)
            if('EAST' in string):
                try:
                    print("success")
                    srv.connect()
                    srv.execute("record HLTV/TFPugs")
                    srv.disconnect()
                    bRecording = 1
                except:
                    print("bad addr")
            elif('CENTRAL' in string):
                try:
                    srv2.connect()
                    srv2.execute("record HLTV/TFPugs")
                    srv2.disconnect()
                    bRecording = 1
                except:
                    print("bad addr")

        if("[MATCH RESULT]" in str(data)):
            with open('activePickups.json') as f:
                activePickups = json.load(f)
            string = str(data)
            begin = string.find('<') + 1
            end = string.find('>')
            winningScore = string[begin:end]
            begin = string.find('(') + 1
            end = string.find(')')
            losingScore = string[begin:end]
            begin = string.find(')') + 2
            end = string.find('\n') - 6
            region = string[begin:end]
            if(len(activePickups) > 0):
                if("Team 1 Wins" in (str(data))):
                    #team 1 wins
                    await pChannel.send("!win 1")
                    #[MATCH RESULT] Team 1 Wins <10> (0)
                    await pChannel.send(f'**AUTO-REPORTING** Team 1 wins {winningScore} to {losingScore}')
                elif("Team 2 Wins" in (str(data))):
                    await pChannel.send("!win 2")
                    #[MATCH RESULT] Team 2 Wins <10> (0)
                    await pChannel.send(f'**AUTO-REPORTING** Team 2 wins {winningScore} to {losingScore}')
                elif("DRAW" in (str(data))):
                    await pChannel.send("!draw")
                    #[MATCH RESULT] DRAW at <0>
                    await pChannel.send(f"**AUTO-REPORTING** DRAW at {losingScore}")
                print(region)
                await pChannel.send(f"!stats {region.lower()}")
                
                # ADDED THIS TO STOP THE HLTV AUTORECORDED AT PICKUP'S END
                # WILL STOP RECORDING
                # SRV = EAST SRV2 = CENTRAL
                if(region.lower() == 'east'):
                    try:
                        srv.connect()
                        srv.execute("stoprecording")
                        srv.disconnect()
                    except:
                        print("bad addr")
                elif(region.lower() == 'central'):
                    try:
                        srv2.connect()
                        srv2.execute("stoprecording")
                        srv2.disconnect()
                    except:
                        print("bad addr")

client.run(v['TOKEN'])
