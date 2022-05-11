from asyncio.tasks import sleep
from email.utils import collapse_rfc2231_value
from http import server
import json
import discord
from discord import player
from discord.ext import commands
from discord.utils import get
import matplotlib.pyplot as plt
from discord.ext import tasks
import os
import random
import itertools
from datetime import datetime
import requests

intents = discord.Intents.all()
client = commands.Bot(command_prefix = ["!", "+", "-"], case_insensitive=True)
client.remove_command('help')

with open('ELOpop.json') as f:
    ELOpop = json.load(f)
with open('variables2.json') as f:
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
winner = None
mapChoice1 = None
mapChoice2 = None
mapChoice3 = None
mapChoice4 = "New Maps"
loveMaps = []
hateMaps = []
mapVotes = {}
alreadyVoted = []
pMsg = None
lastFive = []
mapSelected = []
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
winningMap = None
winningServer = None

@client.command(pass_context=True)
@commands.has_role(v['rater'])
async def search(ctx, searchkey):
    print('test')
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
            pMsgList.append(i + " " * (30 - len(i)) + " ELO: " + str(ELOpop[playerID][1]) + "                 1-20 rank: " + str(ELOpop[playerID][1] / 120) + "\n")
        mMsg = ''.join(pMsgList)
        if(len(searchList) > 0):
            await ctx.send(content = "```\n" + mMsg + "```")
        else:
            await ctx.send("No results with that search string..")

def DePopulatePickup():
    global cap1
    global cap2
    global cap1Name
    global cap2Name
    global playersAdded
    global blueTeam
    global redTeam
    global winner
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
    global lastFive
    global mapSelected
    global winningIP
    global votePhase
    global fTimer
    global inVote
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
    playersAdded = []
    capList = []
    blueTeam = []
    redTeam = []
    winner = None
    mapChoice1 = None
    mapChoice2 = None
    mapChoice3 = None
    mapChoice4 = "New Maps"
    loveMaps = []
    hateMaps = []
    mapVotes = {}
    alreadyVoted = []
    pMsg = None
    lastFive = []
    mapSelected = []
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
    print(redTeam)
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

@client.command(pass_context=True)
async def pickupDisplay(ctx):
    global playersAdded
    global capList
    with open('ELOpop.json') as f:
        ELOpop = json.load(f)
    msgList = []
    for i in playersAdded:
        if(i in capList):
            msgList.append(ELOpop[i][3] + " " + ELOpop[i][0] + " " + v['cptimg'] + "\n")
        else:
            msgList.append(ELOpop[i][3] + " " + ELOpop[i][0] + "\n")
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
        msgList.append(ELOpop[i][3] + " " + ELOpop[i][0] + "\n")
    bMsg = "".join(msgList)
    msgList.clear()
    for i in redTeam:
        msgList.append(ELOpop[i][3] + " " + ELOpop[i][0] + "\n")
    rMsg = "".join(msgList)
    embed = discord.Embed(title = "Teams Sorted!")
    embed.add_field(name = "Blue Team " + v['t1img'] + " " + str(int(team1prob * 100)) + "%", value= bMsg, inline=True)
    embed.add_field(name="\u200b", value = "\u200b")
    embed.add_field(name = "Red Team " + v['t2img'] + " " + str(int(team2prob * 100)) + "%", value= rMsg, inline=True)
    await ctx.send(embed = embed)

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
    if(ctx.channel.name == v['pc']):    
        if(server.lower() == 'west'):
            r = requests.get("https://us-west1-coachoffice-332119.cloudfunctions.net/startWest")
        elif(server.lower() == 'central'):
            r = requests.get("https://us-central1-coachoffice-332119.cloudfunctions.net/startCentral-1")
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
    if(ctx.channel.name == v['pc']):    
        if(server == 'west'):
            r = requests.get("https://us-west1-coachoffice-332119.cloudfunctions.net/stopWest")
        elif(server == 'central'):
            r = requests.get("https://us-central1-coachoffice-332119.cloudfunctions.net/stopCentral-2")
        elif(server == 'east'):    
            r = requests.get("https://us-east4-coachoffice-332119.cloudfunctions.net/stopEast")
        elif(server.lower() == 'latam'):
            r = requests.get("https://southamerica-east1-coachoffice-332119.cloudfunctions.net/stopLATAM")
        elif(server.lower() == 'eu'):
            r = requests.get("https://europe-west3-coachoffice-332119.cloudfunctions.net/stopEU")
        await ctx.send(server + " is shutting down..")

@client.command(pass_context=True)
@commands.has_role(v['runner'])
async def swapteam(ctx, player1: discord.Member, player2: discord.Member):
    if(ctx.channel.name == v['pc']):    
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

        print(blueRank, redRank)

        await teamsDisplay(ctx, blueTeam, redTeam, team1prob, team2prob)

def savePickup():
    global winningMap
    global winningServer
    global blueTeam
    global redTeam
    global captMode

    with open('activePickups.json') as f:
        activePickups = json.load(f)
    with open('ELOpop.json') as f:
                ELOpop = json.load(f)

    serial = random.randint(0, 100000)

    pSerial = random.randint(0, 10000000)
    while(pSerial in list(activePickups)):
        pSerial = random.randint(0, 10000000)
    now = datetime.now()
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

    print(blueTeam, redTeam)
    for i in blueTeam:
        blueRank += int(ELOpop[i][1])
    for i in redTeam:
        redRank += int(ELOpop[i][1])

    team1prob = round(1/(1+10**((redRank - blueRank)/400)), 2)
    team2prob = round(1/(1+10**((blueRank - redRank)/400)), 2)

    activePickups[pSerial] = [team1prob, blueRank, blueTeam, team2prob, redRank, redTeam, now.strftime("%m/%d/%Y %H:%M:%S"), winningMap, winningServer]
    with open('activePickups.json', 'w') as cd:
        json.dump(activePickups, cd,indent= 4)

@client.command(pass_context=True)
async def elo(ctx):
    if(ctx.channel.name == v['pc']):
        await ctx.author.send("!elo no longer works.. but if you type 'elo' to me I will send you your elo info")
        '''with open('ELOpop.json') as f:
            ELOpop = json.load(f)
        print(ELOpop[str(ctx.author.id)][2])
        plt.plot(ELOpop[str(ctx.author.id)][2])
        plt.savefig(ctx.author.display_name + '.png')
        #await ctx.author.send(file = discord.File(ctx.author.display_name + '.png'), content="Your ELO is currently " + ctx.author.display_name][0])
        await ctx.author.send(file = discord.File(ctx.author.display_name + '.png'), content=f"Your ELO is currently {ELOpop[str(ctx.author.id)][1]} with a record of W: {ELOpop[str(ctx.author.id)][4]} L: {ELOpop[str(ctx.author.id)][5]} D: {ELOpop[str(ctx.author.id)][6]}")
        #os.remove(ctx.author.display_name + '.png')
        plt.clf()'''

@client.command(pass_context = True , aliases=['+'])
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
                    ELOpop[playerID] = [ctx.author.display_name, 800, [], "<:questionMark:972369805359337532>", 0, 0, 0]

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
                    print(playersAdded)
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
                                    print(blueTeam, blueRank)
                                    print(redTeam, redRank)
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
                    fTimer = 5
                    fVCoolDown.start()
                    inVote = 1
                
                elif(len(capList) >= 2):
                    print("will use capts")
                    with open('ELOpop.json') as f:
                        ELOpop = json.load(f)    
                    playerCount = int(playerCount)
                    if(len(playersAdded) == playerCount):
                        eligiblePlayers = playersAdded
                    else:    
                        eligiblePlayers = playersAdded[0:playerCount * 2]
                    captMode = 1
                    await ctx.send("Please react to the server you want to play on..")
                    fTimer = 5
                    fVCoolDown.start()
                    inVote = 1
        else:
            await ctx.send("you dont have enough people for that game size..")

@client.command(pass_context=True)
@commands.has_role(v['runner'])
async def addp(ctx, number):
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
                        print(blueTeam, blueRank)
                        print(redTeam, redRank)
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
async def sub(ctx, playerout: discord.Member, playerin: discord.Member):
    if(ctx.channel.name == v['pc']):    
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
        combos = list(itertools.combinations(eligiblePlayers, int(playerCount / 2)))
        random.shuffle(combos)
        
        if(str(playerin.id) in playersAdded):
            playersAdded.remove(str(playerin.id))

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
                    print(blueTeam, blueRank)
                    print(redTeam, redRank)
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
        teamsDisplay(ctx, blueTeam, redTeam, team1prob, team2prob)

@client.command(pass_context=True)
@commands.has_role(v['runner'])
async def win(ctx, team, pNumber = "None"):
    #global ELOpop
    if(ctx.channel.name == v['pc']):    
        with open('activePickups.json') as f:
            activePickups = json.load(f)
        with open('ELOpop.json') as f:
            ELOpop = json.load(f)
        if(pNumber == "None"):
            pNumber = list(activePickups)[-1]

        print(activePickups[pNumber][2])
        blueTeam = activePickups[pNumber][2]
        redTeam = activePickups[pNumber][5]
        blueProb = activePickups[pNumber][0]
        blueRank = activePickups[pNumber][1]
        redProb = activePickups[pNumber][3]
        redRank = activePickups[pNumber][4]
        adjustTeam1 = 0
        adjustTeam2 = 0
        
        if(team == "1"):
            adjustTeam1 = int(blueRank + 50 * (1 - blueProb)) - blueRank
            adjustTeam2 = int(redRank + 50 * (0 - redProb)) - redRank

        if(team == "2"):
            adjustTeam1 = int(blueRank + 50 * (0 - blueProb)) - blueRank
            adjustTeam2 = int(redRank + 50 * (1 - redProb)) - redRank
        if(team == "draw"):
            adjustTeam1 = int(blueRank + 50 * (.5 - blueProb)) - blueRank
            adjustTeam2 = int(redRank + 50 * (.5 - redProb)) - redRank
        for i in blueTeam:
            ELOpop[i][1] += adjustTeam1
            if(int(ELOpop[i][1]) > 2599):
                ELOpop[i][1] = 2599
            ELOpop[i][2].append(int(ELOpop[i][1]))
            if(team == "1"):
                ELOpop[i][4] += 1
            if(team == "2"):
                ELOpop[i][5] += 1
            if(team == "draw"):
                ELOpop[i][6] += 1
            newRank(i)
            print(ELOpop[i][2])
        for i in redTeam:
            print(type(ELOpop[i][1]))
            print(ELOpop)
            ELOpop[i][1] += adjustTeam2
            if(int(ELOpop[i][1]) > 2599):
                ELOpop[i][1] = 2599
            ELOpop[i][2].append(int(ELOpop[i][1]))
            if(team == "1"):
                ELOpop[i][5] += 1
            if(team == "2"):
                ELOpop[i][4] += 1
            if(team == "draw"):
                ELOpop[i][6] += 1
            newRank(i)
        del activePickups[pNumber]
        with open('activePickups.json', 'w') as cd:
            json.dump(activePickups, cd,indent= 4)
        with open('ELOpop.json', 'w') as cd:
            json.dump(ELOpop, cd,indent= 4)
        
        await ctx.send("Match reported.. thank you!")

@client.command(pass_context=True)
async def games(ctx):
    if(ctx.channel.name == v['pc']):    
        await openPickups(ctx)

@client.command(pass_context=True)
async def checkgame(ctx, number):
    if(ctx.channel.name == v['pc']):    
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
        DePopulatePickup()
        await ctx.send("Queue has been cancelled..")

@client.command()
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
        global cap2Name
        global winningMap
        global winningServer

        winningMap = None
        with open('activePickups.json') as f:
            activePickups = json.load(f)
        if(serverVote == 1):
            votes = [len(mapVotes[mapChoice1]), len(mapVotes[mapChoice2]), len(mapVotes[mapChoice3])]
            windex = votes.index(max(votes))
            if(windex == 0):
                await channel.send("West (Las Vegas) server is being launched..")
                r = requests.get("https://us-west1-coachoffice-332119.cloudfunctions.net/startWest")
                winningIP = "steam://connect/34.125.240.0:27015/letsplay!"
                winningServer = "West"
                serverVote = 0
                #activePickups[list(activePickups)[-1]][8] = "West"
            if(windex == 1):
                await channel.send("Central (Iowa) server is being launched..")
                r = requests.get("https://us-central1-coachoffice-332119.cloudfunctions.net/startCentral-1")
                winningIP = "steam://connect/35.188.60.68:27015/letsplay!"
                winningServer = "Central"
                serverVote = 0
            if(windex == 2):
                await channel.send("East (N. Virginia) server is being launched..")
                r = requests.get("https://us-east4-coachoffice-332119.cloudfunctions.net/startEast")
                winningIP = "steam://connect/35.194.65.124:27015/letsplay!"
                winningServer = "East"
                serverVote = 0
        else:
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
                    await channel.send("New maps has won, now selecting new maps..")
                else:
                    await channel.send(f"The winning map is **{mapChoice4}** and will be played at {winningIP}")
                    fVCoolDown.stop()
                    inVote = 0
                    winningMap = mapChoice4
                    if(captMode == 0):
                        savePickup()
            if(windex == 1):
                await channel.send(f"The winning map is **{mapChoice1}** and will be played at {winningIP}")
                fVCoolDown.stop()
                inVote = 0
                winningMap = mapChoice1
                if(captMode == 0):
                    savePickup()
            if(windex == 2):
                await channel.send(f"The winning map is **{mapChoice2}** and will be played at {winningIP}")
                fVCoolDown.stop()
                inVote = 0
                winningMap = mapChoice2
                if(captMode == 0):
                    savePickup()
            if(windex == 3):
                await channel.send(f"The winning map is **{mapChoice3}** and will be played at {winningIP}")
                fVCoolDown.stop()
                inVote = 0
                winningMap = mapChoice3
                if(captMode == 0):
                    savePickup()
            
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
async def shuffle(ctx, game = "None"):
    if(ctx.channel.name == v['pc']):
        with open('activePickups.json') as f:
            activePickups = json.load(f)
        global blueTeam
        global redTeam
        global eligiblePlayers

        if(game == "None"):
            with open('ELOpop.json') as f:
                ELOpop = json.load(f)
                
            playerCount = len(eligiblePlayers)
            counter = 0
            teamsPicked = 0
            
            combos = list(itertools.combinations(eligiblePlayers, int(len(eligiblePlayers) / 2)))
            random.shuffle(combos)

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
                        if((len(blueTeam) == int(playerCount/ 2)) and (len(redTeam) == int(playerCount/ 2))):
                            print(blueTeam, blueRank)
                            print(redTeam, redRank)
                            teamsPicked = 1
                            break
                    else:
                        blueTeam.clear()
                        redTeam.clear()
                        redRank = 0
                        blueRank = 0
                        totalRank = 0
                if(playerCount <= 8):    
                    counter += 2
                else:
                    counter += 20
            
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
        
            with open('ELOpop.json') as f:
                ELOpop = json.load(f)
                
            playerCount = len(neligiblePlayers)
            counter = 0
            teamsPicked = 0
            
            combos = list(itertools.combinations(neligiblePlayers, int(len(neligiblePlayers) / 2)))
            random.shuffle(combos)
            print(neligiblePlayers)
            while teamsPicked == 0:
                nblueTeam = []
                nredTeam = []
                redRank = 0
                blueRank = 0
                totalRank = 0
                half = 0
                diff = 0   
                for i in range(len(combos)):
                    for j in neligiblePlayers:
                        totalRank += int(ELOpop[j][1])
                    half = int(totalRank / 2)
                    nblueTeam = list(combos[i])
                    for j in neligiblePlayers:
                        if(j not in nblueTeam):
                            nredTeam.append(j)

                    for j in nblueTeam:
                        blueRank += int(ELOpop[j][1])
                    for j in nredTeam:
                        redRank += int(ELOpop[j][1])    
                    print(diff, half, blueRank, redRank)
                    diff = abs(blueRank - half)
                    if(diff <= counter):
                        if((len(nblueTeam) == int(playerCount / 2)) and (len(nredTeam) == int(playerCount / 2))):
                            print(nblueTeam, blueRank)
                            print(nredTeam, redRank)
                            teamsPicked = 1
                            team1prob = round(1/(1+10**((redRank - blueRank)/400)), 2)
                            team2prob = round(1/(1+10**((blueRank - redRank)/400)), 2)
                            activePickups[game][0] = team1prob
                            activePickups[game][1] = blueRank
                            activePickups[game][2] = nblueTeam
                            activePickups[game][3] = team2prob
                            activePickups[game][4] = redRank
                            activePickups[game][5] = nredTeam
                            with open('activePickups.json', 'w') as cd:
                                json.dump(activePickups, cd,indent= 4)
                            break
                    else:
                        #print(blueRank, redRank)
                        nblueTeam.clear()
                        nredTeam.clear()
                        redRank = 0
                        blueRank = 0
                        totalRank = 0
                if(playerCount <= 8):    
                    counter += 2
                else:
                    counter += 20
            team1prob = round(1/(1+10**((redRank - blueRank)/400)), 2)
            team2prob = round(1/(1+10**((blueRank - redRank)/400)), 2)
            await teamsDisplay(ctx, nblueTeam, nredTeam, team1prob, team2prob)

@client.command(pass_context=True)
@commands.cooldown(1, 300, commands.BucketType.user)
async def notice(ctx, anumber = 8):
    global playersAdded
    number = len(list(playersAdded))
    role = discord.utils.get(ctx.guild.roles, id=v['TFCPlayer'])

    await ctx.send(f"{role.mention} {number}/{anumber}")


@client.event
async def on_reaction_add(reaction, user):
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
    global pickCount
    global cap1
    global cap2
    global cap1Name
    global cap2Name
    global pTotalPlayers
    global blueTeam
    global redTeam

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
    if(reaction.message == vMsg):
        if((reaction.emoji == '1️⃣') or (reaction.emoji == '2️⃣') or (reaction.emoji == '3️⃣') or (reaction.emoji == '4️⃣')):
            with open('ELOpop.json') as f:
                ELOpop = json.load(f)
            playerCount = len(eligiblePlayers)
            userID = str(user.id)
            forceResults = 0
            channel = await client.fetch_channel(reaction.message.channel.id)
            playerName = ELOpop[str(userID)][0]
            if(inVote == 1):
                print(eligiblePlayers)
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
                        alreadyVoted.append(playerName)

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
                    if(reVote == 1):
                        print(mapVotes)
                    for i in list(mapVotes):
                        if (len(mapVotes[i]) > (playerCount / 2)):
                        #if (len(mapVotes[i]) == 1):
                            forceResults = 1
                            #print(len(mapVotes[i], playerCount / 2))
                            #print(len(alreadyVoted), playerCount)
                    if((playerCount == len(alreadyVoted)) or (forceResults == 1)):
                        await forceVote(channel)
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
            print(ELOpop[str(message.author.id)][2])
            plt.plot(ELOpop[str(message.author.id)][2])
            plt.savefig(message.author.display_name + '.png')
            #await ctx.author.send(file = discord.File(ctx.author.display_name + '.png'), content="Your ELO is currently " + ctx.author.display_name][0])
            await message.author.send(file = discord.File(message.author.display_name + '.png'), content=f"Your ELO is currently {ELOpop[str(message.author.id)][1]} with a record of W: {ELOpop[str(message.author.id)][4]} L: {ELOpop[str(message.author.id)][5]} D: {ELOpop[str(message.author.id)][6]}")
            #os.remove(ctx.author.display_name + '.png')
            plt.clf()

    if (message.channel.name == v['pc']): 
        if(message.content.startswith("Please react to the server")):
            with open('ELOpop.json') as f:
                ELOpop = json.load(f)
            serverVote = 1
            alreadyVoted = []
            mapVotes = {}
            reVote = 0
            mapChoice3 = "North Virginia - East"
            mapVotes[mapChoice3] = []
            mapChoice2 = "Iowa - Central"
            mapVotes[mapChoice2] = []    
            mapChoice1 = "Las Vegas - West"
            mapVotes[mapChoice1] = []

            playersAbstained = []
            for i in eligiblePlayers:
                if i not in alreadyVoted:
                    playersAbstained.append(ELOpop[i][0])
            toVoteString = "```"
            if len(playersAbstained) != 0:
                toVoteString = "\n💩 " + ", ".join(playersAbstained) +  " need to vote 💩```"

            vMsg = await message.channel.send("```Vote for your server!  Be quick, you only have 45 seconds to vote..\n\n"
                                                            + "1️⃣ " + mapChoice1 + " " * (70 - len(mapChoice1)) + mapVoteOutput(mapChoice1) + "\n"
                                                            + "2️⃣ " + mapChoice2 + " " * (70 - len(mapChoice2)) + mapVoteOutput(mapChoice2) + "\n"
                                                            + "3️⃣ " + mapChoice3 + " " * (70 - len(mapChoice3)) + mapVoteOutput(mapChoice3)
                                                            + toVoteString)

            await vMsg.add_reaction("1️⃣")
            await vMsg.add_reaction("2️⃣")
            await vMsg.add_reaction("3️⃣")
        
    if(("server is being launched.." in message.content) or ("selecting new maps.." in message.content)):
        with open('ELOpop.json') as f:
            ELOpop = json.load(f)
        alreadyVoted = []
        mapVotes = {}           
        PickMaps()
        if(("server is being launched.." in message.content)):
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
        vMsg = await message.channel.send("```Vote up and make sure you hydrate!\n\n"
                                        + "1️⃣ " + mapChoice1 + " " * (25 - len(mapChoice1)) + "   " + str(mapList[mapChoice1]) + " mirv" + " " * 15 + mapVoteOutput(mapChoice1) + "\n"
                                        + "2️⃣ " + mapChoice2 + " " * (25 - len(mapChoice2)) + "   " + str(mapList[mapChoice2]) + " mirv" + " " * 15 + mapVoteOutput(mapChoice2) + "\n"
                                        + "3️⃣ " + mapChoice3 + " " * (25 - len(mapChoice3)) + "   " + str(mapList2[mapChoice3]) + " mirv" + " " * 15 + mapVoteOutput(mapChoice3) + "\n"
                                        + "4️⃣ " + mapChoice4 + " " * (49 - len(mapChoice4)) + mapVoteOutput(mapChoice4)
                                        + toVoteString)

        await vMsg.add_reaction("1️⃣")
        await vMsg.add_reaction("2️⃣")
        await vMsg.add_reaction("3️⃣")
        await vMsg.add_reaction("4️⃣")

    await client.process_commands(message)


client.run(v['TOKEN'])
#client.run('NzMyMzcyMTcwMzY5NTMxOTc4.XwzovA.mAG_B40lzStmKPGL7Hplf0cg8aA')