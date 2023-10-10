import asyncio
import discord
from discord.ext import commands
import datetime
import json


#print(discord.__version__)
intents = discord.Intents.all()
client = commands.Bot(command_prefix = ["!", "+", "-"], case_insensitive=True, intents= intents)

with open('variables.json') as f:
    v = json.load(f)


@client.command(pass_context=True)
@commands.has_role(v['runner'])
async def timeout(ctx, user: discord.Member, *, reason = None):
    adminChannel = await client.fetch_channel(836999458431434792)
    if(reason == None):
        await ctx.send("User must be given a reason for timeout..")
    else:
        duration = datetime.timedelta(seconds=0, minutes=0, hours= 0, days=1)
        await user.timeout(duration, reason=reason)
        await ctx.send(f"Successfully timed out {user.name} for 24h")
        await user.send(f"You have been timed out for {reason}")
        await adminChannel.send(f"**{user.display_name}** has been timed out by **{ctx.author.display_name}** for **{reason}** - 24hr")

#use_voice_activation
@client.command(pass_context=True)
@commands.has_role(v['runner'])
async def forcePTT(ctx, user: discord.Member, *, reason = None):
    if(reason == None):
        await ctx.send("User must be given a reason")
    else:    
        adminChannel = await client.fetch_channel(836999458431434792)
        channels = [836633744902586378, 836633820849373184, 840065112484085771, 840065140489060363] 
        for id in channels:    
            vchannel = await client.fetch_channel(id)
            perms = vchannel.overwrites_for(user)
            perms.use_voice_activation=False
            #await vchannel.set_permissions(user, use_voice_activation=not perms.use_voice_activation)
            await vchannel.set_permissions(user, overwrite=perms)
        await ctx.send(f"Successfully set {user.name}'s permission to PTT only")
        await user.send(f"You have been put on PTT for {reason}")
        await adminChannel.send(f"**{user.display_name}** has been forced to PPT by **{ctx.author.display_name}** for **{reason}**")


client.run(v['TOKEN'])