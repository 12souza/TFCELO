from asyncio.tasks import sleep
import json
import discord
from discord import player
from discord.ext import commands
from discord.utils import get
import matplotlib.pyplot as plt
import os

client = commands.Bot(command_prefix = ["!", "+", "-"], case_insensitive=True)
client.remove_command('help')

with open('ELOpop.json') as f:
    ELOpop = json.load(f)

playersAdded = []
capList = []
blueTeam = playersAdded[:4]
redTeam = playersAdded[4:]
@client.event
async def on_ready():
    sChannel = await client.fetch_channel("837640003114762250") 
    #await pickupDisplay(sChannel)
    #await teamsDisplay(sChannel)

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
async def swapteam(ctx, player1, player2):
    if(player1 in blueTeam and player2 in redTeam):
        redTeam.append(player1)
        blueTeam.remove(player1)
        blueTeam.append(player2)
        redTeam.remove(player2)
    await teamsDisplay(ctx)

@client.command(pass_context=True)
async def kick(ctx, player):
    playersAdded.remove(player)
    await pickupDisplay(ctx)

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
    



client.run('NzMyMzcyMTcwMzY5NTMxOTc4.XwzovA.mAG_B40lzStmKPGL7Hplf0cg8aA')