import discord
from discord import player
from discord.ext import commands
from discord.utils import get
import matplotlib.pyplot as plt
from discord.ext import tasks
import json
from datetime import datetime
from ftplib import FTP
import os

intents = discord.Intents.all()
client = commands.Bot(command_prefix = ["!", "+", "-"], case_insensitive=True, intents= intents)

with open('ELOpop.json') as f:
    ELOpop = json.load(f)
with open('variables.json') as f:
    v = json.load(f)

def pruneDict(dictk):   
    for i in list(dictk):
        if(i != "totalgame"):
            if(dictk['totalgame'] != 0):
                percent = dictk[i][0] / dictk['totalgame'] * 100
            else:
                percent = 0
            #print(f"{i} {percent}")
            if(percent < 5.0):
                #print(i)
                del dictk[i]
    return dictk

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

def simplifyDict(dictfrom, idx, pergame = "No"):
    newDict = {}
    for i in list(dictfrom):
        if(i != "totalgame"):
            if(pergame == "No"):
                newDict[i] = dictfrom[i][idx]
            else:
                if(dictfrom[i][0] != 0):
                    newDict[i] = round(dictfrom[i][idx] / dictfrom[i][0], 2)
                else:
                    newDict[i] = 0
    return newDict

def find(haystack, needle, n):
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start+len(needle))
        n -= 1
    return start

def statUpdater(log1, log2):
    with open('kills.json') as f:
        kills = json.load(f)
    with open('damage.json') as f:
        damage = json.load(f)
    with open('flagstats.json') as f:
        flagstats = json.load(f)
    played = []
    currentClass = {}
    blueTeam = []
    redTeam = []
    matchbegin = 0
    file1 = open(log1, 'r')
    Lines = file1.readlines()
    file2 = open(log2, 'r')
    Lines2 = file2.readlines()
    
    for line in Lines:
        try:
            if(matchbegin == 0):
                if("joined" in line):
                    b = find(line,'"',3) + 1
                    e = find(line,'"',4)
                    team = line[b:e]
                    b = find(line,'<',2) + 1
                    e = find(line,'>',2)
                    steamid = line[b:e]
                    if(team == "Blue" or team == "Red"):
                        if(team == "Blue"): blueTeam.append(steamid)
                        if(team == "Red"): redTeam.append(steamid)
                        played.append(steamid)
                    if(team == "SPECTATOR" and steamid in played):
                        played.remove(steamid)
            if("changed role" in line):
                b = find(line,'<',2) + 1
                e = find(line,'>',2)
                steamid = line[b:e]
                b = find(line,'"',3) + 1
                e = find(line,'"',4)
                role = line[b:e]
                currentClass[steamid] = role
                
            if("Match_Begins_Now" in line):
                matchbegin = 1
                for i in played:
                    if(i not in list(kills)):
                                  #[TG,TK,DK,OK,SK,DemoK,MedicK,HWK,SpyK,EngyK,SGK,ESGK,KK,SteamID]
                        kills[i] = [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, i]
                    else:
                        kills[i][0] += 1
                    if(i not in list(damage)):
                        damage[i] = [1, 0, 0, i]
                    else:
                        damage[i][0] += 1
                    if(i not in list(flagstats)):
                        flagstats[i] = [1, 0, 0, i]
                    else:
                        flagstats[i][0] += 1

            if("killed" in line and matchbegin == 1):
                b = find(line,'<',2) + 1
                e = find(line,'>',2)
                steamid = line[b:e]
                b = find(line,'<',6) + 1
                e = find(line,'>',6)
                victeam = line[b:e]
                b = find(line,'<',3) + 1
                e = find(line,'>',3)
                team = line[b:e]
                b = find(line,'"',5) + 1
                e = find(line,'"',6)
                weaponname = line[b:e]
                if(victeam != team):
                    kills[steamid][1] += 1
                    if(team == 'Blue'): kills[steamid][3] += 1
                    elif(team == 'Red'): kills[steamid][2] += 1
                    if(currentClass[steamid] == "Soldier"): kills[steamid][4] += 1
                    elif(currentClass[steamid] == "Demoman"): kills[steamid][5] += 1
                    elif(currentClass[steamid] == "Medic"): kills[steamid][6] += 1
                    elif(currentClass[steamid] == "HWGuy"): kills[steamid][7] += 1
                    elif(currentClass[steamid] == "Spy"): kills[steamid][8] += 1
                    elif(currentClass[steamid] == "Engineer"): kills[steamid][9] += 1
                    if(weaponname == 'sentrygun'): kills[steamid][11] += 1
                    if(weaponname == 'knife'): kills[steamid][12] += 1
            if("Sentry_Destroyed" in line and matchbegin == 1):
                b = find(line,'<',2) + 1
                e = find(line,'>',2)
                steamid = line[b:e]
                b = find(line,'<',6) + 1
                e = find(line,'>',6)
                victeam = line[b:e]
                b = find(line,'<',3) + 1
                e = find(line,'>',3)
                team = line[b:e]
                if(victeam != team):
                    kills[steamid][10] += 1
            #[SUMMARY] "EDEdDNEdDYFaN<1><STEAM_0:0:76483><Blue>" damage summary: enemy - 169, team - 0
            if("[SUMMARY]" in line):
                b = find(line,'<',2) + 1
                e = find(line,'>',2)
                steamid = line[b:e]
                b = find(line,'<',3) + 1
                e = find(line,'>',3)
                team = line[b:e]
                b = find(line,'enemy - ',1) + 8
                e = find(line,', t',1)
                #print(line[b:e])
                dmg = int(line[b:e])
                if(team == "Blue"): damage[steamid][2] += dmg
                if(team == "Red"): damage[steamid][1] += dmg
            #L 12/29/2022 - 00:00:03: "EDEdDNEdDYFaN<51><STEAM_0:0:76483><Blue>" triggered "Red Flag"
            if("triggered \"Red Flag\"" in line):
                b = find(line,'<',2) + 1
                e = find(line,'>',2)
                steamid = line[b:e]
                flagstats[steamid][1] += 1
                #print(line)
            if(("Team 1 dropoff" in line or "Red Flag Cap" in line or "Red Flag Capture" in line) and ("say" in line or "say_team" not in line)):
                b = find(line,'<',2) + 1
                e = find(line,'>',2)
                steamid = line[b:e]
                flagstats[steamid][2] += 1
        except Exception as e:
            print(e)
            continue
    
    for line in Lines2:
        try:
            redTeam = []
            blueTeam = []
            if(matchbegin == 0):
                if("joined" in line):
                    b = find(line,'"',3) + 1
                    e = find(line,'"',4)
                    team = line[b:e]
                    b = find(line,'<',2) + 1
                    e = find(line,'>',2)
                    steamid = line[b:e]
                    if(team == "Blue" or team == "Red"):
                        if(team == "Blue"): blueTeam.append(steamid)
                        if(team == "Red"): redTeam.append(steamid)

            if("changed role" in line):
                b = find(line,'<',2) + 1
                e = find(line,'>',2)
                steamid = line[b:e]
                b = find(line,'"',3) + 1
                e = find(line,'"',4)
                role = line[b:e]
                currentClass[steamid] = role
            if("Match_Begins_Now" in line):
                matchbegin = 1
                
            if("killed" in line and matchbegin == 1):
                b = find(line,'<',2) + 1
                e = find(line,'>',2)
                steamid = line[b:e]
                b = find(line,'<',6) + 1
                e = find(line,'>',6)
                victeam = line[b:e]
                b = find(line,'<',3) + 1
                e = find(line,'>',3)
                team = line[b:e]
                b = find(line,'"',5) + 1
                e = find(line,'"',6)
                weaponname = line[b:e]
                if(victeam != team):
                    kills[steamid][1] += 1
                    if(team == 'Blue'): kills[steamid][3] += 1
                    elif(team == 'Red'): kills[steamid][2] += 1
                    if(currentClass[steamid] == "Soldier"): kills[steamid][4] += 1
                    elif(currentClass[steamid] == "Demoman"): kills[steamid][5] += 1
                    elif(currentClass[steamid] == "Medic"): kills[steamid][6] += 1
                    elif(currentClass[steamid] == "HWGuy"): kills[steamid][7] += 1
                    elif(currentClass[steamid] == "Spy"): kills[steamid][8] += 1
                    elif(currentClass[steamid] == "Engineer"): kills[steamid][9] += 1
                    if(weaponname == 'sentrygun'): kills[steamid][11] += 1
                    if(weaponname == 'knife'): kills[steamid][12] += 1
            if("Sentry_Destroyed" in line and matchbegin == 1):
                b = find(line,'<',2) + 1
                e = find(line,'>',2)
                steamid = line[b:e]
                b = find(line,'<',6) + 1
                e = find(line,'>',6)
                victeam = line[b:e]
                b = find(line,'<',3) + 1
                e = find(line,'>',3)
                team = line[b:e]
                if(victeam != team):
                    kills[steamid][10] += 1
            #[SUMMARY] "EDEdDNEdDYFaN<1><STEAM_0:0:76483><Blue>" damage summary: enemy - 169, team - 0
            if("[SUMMARY]" in line):
                b = find(line,'<',2) + 1
                e = find(line,'>',2)
                steamid = line[b:e]
                b = find(line,'<',3) + 1
                e = find(line,'>',3)
                team = line[b:e]
                b = find(line,'enemy - ',1) + 8
                e = find(line,', t',1)
                #print(line[b:e])
                dmg = int(line[b:e])
                if(team == "Blue"): damage[steamid][2] += dmg
                if(team == "Red"): damage[steamid][1] += dmg
            #L 12/29/2022 - 00:00:03: "EDEdDNEdDYFaN<51><STEAM_0:0:76483><Blue>" triggered "Red Flag"
            if("triggered \"Red Flag\"" in line):
                b = find(line,'<',2) + 1
                e = find(line,'>',2)
                steamid = line[b:e]
                flagstats[steamid][1] += 1
                #print(line)
            if(("Team 1 dropoff" in line or "Red Flag Cap" in line or "Red Flag Capture" in line) and ("say" in line or "say_team" not in line)):
                b = find(line,'<',2) + 1
                e = find(line,'>',2)
                steamid = line[b:e]
                flagstats[steamid][2] += 1
        except Exception as e:
            print(e)
            continue
    kills['totalgame'] += 1
    damage['totalgame'] += 1
    flagstats['totalgame'] += 1

    with open('kills.json', 'w') as cd:
        json.dump(kills, cd,indent= 4)
    with open('damage.json', 'w') as cd:
        json.dump(damage, cd,indent= 4)
    with open('flagstats.json', 'w') as cd:
        json.dump(flagstats, cd,indent= 4)

@client.command(pass_context = True)
@commands.has_role(v['tfc'])
async def refreshlb(ctx):
    with open('kills.json') as f:
        kills = json.load(f)
    with open('damage.json') as f:
        damage = json.load(f)
    with open('flagstats.json') as f:
        flagstats = json.load(f)
    kills2 = pruneDict(kills)
    with open('kills.json') as f:
        kills = json.load(f)
    damage2 = pruneDict(damage)
    with open('damage.json') as f:
        damage = json.load(f)
    flagstats2 = pruneDict(flagstats)
    with open('flagstats.json') as f:
        flagstats = json.load(f)

    print(f'{kills}\n{damage}\n{flagstats}')
    print(f'{len(list(kills))}\n{len(list(damage))}\n{len(list(flagstats))}')
    
    '''channel = await client.fetch_channel(1058272007843754075)
    kmsg = await channel.fetch_message(1058325463950446622)
    kmsg2 = await channel.fetch_message(1058325464994816000)
    fmsg = await channel.fetch_message(1058325467976970320)'''
    channel = await client.fetch_channel(1058272007843754075)
    kmsg = await channel.fetch_message(1058325463950446622)
    kmsg2 = await channel.fetch_message(1058325464994816000)
    fmsg = await channel.fetch_message(1058325467976970320)

    #total kills
    space = " "
    totalKills = simplifyDict(kills2, 1)
    totalKills = {k: v for k, v in sorted(totalKills.items(), key=lambda item: item[1], reverse=True)}
    x = 0
    msgList = [f'LAST REFRESH: {str(datetime.now())}\n\n',"TOTAL KILLS\n"]
    for i in list(totalKills):
        #print("totalKills[list(totalKills)[0]")
        if (x < 4): msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')        
        elif(x == 4):msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')
        x += 1
        if(x == 5): break

    #total kills per game
    totalKills = simplifyDict(kills2, 1, "Yes")
    totalKills = {k: v for k, v in sorted(totalKills.items(), key=lambda item: item[1], reverse=True)}
    x = 0
    msgList.append("\nTOTAL KILLS PER GAME\n")
    for i in list(totalKills):
        if (x < 4): msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')        
        elif(x == 4): msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')
        x += 1
        if(x == 5): break
    #total defensive kills
    totalKills = simplifyDict(kills2, 2)
    totalKills = {k: v for k, v in sorted(totalKills.items(), key=lambda item: item[1], reverse=True)}
    x = 0
    msgList.append("\nTOTAL DEFENSIVE KILLS\n")
    for i in list(totalKills):
        if (x < 4): msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')        
        elif(x == 4):msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')
        x += 1
        if(x == 5): break
    #total offensive kills
    totalKills = simplifyDict(kills2, 3)
    totalKills = {k: v for k, v in sorted(totalKills.items(), key=lambda item: item[1], reverse=True)}
    x = 0
    msgList.append("\nTOTAL OFFENSIVE KILLS\n")
    for i in list(totalKills):
        if (x < 4): msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')        
        elif(x == 4): msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')
        x += 1
        if(x == 5): break
    msg = "".join(msgList)
    await kmsg.edit(content=f"```{msg}```")
    #total kills as Soldier
    totalKills = simplifyDict(kills2, 4)
    totalKills = {k: v for k, v in sorted(totalKills.items(), key=lambda item: item[1], reverse=True)}
    x = 0
    msgList = ["\nTOTAL KILLS AS SOLDIER\n"]
    for i in list(totalKills):
        if (x < 4): msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')        
        elif(x == 4): msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')
        x += 1
        if(x == 5): break
    #total kills as Demoman
    totalKills = simplifyDict(kills2, 5)
    totalKills = {k: v for k, v in sorted(totalKills.items(), key=lambda item: item[1], reverse=True)}
    x = 0
    msgList.append("\nTOTAL KILLS AS DEMOMAN\n")
    for i in list(totalKills):
        if (x < 4): msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')        
        elif(x == 4):msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')
        x += 1
        if(x == 5): break
    #total kills as medic
    totalKills = simplifyDict(kills2, 6)
    totalKills = {k: v for k, v in sorted(totalKills.items(), key=lambda item: item[1], reverse=True)}
    x = 0
    msgList.append("\nTOTAL KILLS AS MEDIC\n")
    for i in list(totalKills):
        if (x < 4): msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')        
        elif(x == 4):msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')
        x += 1
        if(x == 5): break
    #total kills as hwguy
    totalKills = simplifyDict(kills2, 7)
    totalKills = {k: v for k, v in sorted(totalKills.items(), key=lambda item: item[1], reverse=True)}
    x = 0
    msgList.append("\nTOTAL KILLS AS HWGUY\n")
    for i in list(totalKills):
        if (x < 4): msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')        
        elif(x == 4): msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')
        x += 1
        if(x == 5): break
    #total kills as Spy
    totalKills = simplifyDict(kills2, 8)
    totalKills = {k: v for k, v in sorted(totalKills.items(), key=lambda item: item[1], reverse=True)}
    x = 0
    msgList.append("\nTOTAL KILLS AS SPY\n")
    for i in list(totalKills):
        if (x < 4): msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')        
        elif(x == 4):msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')
        x += 1
        if(x == 5): break
    #total kills as Engineer
    totalKills = simplifyDict(kills2, 9)
    totalKills = {k: v for k, v in sorted(totalKills.items(), key=lambda item: item[1], reverse=True)}
    x = 0
    msgList.append("\nTOTAL KILLS AS ENGINEER\n")
    for i in list(totalKills):
        if (x < 4): msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')        
        elif(x == 4):msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')
        x += 1
        if(x == 5): break
    #total SG Kills
    totalKills = simplifyDict(kills2, 10)
    totalKills = {k: v for k, v in sorted(totalKills.items(), key=lambda item: item[1], reverse=True)}
    x = 0
    msgList.append("\nTOTAL SGs DESTROYED\n")
    for i in list(totalKills):
        if (x < 4): msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')        
        elif(x == 4): msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')
        x += 1
        if(x == 5): break
    #total kills with SG
    totalKills = simplifyDict(kills2, 11)
    totalKills = {k: v for k, v in sorted(totalKills.items(), key=lambda item: item[1], reverse=True)}
    x = 0
    msgList.append("\nTOTAL KILLS WITH SG\n")
    for i in list(totalKills):
        if (x < 4): msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')        
        elif(x == 4):msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')
        x += 1
        if(x == 5): break
    #total kills with knife
    totalKills = simplifyDict(kills2, 12)
    totalKills = {k: v for k, v in sorted(totalKills.items(), key=lambda item: item[1], reverse=True)}
    x = 0
    msgList.append("\nTOTAL KILLS WITH KNIFE\n")
    for i in list(totalKills):
        if (x < 4): msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')        
        elif(x == 4):msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')
        x += 1
        if(x == 5): break
    msg = "".join(msgList)
    await kmsg2.edit(content=f'```{msg}```')

    #total offensive damage
    totalKills = simplifyDict(damage2, 2)
    totalKills = {k: v for k, v in sorted(totalKills.items(), key=lambda item: item[1], reverse=True)}
    x = 0
    msgList = ["TOTAL OFFENSIVE DAMAGE\n"]
    for i in list(totalKills):
        if (x < 4): msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')        
        elif(x == 4):msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')
        x += 1
        if(x == 5): break
    #total offensive damage per game
    totalKills = simplifyDict(damage2, 2, "yes")
    totalKills = {k: v for k, v in sorted(totalKills.items(), key=lambda item: item[1], reverse=True)}
    x = 0
    msgList.append("\nTOTAL OFFENSIVE DAMAGE PER GAME\n")
    for i in list(totalKills):
        if (x < 4): msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')        
        elif(x == 4): msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')
        x += 1
        if(x == 5): break
    #total defensive damage
    totalKills = simplifyDict(damage2, 1)
    totalKills = {k: v for k, v in sorted(totalKills.items(), key=lambda item: item[1], reverse=True)}
    x = 0
    msgList.append("\nTOTAL DEFENSIVE DAMAGE\n")
    for i in list(totalKills):
        if (x < 4): msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')        
        elif(x == 4): msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')
        x += 1
        if(x == 5): break
    #total defensive damage per game
    totalKills = simplifyDict(damage2, 1, "yes")
    totalKills = {k: v for k, v in sorted(totalKills.items(), key=lambda item: item[1], reverse=True)}
    x = 0
    msgList.append("\nTOTAL DEFENSIVE DAMAGE PER GAME\n")
    for i in list(totalKills):
        if (x < 4): msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')        
        elif(x == 4):msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')
        x += 1
        if(x == 5): break

    #total touches 
    totalKills = simplifyDict(flagstats2, 1)
    totalKills = {k: v for k, v in sorted(totalKills.items(), key=lambda item: item[1], reverse=True)}
    x = 0
    msgList.append("\nTOTAL FLAG TOUCHES\n")
    for i in list(totalKills):
        if (x < 4): msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')        
        elif(x == 4): msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')
        x += 1
        if(x == 5): break
    #total touches per game
    totalKills = simplifyDict(flagstats2, 1, "yes")
    totalKills = {k: v for k, v in sorted(totalKills.items(), key=lambda item: item[1], reverse=True)}
    x = 0
    msgList.append("\nTOTAL FLAG TOUCHES PER GAME\n")
    for i in list(totalKills):
        if (x < 4): msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')        
        elif(x == 4): msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')
        x += 1
        if(x == 5): break
    #total caps
    totalKills = simplifyDict(flagstats2, 2)
    totalKills = {k: v for k, v in sorted(totalKills.items(), key=lambda item: item[1], reverse=True)}
    x = 0
    msgList.append("\nTOTAL CAPTURES\n")
    for i in list(totalKills):
        if (x < 4): msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')        
        elif(x == 4):msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')
        x += 1
        if(x == 5): break
    #total caps PER GAME
    totalKills = simplifyDict(flagstats2, 2, "yes")
    totalKills = {k: v for k, v in sorted(totalKills.items(), key=lambda item: item[1], reverse=True)}
    x = 0
    msgList.append("\nTOTAL CAPTURES PER GAME\n")
    for i in list(totalKills):
        if (x < 4): msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')        
        elif(x == 4): msgList.append(f'{i}{space * (30 - len(i))}{totalKills[i]}\n')
        x += 1
        if(x == 5): break
    print(len(kills2))
    msg = "".join(msgList)
    await fmsg.edit(content=f'```{msg}```')

@client.command(pass_context=True)
@commands.cooldown(1, 300, commands.BucketType.user)
async def reg(ctx, steamid):
    playername = ctx.author.display_name

    with open('kills.json') as f:
        kills = json.load(f)
    with open('damage.json') as f:
        damage = json.load(f)
    with open('flagstats.json') as f:
        flagstats = json.load(f)

    if(steamid in list(kills) and steamid in list(damage) and steamid in list(flagstats)):
        kills[steamid][13] = playername
        damage[steamid][3] = playername
        flagstats[steamid][3] = playername
    else:
        kills[steamid] = [0,0,0,0,0,0,0,0,0,0,0,0,0,playername]
        damage[steamid] = [0,0,0,playername]
        flagstats[steamid] = [0,0,0,playername]

    with open('kills.json', 'w') as cd:
        json.dump(kills, cd,indent= 4)
    with open('damage.json', 'w') as cd:
        json.dump(damage, cd,indent= 4)
    with open('flagstats.json', 'w') as cd:
        json.dump(flagstats, cd,indent= 4)

    await ctx.author.send("Recorded")


@client.command(pass_context=True)
async def stats(ctx, region = None):
    with open('login.json') as f:
        logins = json.load(f)
    schannel = await client.fetch_channel(1000847501194174675)
    if(region.lower() == "none"):
        await ctx.send("please specify region..")
    elif(region.lower() == 'east' or region.lower() == 'central'):
      try:
        ftp = FTP(logins[region][0])
        ftp.login(user= logins[region][1], passwd=logins[region][2])
        ftp.cwd('tfc')
        ftp.cwd('logs')

        list = ftp.nlst()

        newList = []
        for i in list:
            size = (ftp.size(i))
            if((size > 300000) and (".log" in i)):
                newList.append(i)

        logToParse1 = newList[-2]
        logToParse2 = newList[-1]

        try:
            ftp.retrbinary("RETR " + logToParse1 ,open(logToParse1, 'wb').write)
            ftp.retrbinary("RETR " + logToParse2 ,open(logToParse2, 'wb').write)
        except:
            print("Error")

        f = open(logToParse1)
        pDate = None
        pMap = None
        for line in f:
          if("Loading map" in line):
            mapstart = line.find('map "') + 5
            mapend = line.find('"', mapstart)
            datestart = line.find('L ') + 2
            dateend = line.find('-', datestart)
            pDate =  line[datestart:dateend]
            pMap = line[mapstart:mapend]
        f.close()


        #os.system(f"cp {logToParse1} coachn-{logToParse1}")
        #os.system(f"cp {logToParse2} coachn-{logToParse2}")

        #logToParse1 = "coachn-" + logToParse1
        #logToParse2 = "coachn-" + logToParse2
        #print(logToParse1[7:])
        #print(logToParse2[7:])
        #newCMD = 'curl -v -F "process=true" -F "inptImage=@' + logToParse1 + '" -F "language=en" -F "blarghalyze=Blarghalyze!" http://blarghalyzer.com/Blarghalyzer.php'
        #output = os.popen(newCMD).read()
        #newCMD = 'curl -v -F "process=true" -F "inptImage=@' + logToParse2 + '" -F "language=en" -F "blarghalyze=Blarghalyze!" http://blarghalyzer.com/Blarghalyzer.php'
        #output2 = os.popen(newCMD).read()
        #site = "**Round 1:** https://blarghalyzer.com/parsedlogs/" + logToParse1[:-4].lower() + "/ **Round 2:** https://blarghalyzer.com/parsedlogs/" + logToParse2[:-4].lower() + "/"
        #newCMD = 'curl -X POST -F logs[]=@' + logToParse1 + ' -F logs[]=@' + logToParse2 + ' http://app.hampalyzer.com/api/parseGame'
        output3 = "34879y45987543987453987043987439870453987345987439874387943578934578" #os.popen(newCMD).read()
        hampa = "http://app.hampalyzer.com/" + output3[21:-3]
        
        #os.remove(logToParse1[7:])
        #os.remove(logToParse2[7:])

        '''try:
            os.chdir('..')
            os.chdir('demos')
            list = []
            list = sorted(os.listdir())

            newList = []
            for i in list:
                size = (os.path.getsize(i))
                if((size > 10000000) and (".dem" in i)):
                    newList.append(i)

            demoToZip1 = newList[-2]
            demoToZip2 = newList[-1]
            dDate = pDate.replace("/", "")
            try:
                import zlib
                mode= zipfile.ZIP_DEFLATED
            except:
                mode= zipfile.ZIP_STORED
            newfile = pMap + "-" + dDate + ".zip"
            zip= zipfile.ZipFile(newfile, 'w', mode)
            zip.write(demoToZip1)
            zip.write(demoToZip2)
            zip.close()
            #os.remove(demo)

        except:
            newfile = None'''

        await schannel.send(f"**Hampalyzer:** {hampa} {pMap} {pDate} {region}")
        try:
            statUpdater(logToParse1,logToParse2)
        except Exception as e:
            print('su failed', e)
        try:
            await refreshlb(ctx)
        except:
            print("rlb failed")
        os.remove(logToParse1)
        os.remove(logToParse2)
        

        #if(newfile == None):
            #await pChannel.send(content=f"{site} {pMap} {pDate}\n **Hampalyzer:** {hampa}")

        '''delList = ftp.nlst()
        for i in delList:
          if(i not in newList):
            ftp.delete(i)
        ftp.delete(logToParse1)
        ftp.delete(logToParse2)'''
        '''else:
            #await pChannel.send(file = discord.File(newfile), content=f"{site} {pMap} {pDate}\n **Hampalyzer:** {hampa}")
            os.remove(demoToZip1)
            os.remove(demoToZip2)
            os.remove(newfile)'''
      except Exception as e:
        await ctx.send(f"{e}")

@client.command(pass_context=True)
@commands.has_role(v['runner'])
async def bwin(ctx, team, pNumber = "None"):
    global ELOpop
    if((ctx.name == v['pc']) or (ctx.name == 'tfc-admins') or (ctx.name == 'tfc-runners')):    
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

        await ctx.send("**AUTO-REPORTING** CONFIRMED")

@client.event
async def on_message(message):
    channel = await client.fetch_channel(v['pID'])
    if(message.content == "!draw" or message.content == "!win 1" or message.content == "!win 2"):
        user = await client.fetch_user(message.author.id)
        if(user.bot):
            if("!draw" in message.content):
                await bwin(channel, "draw")
            if("!win 1" in message.content):
                await bwin(channel, "1")
            if("!win 2" in message.content):
                await bwin(channel, "2")
    if("!stats" in message.content):
        user = await client.fetch_user(message.author.id)
        if(user.bot):
            content = str(message.content)
            content = content[7:]
            await stats(channel, content.lower())
            


    await client.process_commands(message)


client.run(MAKE SURE TO PUT TOKEN HERE)
