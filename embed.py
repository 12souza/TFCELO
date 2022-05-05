from asyncio.tasks import sleep
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

client = commands.Bot(command_prefix = ["!", "+", "-"], case_insensitive=True)
client.remove_command('help')

with open('ELOpop.json') as f:
    ELOpop = json.load(f)

#globals
playersAdded = []
capList = []
blueTeam = []
redTeam = []
mapChoice1 = None
mapChoice2 = None
mapChoice3 = None
mapChoice4 = "New Maps"
loveMaps = []
hateMaps = []
mapVotes = {}
alreadyVoted = []
lastFive = []
mapSelected = []
votePhase = 0
fTimer = 0
inVote = 0
eligiblePlayers = []
reVote = 0
vMsg = None
serverVote = 0
mapVote = 0

@client.event
async def on_ready():
    sChannel = await client.fetch_channel("837640003114762250") 
    #await pickupDisplay(sChannel)
    #await teamsDisplay(sChannel)

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
    print(loveMaps)
    print(hateMaps)
    print(mapPick, mapPick2)

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

@client.command(pass_context=True)
async def pickupDisplay(ctx):
    global playersAdded
    global capList
    with open('ELOpop.json') as f:
        ELOpop = json.load(f)
    msgList = []
    for i in playersAdded:
        if(i in capList):
            msgList.append(ELOpop[i][3] + " " + ELOpop[i][0] + " <:capt:971290940037824574>\n")
        else:
            msgList.append(ELOpop[i][3] + " " + ELOpop[i][0] + "\n")
    msg = "".join(msgList)
    embed = discord.Embed(title = "Pickup Started!")
    if(len(playersAdded) > 0):
        embed.add_field(name = "Players Added", value= msg)
    elif(len(playersAdded) == 0):
        embed.add_field(name = "Players Added", value= "PUG IS EMPTY!")
    await ctx.send(embed = embed)

async def teamsDisplay(ctx):
    msgList = []
    global blueTeam
    global redTeam

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



    vMsg = await ctx.send(embed = embed)

def newRank(ID):
    global ELOpop

    if(ELOpop[ID][1] < 100): #1
        ELOpop[ID][3] = "<:rank1:971270259120148510>"
    if(ELOpop[ID][1] > 400): #2
        ELOpop[ID][3] = "<:rank2:971270266321780746>"
    if(ELOpop[ID][1] > 700): #3
        ELOpop[ID][3] = "<:rank3:971270247837470730>"
    if(ELOpop[ID][1] > 1000): #4
        ELOpop[ID][3] = "<:rank4:971270275008196618>"
    if(ELOpop[ID][1] > 1200): #5
        ELOpop[ID][3] = "<:rank5:971270333631983637>"
    if(ELOpop[ID][1] > 1500): #6
        ELOpop[ID][3] = "<:rank6:971270317186117682>"
    if(ELOpop[ID][1] > 1800): #7
        ELOpop[ID][3] = "<:rank7:971270309414076447>"
    if(ELOpop[ID][1] > 2000): #8
        ELOpop[ID][3] = "<:rank8:971270302594134086>" 
    if(ELOpop[ID][1] > 2200): #9
        ELOpop[ID][3] = "<:rank9:971270284726399047>" 
    if(ELOpop[ID][1] > 2300): #10
        ELOpop[ID][3] = "<:rank10:971270292540379156>"

@client.command(pass_context=True)
async def swapteam(ctx, player1: discord.Member, player2: discord.Member):
    global redTeam
    global blueTeam
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
        blueRank += ELOpop[j][1]
    for j in redTeam:
        redRank += ELOpop[j][1]

    print(blueRank, redRank)

    await teamsDisplay(ctx)

@client.command(pass_context=True)
async def elo(ctx):
    plt.plot(ELOpop[ctx.author.display_name][1])
    plt.savefig(ctx.author.display_name + '.png')
    #await ctx.author.send(file = discord.File(ctx.author.display_name + '.png'), content="Your ELO is currently " + ctx.author.display_name][0])
    await ctx.author.send(file = discord.File(ctx.author.display_name + '.png'), content="Your ELO is currently " + str(ELOpop[ctx.author.display_name][0]))
    os.remove(ctx.author.display_name + '.png')

@client.command(pass_context=True)
async def add(ctx, cap = None):
    global playersAdded
    global capList
    playerID = str(ctx.author.id)
    with open('ELOpop.json') as f:
        ELOpop = json.load(f)
    if(playerID not in playersAdded):
        if(playerID not in list(ELOpop)):
            ELOpop[playerID] = [ctx.author.display_name, 800, [], None]

            with open('ELOpop.json', 'w') as cd:
                json.dump(ELOpop, cd,indent= 4)
        
        if(cap == "cap"):
            capList.append(playerID)
        
        playersAdded.append(playerID)
    else:
        await ctx.author.send("you are already added to this pickup..")
    
    await pickupDisplay(ctx)

@client.command(pass_context=True)
async def remove(ctx):
    global playersAdded
    global capList
    playerID = str(ctx.author.id)
    if(playerID in playersAdded):
        playersAdded.remove(playerID)
        if(playerID in capList):
            capList.remove(playerID)
    
    await pickupDisplay(ctx)

@client.command(pass_context=True)
async def kick(ctx, player: discord.Member):
    global playersAdded
    global capList
    playerID = str(player.id)
    if(playerID in playersAdded):
        playersAdded.remove(playerID)
        if(playerID in capList):
            capList.remove(playerID)
    await pickupDisplay(ctx)
    
@client.command(pass_context=True)
async def addplayer(ctx, player: discord.Member):
    global playersAdded
    global capList
    playerID = str(player.id)
    if(playerID not in playersAdded):
        playersAdded.append(playerID)

    await pickupDisplay(ctx)

@client.command(pass_context=True)
async def teams(ctx, playerCount = 4):
    global playersAdded
    global capList
    global inVote
    global blueTeam
    global redTeam
    global inVote
    global eligiblePlayers
    global fTimer
    global capList

    if(len(capList) < 2):    
        with open('ELOpop.json') as f:
            ELOpop = json.load(f)

        if(inVote == 0):    
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
                    counter += 2
                else:
                    counter += 20
            with open('activePickups.json') as f:
                activePickups = json.load(f)
            
            team1prob = round(1/(1+10**((redRank - blueRank)/400)), 2)
            team2prob = round(1/(1+10**((blueRank - redRank)/400)), 2)

            pSerial = random.randint(0, 10000000)
            while(pSerial in list(activePickups)):
                pSerial = random.randint(0, 10000000)
            now = datetime.now()

            activePickups[pSerial] = [team1prob, blueRank, blueTeam, team2prob, redRank, redTeam, now.strftime("%m/%d/%Y %H:%M:%S"), None]
            with open('activePickups.json', 'w') as cd:
                json.dump(activePickups, cd,indent= 4)

            await teamsDisplay(ctx)
            await ctx.send("Please react to the server you want to play on..")
            fTimer = 5
            fVCoolDown.start()
            inVote = 1

@client.command(pass_context=True)
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
    await pickupDisplay(ctx)

@client.command(pass_context=True)
async def next(ctx, player: discord.Member):
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

    await teamsDisplay(ctx)

@client.command(pass_context=True)
async def sub(ctx, playerout: discord.Member, playerin: discord.Member):
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

    await teamsDisplay(ctx)

@client.command(pass_context=True)
async def win(ctx, pNumber, team):
    global ELOpop
    with open('activePickups.json') as f:
        activePickups = json.load(f)
    with open('ELOpop.json') as f:
        ELOpop = json.load(f)
    
    blueTeam = activePickups[pNumber][2]
    redTeam = activePickups[pNumber][5]
    blueProb = activePickups[pNumber][0]
    blueRank = activePickups[pNumber][1]
    redProb = activePickups[pNumber][3]
    redRank = activePickups[pNumber][4]
    adjustTeam1 = 0
    adjustTeam2 = 0
    with open('activePickups.json', 'w') as cd:
        json.dump(activePickups, cd,indent= 4)
    if(team == "1"):
        adjustTeam1 = int(blueRank + 100 * (1 - blueProb)) - blueRank
        adjustTeam2 = int(redRank + 100 * (0 - redProb)) - redRank

    if(team == "2"):
        adjustTeam1 = int(blueRank + 100 * (0 - blueProb)) - blueRank
        adjustTeam2 = int(redRank + 100 * (1 - redProb)) - redRank
    if(team == "draw"):
        adjustTeam1 = int(blueRank + 100 * (.5 - blueProb)) - blueRank
        adjustTeam2 = int(redRank + 100 * (.5 - redProb)) - redRank
    for i in blueTeam:
        ELOpop[i][1] += adjustTeam1
        ELOpop[i][2].append(ELOpop[i][1])
        newRank(i)
    for i in redTeam:
        ELOpop[i][1] += adjustTeam2
        ELOpop[i][2].append(ELOpop[i][1])
        newRank(i)
    del activePickups[pNumber]
    with open('activePickups.json', 'w') as cd:
        json.dump(activePickups, cd,indent= 4)
    with open('ELOpop.json', 'w') as cd:
        json.dump(ELOpop, cd,indent= 4)
    
    await ctx.send("Match reported.. thank you!")

@client.command(pass_context=True)
async def games(ctx):
    await openPickups(ctx)

@client.command(pass_context=True)
async def checkgame(ctx, number):
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
async def removegame(ctx, number):
    with open('activePickups.json') as f:
        activePickups = json.load(f)

    del activePickups[number]

    with open('activePickups.json', 'w') as cd:
        json.dump(activePickups, cd,indent= 4)
    
    await ctx.send("Game has been removed..")

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

    if(reaction.message == vMsg):
        if((reaction.emoji == '1️⃣') or (reaction.emoji == '2️⃣') or (reaction.emoji == '3️⃣') or (reaction.emoji == '4️⃣')):
            playerCount = len(eligiblePlayers)
            userID = str(user.id)

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
                        await vMsg.edit(content="```Vote up and make sure you hydrate!\n\n"
                                                            + "1️⃣ " + mapChoice1 + " " * (70 - len(mapChoice1)) + mapVoteOutput(mapChoice1) + "\n"
                                                            + "2️⃣ " + mapChoice2 + " " * (70 - len(mapChoice2)) + mapVoteOutput(mapChoice2) + "\n"
                                                            + "3️⃣ " + mapChoice3 + " " * (70 - len(mapChoice3)) + mapVoteOutput(mapChoice3) + "\n```")  
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

    if (message.channel.name == "tfc-pickup-na"): 
        if(message.content.startswith("Please react to the server")):
            serverVote = 1
            alreadyVoted = []
            mapVotes = {}
            reVote = 1
            mapChoice3 = "North Virginia - East"
            mapVotes[mapChoice3] = []
            mapChoice2 = "Iowa - Central"
            mapVotes[mapChoice2] = []    
            mapChoice1 = "Las Vegas - West"
            mapVotes[mapChoice1] = []

            vMsg = await message.channel.send("```Vote for your server!  Be quick, you only have 45 seconds to vote..\n\n"
                                                            + "1️⃣ " + mapChoice1 + " " * (70 - len(mapChoice1)) + mapVoteOutput(mapChoice1) + "\n"
                                                            + "2️⃣ " + mapChoice2 + " " * (70 - len(mapChoice2)) + mapVoteOutput(mapChoice2) + "\n"
                                                            + "3️⃣ " + mapChoice3 + " " * (70 - len(mapChoice3)) + mapVoteOutput(mapChoice3) + "\n```")

            await vMsg.add_reaction("1️⃣")
            await vMsg.add_reaction("2️⃣")
            await vMsg.add_reaction("3️⃣")

        await client.process_commands(message)


client.run('NzMyMzcyMTcwMzY5NTMxOTc4.XwzovA.mAG_B40lzStmKPGL7Hplf0cg8aA')