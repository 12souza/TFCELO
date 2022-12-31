from asyncio.tasks import sleep
from email.utils import collapse_rfc2231_value
from http import server
import json
from platform import python_build, python_version
from sre_constants import NOT_LITERAL_LOC_IGNORE
import discord
from discord import player
from discord.ext import commands
from discord.utils import get
import matplotlib.pyplot as plt
from discord.ext import tasks
import os
import random
import itertools
import time
import requests
#from discord import app_commands
#from discord_slash import SlashCommand


#print(discord.__version__)
intents = discord.Intents.all()
client = commands.Bot(command_prefix = ["!", "+", "-"], case_insensitive=True, intents= intents)
client.remove_command('help')
#slash = SlashCommand(client)

#print(python_build)

with open('ELOpop.json') as f:
    ELOpop = json.load(f)
with open('variables.json') as f:
    v = json.load(f)

#globals
cap1 = None
cap1Name = None
cap2 = None
cap2Name = None
playersAdded = []
capList = []
blueTeam = []
redTeam = []
votable = 0
winner = None
mapChoice1 = None
mapChoice2 = None
mapChoice3 = None
mapChoice4 = "New Maps"
loveMaps = []
vnoELO = 0
hateMaps = []
mapVotes = {}
alreadyVoted = []
pMsg = None
oMsg = None
lastFive = []
mapSelected = []
winningIP = "None"
votePhase = 0
ready = []
fTimer = 0
inVote = 0
eligiblePlayers = []
reVote = 0
captMode = 0
vMsg = None
serverVote = 0
mapVote = 0
pickCount = 0
msg = None
pTotalPlayers = []
winningMap = None
winningServer = None

#just a command used for raters to adjust ELO if necessary
@client.command(pass_context=True)
@commands.has_role(v['rater'])
async def search(ctx, searchkey):
    #print('test')
    if(ctx.channel.name == 'tfc-ratings'):    
        with open('ELOpop.json') as f:
            ELOpop = json.load(f)
        searchList = []
        for i in list(ELOpop):
            if(searchkey.lower() in ELOpop[i][0].lower()):
                searchList.append(ELOpop[i][0])

        pMsgList = []
        for i in searchList:
            playerID = None
            for j in list(ELOpop):
                if(i == ELOpop[j][0]):
                    playerID = j
            pMsgList.append(i + " " * (30 - len(i)) + " ELO: " + str(ELOpop[playerID][1]) + "                 1-20 rank: " + str(ELOpop[playerID][1] / 120) + f"     W:{ELOpop[playerID][4]} L:{ELOpop[playerID][5]} D:{ELOpop[playerID][6]}\n")
        mMsg = ''.join(pMsgList)
        if(len(searchList) > 0):
            await ctx.send(content = "```\n" + mMsg + "```")
        else:
            await ctx.send("No results with that search string..")

@client.command(pass_context=True)
async def private(ctx):
    global ELOpop
    with open('ELOpop.json') as f:
        ELOpop = json.load(f)

    if(ELOpop[str(ctx.author.id)][3] != "<:norank:1001265843683987487>"):
        ELOpop[str(ctx.author.id)][3] = "<:norank:1001265843683987487>"
        await ctx.author.send("Your ELO Rank is now private")

        with open('ELOpop.json', 'w') as cd:
            json.dump(ELOpop, cd,indent= 4)
    else:
        newRank(str(ctx.author.id))
        await ctx.author.send("Your ELO Rank is back")

   

def DePopulatePickup():
    global cap1
    global cap2
    global cap1Name
    global cap2Name
    global playersAdded
    global blueTeam
    global redTeam
    global winner
    global oMsg
    global mapChoice1
    global mapChoice2
    global mapChoice3
    global mapChoice4
    global capList
    global captMode
    global loveMaps
    global mapVotes
    global hateMaps
    global alreadyVoted
    global vMsg
    global pMsg
    global mapSelected
    global winningIP
    global votePhase
    global fTimer
    global ready
    global inVote
    global vnoELO
    global eligiblePlayers
    global reVote
    global serverVote
    global mapVote
    global pickCount
    global msg
    global pTotalPlayers

    cap1 = None
    cap1Name = None
    cap2 = None
    cap2Name = None
    #playersAdded = []
    capList = []
    blueTeam = []
    ready = []
    redTeam = []
    winner = None
    vnoELO = 0
    mapChoice1 = None
    mapChoice2 = None
    mapChoice3 = None
    mapChoice4 = "New Maps"
    loveMaps = []
    hateMaps = []
    mapVotes = {}
    alreadyVoted = []
    pMsg = None
    mapSelected = []
    oMsg = None
    winningIP = "None"
    votePhase = 0
    fTimer = 0
    inVote = 0
    eligiblePlayers = []
    reVote = 0
    captMode = 0
    vMsg = None
    serverVote = 0
    mapVote = 0
    pickCount = 0
    msg = None
    pTotalPlayers = []
    fVCoolDown.stop()

def mapVoteOutput(mapChoice):
    global mapVotes
    with open('ELOpop.json') as f:
        ELOpop = json.load(f)
    whoVoted = []
    for i in mapVotes[mapChoice]:
        #whoVoted.append(ELOpop[i][0])
        whoVoted.append(i)
    numVotes = len(whoVoted)    
    whoVoted = ", ".join(whoVoted)
    
    if len(whoVoted) == 0:
        return "0 votes"

    return "%d votes (%s)" % (numVotes, whoVoted)

@tasks.loop(seconds = 1) # repeat after every 10 seconds
async def fVCoolDown():
    global fTimer
    #print(fTimer)
    if(fTimer > 0):
        fTimer = fTimer - 1

def PickMaps():
    global mapChoice1
    global mapChoice2
    global mapChoice3
    global loveMaps
    global hateMaps
    global mapVotes
    global alreadyVoted
    global votePhase
    multiple = 0
    with open('mainmaps.json') as f:
        mapList = json.load(f)
    
    mapVotes = {}
    alreadyVoted = []
    #print(mapList)
    mapPick = []
    for i in list(mapList):
        if(i not in mapSelected):
            if((i not in lastFive) and (i not in hateMaps)):
                if(i in loveMaps):
                    mapPick.append(i)
                    mapPick.append(i)
                    mapPick.append(i)
                    mapPick.append(i)
                    mapPick.append(i)
                else:
                    mapPick.append(i)
    mapPick2 = []
    with open('specmaps.json') as f:
        mapList = json.load(f)

    for i in list(mapList):
        if(i not in mapSelected):
            if((i not in lastFive) and (i not in hateMaps)):
                if(i in loveMaps):
                    mapPick2.append(i)
                    mapPick2.append(i)
                    mapPick2.append(i)
                    mapPick2.append(i)
                    mapPick2.append(i)
                else:
                    mapPick2.append(i)

    print(f"Map Lists: {mapPick} {mapPick2}" )
    print(f"Maps Selected: {mapSelected}")
    print(f"Love Maps: {loveMaps}")
    print(f"Hate Maps: {hateMaps}")
    print(f"Last Five: {lastFive}")

    #print(mapPick)
    mapChoice1 = random.choice(mapPick)
    while(mapChoice1 in mapPick):
        mapPick.remove(mapChoice1)
    mapVotes[mapChoice1] = []
    mapSelected.append(mapChoice1)
    mapChoice2 = random.choice(mapPick)
    while(mapChoice2 in mapPick):
        mapPick.remove(mapChoice2)
    mapVotes[mapChoice2] = []
    mapSelected.append(mapChoice2)
    mapChoice3 = random.choice(mapPick2)
    while(mapChoice3 in mapPick):
        mapPick2.remove(mapChoice3)
    mapVotes[mapChoice3] = []
    mapSelected.append(mapChoice3)

def TeamPickPopulate():
    global msg
    global eligiblePlayers
    global pickCount
    global pTotalPlayers
    with open('ELOpop.json') as f:
        ELOpop = json.load(f)
    msgList = []
    redTeamList = ["🔴 Red Team 🔴\n"]
    blueTeamList = ["🔵 Blue Team 🔵\n"]
    #pTotalPlayers = list(eligiblePlayers)
    for i in pTotalPlayers:
        msgList.append(str(i[0]) + ". " + i[1] + "\n")
    #print(redTeam)
    for i in redTeam:
        redTeamList.append(i + "\n")
    for i in blueTeam:
        blueTeamList.append(i + "\n")

    msg = "".join(msgList)
    blueMsg = "".join(blueTeamList)
    redMsg = "".join(redTeamList)
    if((pickCount == 0) or (pickCount == 2)):
        msg = ("🔴 Red Team 🔴 picks!\n\n" + msg + "\n" + blueMsg + "\n" + redMsg)
    elif(pickCount > 4):
        msg = (msg + "\n" + blueMsg + "\n" + redMsg)
    else:
        msg = ("🔵 Blue Team 🔵 picks!\n\n" + msg + "\n" + blueMsg + "\n" + redMsg)
    return msg

async def voteSetup():
    global mapChoice1
    global mapChoice2
    global mapChoice3
    global mapChoice4
    global mapVotes
    global serverVote
    global reVote
    global alreadyVoted
    global vMsg
    global votable


    channel = await client.fetch_channel(v['pID'])
    with open('ELOpop.json') as f:
        ELOpop = json.load(f)
    if(serverVote == 1):
        mapChoice3 = "New York - East"
        mapVotes[mapChoice3] = []
        mapChoice2 = "Chicago - Central"
        mapVotes[mapChoice2] = []    
        mapChoice1 = "None - None"
        mapVotes[mapChoice1] = []

        playersAbstained = []
        for i in eligiblePlayers:
            if i not in alreadyVoted:
                playersAbstained.append(ELOpop[i][0])
        toVoteString = "```"
        if len(playersAbstained) != 0:
            toVoteString = "\n💩 " + ", ".join(playersAbstained) +  " need to vote 💩```"

        vMsg = await channel.send("```Vote for your server!  Be quick, you only have 45 seconds to vote..\n\n"
                                                        + "1️⃣ " + mapChoice1 + " " * (70 - len(mapChoice1)) + mapVoteOutput(mapChoice1) + "\n"
                                                        + "2️⃣ " + mapChoice2 + " " * (70 - len(mapChoice2)) + mapVoteOutput(mapChoice2) + "\n"
                                                        + "3️⃣ " + mapChoice3 + " " * (70 - len(mapChoice3)) + mapVoteOutput(mapChoice3)
                                                        + toVoteString)

        await vMsg.add_reaction("1️⃣")
        await vMsg.add_reaction("2️⃣")
        await vMsg.add_reaction("3️⃣")
        votable = 1
        
    elif((reVote == 0) and (serverVote == 0)):
        with open('ELOpop.json') as f:
            ELOpop = json.load(f)
        
        alreadyVoted = []
        mapVotes = {}           
        PickMaps()
        mapChoice4 = "New Maps"
        mapVotes[mapChoice4] = []
        
        playersAbstained = []
        for i in eligiblePlayers:
            if i not in alreadyVoted:
                playersAbstained.append(ELOpop[i][0])
        toVoteString = "```"
        if len(playersAbstained) != 0:
            toVoteString = "\n💩 " + ", ".join(playersAbstained) +  " need to vote 💩```"
        with open('mainmaps.json') as f:
            mapList = json.load(f)
        with open('specmaps.json') as f:
            mapList2 = json.load(f)
        vMsg = await channel.send("```Vote up and make sure you hydrate!\n\n"
                                        + "1️⃣ " + mapChoice1 + " " * (25 - len(mapChoice1)) + "   " + str(mapList[mapChoice1]) + " mirv" + " " * 15 + mapVoteOutput(mapChoice1) + "\n"
                                        + "2️⃣ " + mapChoice2 + " " * (25 - len(mapChoice2)) + "   " + str(mapList[mapChoice2]) + " mirv" + " " * 15 + mapVoteOutput(mapChoice2) + "\n"
                                        + "3️⃣ " + mapChoice3 + " " * (25 - len(mapChoice3)) + "   " + str(mapList2[mapChoice3]) + " mirv" + " " * 15 + mapVoteOutput(mapChoice3) + "\n"
                                        + "4️⃣ " + mapChoice4 + " " * (49 - len(mapChoice4)) + mapVoteOutput(mapChoice4)
                                        + toVoteString)

        await vMsg.add_reaction("1️⃣")
        await vMsg.add_reaction("2️⃣")
        await vMsg.add_reaction("3️⃣")
        await vMsg.add_reaction("4️⃣")
        votable = 1

    elif((reVote == 1) and (serverVote == 0)):
        with open('ELOpop.json') as f:
            ELOpop = json.load(f)
        
        alreadyVoted = []
        mapVotes = {}           
        PickMaps()
        mapVotes[mapChoice4] = []
        
        playersAbstained = []
        for i in eligiblePlayers:
            if i not in alreadyVoted:
                playersAbstained.append(ELOpop[i][0])
        toVoteString = "```"
        if len(playersAbstained) != 0:
            toVoteString = "\n💩 " + ", ".join(playersAbstained) +  " need to vote 💩```"
        with open('mainmaps.json') as f:
            mapList = json.load(f)
        with open('specmaps.json') as f:
            mapList2 = json.load(f)
        vMsg = await channel.send("```Vote up and make sure you hydrate!\n\n"
                                        + "1️⃣ " + mapChoice1 + " " * (25 - len(mapChoice1)) + "   " + str(mapList[mapChoice1]) + " mirv" + " " * 15 + mapVoteOutput(mapChoice1) + "\n"
                                        + "2️⃣ " + mapChoice2 + " " * (25 - len(mapChoice2)) + "   " + str(mapList[mapChoice2]) + " mirv" + " " * 15 + mapVoteOutput(mapChoice2) + "\n"
                                        + "3️⃣ " + mapChoice3 + " " * (25 - len(mapChoice3)) + "   " + str(mapList2[mapChoice3]) + " mirv" + " " * 15 + mapVoteOutput(mapChoice3) + "\n"
                                        + "4️⃣ " + mapChoice4 + " " * (49 - len(mapChoice4)) + mapVoteOutput(mapChoice4)
                                        + toVoteString)

        await vMsg.add_reaction("1️⃣")
        await vMsg.add_reaction("2️⃣")
        await vMsg.add_reaction("3️⃣")
        await vMsg.add_reaction("4️⃣")
        votable = 1

@client.command(pass_context=True)
@commands.has_role(v['admin'])
async def addach(ctx, key, value):
    with open('emotes.json') as f:
        e = json.load(f)

    e[key] = value

    with open('emotes.json', 'w') as cd:
        json.dump(e, cd,indent= 4)
    await ctx.send(f"value has been added to the list of achievements")

@client.command(pass_context=True)
@commands.has_role(v['admin'])
async def ach(ctx, player: discord.Member, ach):
    with open('ELOpop.json') as f:
        ELOpop = json.load(f)
    with open('emotes.json') as f:
        e = json.load(f)
    channel = await client.fetch_channel(1004934664475115582)
    ELOpop[str(player.id)][7].append(e[ach])

    with open('ELOpop.json', 'w') as cd:
        json.dump(ELOpop, cd,indent= 4)

    await ctx.send(f"{player.id} has been successfully given the achievement {e[ach]}")
    await channel.send(f"Congratulations {player.display_name} for completing the {e[ach]} achievement!")

@client.command(pass_context=True)
async def pickupDisplay(ctx):
    global playersAdded
    global capList
    global oMsg
    global ready
    with open('ELOpop.json') as f:
        ELOpop = json.load(f)
    print("hello")
    if(len(playersAdded) >= 8):    
        msgList = []
        for i in playersAdded:
            achList = ELOpop[i][7]
            ach = "".join(achList)
            if(i in capList):
                msgList.append(ELOpop[i][3] + " " + ELOpop[i][0] + " " + v['cptimg'] + " " + ach + "\n")
                #msgList.append(ELOpop[i][0] + " " + v['cptimg'] + "\n")
            else:
                
                msgList.append(ELOpop[i][3] + " " + ELOpop[i][0] + " " + ach + "\n")
                #msgList.append(ELOpop[i][0] + "\n")
        msg = "".join(msgList)
        readyList = []
        for i in ready:
            readyList.append(f"{ELOpop[i][0]}\n")
        rMsg = "".join(readyList)
        embed = discord.Embed(title = "Pickup Has 8 or more Players")
        if(len(playersAdded) > 0):
            embed.add_field(name = f"Players Added - {len(playersAdded)} Queued", value= msg)
        elif(len(playersAdded) == 0):
            embed.add_field(name = "Players Added", value= "PUG IS EMPTY!")
        if(len(ready) != 0):    
            embed.add_field(name = "Players Ready", value = rMsg)
        elif(len(ready) == 0):
            embed.add_field(name = "Players Ready", value = "\u200b")
        oMsg = await ctx.send(embed = embed)

        await oMsg.add_reaction("👍")
        notiflist = []
        for i in playersAdded[0:8]:
            notiflist.append(f"<@{i}> ")
        notiflist.append("... React with 👍 when ready to teams if no runner available.")
        msg = "".join(notiflist)
        await ctx.send(msg)
            

    elif(len(playersAdded) < 8):
        oMsg = None
        msgList = []
        for i in playersAdded:
            achList = ELOpop[i][7]
            ach = "".join(achList)
            if(i in capList):
                msgList.append(ELOpop[i][3] + " " + ELOpop[i][0] + " " + v['cptimg'] + "\n")
                #msgList.append(ELOpop[i][0] + " " + v['cptimg'] + "\n")
            else:
                msgList.append(ELOpop[i][3] + " " + ELOpop[i][0] + " " + ach + "\n")
                #msgList.append(ELOpop[i][0] + "\n")
        msg = "".join(msgList)
        embed = discord.Embed(title = "Pickup Started!")
        if(len(playersAdded) > 0):
            embed.add_field(name = f"Players Added - {len(playersAdded)} Queued", value= msg)
        elif(len(playersAdded) == 0):
            embed.add_field(name = "Players Added", value= "PUG IS EMPTY!")
        await ctx.send(embed = embed)  

async def teamsDisplay(ctx, blueTeam, redTeam, team1prob, team2prob):
    msgList = []

    for i in blueTeam:
        #msgList.append(ELOpop[i][3] + " " + ELOpop[i][0] + "\n")
        msgList.append(ELOpop[i][0] + "\n")
    bMsg = "".join(msgList)
    msgList.clear()
    for i in redTeam:
        #msgList.append(ELOpop[i][3] + " " + ELOpop[i][0] + "\n")
        msgList.append(ELOpop[i][0] + "\n")
    rMsg = "".join(msgList)
    embed = discord.Embed(title = "Teams Sorted!")
    #embed.add_field(name = "Blue Team " + v['t1img'] + " " + str(int(team1prob * 100)) + "%", value= bMsg, inline=True)
    embed.add_field(name = "Blue Team " + v['t1img'], value= bMsg, inline=True)
    embed.add_field(name="\u200b", value = "\u200b")
    #embed.add_field(name = "Red Team " + v['t2img'] + " " + str(int(team2prob * 100)), value= rMsg, inline=True)
    embed.add_field(name = "Red Team " + v['t2img'], value= rMsg, inline=True)
    await ctx.send(embed = embed)

    

async def pastGames(ctx):
    with open('pastten.json') as f:
        pastTen = json.load(f)
    msgList = []
    for i in pastTen:
        msgList.append(i + "\n")
    msg = "".join(msgList)
    timeList = []
    for i in pastTen:
        if(i != 0):
            timeList.append("Team " + str(pastTen[i][8]) + "\n")
        elif(i == 0):
            timeList.append("DRAW" + str(pastTen[i][8]) + "\n")
            
    tMsg = "".join(timeList)
    mapList = []
    for i in pastTen:
        mapList.append(pastTen[i][9] + "\n")
    mMsg = "".join(mapList)
    embed = discord.Embed(title = "Active Pickups")
    if(len(pastTen) > 0):    
        embed.add_field(name = "Pickup #", value= msg, inline=True)
        embed.add_field(name = "Winner:", value= tMsg, inline=True)
        embed.add_field(name = "Pickup Map", value= mMsg, inline=True)
    elif(len(pastTen) == 0):
        embed.add_field(name = "#", value= "No unreported pickups!!", inline=True) 

    await ctx.send(embed = embed)

    await pMsg.add_reaction("1️⃣")

async def openPickups(ctx):
    with open('activePickups.json') as f:
        activePickups = json.load(f)
    with open('ELOpop.json') as f:
        ELOpop = json.load(f)
    msgList = []
    for i in activePickups:
        msgList.append(i + "\n")
    msg = "".join(msgList)
    timeList = []
    for i in activePickups:
        timeList.append(activePickups[i][6] + "\n")
    tMsg = "".join(timeList)
    mapList = []
    for i in activePickups:
        mapList.append(activePickups[i][7] + "\n")
    mMsg = "".join(mapList)
    embed = discord.Embed(title = "Active Pickups")
    if(len(activePickups) > 0):    
        embed.add_field(name = "Pickup #", value= msg, inline=True)
        embed.add_field(name = "Pickup Date", value= tMsg, inline=True)
        embed.add_field(name = "Pickup Map", value= mMsg, inline=True)
    elif(len(activePickups) == 0):
        embed.add_field(name = "#", value= "No unreported pickups!!", inline=True) 

    await ctx.send(embed = embed)


def newRank(ID):
    global ELOpop
    
    if(len(ELOpop[ID][2]) > 9):
        if(ELOpop[ID][1] < 240): #1
            ELOpop[ID][3] = v['rank1']
        if(ELOpop[ID][1] >= 240): #2
            ELOpop[ID][3] = v['rank2']
        if(ELOpop[ID][1] > 720): #3
            ELOpop[ID][3] = v['rank3']
        if(ELOpop[ID][1] > 960): #4
            ELOpop[ID][3] = v['rank4']
        if(ELOpop[ID][1] > 1200): #5
            ELOpop[ID][3] = v['rank5']
        if(ELOpop[ID][1] > 1440): #6
            ELOpop[ID][3] = v['rank6']
        if(ELOpop[ID][1] > 1680): #7
            ELOpop[ID][3] = v['rank7']
        if(ELOpop[ID][1] > 1920): #8
            ELOpop[ID][3] = v['rank8'] 
        if(ELOpop[ID][1] > 2160): #9
            ELOpop[ID][3] = v['rank9'] 
        if(ELOpop[ID][1] > 2300): #10
            ELOpop[ID][3] = v['rank10']
        if(ELOpop[ID][1] > 2600): #10
            ELOpop[ID][3] = v['rankS']

    with open('ELOpop.json', 'w') as cd:
        json.dump(ELOpop, cd,indent= 4)

@client.command(pass_context=True)
@commands.has_role(v['rater'])
async def avatar(ctx, player: discord.Member, emote):
    with open('ELOpop.json') as f:
        ELOpop = json.load(f)

    playerID = player.id

    ELOpop[playerID][2] = emote
    
    with open('ELOpop.json', 'w') as cd:
        json.dump(ELOpop, cd,indent= 4)

@client.command(pass_context=True)
@commands.has_role(v['rater'])
async def adjustELO(ctx, player, ELO):
    if(ctx.channel.name == v['ratingsChannel']):
        with open('ELOpop.json') as f:
            ELOpop = json.load(f)
        ELO = int(ELO)

        with open('ELOpop.json') as f:
            ELOpop = json.load(f)
        playerID = None
        for i in ELOpop:
            if(ELOpop[i][0] == player):
                playerID = i
        ELOpop[playerID][1] = ELO

        with open('ELOpop.json', 'w') as cd:
            json.dump(ELOpop, cd,indent= 4)
        
@client.command(pass_context=True)
#@commands.has_role(variables['runner'])
async def hello(ctx):
    await ctx.send("bye")

@client.command(pass_context=True)
@commands.has_role(v['runner'])
async def startserver(ctx, server):
    #if(ctx.channel.name == v['pc']):    
    if(server.lower() == 'west'):
        r = requests.get("https://us-west1-coachoffice-332119.cloudfunctions.net/startWest")
    #elif(server.lower() == 'central'):
        #r = requests.get("https://us-central1-coachoffice-332119.cloudfunctions.net/startCentral-1")
    elif(server.lower() == 'east'):
        r = requests.get("https://us-east4-coachoffice-332119.cloudfunctions.net/startEast")
    elif(server.lower() == 'latam'):
        r = requests.get("https://southamerica-east1-coachoffice-332119.cloudfunctions.net/startLATAM")
    elif(server.lower() == 'eu'):
        r = requests.get("https://europe-west3-coachoffice-332119.cloudfunctions.net/startEU")
    await ctx.send(server + " is starting up..")

@client.command(pass_context=True)
@commands.has_role(v['runner'])
async def stopserver(ctx, server):
    #if(ctx.channel.name == v['pc']):    
    if(server == 'west'):
        r = requests.get("https://us-west1-coachoffice-332119.cloudfunctions.net/stopWest")
    #elif(server == 'central'):
        #r = requests.get("https://us-central1-coachoffice-332119.cloudfunctions.net/stopCentral-2")
    elif(server == 'east'):    
        r = requests.get("https://us-east4-coachoffice-332119.cloudfunctions.net/stopEast")
    elif(server.lower() == 'latam'):
        r = requests.get("https://southamerica-east1-coachoffice-332119.cloudfunctions.net/stopLATAM")
    elif(server.lower() == 'eu'):
        r = requests.get("https://europe-west3-coachoffice-332119.cloudfunctions.net/stopEU")
    await ctx.send(server + " is shutting down..")

@client.command(pass_context=True)
@commands.has_role(v['runner'])
async def swapteam(ctx, player1: discord.Member, player2: discord.Member, number = "None"):
    if(ctx.channel.name == v['pc']):    
        if(number == "None"):    
            global redTeam
            global blueTeam
            with open('ELOpop.json') as f:
                ELOpop = json.load(f)
            player1ID = str(player1.id)
            player2ID = str(player2.id)
            
            blueRank = 0
            redRank = 0

            if(player1ID in blueTeam and player2ID in redTeam):
                redTeam.append(player1ID)
                blueTeam.remove(player1ID)
                blueTeam.append(player2ID)
                redTeam.remove(player2ID)
            
            elif(player1ID in redTeam and player2ID):
                blueTeam.append(player1ID)
                redTeam.remove(player1ID)
                redTeam.append(player2ID)
                blueTeam.remove(player2ID)

            for j in blueTeam:
                blueRank += int(ELOpop[j][1])
            for j in redTeam:
                redRank += int(ELOpop[j][1])

            team1prob = round(1/(1+10**((redRank - blueRank)/400)), 2)
            team2prob = round(1/(1+10**((blueRank - redRank)/400)), 2)

            #print(blueRank, redRank)

            await teamsDisplay(ctx, blueTeam, redTeam, team1prob, team2prob)
        else:
            with open('ELOpop.json') as f:
                ELOpop = json.load(f)
            with open('activePickups.json') as f:
                activePickups = json.load(f)
            blueTeam = activePickups[number][2] 
            redTeam = activePickups[number][5] 
            player1ID = str(player1.id)
            player2ID = str(player2.id)
            
            blueRank = 0
            redRank = 0

            if(player1ID in blueTeam and player2ID in redTeam):
                redTeam.append(player1ID)
                blueTeam.remove(player1ID)
                blueTeam.append(player2ID)
                redTeam.remove(player2ID)
            
            elif(player1ID in redTeam and player2ID):
                blueTeam.append(player1ID)
                redTeam.remove(player1ID)
                redTeam.append(player2ID)
                blueTeam.remove(player2ID)

            for j in blueTeam:
                blueRank += int(ELOpop[j][1])
            for j in redTeam:
                redRank += int(ELOpop[j][1])

            team1prob = round(1/(1+10**((redRank - blueRank)/400)), 2)
            team2prob = round(1/(1+10**((blueRank - redRank)/400)), 2)
            activePickups[number] = [team1prob, blueRank, blueTeam, team2prob, redRank, redTeam, activePickups[number][6], activePickups[number][7], activePickups[number][8]]
            #print(blueRank, redRank)
            with open('activepickups.json', 'w') as cd:
                json.dump(activePickups, cd,indent= 4)
            await teamsDisplay(ctx, blueTeam, redTeam, team1prob, team2prob)


def savePickup():
    global winningMap
    global winningServer
    global blueTeam
    global redTeam
    global captMode
    global vnoELO

    if(vnoELO == 0):    
        with open('activePickups.json') as f:
            activePickups = json.load(f)
        with open('ELOpop.json') as f:
                    ELOpop = json.load(f)

        serial = random.randint(0, 100000)

        pSerial = random.randint(0, 10000000)
        while(pSerial in list(activePickups)):
            pSerial = random.randint(0, 10000000)
        now = round(time.time())
        blueRank = 0
        redRank = 0

        if(captMode == 1):
            for i in blueTeam:
                #print(i)
                for j in ELOpop:
                    if(ELOpop[j][0] == i):
                        blueTeam.append(j)
                        #blueTeam.remove(i)
            for i in redTeam:
                #print(i)
                for j in ELOpop:
                    if(ELOpop[j][0] == i):
                        redTeam.append(j)
                        #blueTeam.remove(i)

            blueTeam = blueTeam[4:]
            redTeam = redTeam[4:]

        #print(blueTeam, redTeam)
        for i in blueTeam:
            blueRank += int(ELOpop[i][1])
        for i in redTeam:
            redRank += int(ELOpop[i][1])

        team1prob = round(1/(1+10**((redRank - blueRank)/400)), 2)
        team2prob = round(1/(1+10**((blueRank - redRank)/400)), 2)

        activePickups[pSerial] = [team1prob, blueRank, blueTeam, team2prob, redRank, redTeam, f"<t:{now}:f>", winningMap, winningServer]
        with open('activePickups.json', 'w') as cd:
            json.dump(activePickups, cd,indent= 4)

'''@client.command(pass_context=True)
async def elo(ctx):
    if(ctx.channel.name == v['pc']):
        await ctx.author.send("!elo no longer works.. but if you type 'elo' to me I will send you your elo info")
        with open('ELOpop.json') as f:
            ELOpop = json.load(f)
        print(ELOpop[str(ctx.author.id)][2])
        plt.plot(ELOpop[str(ctx.author.id)][2])
        plt.savefig(ctx.author.display_name + '.png')
        #await ctx.author.send(file = discord.File(ctx.author.display_name + '.png'), content="Your ELO is currently " + ctx.author.display_name][0])
        await ctx.author.send(file = discord.File(ctx.author.display_name + '.png'), content=f"Your ELO is currently {ELOpop[str(ctx.author.id)][1]} with a record of W: {ELOpop[str(ctx.author.id)][4]} L: {ELOpop[str(ctx.author.id)][5]} D: {ELOpop[str(ctx.author.id)][6]}")
        #os.remove(ctx.author.display_name + '.png')
        plt.clf()'''

@client.command(pass_context = True , aliases=['+'])
@commands.has_role(v['tfc'])
async def add(ctx, cap = None):
    if(ctx.channel.name == v['pc']):    
        global playersAdded
        global capList
        global ELOpop
        playerID = str(ctx.author.id)
        if(len(playersAdded) <= 19):    
            with open('ELOpop.json') as f:
                ELOpop = json.load(f)
            if(playerID not in playersAdded):
                if(playerID not in list(ELOpop)):
                    ELOpop[playerID] = [ctx.author.display_name, 800, [], "<:questionMark:972369805359337532>", 0, 0, 0, []]

                    with open('ELOpop.json', 'w') as cd:
                        json.dump(ELOpop, cd,indent= 4)
                
                if(cap == "cap"):
                    capList.append(playerID)
                
                playersAdded.append(playerID)
            else:
                await ctx.author.send("you are already added to this pickup..")
        with open('ELOpop.json', 'w') as cd:
            json.dump(ELOpop, cd,indent= 4)
        await pickupDisplay(ctx)

@client.command(pass_context = True , aliases=['-'])
async def remove(ctx):
    if(ctx.channel.name == v['pc']):
        global playersAdded
        global capList
        playerID = str(ctx.author.id)
        if(playerID in playersAdded):
            playersAdded.remove(playerID)
            if(playerID in capList):
                capList.remove(playerID)
        
        await pickupDisplay(ctx)

@client.command(pass_context=True)
@commands.has_role(v['runner'])
async def kick(ctx, player: discord.Member):
    if(ctx.channel.name == v['pc']):
        global playersAdded
        global capList
        playerID = str(player.id)
        if(playerID in playersAdded):
            playersAdded.remove(playerID)
            if(playerID in capList):
                capList.remove(playerID)
        await pickupDisplay(ctx)
    
@client.command(pass_context=True)
@commands.has_role(v['runner'])
async def addplayer(ctx, player: discord.Member):
    if(ctx.channel.name == v['pc']):
        global playersAdded
        global capList
        playerID = str(player.id)
        if(playerID not in playersAdded):
            playersAdded.append(playerID)

        await pickupDisplay(ctx)

@client.command(pass_context=True)
@commands.has_role(v['runner'])
async def noELO(ctx):
    global vnoELO
    print(vnoELO)
    if(vnoELO == 0):
        vnoELO = 1
        await ctx.send("ELO has been turned **OFF** for this game.")
    elif(vnoELO == 1):
        vnoELO = 0
        await ctx.send("ELO has been turned **ON** for this game.")

async def doteams(channel2, playerCount = 4):    
        global playersAdded
        global capList
        global inVote
        global blueTeam
        global redTeam
        global inVote
        global eligiblePlayers
        global fTimer
        global captMode
        global serverVote
        global rankedOrder
        global ready
        global oMsg
        #global pastTeams
        ready = []
        oMsg = None
        DMList = []
        channel2 = await client.fetch_channel(v['pID'])
        print("test1")
        if(len(playersAdded) >= int(playerCount * 2)):
            print("test2")
            if(inVote == 0):
                print("test3")
                if(len(capList) < 2):  
                    with open('ELOpop.json') as f:
                        ELOpop = json.load(f)    
                    playerCount = int(playerCount)
                    if(len(playersAdded) == playerCount):
                        eligiblePlayers = playersAdded
                    else:    
                        eligiblePlayers = playersAdded[0:playerCount * 2]
                    counter = 0
                    teamsPicked = 0
                    
                    combos = list(itertools.combinations(eligiblePlayers, int(len(eligiblePlayers) / 2)))
                    random.shuffle(combos)
                    
                    for i in eligiblePlayers:
                        if i in playersAdded:
                            playersAdded.remove(i)
                    #print(playersAdded)
                    #while teamsPicked == 0:
                    blueTeam = []
                    redTeam = []
                    rankedOrder = [] 
                    redRank = 0
                    blueRank = 0
                    totalRank = 0
                    half = 0
                    for j in eligiblePlayers:
                        totalRank += int(ELOpop[j][1])
                    half = int(totalRank / 2)
                    
                    if(playerCount <= 8):
                        if("303845825476558859" in eligiblePlayers and "120411697184768000" in eligiblePlayers):
                            for i in list(combos):
                                blueRank = 0
                                for j in list(i):
                                    blueRank += int(ELOpop[j][1])
                                    if("303845825476558859" in i and "120411697184768000" in i):
                                        rankedOrder.append((list(i), abs(blueRank - half)))
                                #print((list(i), abs(blueRank - half)))
                            rankedOrder = sorted(rankedOrder, key=lambda x: x[1])
                        else:   
                            for i in list(combos):
                                blueRank = 0
                                for j in list(i):
                                    blueRank += int(ELOpop[j][1])
                                rankedOrder.append((list(i), abs(blueRank - half)))
                                #print((list(i), abs(blueRank - half)))
                            rankedOrder = sorted(rankedOrder, key=lambda x: x[1])
                    elif(playerCount > 8):
                        teamList = []
                        for i in range(100):
                            rTeam = random.choice(combos)
                            teamList.append(rTeam)
                            combos.remove(rTeam)
                        for i in list(teamList):
                            blueRank = 0
                            for j in list(i):
                                blueRank += int(ELOpop[j][1])
                            rankedOrder.append((list(i), abs(blueRank - half)))
                            #print((list(i), abs(blueRank - half)))
                        rankedOrder = sorted(rankedOrder, key=lambda x: x[1])
                        
                    for i in rankedOrder:
                        print(i)
                    blueTeam = list(rankedOrder[0][0])

                    for j in eligiblePlayers:
                        if(j not in blueTeam):
                            redTeam.append(j)
                    blueRank = 0
                    for j in blueTeam:
                        blueRank += int(ELOpop[j][1])
                    diff = abs(blueRank - half)
                    print(blueTeam, diff)
                    for j in redTeam:
                        redRank += int(ELOpop[j][1])
                    diff = abs(redRank - half)
                    print(redTeam, diff)  
                    team1prob = round(1/(1+10**((redRank - blueRank)/400)), 2)
                    team2prob = round(1/(1+10**((blueRank - redRank)/400)), 2)
                    await teamsDisplay(channel2, blueTeam, redTeam, team1prob, team2prob)
                    for i in eligiblePlayers:
                        DMList.append(f"<@{i}> ")
                        
                    dmMsg = "".join(DMList)
                    await channel2.send(dmMsg)
                    #await ctx.send("Please react to the map you want to play on..")
                    await channel2.send("Please react to the server you want to play on..")
                    serverVote = 1
                    await voteSetup()
                    fTimer = 5
                    fVCoolDown.start()
                    inVote = 1
                
                elif(len(capList) >= 2):
                    #print("will use capts")
                    with open('ELOpop.json') as f:
                        ELOpop = json.load(f)    
                    playerCount = int(playerCount)
                    if(len(playersAdded) == playerCount):
                        eligiblePlayers = playersAdded
                    else:    
                        eligiblePlayers = playersAdded[0:playerCount * 2]
                    captMode = 1
                    DMList = []
                    for i in eligiblePlayers:
                        DMList.append(f"<@{i}> ")
                        
                    dmMsg = "".join(DMList)
                    await channel2.send(dmMsg)
                    #await ctx.send("Please react to the map you want to play on..")
                    await channel2.send("Please react to the server you want to play on..")
                    serverVote = 1
                    await voteSetup()
                    fTimer = 5
                    fVCoolDown.start()
                    inVote = 1
        else:
            await channel2.send("you dont have enough people for that game size..")

@client.command(pass_context=True)
@commands.has_role(v['runner'])
async def teams(ctx, playerCount = 4):
    if(ctx.channel.name == v['pc']):    
        global playersAdded
        global capList
        global inVote
        global blueTeam
        global redTeam
        global inVote
        global eligiblePlayers
        global fTimer
        global oMsg
        global captMode
        global serverVote
        global rankedOrder
        global ready
        #global pastTeams
        ready = []
        oMsg = None
        DMList = []
        channel2 = client.fetch_channel(v['pID'])
        print("test1")
        if(len(playersAdded) >= int(playerCount * 2)):
            print("test2")
            if(inVote == 0):
                print("test3")
                if(len(capList) < 2):  
                    with open('ELOpop.json') as f:
                        ELOpop = json.load(f)    
                    playerCount = int(playerCount)
                    if(len(playersAdded) == playerCount):
                        eligiblePlayers = playersAdded
                    else:    
                        eligiblePlayers = playersAdded[0:playerCount * 2]
                    counter = 0
                    teamsPicked = 0
                    
                    combos = list(itertools.combinations(eligiblePlayers, int(len(eligiblePlayers) / 2)))
                    random.shuffle(combos)
                    
                    for i in eligiblePlayers:
                        if i in playersAdded:
                            playersAdded.remove(i)
                    #print(playersAdded)
                    #while teamsPicked == 0:
                    blueTeam = []
                    redTeam = []
                    rankedOrder = [] 
                    redRank = 0
                    blueRank = 0
                    totalRank = 0
                    half = 0
                    for j in eligiblePlayers:
                        totalRank += int(ELOpop[j][1])
                    half = int(totalRank / 2)
                    
                    if(playerCount <= 8):
                        if("303845825476558859" in eligiblePlayers and "120411697184768000" in eligiblePlayers):
                            for i in list(combos):
                                blueRank = 0
                                for j in list(i):
                                    blueRank += int(ELOpop[j][1])
                                    if("303845825476558859" in i and "120411697184768000" in i):
                                        rankedOrder.append((list(i), abs(blueRank - half)))
                                #print((list(i), abs(blueRank - half)))
                            rankedOrder = sorted(rankedOrder, key=lambda x: x[1])
                        else:   
                            for i in list(combos):
                                blueRank = 0
                                for j in list(i):
                                    blueRank += int(ELOpop[j][1])
                                rankedOrder.append((list(i), abs(blueRank - half)))
                                #print((list(i), abs(blueRank - half)))
                            rankedOrder = sorted(rankedOrder, key=lambda x: x[1])
                    elif(playerCount > 8):
                        teamList = []
                        for i in range(100):
                            rTeam = random.choice(combos)
                            teamList.append(rTeam)
                            combos.remove(rTeam)
                        for i in list(teamList):
                            blueRank = 0
                            for j in list(i):
                                blueRank += int(ELOpop[j][1])
                            rankedOrder.append((list(i), abs(blueRank - half)))
                            #print((list(i), abs(blueRank - half)))
                        rankedOrder = sorted(rankedOrder, key=lambda x: x[1])
                        
                    for i in rankedOrder:
                        print(i)
                    blueTeam = list(rankedOrder[0][0])

                    for j in eligiblePlayers:
                        if(j not in blueTeam):
                            redTeam.append(j)
                    blueRank = 0
                    for j in blueTeam:
                        blueRank += int(ELOpop[j][1])
                    diff = abs(blueRank - half)
                    print(blueTeam, diff)
                    for j in redTeam:
                        redRank += int(ELOpop[j][1])
                    diff = abs(redRank - half)
                    print(redTeam, diff)  
                    team1prob = round(1/(1+10**((redRank - blueRank)/400)), 2)
                    team2prob = round(1/(1+10**((blueRank - redRank)/400)), 2)
                    await teamsDisplay(ctx, blueTeam, redTeam, team1prob, team2prob)
                    for i in eligiblePlayers:
                        DMList.append(f"<@{i}> ")
                        
                    dmMsg = "".join(DMList)
                    await ctx.send(dmMsg)
                    #await ctx.send("Please react to the map you want to play on..")
                    await ctx.send("Please react to the server you want to play on..")
                    serverVote = 1
                    await voteSetup()
                    fTimer = 5
                    fVCoolDown.start()
                    inVote = 1
                
                elif(len(capList) >= 2):
                    #print("will use capts")
                    with open('ELOpop.json') as f:
                        ELOpop = json.load(f)    
                    playerCount = int(playerCount)
                    if(len(playersAdded) == playerCount):
                        eligiblePlayers = playersAdded
                    else:    
                        eligiblePlayers = playersAdded[0:playerCount * 2]
                    captMode = 1
                    DMList = []
                    for i in eligiblePlayers:
                        DMList.append(f"<@{i}> ")
                        
                    dmMsg = "".join(DMList)
                    await ctx.send(dmMsg)
                    #await ctx.send("Please react to the map you want to play on..")
                    await ctx.send("Please react to the server you want to play on..")
                    serverVote = 1
                    await voteSetup()
                    fTimer = 5
                    fVCoolDown.start()
                    inVote = 1
        else:
            await ctx.send("you dont have enough people for that game size..")

'''@client.command(pass_context=True)
@commands.has_role(v['runner'])
async def teams(ctx, playerCount = 4):
    if(ctx.channel.name == v['pc']):    
        global playersAdded
        global capList
        global inVote
        global blueTeam
        global redTeam
        global inVote
        global eligiblePlayers
        global fTimer
        global captMode
        global serverVote

        if(len(playersAdded) >= int(playerCount * 2)):
            if(inVote == 0):
                if(len(capList) < 2):    
                    with open('ELOpop.json') as f:
                        ELOpop = json.load(f)    
                    playerCount = int(playerCount)
                    if(len(playersAdded) == playerCount):
                        eligiblePlayers = playersAdded
                    else:    
                        eligiblePlayers = playersAdded[0:playerCount * 2]
                    counter = 0
                    teamsPicked = 0
                    
                    combos = list(itertools.combinations(eligiblePlayers, int(len(eligiblePlayers) / 2)))
                    random.shuffle(combos)
                    
                    for i in eligiblePlayers:
                        if i in playersAdded:
                            playersAdded.remove(i)
                    #print(playersAdded)
                    while teamsPicked == 0:
                        blueTeam = []
                        redTeam = [] 
                        redRank = 0
                        blueRank = 0
                        totalRank = 0
                        half = 0
                        diff = 0   
                        for i in range(len(combos)):
                            for j in eligiblePlayers:
                                totalRank += int(ELOpop[j][1])
                            half = int(totalRank / 2)
                            blueTeam = list(combos[i])
                            for j in eligiblePlayers:
                                if(j not in blueTeam):
                                    redTeam.append(j)

                            for j in blueTeam:
                                blueRank += int(ELOpop[j][1])
                            for j in redTeam:
                                redRank += int(ELOpop[j][1])    
                            
                            diff = abs(blueRank - half)
                            if(diff <= counter):
                                if((len(blueTeam) == playerCount) and (len(redTeam) == playerCount)):
                                    #print(blueTeam, blueRank)
                                    #print(redTeam, redRank)
                                    teamsPicked = 1
                                    break
                            else:
                                blueTeam.clear()
                                redTeam.clear()
                                redRank = 0
                                blueRank = 0
                                totalRank = 0
                        if(playerCount * 2 <= 8):    
                            counter += 2
                        else:
                            counter += 20
                    
                    team1prob = round(1/(1+10**((redRank - blueRank)/400)), 2)
                    team2prob = round(1/(1+10**((blueRank - redRank)/400)), 2)
                    await teamsDisplay(ctx, blueTeam, redTeam, team1prob, team2prob)
                    await ctx.send("Please react to the server you want to play on..")
                    serverVote = 1
                    await voteSetup()
                    fTimer = 5
                    fVCoolDown.start()
                    inVote = 1
                
                elif(len(capList) >= 2):
                    #print("will use capts")
                    with open('ELOpop.json') as f:
                        ELOpop = json.load(f)    
                    playerCount = int(playerCount)
                    if(len(playersAdded) == playerCount):
                        eligiblePlayers = playersAdded
                    else:    
                        eligiblePlayers = playersAdded[0:playerCount * 2]
                    captMode = 1
                    await ctx.send("Please react to the server you want to play on..")
                    serverVote = 1
                    await voteSetup()
                    fTimer = 5
                    fVCoolDown.start()
                    inVote = 1
        else:
            await ctx.send("you dont have enough people for that game size..")'''

@client.command(pass_context=True)
@commands.has_role(v['runner'])
async def addp(ctx, number):
    if(ctx.channel.name == v['pc']):    
        global playersAdded
        global capList
        number = int(number)
        with open('ELOpop.json') as f:
            ELOpop = json.load(f)
        pickfrom = list(ELOpop)
        for i in range(number):

            player = random.choice(pickfrom)
            playersAdded.append(player)
            pickfrom.remove(player)

        await pickupDisplay(ctx)

@client.command(pass_context=True)
async def status(ctx):
    if(ctx.channel.name == v['pc']):
        await pickupDisplay(ctx)

@client.command(pass_context=True)
@commands.has_role(v['runner'])
async def next(ctx, player: discord.Member):
    if(ctx.channel.name == v['pc']):    
        global blueTeam
        global redTeam
        global playersAdded
        global eligiblePlayers

        eligiblePlayers = []
        for i in blueTeam:
            if(i != str(player.id)):
                eligiblePlayers.append(i)

        for i in redTeam:
            if(i != str(player.id)):
                eligiblePlayers.append(i)

        eligiblePlayers.append(playersAdded[0])
        playerCount = len(eligiblePlayers)
        counter = 0
        teamsPicked = 0
        #print(eligiblePlayers)
        combos = list(itertools.combinations(eligiblePlayers, int(playerCount / 2)))
        random.shuffle(combos)
        
        for i in eligiblePlayers:
            if i in playersAdded:
                playersAdded.remove(i)
        #print(playersAdded)
        while teamsPicked == 0:
            blueTeam = []
            redTeam = [] 
            redRank = 0
            blueRank = 0
            totalRank = 0
            half = 0
            diff = 0   
            for i in range(len(combos)):
                for j in eligiblePlayers:
                    totalRank += ELOpop[j][1]
                half = int(totalRank / 2)
                blueTeam = list(combos[i])
                for j in eligiblePlayers:
                    if(j not in blueTeam):
                        redTeam.append(j)

                for j in blueTeam:
                    blueRank += ELOpop[j][1]
                for j in redTeam:
                    redRank += ELOpop[j][1]    
                
                diff = abs(blueRank - half)
                if(diff <= counter):
                    if((len(blueTeam) == playerCount / 2) and (len(redTeam) == playerCount / 2)):
                        #print(blueTeam, blueRank)
                        #print(redTeam, redRank)
                        teamsPicked = 1
                        break
                else:
                    blueTeam.clear()
                    redTeam.clear()
                    redRank = 0
                    blueRank = 0
                    totalRank = 0
            if(playerCount <= 8):    
                counter += 5
            else:
                counter += 20
        team1prob = round(1/(1+10**((redRank - blueRank)/400)), 2)
        team2prob = round(1/(1+10**((blueRank - redRank)/400)), 2)
        await teamsDisplay(ctx, blueTeam, redTeam, team1prob, team2prob)

@client.command(pass_context=True)
@commands.has_role(v['runner'])
async def sub(ctx, playerout: discord.Member, playerin: discord.Member, number = "None"):
    if(ctx.channel.name == v['pc']):    
        with open('activePickups.json') as f:
            activePickups = json.load(f)
        '''global eligiblePlayers
        global blueTeam
        global redTeam
        global playersAdded'''
        if(number == "None"):
            global eligiblePlayers
            global blueTeam
            global redTeam
            global playersAdded    
            eligiblePlayers = []
            for i in blueTeam:
                if(i != str(playerout.id)):
                    eligiblePlayers.append(i)

            for i in redTeam:
                if(i != str(playerout.id)):
                    eligiblePlayers.append(i)

            eligiblePlayers.append(str(playerin.id))
            #eligiblePlayers.remove(str(playerout.id))
            playerCount = len(eligiblePlayers)
            counter = 0
            teamsPicked = 0
            #print(eligiblePlayers)
            
            combos = list(itertools.combinations(eligiblePlayers, int(len(eligiblePlayers) / 2)))
            random.shuffle(combos)

            if(str(playerin.id) in playersAdded):
                playersAdded.remove(str(playerin.id))
            
            for i in eligiblePlayers:
                if i in playersAdded:
                    playersAdded.remove(i)
            #print(playersAdded)
            #while teamsPicked == 0:
            blueTeam = []
            redTeam = []
            rankedOrder = [] 
            redRank = 0
            blueRank = 0
            totalRank = 0
            half = 0
            for j in eligiblePlayers:
                totalRank += int(ELOpop[j][1])
            half = int(totalRank / 2)  
                
            for i in list(combos):
                blueRank = 0
                for j in list(i):
                    blueRank += int(ELOpop[j][1])
                rankedOrder.append((list(i), abs(blueRank - half)))
                #print((list(i), abs(blueRank - half)))
            rankedOrder = sorted(rankedOrder, key=lambda x: x[1])
            for i in rankedOrder:
                print(i)
            blueTeam = list(rankedOrder[0][0])

            for j in eligiblePlayers:
                if(j not in blueTeam):
                    redTeam.append(j)
            blueRank = 0
            for j in blueTeam:
                blueRank += int(ELOpop[j][1])
            diff = abs(blueRank - half)
            print(blueTeam, diff)
            for j in redTeam:
                redRank += int(ELOpop[j][1])
            diff = abs(redRank - half)
            print(redTeam, diff)  
            team1prob = round(1/(1+10**((redRank - blueRank)/400)), 2)
            team2prob = round(1/(1+10**((blueRank - redRank)/400)), 2)
            await teamsDisplay(ctx, blueTeam, redTeam, team1prob, team2prob)
        elif(number != "None"):    
            eligiblePlayers = []
            playerIn = str(playerin.id)
            playerOut = str(playerout.id)
            blueTeam = activePickups[number][2]
            redTeam = activePickups[number][5]
            '''for i in blueTeam:
                if(i != str(playerout.id)):
                    eligiblePlayers.append(i)

            for i in redTeam:
                if(i != str(playerout.id)):
                    eligiblePlayers.append(i)'''
            eligiblePlayers = blueTeam + redTeam
            print(eligiblePlayers)
            eligiblePlayers.remove(playerOut)
            eligiblePlayers.append(playerIn)

            #eligiblePlayers.append(str(playerin.id))
            #eligiblePlayers.remove(str(playerout.id))
            playerCount = len(eligiblePlayers)
            counter = 0
            teamsPicked = 0
            #print(eligiblePlayers)
            combos = list(itertools.combinations(eligiblePlayers, int(len(eligiblePlayers) / 2)))
            random.shuffle(combos)
            
            for i in eligiblePlayers:
                if i in playersAdded:
                    playersAdded.remove(i)
            #print(playersAdded)
            #while teamsPicked == 0:
            blueTeam = []
            redTeam = []
            rankedOrder = [] 
            redRank = 0
            blueRank = 0
            totalRank = 0
            half = 0
            for j in eligiblePlayers:
                totalRank += int(ELOpop[j][1])
            half = int(totalRank / 2)  
                
            for i in list(combos):
                blueRank = 0
                for j in list(i):
                    blueRank += int(ELOpop[j][1])
                rankedOrder.append((list(i), abs(blueRank - half)))
                #print((list(i), abs(blueRank - half)))
            rankedOrder = sorted(rankedOrder, key=lambda x: x[1])
            for i in rankedOrder:
                print(i)
            blueTeam = list(rankedOrder[0][0])

            for j in eligiblePlayers:
                if(j not in blueTeam):
                    redTeam.append(j)
            blueRank = 0
            for j in blueTeam:
                blueRank += int(ELOpop[j][1])
            diff = abs(blueRank - half)
            print(blueTeam, diff)
            for j in redTeam:
                redRank += int(ELOpop[j][1])
            diff = abs(redRank - half)
            print(redTeam, diff)  
            team1prob = round(1/(1+10**((redRank - blueRank)/400)), 2)
            team2prob = round(1/(1+10**((blueRank - redRank)/400)), 2)
            activePickups[number] = [team1prob, blueRank, blueTeam, team2prob, redRank, redTeam, activePickups[number][6], activePickups[number][7], activePickups[number][8]]
            with open('activePickups.json', 'w') as cd:
                json.dump(activePickups, cd,indent= 4) 
            await teamsDisplay(ctx, blueTeam, redTeam, team1prob, team2prob)

@client.command(pass_context=True)
@commands.has_role(v['runner'])
async def draw(ctx, pNumber = "None"):
    global ELOpop
    if(ctx.channel.name == v['pc']):    
        with open('activePickups.json') as f:
            activePickups = json.load(f)
        with open('ELOpop.json') as f:
            ELOpop = json.load(f)
        with open('pastten.json') as f:
            pastTen = json.load(f)

        if(pNumber == "None"):
            pNumber = list(activePickups)[-1]

        #print(activePickups[pNumber][2])
        blueTeam = activePickups[pNumber][2]
        redTeam = activePickups[pNumber][5]
        blueProb = activePickups[pNumber][0]
        blueRank = activePickups[pNumber][1]
        redProb = activePickups[pNumber][3]
        redRank = activePickups[pNumber][4]
        adjustTeam1 = 0
        adjustTeam2 = 0
        
        adjustTeam1 = int(blueRank + 50 * (.5 - blueProb)) - blueRank
        adjustTeam2 = int(redRank + 50 * (.5 - redProb)) - redRank
        for i in blueTeam:
            ELOpop[i][1] += adjustTeam1
            #if(int(ELOpop[i][1]) > 2599):
                #ELOpop[i][1] = 2599
            if(int(ELOpop[i][1]) < 0):
                ELOpop[i][1] = 0    
            ELOpop[i][2].append([int(ELOpop[i][1]), pNumber])
            ELOpop[i][6] += 1
            if(ELOpop[i][3] != "<:norank:1001265843683987487>"):
                newRank(i)
            #print(ELOpop[i][2])
        for i in redTeam:
            #print(type(ELOpop[i][1]))
            #print(ELOpop)
            ELOpop[i][1] += adjustTeam2
            #if(int(ELOpop[i][1]) > 2599):
                #ELOpop[i][1] = 2599
            if(int(ELOpop[i][1]) < 0):
                ELOpop[i][1] = 0
            ELOpop[i][2].append([int(ELOpop[i][1]), pNumber])
            ELOpop[i][6] += 1
            if(ELOpop[i][3] != "<:norank:1001265843683987487>"):
                newRank(i)

        if(len(list(pastTen)) >= 10):
            while (len(list(pastTen)) > 9):
                ID = list(pastTen)[0]
                del pastTen[ID]
        
        pastTen[pNumber] = [blueTeam, blueProb, adjustTeam1, blueRank, redTeam, redProb, adjustTeam2, redRank, 0, activePickups[pNumber][7]] #winningTeam, team1prob, adjustmentTeam1, losingteam, team2prob, adjustmentTeam2    
        del activePickups[pNumber]
        with open('activePickups.json', 'w') as cd:
            json.dump(activePickups, cd,indent= 4)
        with open('ELOpop.json', 'w') as cd:
            json.dump(ELOpop, cd,indent= 4)
        with open('pastten.json', 'w') as cd:
            json.dump(pastTen, cd,indent= 4)
        
        await ctx.send("Match reported.. thank you!")

@client.command(pass_context=True)
@commands.has_role(v['runner'])
async def win(ctx, team, pNumber = "None"):
    global ELOpop
    if((ctx.channel.name == v['pc']) or (ctx.channel.name == 'tfc-admins') or (ctx.channel.name == 'tfc-runners')):    
        with open('activePickups.json') as f:
            activePickups = json.load(f)
        with open('ELOpop.json') as f:
            ELOpop = json.load(f)
        with open('pastten.json') as f:
            pastTen = json.load(f)
        if(pNumber == "None"):
            pNumber = list(activePickups)[-1]

        #print(activePickups[pNumber][2])
        blueTeam = activePickups[pNumber][2]
        redTeam = activePickups[pNumber][5]
        blueProb = activePickups[pNumber][0]
        blueRank = activePickups[pNumber][1]
        redProb = activePickups[pNumber][3]
        redRank = activePickups[pNumber][4]
        adjustTeam1 = 0
        adjustTeam2 = 0
        winner = 0
        if(team == "1"):
            adjustTeam1 = int(blueRank + 50 * (1 - blueProb)) - blueRank
            adjustTeam2 = int(redRank + 50 * (0 - redProb)) - redRank
            winner = 1
        if(team == "2"):
            adjustTeam1 = int(blueRank + 50 * (0 - blueProb)) - blueRank
            adjustTeam2 = int(redRank + 50 * (1 - redProb)) - redRank
            winner = 2
        if(team == "draw"):
            adjustTeam1 = int(blueRank + 50 * (.5 - blueProb)) - blueRank
            adjustTeam2 = int(redRank + 50 * (.5 - redProb)) - redRank
        for i in blueTeam:
            ELOpop[i][1] += adjustTeam1
            #if(int(ELOpop[i][1]) > 2599):
                #ELOpop[i][1] = 2599
            if(int(ELOpop[i][1]) < 0):
                ELOpop[i][1] = 0    
            ELOpop[i][2].append([int(ELOpop[i][1]), pNumber])
            if(team == "1"):
                ELOpop[i][4] += 1
            if(team == "2"):
                ELOpop[i][5] += 1
            if(team == "draw"):
                ELOpop[i][6] += 1
            if(ELOpop[i][3] != "<:norank:1001265843683987487>"):
                newRank(i)
            #print(ELOpop[i][2])
        for i in redTeam:
            #print(type(ELOpop[i][1]))
            #print(ELOpop)
            ELOpop[i][1] += adjustTeam2
            #if(int(ELOpop[i][1]) > 2599):
                #ELOpop[i][1] = 2599
            if(int(ELOpop[i][1]) < 0):
                ELOpop[i][1] = 0
            ELOpop[i][2].append([int(ELOpop[i][1]), pNumber])
            if(team == "1"):
                ELOpop[i][5] += 1
            if(team == "2"):
                ELOpop[i][4] += 1
            if(team == "draw"):
                ELOpop[i][6] += 1
            if(ELOpop[i][3] != "<:norank:1001265843683987487>"):
                print(i)
                newRank(i)
        

        if(len(list(pastTen)) >= 10):
            while (len(list(pastTen)) > 9):
                ID = list(pastTen)[0]
                del pastTen[ID]
        
        pastTen[pNumber] = [blueTeam, blueProb, adjustTeam1, blueRank, redTeam, redProb, adjustTeam2, redRank, winner, activePickups[pNumber][7]] #winningTeam, team1prob, adjustmentTeam1, losingteam, team2prob, adjustmentTeam2
        del activePickups[pNumber]
        
        with open('activePickups.json', 'w') as cd:
            json.dump(activePickups, cd,indent= 4)
        with open('ELOpop.json', 'w') as cd:
            json.dump(ELOpop, cd,indent= 4)
        with open('pastten.json', 'w') as cd:
            json.dump(pastTen, cd,indent= 4)
        
        pastTen[pNumber] = []

        await ctx.send("Match reported.. thank you!")

@client.command(pass_context = True)
@commands.has_role(v['runner'])
async def tfc(ctx, person: discord.Member):
    #print("hello")
    role = get(person.guild.roles, name="TFC Player")
    await person.add_roles(role)
    await ctx.author.send(f"You have given {person.display_name} the TFC Player role and they can now add to pickups")

@client.command(pass_context=True)
@commands.has_role(v['runner'])
async def reg(ctx, player:discord.Member):
    if(ctx.channel.name == v['pc']):
        with open('ELOpop.json') as f:
            ELOpop = json.load(f)
        playerID = str(player.id)
        playerName = player.display_name

        ELOpop[playerID] = [playerName, 800, [], "<:questionMark:972369805359337532>", 0, 0, 0, []]

        with open('ELOpop.json', 'w') as cd:
            json.dump(ELOpop, cd,indent= 4)
        await ctx.send(f"{playerName} added")

@client.command(pass_context=True)
@commands.has_role(v['runner'])
async def undo(ctx, pNumber = "None"):
    with open('pastten.json') as f:
        pastTen = json.load(f)
    with open('ELOpop.json') as f:
        ELOpop = json.load(f)
    with open('activePickups.json') as f:
            activePickups = json.load(f)

    blueTeam = pastTen[pNumber][0]
    redTeam = pastTen[pNumber][4]
    winningTeam = pastTen[pNumber][8]
    team1Adjust = pastTen[pNumber][2]
    team2Adjust = pastTen[pNumber][6]

    
    
    for i in blueTeam:
        ELOpop[i][1] += -1 * team1Adjust
        if(winningTeam == 1):
            ELOpop[i][4] += -1
        elif(winningTeam == 2):
            ELOpop[i][5] += -1
        elif(winningTeam == 0):
            ELOpop[i][6] += -1
        for j in list(ELOpop[i][2]):
            if(j[1] == pNumber):
                ELOpop[i][2].remove(j)
    
    for i in redTeam:
        ELOpop[i][1] += -1 * team2Adjust
        if(winningTeam == 2):
            ELOpop[i][4] += -1
        elif(winningTeam == 1):
            ELOpop[i][5] += -1
        elif(winningTeam == 0):
            ELOpop[i][6] += -1
        for j in list(ELOpop[i][2]):
            if(j[1] == pNumber):
                ELOpop[i][2].remove(j)

                
    #pastTen[pNumber] = [blueTeam, blueProb, adjustTeam1, blueRank, redTeam, redProb, adjustTeam2, redRank, winner, activePickups[pNumber][7]]
    activePickups[pNumber] = [pastTen[pNumber][1], pastTen[pNumber][3], blueTeam, pastTen[pNumber][5], pastTen[pNumber][7], redTeam, "None", pastTen[pNumber][9], "None"]

    await ctx.send(f"Match Number {pNumber} has been undone")
    del pastTen[pNumber]
    with open('activePickups.json', 'w') as cd:
            json.dump(activePickups, cd,indent= 4)
    with open('ELOpop.json', 'w') as cd:
        json.dump(ELOpop, cd,indent= 4)
    with open('pastten.json', 'w') as cd:
        json.dump(pastTen, cd,indent= 4)

@client.command(pass_context=True)
async def games(ctx):
    if((ctx.channel.name == v['pc']) or (ctx.channel.name == 'tfc-admins') or (ctx.channel.name == 'tfc-runners')):    
        await openPickups(ctx)

@client.command(pass_context=True)
async def recent(ctx):
    if((ctx.channel.name == v['pc']) or (ctx.channel.name == 'tfc-admins') or (ctx.channel.name == 'tfc-runners')):
        await pastGames(ctx)

@client.command(pass_context=True)
async def checkgame(ctx, number):
    if((ctx.channel.name == v['pc']) or (ctx.channel.name == 'tfc-admins') or (ctx.channel.name == 'tfc-runners')):   
        with open('activePickups.json') as f:
            activePickups = json.load(f)
        with open('ELOpop.json') as f:
            ELOpop = json.load(f)
        msgList = []
        blueTeam = activePickups[number][2]
        redTeam = activePickups[number][5]

        for i in blueTeam:
            msgList.append(ELOpop[i][3] + " " + ELOpop[i][0] + "\n")
        bMsg = "".join(msgList)
        msgList.clear()
        for i in redTeam:
            msgList.append(ELOpop[i][3] + " " + ELOpop[i][0] + "\n")
        rMsg = "".join(msgList)
        embed = discord.Embed(title = "Teams Sorted!")
        embed.add_field(name = "Blue Team <:blueLogo:971294076676763699>", value= bMsg, inline=True)
        embed.add_field(name="\u200b", value = "\u200b")
        embed.add_field(name = "Red Team <:redLogo:971296302803587082>", value= rMsg, inline=True)
        await ctx.send(embed = embed)

@client.command(pass_context=True)
@commands.has_role(v['runner'])
async def removegame(ctx, number):
    if(ctx.channel.name == v['pc']):    
        with open('activePickups.json') as f:
            activePickups = json.load(f)

        del activePickups[number]

        with open('activePickups.json', 'w') as cd:
            json.dump(activePickups, cd,indent= 4)
        
        await ctx.send("Game has been removed..")

@client.command(pass_context=True)
@commands.has_role(v['runner'])
async def cancel(ctx):
    if(ctx.channel.name == v['pc']):
        global playersAdded

        playersAdded.clear()
        DePopulatePickup()
        await ctx.send("Queue has been cancelled..")

@client.command(pass_context = True)
@commands.has_role(v['runner'])
async def requeue(ctx):
    global blueTeam
    global redTeam
    global playersAdded
    
    neligibleplayers = blueTeam + redTeam
    #print(neligibleplayers)
    DePopulatePickup()
    #print(neligibleplayers)
    playersAdded = neligibleplayers.copy() + playersAdded
    neligibleplayers.clear()
    #print(playersAdded)
    await pickupDisplay(ctx)

@client.command(aliases=['fv'])
@commands.cooldown(1, 3, commands.BucketType.default)
@commands.has_role(v['runner'])
async def forceVote(channel):
    channel = await client.fetch_channel(v['pID'])
    if(channel.name == v['pc']):
        global mapVotes
        global mapChoice4
        global mapChoice3
        global mapChoice2
        global mapChoice1
        global winningIP
        global serverVote
        global eligiblePlayers
        global pTotalPlayers
        global inVote
        global reVote
        global captMode
        global pMsg
        global cap1
        global cap1Name
        global cap2
        global fTimer
        global cap2Name
        global winningMap
        global winningServer
        global alreadyVoted
        global lastFive
        global vMsg
        print("executed")
        winningMap = None
        with open('activePickups.json') as f:
            activePickups = json.load(f)
        alreadyVoted = []
        if(serverVote == 1):
            votes = [len(mapVotes[mapChoice1]), len(mapVotes[mapChoice2]), len(mapVotes[mapChoice3])]
            windex = votes.index(max(votes))
            if(windex == 0):
                await channel.send("West (Las Vegas) server is being launched..")
                r = requests.get("https://us-west1-coachoffice-332119.cloudfunctions.net/startWest")
                winningIP = "NONE"
                winningServer = "NONE"
                serverVote = 0
                #alreadyVoted = []
                #activePickups[list(activePickups)[-1]][8] = "West"
            elif(windex == 1):
                #await channel.send("Central (Iowa) server is being launched..")
                #r = requests.get("https://us-central1-coachoffice-332119.cloudfunctions.net/startCentral-1")
                winningIP = "steam://connect/coachcent.game.nfoservers.com:27015/letsplay!"
                winningServer = "Central (Chi)"
                serverVote = 0
                #alreadyVoted = []
            elif(windex == 2):
                #await channel.send("East (N. Virginia) server is being launched..")
                #r = requests.get("https://us-east4-coachoffice-332119.cloudfunctions.net/startEast")
                winningIP = "steam://connect/coach.game.nfoservers.com:27015/letsplay!"
                winningServer = "East (NY)"
                serverVote = 0
                #alreadyVoted = []
            fTimer = 3
            await voteSetup()
        elif(serverVote == 0):
            votes = [len(mapVotes[mapChoice4]), len(mapVotes[mapChoice1]), len(mapVotes[mapChoice2]), len(mapVotes[mapChoice3])]
            windex = votes.index(max(votes))
            if(windex == 0):
                if(mapChoice4 == "New Maps"):
                    reVote = 1    
                    del votes[0]
                    windex = votes.index(max(votes))
                    if(windex == 0):
                        mapChoice4 = mapChoice1
                    if(windex == 1):
                        mapChoice4 = mapChoice2
                    if(windex == 2):
                        mapChoice4 = mapChoice3
                    #alreadyVoted = []
                    await channel.send("New maps has won, now selecting new maps..")
                    fTimer = 3
                    await voteSetup()
                else:
                    await channel.send(f"The winning map is **{mapChoice4}** and will be played at {winningIP}")
                    fVCoolDown.stop()
                    
                    inVote = 0
                    winningMap = mapChoice4
                    if(len(lastFive) >= 5):
                        lastFive.remove(lastFive[0])
                    lastFive.append(mapChoice4)
                    if(captMode == 0):
                        savePickup()
                        DePopulatePickup()
            elif(windex == 1):
                await channel.send(f"The winning map is **{mapChoice1}** and will be played at {winningIP}")
                fVCoolDown.stop()
                inVote = 0
                winningMap = mapChoice1
                if(len(lastFive) >= 5):
                    lastFive.remove(lastFive[0])
                lastFive.append(mapChoice1)
                if(captMode == 0):
                    savePickup()
                    DePopulatePickup()
            elif(windex == 2):
                await channel.send(f"The winning map is **{mapChoice2}** and will be played at {winningIP}")
                fVCoolDown.stop()
                inVote = 0
                winningMap = mapChoice2
                if(len(lastFive) >= 5):
                    lastFive.remove(lastFive[0])
                lastFive.append(mapChoice2)
                if(captMode == 0):
                    savePickup()
                    DePopulatePickup()
            elif(windex == 3):
                await channel.send(f"The winning map is **{mapChoice3}** and will be played at {winningIP}")
                fVCoolDown.stop()
                inVote = 0
                
                winningMap = mapChoice3
                if(len(lastFive) >= 5):
                    lastFive.remove(lastFive[0])
                lastFive.append(mapChoice3)
                if(captMode == 0):
                    savePickup()
                    DePopulatePickup()
            
        if(inVote == 0 and captMode == 1):
            with open('ELOpop.json') as f:
                ELOpop = json.load(f)
            for i in eligiblePlayers:
                if(i not in capList):
                    pTotalPlayers.append(ELOpop[i][0])
            cap1 = random.choice(capList)
            capList.remove(cap1)
            cap1Name = ELOpop[str(cap1)][0]
            cap2 = random.choice(capList)
            capList.remove(cap2)
            cap2Name = ELOpop[str(cap2)][0]
            
            redTeam.append(cap1Name)
            blueTeam.append(cap2Name)
            pTotalPlayers = list(enumerate(pTotalPlayers, 1))
            TeamPickPopulate()
            pMsg = await channel.send("```" + str(cap1Name) + " and " + str(cap2Name) + " are the captains.\n\n" + msg + "```")
            await pMsg.add_reaction("1️⃣")
            await pMsg.add_reaction("2️⃣")
            await pMsg.add_reaction("3️⃣")
            await pMsg.add_reaction("4️⃣")
            await pMsg.add_reaction("5️⃣")
            await pMsg.add_reaction("6️⃣")
            
@client.command(pass_context=True)
@commands.has_role(v['runner'])
async def shufflee(ctx, idx = None, game = "None"):
    #global sMsg
    #if(ctx.channel.name == v['pc']):
    if(idx == None):
        idx = random.randint(1, 11)
    with open('activePickups.json') as f:
        activePickups = json.load(f)
    with open('ELOpop.json') as f:
            ELOpop = json.load(f)
    global rankedOrder
    global blueTeam
    global redTeam
    global team1prob
    global team2prob
    global blueRank
    global redRank
    global tMsg
    if(game == "None"):
        blueRank = 0
        redRank = 0
        blueTeam = []
        redTeam = []
        print(rankedOrder)
        blueTeam = list(rankedOrder[int(idx)][0])
        for j in eligiblePlayers:
            if(j not in blueTeam):
                redTeam.append(j)
        for j in blueTeam:
            blueRank += int(ELOpop[j][1])
        for j in redTeam:
            redRank += int(ELOpop[j][1])  
        team1prob = round(1/(1+10**((redRank - blueRank)/400)), 2)
        team2prob = round(1/(1+10**((blueRank - redRank)/400)), 2)
        await teamsDisplay(ctx, blueTeam, redTeam, team1prob, team2prob)
    else:
        nblueTeam = activePickups[game][2]
        nredTeam = activePickups[game][5]
        neligiblePlayers = []
        for i in nblueTeam:
            neligiblePlayers.append(i)
        for i in nredTeam:
            neligiblePlayers.append(i)
            
        playerCount = len(neligiblePlayers)
        counter = 0
        teamsPicked = 0
        
        combos = list(itertools.combinations(neligiblePlayers, int(len(neligiblePlayers) / 2)))
        random.shuffle(combos)
        #print(neligiblePlayers)
        blueTeam = []
        redTeam = []
        rankedOrder = [] 
        redRank = 0
        blueRank = 0
        totalRank = 0
        half = 0
        diff = 0
        for j in neligiblePlayers:
            totalRank += int(ELOpop[j][1])
        half = int(totalRank / 2)   
        for i in list(combos):
            blueRank = 0
            for j in i:
                blueRank += int(ELOpop[j][1])
            rankedOrder.append((i, abs(blueRank - half)))
        rankedOrder = sorted(rankedOrder, key=lambda x: x[1])
        
        blueTeam = list(rankedOrder[int(idx)][0])
        for j in neligiblePlayers:
            if(j not in blueTeam):
                redTeam.append(j)
        blueRank = 0
        for j in blueTeam:
            blueRank += int(ELOpop[j][1])
        for j in redTeam:
            redRank += int(ELOpop[j][1])  
        team1prob = round(1/(1+10**((redRank - blueRank)/400)), 2)
        team2prob = round(1/(1+10**((blueRank - redRank)/400)), 2)
        #print(redTeam)
        await teamsDisplay(ctx, blueTeam, redTeam, team1prob, team2prob)
        activePickups[game][0] = team1prob
        activePickups[game][1] = blueRank
        activePickups[game][2] = blueTeam
        activePickups[game][3] = team2prob
        activePickups[game][4] = redRank
        activePickups[game][5] = redTeam

        with open('activepickups.json', 'w') as cd:
            json.dump(activePickups, cd,indent= 4)

@client.command(pass_context=True)
@commands.has_role(v['runner'])
async def shuffle(ctx, idx = None, game = "None"):
    #global sMsg
    global rankedOrder
    global blueTeam
    global redTeam
    global team1prob
    global team2prob
    global blueRank
    global redRank
    global tMsg
    #rankedOrder = []
    if(ctx.channel.name == v['pc']):
        if(idx == None):
            idx = random.randint(1, 11)
        with open('activePickups.json') as f:
            activePickups = json.load(f)
        with open('ELOpop.json') as f:
                ELOpop = json.load(f)
        
        if(game == "None"):
            blueRank = 0
            redRank = 0
            blueTeam = []
            redTeam = []
            print(rankedOrder)
            blueTeam = list(rankedOrder[int(idx)][0])
            for j in eligiblePlayers:
                if(j not in blueTeam):
                    redTeam.append(j)
            for j in blueTeam:
                blueRank += int(ELOpop[j][1])
            for j in redTeam:
                redRank += int(ELOpop[j][1])  
            team1prob = round(1/(1+10**((redRank - blueRank)/400)), 2)
            team2prob = round(1/(1+10**((blueRank - redRank)/400)), 2)
            await teamsDisplay(ctx, blueTeam, redTeam, team1prob, team2prob)
        else:
            rankedOrder = []
            nblueTeam = activePickups[game][2]
            nredTeam = activePickups[game][5]
            neligiblePlayers = []
            for i in nblueTeam:
                neligiblePlayers.append(i)
            for i in nredTeam:
                neligiblePlayers.append(i)
                
            playerCount = len(neligiblePlayers)
            counter = 0
            teamsPicked = 0
            
            combos = list(itertools.combinations(neligiblePlayers, int(len(neligiblePlayers) / 2)))
            random.shuffle(combos)
            #print(neligiblePlayers)
            blueTeam = []
            redTeam = []
            rankedOrder = [] 
            redRank = 0
            blueRank = 0
            totalRank = 0
            half = 0
            diff = 0
            for j in neligiblePlayers:
                totalRank += int(ELOpop[j][1])
            half = int(totalRank / 2)   
            for i in list(combos):
                blueRank = 0
                for j in i:
                    blueRank += int(ELOpop[j][1])
                rankedOrder.append((i, abs(blueRank - half)))
            rankedOrder = sorted(rankedOrder, key=lambda x: x[1])
            
            blueTeam = list(rankedOrder[int(idx)][0])
            for j in neligiblePlayers:
                if(j not in blueTeam):
                    redTeam.append(j)
            blueRank = 0
            for j in blueTeam:
                blueRank += int(ELOpop[j][1])
            for j in redTeam:
                redRank += int(ELOpop[j][1])  
            team1prob = round(1/(1+10**((redRank - blueRank)/400)), 2)
            team2prob = round(1/(1+10**((blueRank - redRank)/400)), 2)
            #print(redTeam)
            await teamsDisplay(ctx, blueTeam, redTeam, team1prob, team2prob)
            activePickups[game][0] = team1prob
            activePickups[game][1] = blueRank
            activePickups[game][2] = blueTeam
            activePickups[game][3] = team2prob
            activePickups[game][4] = redRank
            activePickups[game][5] = redTeam

            with open('activepickups.json', 'w') as cd:
                json.dump(activePickups, cd,indent= 4)

@client.command(pass_context=True)
@commands.cooldown(1, 300, commands.BucketType.default)
async def notice(ctx, anumber = 8):
    if(ctx.channel.name == v['pc']):    
        global playersAdded
        number = len(list(playersAdded))
        role = discord.utils.get(ctx.guild.roles, id=v['TFCPlayer'])

    await ctx.send(f"{role.mention} {number}/{anumber}")


'''@slash.slash(name="slap")
async def slap(ctx, player: discord.Member):
    await ctx.send(f"{ctx.author.display_name} slapped {player.display_name} around a bit with a large trout")'''

@client.event
async def on_reaction_add(reaction, user):
    if(not user.bot):    
        global vMsg
        global mapVotes
        global serverVote
        global inVote
        global eligiblePlayers
        global mapChoice1
        global mapChoice2
        global mapChoice3
        global mapChoice4
        global reVote
        global pMsg
        global votable
        global pickCount
        global cap1
        global playersAdded
        global ready
        global cap2
        global cap1Name
        global cap2Name
        global pTotalPlayers
        global blueTeam
        global redTeam
        global alreadyVoted

        if(reaction.message == pMsg):
            if((str(user.id) == cap1) or (str(user.id) == cap2)):
                if(reaction.emoji == '1️⃣'):
                    playerPicked = 1
                elif(reaction.emoji == '2️⃣'):
                    playerPicked = 2
                elif(reaction.emoji == '3️⃣'):
                    playerPicked = 3
                elif(reaction.emoji == '4️⃣'):
                    playerPicked = 4
                elif(reaction.emoji == '5️⃣'):
                    playerPicked = 5
                elif(reaction.emoji == '6️⃣'):
                    playerPicked = 6
                
                if(pickCount == 0 and str(user.id) == cap1):
                    for i in pTotalPlayers:
                        if playerPicked in i:
                            pTotalPlayers.remove(i)
                            redTeam.append(i[1])
                            pickCount += 1
                            TeamPickPopulate()
                            await pMsg.edit(content="```" + msg + "```")
                elif(pickCount == 1 and str(user.id) == cap2):
                    for i in pTotalPlayers:
                        if playerPicked in i:
                            pTotalPlayers.remove(i)
                            blueTeam.append(i[1])
                            pickCount += 1
                            TeamPickPopulate()
                            await pMsg.edit(content="```" + msg + "```")
                elif(pickCount == 2 and str(user.id) == cap1):
                    #print("recognized pick")
                    for i in pTotalPlayers:
                        if playerPicked in i:
                            pTotalPlayers.remove(i)
                            redTeam.append(i[1])
                            pickCount += 1
                            TeamPickPopulate()
                            await pMsg.edit(content="```" + msg + "```")
                elif(pickCount == 3 and str(user.id) == cap2):
                    #print("recognized pick")
                    for i in pTotalPlayers:
                        if playerPicked in i:
                            pTotalPlayers.remove(i)
                            blueTeam.append(i[1])
                            pickCount += 1
                            TeamPickPopulate()
                            await pMsg.edit(content="```" + msg + "```")
                            await reaction.message.remove_reaction(reaction, user)
                            await reaction.message.remove_reaction(reaction, pMsg)
                elif(pickCount == 4 and str(user.id) == cap2):
                    #print("recognized pick")
                    for i in pTotalPlayers:
                        if playerPicked in i:
                            pTotalPlayers.remove(i)
                            blueTeam.append(i[1])
                            redTeam.append(pTotalPlayers[0][1])
                            pTotalPlayers.remove(pTotalPlayers[0])
                            pickCount += 1
                            TeamPickPopulate()
                            
                            await reaction.message.channel.send("```Teams are done being picked!  Here are the teams:\n\n" + msg + "```")
                            await reaction.message.channel.send("Picking has ended.. join the server")
                            savePickup()
                            DePopulatePickup()
                            inVote = 0
                            reVote = 0
                            
                else:
                    await user.send("It is not your pick..")
                    await reaction.message.remove_reaction(reaction, user)
        if(reaction.message == oMsg):
            if(reaction.emoji == "👍"):
                with open('ELOpop.json') as f:
                    ELOpop = json.load(f)
                if(str(user.id) in playersAdded[0:8]):
                    ready.append(str(user.id))
                    if(len(ready) < 8):
                        msgList = []
                        for i in playersAdded:
                            if(i in capList):
                                msgList.append(ELOpop[i][3] + " " + ELOpop[i][0] + " " + v['cptimg'] + "\n")
                                #msgList.append(ELOpop[i][0] + " " + v['cptimg'] + "\n")
                            else:
                                msgList.append(ELOpop[i][3] + " " + ELOpop[i][0] + "\n")
                                #msgList.append(ELOpop[i][0] + "\n")
                        msg = "".join(msgList)
                        readyList = []
                        for i in ready:
                            readyList.append(f"{ELOpop[i][0]}\n")
                        rMsg = "".join(readyList)
                        embed = discord.Embed(title = "Pickup Has 8 or more Players")
                        if(len(playersAdded) > 0):
                            embed.add_field(name = f"Players Added - {len(playersAdded)} Queued", value= msg)
                        elif(len(playersAdded) == 0):
                            embed.add_field(name = "Players Added", value= "PUG IS EMPTY!")
                        embed.add_field(name = "Players Ready", value = rMsg)

                        await oMsg.edit(embed = embed)
                    elif(len(ready) == 8):
                        print("go!")
                        channel2 = await client.fetch_channel(reaction.message.channel.id)
                        await doteams(channel2)
                else:
                    await reaction.message.remove_reaction(reaction, user)
                    await user.send("You are not among the first 8 added...")

        if(reaction.message == vMsg):
            if(votable == 1):    
                if((reaction.emoji == '1️⃣') or (reaction.emoji == '2️⃣') or (reaction.emoji == '3️⃣') or (reaction.emoji == '4️⃣')):
                    with open('ELOpop.json') as f:
                        ELOpop = json.load(f)
                    playerCount = len(eligiblePlayers)
                    userID = str(user.id)
                    forceResults = 0
                    channel = await client.fetch_channel(reaction.message.channel.id)
                    playerName = ELOpop[str(userID)][0]
                    if(inVote == 1):
                        #print(eligiblePlayers)
                        if(userID in eligiblePlayers):
                            for i in list(mapVotes):
                                if playerName in mapVotes[i]:
                                    mapVotes[i].remove(playerName)
                            if(reaction.emoji == '1️⃣'):
                                mapVotes[mapChoice1].append(playerName)
                            if(reaction.emoji == '2️⃣'):
                                mapVotes[mapChoice2].append(playerName)
                            if(reaction.emoji == '3️⃣'):
                                mapVotes[mapChoice3].append(playerName)
                            if(reaction.emoji == '4️⃣'):
                                mapVotes[mapChoice4].append(playerName)
                            if(playerName not in alreadyVoted):    
                                alreadyVoted.append(userID)

                            playersAbstained = []
                            for i in eligiblePlayers:
                                if i not in alreadyVoted:
                                    playersAbstained.append(ELOpop[str(i)][0])
                            toVoteString = "```"
                            if len(playersAbstained) != 0:
                                toVoteString = "\n💩 " + ", ".join(playersAbstained) +  " need to vote 💩```"

                            with open('mainmaps.json') as f:
                                mapList = json.load(f)
                            with open('specmaps.json') as f:
                                mapList2 = json.load(f)
                            #print(mapVotes)   
                            if(serverVote == 1):    
                                await vMsg.edit(content="```Vote for your server!  Be quick, you only have 45 seconds to vote..\n\n"
                                                                    + "1️⃣ " + mapChoice1 + " " * (70 - len(mapChoice1)) + mapVoteOutput(mapChoice1) + "\n"
                                                                    + "2️⃣ " + mapChoice2 + " " * (70 - len(mapChoice2)) + mapVoteOutput(mapChoice2) + "\n"
                                                                    + "3️⃣ " + mapChoice3 + " " * (70 - len(mapChoice3)) + mapVoteOutput(mapChoice3)
                                                                    + toVoteString) 
                            elif(serverVote == 0):  
                                if(reVote == 0):    
                                    await vMsg.edit(content="```Vote up and make sure you hydrate!\n\n"
                                                    + "1️⃣ " + mapChoice1 + " " * (25 - len(mapChoice1)) + "   " + str(mapList[mapChoice1]) + " mirv" + " " * 15 + mapVoteOutput(mapChoice1) + "\n"
                                                    + "2️⃣ " + mapChoice2 + " " * (25 - len(mapChoice2)) + "   " + str(mapList[mapChoice2]) + " mirv" + " " * 15 + mapVoteOutput(mapChoice2) + "\n"
                                                    + "3️⃣ " + mapChoice3 + " " * (25 - len(mapChoice3)) + "   " + str(mapList2[mapChoice3]) + " mirv" + " " * 15 + mapVoteOutput(mapChoice3) + "\n"
                                                    + "4️⃣ " + mapChoice4 + " " * (49 - len(mapChoice4)) + mapVoteOutput(mapChoice4)
                                                    + toVoteString)
                                elif(reVote == 1):
                                    if(serverVote == 0):
                                        await vMsg.edit(content="```Vote up and make sure you hydrate!\n\n"
                                                    + "1️⃣ " + mapChoice1 + " " * (25 - len(mapChoice1)) + "   " + str(mapList[mapChoice1]) + " mirv" + " " * 15 + mapVoteOutput(mapChoice1) + "\n"
                                                    + "2️⃣ " + mapChoice2 + " " * (25 - len(mapChoice2)) + "   " + str(mapList[mapChoice2]) + " mirv" + " " * 15 + mapVoteOutput(mapChoice2) + "\n"
                                                    + "3️⃣ " + mapChoice3 + " " * (25 - len(mapChoice3)) + "   " + str(mapList2[mapChoice3]) + " mirv" + " " * 15 + mapVoteOutput(mapChoice3) + "\n"
                                                    + "4️⃣ " + mapChoice4 + " " * (49 - len(mapChoice4)) + mapVoteOutput(mapChoice4)
                                                    + toVoteString)
                            print(alreadyVoted)
                            print(mapVotes)
                            print(playerCount)
                            '''for i in list(mapVotes):
                                if (len(mapVotes[i]) > (int(playerCount / 2))):
                                #if (len(mapVotes[i]) == 1):
                                    forceResults = 1
                                    break
                            if((playerCount == len(alreadyVoted)) or (forceResults == 1)):
                                alreadyVoted = []
                                forceResults = 0
                                votable = 0
                                vMsg = None
                                await forceVote(channel)'''
                        else:
                            await reaction.message.remove_reaction(reaction, user)
                            await user.send("You are not in this pickup..")
                else:
                    await reaction.message.remove_reaction(reaction, user)
                    


@client.event
async def on_message(message):
    global eligiblePlayers
    global alreadyVoted
    global serverVote
    global reVote
    global vMsg
    global mapVotes
    global mapChoice1
    global mapChoice2
    global mapChoice3
    global mapChoice4

    if(message.content == "elo"):
        user = await client.fetch_user(message.author.id)
        if message.guild is None and message.author != client.user:
            with open('ELOpop.json') as f:
                ELOpop = json.load(f)
            #print(ELOpop[str(message.author.id)][2])
            plotList = []
            for i in ELOpop[str(message.author.id)][2]:
                print(i[0])
                plotList.append(i[0])
            plt.plot(plotList)
            print(plotList)
            plt.savefig(message.author.display_name + '.png')
            #await ctx.author.send(file = discord.File(ctx.author.display_name + '.png'), content="Your ELO is currently " + ctx.author.display_name][0])
            await message.author.send(file = discord.File(message.author.display_name + '.png'), content=f"Your ELO is currently {ELOpop[str(message.author.id)][1]} with a record of W: {ELOpop[str(message.author.id)][4]} L: {ELOpop[str(message.author.id)][5]} D: {ELOpop[str(message.author.id)][6]}")
            os.remove(message.author.display_name + '.png')
            plt.clf()


    await client.process_commands(message)


client.run(v['TOKEN'])
#client.run('NzMyMzcyMTcwMzY5NTMxOTc4.XwzovA.mAG_B40lzStmKPGL7Hplf0cg8aA')