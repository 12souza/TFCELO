import socket
from ftplib import FTP
import os
import zipfile
import discord
from discord.ext import commands
import json
from datetime import datetime

client = commands.Bot(command_prefix = "!")
UDP_IP_ADDRESS = "0.0.0.0"
UDP_PORT_NO = 6789
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



@client.event
async def on_ready():
    print("connected")
    #channel = await client.fetch_channel(860987432329019413)#1000847501194174675
    pChannel = await client.fetch_channel(v['pID'])#836633689248104518
    user = await client.fetch_user(118900492607684614)
    #await pChannel.send("test")
    while True:
        
        #await pChannel.send("!stats EAST")
        data, addr = serverSock.recvfrom(1024)
        #if("killed" in str(data)):
        print(str(data))
        #L 12/31/2022 - 11:21:34: [MATCH RESULT] DRAW at <0> EAST
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
            reported_match = list(activePickups)[-1]
            if(len(activePickups) > 0):
                await pChannel.send(f"**AUTO-REPORTING** Reporting for game {reported_match}")
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
                await pChannel.send(f"!stats {region.lower()} {reported_match} {winningScore} {losingScore}")
        
client.run(v['TOKEN'])
#client.run("NzMyMzcyMTcwMzY5NTMxOTc4.GPL0pm.iRN9voORDs1haOXvmlhZu26tWOtS-e7Xpmf7LM")