import asyncio
import json
import discord
from discord.ext import commands
from discord.utils import get
import matplotlib.pyplot as plt
from discord.ext import tasks
import os
import random
import itertools
import time
import requests
import mysql.connector
import logging

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

intents = discord.Intents.all()
client = commands.Bot(
    command_prefix=["!", "+", "-"], case_insensitive=True, intents=intents
)
client.remove_command("help")

# Load in ELO configuration
with open("ELOpop.json") as f:
    ELOpop = json.load(f)

# Load in main script configuration
with open("variables.json") as f:
    v = json.load(f)

# TODO: Update login to work differently..

with open("login.json") as f:
    logins = json.load(f)

# =====================================
# =========== DEFINE GLOBALS ==========
# =====================================

GLOBAL_LOCK = asyncio.Lock()

# ELOpop scheme
# ELOpop contains at the root a map of player ID (i.e. str(ctx.author.id)) to a list of variables metadata slots
PLAYER_MAP_VISUAL_NAME_INDEX = 0  # Player's visual name
PLAYER_MAP_CURRENT_ELO_INDEX = 1  # Player's current ELO number
PLAYER_MAP_VISUAL_RANK_INDEX = 3  # current visual rank icon
PLAYER_MAP_WIN_INDEX = 4
PLAYER_MAP_LOSS_INDEX = 5
PLAYER_MAP_DRAW_INDEX = 6
PLAYER_MAP_ACHIEVEMENT_INDEX = 7  # list of achievement icons
PLAYER_MAP_DUNCE_FLAG_INDEX = 8  # Is this player a dunce or not?
PLAYER_MAP_NUM_ENTRIES = 9  # Note: Bump this when adding another player map entry
PAST_TEN_BLUE_TEAM_INDEX = 0
PAST_TEN_RED_TEAM_INDEX = 4
PAST_TEN_MATCH_OUTCOME_INDEX = 8
PAST_TEN_MAP_INDEX = 9
LOCAL_DEV_ENABLED = bool(os.getenv("TFCELO_LOCAL_DEV")) is True
DEV_TESTING_CHANNEL = 1139762727275995166
MAP_VOTE_FIRST = True

cap1 = None
cap1Name = None
cap2 = None
cap2Name = None
playersAdded = []
playersAbstained = []
players_abstained_discord_id = []
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

# =====================================
# =====================================
# =====================================

# ========= DATA CONVERSION ========
# Add any data conversion if necessary to the database
for playerIDKey, playerValues in ELOpop.items():
    # print (ELOpop[playerIDKey])
    if len(playerValues) < (PLAYER_MAP_DUNCE_FLAG_INDEX + 1):
        playerValues.append(None)  # Start out not as a dunce
        logging.info(f"Converted: {playerValues}")
# ========= END DATA CONVERSION ====

# Write ELO database changes out
with open("ELOpop.json", "w") as cd:
    json.dump(ELOpop, cd, indent=4)


@client.event
async def on_ready():
    global GLOBAL_LOCK
    logging.info("on_ready!")
    # Remake the global lock to try to get it compatible with the bot's event loop
    # TODO: I don't fully understand why or if this helps exactly.
    GLOBAL_LOCK = asyncio.Lock()


@client.command(pass_context=True)
@commands.has_role(v["rater"])
async def search(ctx, searchkey):
    """
    Allow users with "rater" role to search for a player's ELO

    Example usage: "!search kix" in the #tfc-ratings channel
    ctx: Discord context object
    searchkey: string to search for in list of players
    """
    async with GLOBAL_LOCK:
        if (ctx.channel.name == "tfc-ratings") or (
            LOCAL_DEV_ENABLED and ctx.channel.name == "test-zero"
        ):
            with open("ELOpop.json") as f:
                ELOpop = json.load(f)
            searchList = []
            for i in list(ELOpop):
                if searchkey.lower() in ELOpop[i][0].lower():
                    searchList.append(ELOpop[i][0])

            pMsgList = []
            for i in searchList:
                playerID = None
                for j in list(ELOpop):
                    if i == ELOpop[j][0]:
                        playerID = j
                pMsgList.append(
                    i
                    + " " * (30 - len(i))
                    + " ELO: "
                    + str(ELOpop[playerID][1])
                    + "                 1-20 rank: "
                    + str(ELOpop[playerID][1] / 120)
                    + f"     W:{ELOpop[playerID][4]} L:{ELOpop[playerID][5]} D:{ELOpop[playerID][6]}\n"
                )
            mMsg = "".join(pMsgList)

            if len(searchList) > 0:
                await ctx.send(content="```\n" + mMsg + "```")
            else:
                await ctx.send("No results with that search string..")


# Allow all players to toggle their rank being private or hidden
# Example: !private
@client.command(pass_context=True)
async def private(ctx):
    global ELOpop
    async with GLOBAL_LOCK:
        with open("ELOpop.json") as f:
            ELOpop = json.load(f)

        if ELOpop[str(ctx.author.id)][3] != "<:norank:1001265843683987487>":
            ELOpop[str(ctx.author.id)][3] = "<:norank:1001265843683987487>"
            await ctx.author.send("Your ELO Rank is now private")

        else:
            # newRank(str(ctx.author.id))
            ELOpop[str(ctx.author.id)][3] = getRank(str(ctx.author.id))
            await ctx.author.send("Your ELO Rank is back")

        with open("ELOpop.json", "w") as cd:
            json.dump(ELOpop, cd, indent=4)


@client.command(pass_context=True)
async def top15(ctx):
    """"
    Show the list of top, non-private players in the discord

    Example usage: "!top15"
    ctx: Discord context object
    """
    global ELOpop
    async with GLOBAL_LOCK:
        with open("ELOpop.json") as f:
            ELOpop = json.load(f)

        db = mysql.connector.connect(
            host=logins['mysql']['host'],
            user=logins['mysql']['user'],
            passwd=logins['mysql']['passwd'],
            database=logins['mysql']['database'],
        )
        mycursor = db.cursor()

        try:
            mycursor.execute(
                    """
                    with elo_row_numbered as (
                        select player_name, discord_id, player_elos, row_number() over (partition by player_name order by entryID desc) as row_num from player_elo
                    )

                    select player_name, discord_id, player_elos from elo_row_numbered where row_num = 1
                    order by player_elos desc;""")
            top_15 = []

            for row in mycursor:
                print(row)
                discord_id = str(row[1])
                if ELOpop[discord_id][PLAYER_MAP_VISUAL_RANK_INDEX] != "<:norank:1001265843683987487>" and getRank(discord_id) != "<:questionMark:972369805359337532>":
                    top_15.append(getRank(discord_id) + " " + ELOpop[discord_id][PLAYER_MAP_VISUAL_NAME_INDEX] + "\n")
                if len(top_15) == 15:
                    break

            message_formatted = "".join(top_15)
            embed = discord.Embed(title="Top 15 Non-Private Players")
            embed.add_field(
                name="Player List", value=message_formatted, inline=True
            )
            await ctx.send(embed=embed)
        except Exception as e:
            logging.error(e)
            await ctx.send(e)


# Toggle the "dunce" on a player (for being naughty) at admin discretion
# Example: !dunce @MILOS chopping
@client.command(pass_context=True)
@commands.has_role(v["admin"])
async def dunce(ctx, player: discord.Member, reason=None):
    global PLAYER_MAP_DUNCE_FLAG_INDEX
    async with GLOBAL_LOCK:
        # Open ELO database
        with open("ELOpop.json") as f:
            ELOpop = json.load(f)

        if ELOpop[str(player.id)][PLAYER_MAP_DUNCE_FLAG_INDEX] is None:
            if reason is None:
                await ctx.send("Please provide a reason!")
            else:
                ELOpop[str(player.id)][PLAYER_MAP_DUNCE_FLAG_INDEX] = reason
                await ctx.send(f"{player.display_name} is a dunce! Reason: {reason}")
        else:
            originalReason = ELOpop[str(player.id)][PLAYER_MAP_DUNCE_FLAG_INDEX]
            ELOpop[str(player.id)][PLAYER_MAP_DUNCE_FLAG_INDEX] = None
            await ctx.send(
                f"{player.display_name} is no longer a dunce! (original reason: {originalReason})"
            )

        # Write ELO database changes out
        with open("ELOpop.json", "w") as cd:
            json.dump(ELOpop, cd, indent=4)


# Resets pickup upon a completed vote or !cancel
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
    # playersAdded = []
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


# Populates a list of players whom have voted for a particular map
def mapVoteOutput(mapChoice):
    global mapVotes
    whoVoted = []
    for i in mapVotes[mapChoice]:
        # whoVoted.append(ELOpop[i][0])
        whoVoted.append(i)
    numVotes = len(whoVoted)
    whoVoted = ", ".join(whoVoted)

    if len(whoVoted) == 0:
        return "0 votes"

    return "%d votes (%s)" % (numVotes, whoVoted)


@tasks.loop(seconds=1)  # repeat after every 10 seconds
async def fVCoolDown():
    global fTimer
    if fTimer > 0:
        fTimer = fTimer - 1


# Selects maps from two different json files.  options 1/2 are from mainmaps.json and option 3 is from specmaps.json
def PickMaps():
    global mapChoice1
    global mapChoice2
    global mapChoice3
    global loveMaps
    global hateMaps
    global mapVotes
    global alreadyVoted
    global votePhase
    global lastFive
    with open("mainmaps.json") as f:
        mapList = json.load(f)

    mapVotes = {}
    alreadyVoted = []
    mapPick = []
    if len(lastFive) == 0:
        # Seed lastFive from the last 5 pickups played so that this value is never empty
        with open("pastten.json") as f:
            past_ten = json.load(f)
            print(past_ten)
            past_ten_keys_list = list(past_ten.keys())
            past_ten_keys_list.reverse()
            for match in past_ten_keys_list:
                map = past_ten[match][PAST_TEN_MAP_INDEX].replace("Bot's Choice - ", '')
                lastFive.append(map)
                if len(lastFive) == 5:
                    break

    for i in list(mapList):
        if i not in mapSelected:
            if (i not in lastFive) and (i not in hateMaps):
                if i in loveMaps:
                    mapPick.append(i)
                    mapPick.append(i)
                    mapPick.append(i)
                    mapPick.append(i)
                    mapPick.append(i)
                else:
                    mapPick.append(i)
    mapPick2 = []
    with open("specmaps.json") as f:
        mapList = json.load(f)

    for i in list(mapList):
        if i not in mapSelected:
            if (i not in lastFive) and (i not in hateMaps):
                if i in loveMaps:
                    mapPick2.append(i)
                    mapPick2.append(i)
                    mapPick2.append(i)
                    mapPick2.append(i)
                    mapPick2.append(i)
                else:
                    mapPick2.append(i)

    logging.info(f"Map Lists: {mapPick} {mapPick2}")
    logging.info(f"Maps Selected: {mapSelected}")
    logging.info(f"Love Maps: {loveMaps}")
    logging.info(f"Hate Maps: {hateMaps}")
    logging.info(f"Last Five: {lastFive}")

    mapChoice1 = random.choice(mapPick)
    while mapChoice1 in mapPick:
        mapPick.remove(mapChoice1)
    mapVotes[mapChoice1] = []
    mapSelected.append(mapChoice1)
    mapChoice2 = random.choice(mapPick)
    while mapChoice2 in mapPick:
        mapPick.remove(mapChoice2)
    mapVotes[mapChoice2] = []
    mapSelected.append(mapChoice2)
    mapChoice3 = random.choice(mapPick2)
    while mapChoice3 in mapPick2:
        mapPick2.remove(mapChoice3)
    mapVotes[mapChoice3] = []
    mapSelected.append(mapChoice3)


# function for testing visualizing map choices without needing a full game
# !pick_maps_test
@client.command(pass_context=True, aliases=["pmtest"])
@commands.has_role(v["admin"])
async def pick_maps_test(ctx):
    PickMaps()


# This function manages the captain's mode.
def TeamPickPopulate():
    global msg
    global eligiblePlayers
    global pickCount
    global pTotalPlayers
    msgList = []
    redTeamList = ["🔴 Red Team 🔴\n"]
    blueTeamList = ["🔵 Blue Team 🔵\n"]
    for i in pTotalPlayers:
        msgList.append(str(i[0]) + ". " + i[1] + "\n")
    for i in redTeam:
        redTeamList.append(i + "\n")
    for i in blueTeam:
        blueTeamList.append(i + "\n")

    msg = "".join(msgList)
    blueMsg = "".join(blueTeamList)
    redMsg = "".join(redTeamList)
    if (pickCount == 0) or (pickCount == 2):
        msg = "🔴 Red Team 🔴 picks!\n\n" + msg + "\n" + blueMsg + "\n" + redMsg
    elif pickCount > 4:
        msg = msg + "\n" + blueMsg + "\n" + redMsg
    else:
        msg = "🔵 Blue Team 🔵 picks!\n\n" + msg + "\n" + blueMsg + "\n" + redMsg
    return msg

@client.command(pass_context=True)
async def testVote(ctx):
    async with GLOBAL_LOCK:
        channel = await client.fetch_channel(v["pID"])
        if channel.name == v["pc"]:
            global vMsg
            await vMsg.reply("Click the link above to go the current vote!")
            # await channel.send(vMsg)

# Sets up voting and manages the voting process
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
    global playersAbstained
    global players_abstained_discord_id

    channel = await client.fetch_channel(v["pID"])
    with open("ELOpop.json") as f:
        ELOpop = json.load(f)
    if serverVote == 1:
        mapChoice1 = "London - EU"
        mapVotes[mapChoice1] = []
        mapChoice2 = "Chicago - Central"
        mapVotes[mapChoice2] = []
        mapChoice3 = "New York - East"
        mapVotes[mapChoice3] = []

        playersAbstained = []
        players_abstained_discord_id = []
        for i in eligiblePlayers:
            if i not in alreadyVoted:
                playersAbstained.append(ELOpop[i][0])
                players_abstained_discord_id.append(i)
        toVoteString = "```"
        if len(playersAbstained) != 0:
            toVoteString = "\n💩 " + ", ".join(playersAbstained) + " need to vote 💩```"

        vMsg = await channel.send(
            "````Vote for your server! (Please wait for everyone to vote, or sub AFK players)\n\n"
            + "1️⃣ "
            + mapChoice1
            + " " * (70 - len(mapChoice1))
            + mapVoteOutput(mapChoice1)
            + "\n"
            + "2️⃣ "
            + mapChoice2
            + " " * (70 - len(mapChoice2))
            + mapVoteOutput(mapChoice2)
            + "\n"
            + "3️⃣ "
            + mapChoice3
            + " " * (70 - len(mapChoice3))
            + mapVoteOutput(mapChoice3)
            + toVoteString
        )

        await vMsg.add_reaction("1️⃣")
        await vMsg.add_reaction("2️⃣")
        await vMsg.add_reaction("3️⃣")
        votable = 1

    elif (reVote == 0) and (serverVote == 0):
        with open("ELOpop.json") as f:
            ELOpop = json.load(f)

        alreadyVoted = []
        mapVotes = {}
        PickMaps()
        mapChoice4 = "New Maps"
        mapVotes[mapChoice4] = []

        playersAbstained = []
        players_abstained_discord_id = []
        for i in eligiblePlayers:
            if i not in alreadyVoted:
                playersAbstained.append(ELOpop[i][0])
                players_abstained_discord_id.append(i)
        toVoteString = "```"
        if len(playersAbstained) != 0:
            toVoteString = "\n💩 " + ", ".join(playersAbstained) + " need to vote 💩```"
        with open("mainmaps.json") as f:
            mapList = json.load(f)
        with open("specmaps.json") as f:
            mapList2 = json.load(f)
        vMsg = await channel.send(
            "```Vote up and make sure you hydrate!\n\n"
            + "1️⃣ "
            + mapChoice1
            + " " * (25 - len(mapChoice1))
            + "   "
            + str(mapList[mapChoice1])
            + " mirv"
            + " " * 15
            + mapVoteOutput(mapChoice1)
            + "\n"
            + "2️⃣ "
            + mapChoice2
            + " " * (25 - len(mapChoice2))
            + "   "
            + str(mapList[mapChoice2])
            + " mirv"
            + " " * 15
            + mapVoteOutput(mapChoice2)
            + "\n"
            + "3️⃣ "
            + mapChoice3
            + " " * (25 - len(mapChoice3))
            + "   "
            + str(mapList2[mapChoice3])
            + " mirv"
            + " " * 15
            + mapVoteOutput(mapChoice3)
            + "\n"
            + "4️⃣ "
            + mapChoice4
            + " " * (49 - len(mapChoice4))
            + mapVoteOutput(mapChoice4)
            + toVoteString
        )

        await vMsg.add_reaction("1️⃣")
        await vMsg.add_reaction("2️⃣")
        await vMsg.add_reaction("3️⃣")
        await vMsg.add_reaction("4️⃣")
        votable = 1

    elif (reVote == 1) and (serverVote == 0):
        with open("ELOpop.json") as f:
            ELOpop = json.load(f)

        alreadyVoted = []
        mapVotes = {}
        PickMaps()
        mapVotes[mapChoice4] = []

        playersAbstained = []
        players_abstained_discord_id = []
        for i in eligiblePlayers:
            if i not in alreadyVoted:
                playersAbstained.append(ELOpop[i][0])
                players_abstained_discord_id.append(i)
        toVoteString = "```"
        if len(playersAbstained) != 0:
            toVoteString = "\n💩 " + ", ".join(playersAbstained) + " need to vote 💩```"
        with open("mainmaps.json") as f:
            mapList = json.load(f)
        with open("specmaps.json") as f:
            mapList2 = json.load(f)
        vMsg = await channel.send(
            "```Vote up and make sure you hydrate!\n\n"
            + "1️⃣ "
            + mapChoice1
            + " " * (25 - len(mapChoice1))
            + "   "
            + str(mapList[mapChoice1])
            + " mirv"
            + " " * 15
            + mapVoteOutput(mapChoice1)
            + "\n"
            + "2️⃣ "
            + mapChoice2
            + " " * (25 - len(mapChoice2))
            + "   "
            + str(mapList[mapChoice2])
            + " mirv"
            + " " * 15
            + mapVoteOutput(mapChoice2)
            + "\n"
            + "3️⃣ "
            + mapChoice3
            + " " * (25 - len(mapChoice3))
            + "   "
            + str(mapList2[mapChoice3])
            + " mirv"
            + " " * 15
            + mapVoteOutput(mapChoice3)
            + "\n"
            + "4️⃣ "
            + mapChoice4
            + " " * (49 - len(mapChoice4))
            + mapVoteOutput(mapChoice4)
            + toVoteString
        )

        await vMsg.add_reaction("1️⃣")
        await vMsg.add_reaction("2️⃣")
        await vMsg.add_reaction("3️⃣")
        await vMsg.add_reaction("4️⃣")
        votable = 1


@client.command(pass_context=True)
@commands.has_role(v["admin"])
async def addach(ctx, key, value):
    async with GLOBAL_LOCK:
        with open("emotes.json") as f:
            e = json.load(f)

        e[key] = value

        with open("emotes.json", "w") as cd:
            json.dump(e, cd, indent=4)
        await ctx.send("value has been added to the list of achievements")


# will pick a random map
@client.command(pass_context=True, aliases=["map"])
@commands.has_role(v["runner"])
async def pickRandomMap(ctx):
    with open("mainmaps.json") as f:
        mapList = json.load(f)
    global lastFive

    rMap = random.choice(list(mapList))
    channel = await client.fetch_channel(v["pID"])

    while rMap in lastFive:
        rMap = random.choice(list(mapList))
    await channel.send(f"The map chosen is **{rMap}**")

    return rMap


@client.command(pass_context=True)
@commands.has_role(v["admin"])
async def ach(ctx, player: discord.Member, ach):
    async with GLOBAL_LOCK:
        with open("ELOpop.json") as f:
            ELOpop = json.load(f)
        with open("emotes.json") as f:
            e = json.load(f)
        channel = await client.fetch_channel(1004934664475115582)
        ELOpop[str(player.id)][7].append(e[ach])

        with open("ELOpop.json", "w") as cd:
            json.dump(ELOpop, cd, indent=4)

        await ctx.send(
            f"{player.id} has been successfully given the achievement {e[ach]}"
        )
        await channel.send(
            f"Congratulations {player.display_name} for completing the {e[ach]} achievement!"
        )


# Utility function for showing the pickup
async def showPickup(ctx, showReact=False, mapVoteFirstPickupStarted=False):
    global playersAdded
    global capList
    global oMsg
    global ready
    global PLAYER_MAP_DUNCE_FLAG_INDEX
    global PLAYER_MAP_VISUAL_NAME_INDEX
    global PLAYER_MAP_VISUAL_RANK_INDEX
    with open("ELOpop.json") as f:
        ELOpop = json.load(f)

    isMapVoteFirstPickupStarted = False
    if ((inVote == 1 or mapVoteFirstPickupStarted) and MAP_VOTE_FIRST == True):
        isMapVoteFirstPickupStarted = True

    msgList = []
    msgListLight = []
    for i in playersAdded:
        achList = ELOpop[i][7]
        if "norank" in ELOpop[i][3]:
            visualRank = ELOpop[i][3]
        else:
            visualRank = getRank(i)  # ELOpop[i][PLAYER_MAP_VISUAL_RANK_INDEX]
            # await ctx.send(f"{ELOpop[i][3]}")

        if (
            ELOpop[i][PLAYER_MAP_DUNCE_FLAG_INDEX] is not None
        ):  # Is player a naughty dunce?
            ach = (
                v["dunce"]
                + "- Dunce cap for: "
                + ELOpop[i][PLAYER_MAP_DUNCE_FLAG_INDEX]
            )  # Achievements get wiped and replaced with the dunce cap
            visualRank = getRank(i)  # Always show the rank of the dunce as a punishment
            win_emblem = '' # Dunces don't get an emblem to show off
        else:
            ach = "".join(achList)  # Not a dunce, use their real achievements
            win_emblem = str(get_win_emblem(ctx, i))

        if i in capList:
            msgList.append(
                visualRank
                + " "
                + win_emblem
                + " "
                + ELOpop[i][PLAYER_MAP_VISUAL_NAME_INDEX]
                + " "
                + v["cptimg"]
                + " "
                + ach
                + "\n"
            )
            msgListLight.append(
                visualRank
                + " "
                + ELOpop[i][PLAYER_MAP_VISUAL_NAME_INDEX]
                + " "
                + v["cptimg"]
                + "\n"
            )
        else:
            msgList.append(
                visualRank
                + " "
                + win_emblem
                + " "
                + ELOpop[i][PLAYER_MAP_VISUAL_NAME_INDEX]
                + " "
                + ach
                + "\n"
            )
            msgListLight.append(
                visualRank + " " + ELOpop[i][PLAYER_MAP_VISUAL_NAME_INDEX] + "\n"
            )
    msg = "".join(msgList)
    msgLight = "".join(msgListLight)

    # TODO: We are building a very long string for a single field value.  Max
    # length is 1024.  We should do something smarter if we want to show the achievements
    # for the player ready embed.
    if len(msg) > 1000:
        msg = msgLight

    if len(playersAdded) >= 8:
        # Create the ready message
        readyList = []
        for i in ready:
            readyList.append(f"{ELOpop[i][0]}\n")
        readyMsg = "".join(readyList)

        # Create the emebd
        embed = None
        if (isMapVoteFirstPickupStarted == True):
            embed = discord.Embed(title="Pickup Voting Phase!")
        else:
            embed = discord.Embed(title="Pickup Has 8 or more Players")

        if len(playersAdded) > 0:
            if (isMapVoteFirstPickupStarted == True):
                embed.add_field(
                    name=f"Players Selected (Please Vote!)", value=msg
                )
            else:
                embed.add_field(
                    name=f"Players Added - {len(playersAdded)} Queued", value=msg
                )
        elif len(playersAdded) == 0:
            embed.add_field(name="Players Added", value="PUG IS EMPTY!")

        # Add the ready field to show who is ready
        if len(ready) != 0:
            embed.add_field(name="Players Ready", value=readyMsg)
        elif len(ready) == 0:
            embed.add_field(name="Players Ready", value="\u200b")

        oMsg = await ctx.send(embed=embed)

        if (showReact == True):
            await oMsg.add_reaction("👍")
        notiflist = []
        for i in playersAdded[0:8]:
            notiflist.append(f"<@{i}> ")
        if (showReact == True):
            notiflist.append("... React with 👍 when ready to teams if no runner available.")
        msg = "".join(notiflist)
        await ctx.send(msg)

    elif len(playersAdded) < 8:
        oMsg = None
        embed = discord.Embed(title="Pickup Started!")
        if len(playersAdded) > 0:
            embed.add_field(
                name=f"Players Added - {len(playersAdded)} Queued", value=msg
            )
        elif len(playersAdded) == 0:
            embed.add_field(name="Players Added", value="PUG IS EMPTY!")
        await ctx.send(embed=embed)
    
    if (inVote == 1 and vMsg != None):
        await vMsg.reply("Click the link above to go the current vote!")


async def teamsDisplay(ctx, blueTeam, redTeam, team1prob, team2prob):
    msgList = []

    for i in blueTeam:
        # msgList.append(ELOpop[i][3] + " " + ELOpop[i][0] + "\n")
        msgList.append(ELOpop[i][0] + "\n")
    bMsg = "".join(msgList)
    msgList.clear()
    for i in redTeam:
        # msgList.append(ELOpop[i][3] + " " + ELOpop[i][0] + "\n")
        msgList.append(ELOpop[i][0] + "\n")
    rMsg = "".join(msgList)
    embed = discord.Embed(title="Teams Sorted!")
    # embed.add_field(name = "Blue Team " + v['t1img'] + " " + str(int(team1prob * 100)) + "%", value= bMsg, inline=True)
    embed.add_field(name="Blue Team " + v["t1img"], value=bMsg, inline=True)
    embed.add_field(name="\u200b", value="\u200b")
    # embed.add_field(name = "Red Team " + v['t2img'] + " " + str(int(team2prob * 100)), value= rMsg, inline=True)
    embed.add_field(name="Red Team " + v["t2img"], value=rMsg, inline=True)
    await ctx.send(embed=embed)


async def pastGames(ctx):
    with open("pastten.json") as f:
        past_ten_matches = json.load(f)
    msgList = []
    for i in past_ten_matches:
        match_outcome_string = "Team " + str(past_ten_matches[i][PAST_TEN_MATCH_OUTCOME_INDEX])
        msgList.append(f'{i:.<8}|{match_outcome_string:.^10}|{past_ten_matches[i][PAST_TEN_MAP_INDEX]:.>25}\n')
    msg = "".join(msgList)
    embed = discord.Embed(title="Last 10 Games")
    if len(past_ten_matches) > 0:
        embed.add_field(name="Pickup # | Winner | Map", value=msg, inline=True)
    elif len(past_ten_matches) == 0:
        embed.add_field(name="#", value="Somehow, no last 10 games?", inline=True)
    await ctx.send(embed=embed)


async def openPickups(ctx):
    with open("activePickups.json") as f:
        activePickups = json.load(f)
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
    embed = discord.Embed(title="Active Pickups")
    if len(activePickups) > 0:
        embed.add_field(name="Pickup #", value=msg, inline=True)
        embed.add_field(name="Pickup Date", value=tMsg, inline=True)
        embed.add_field(name="Pickup Map", value=mMsg, inline=True)
    elif len(activePickups) == 0:
        embed.add_field(name="#", value="No unreported pickups!!", inline=True)

    await ctx.send(embed=embed)


def get_win_emblem(ctx, discord_id):
    """Return the corresponding emblem for a player given their win count"""
    with open("ELOpop.json") as f:
        ELOpop = json.load(f)

    if ELOpop[discord_id][PLAYER_MAP_WIN_INDEX] < 10:
        return get(ctx.message.guild.emojis, name="we0") # Civilian
    elif ELOpop[discord_id][PLAYER_MAP_WIN_INDEX] < 25:
        return get(ctx.message.guild.emojis, name="we1") # Scout
    elif ELOpop[discord_id][PLAYER_MAP_WIN_INDEX] < 50:
        return get(ctx.message.guild.emojis, name="we2") # Pyro
    elif ELOpop[discord_id][PLAYER_MAP_WIN_INDEX] < 75:
        return get(ctx.message.guild.emojis, name="we3") # Medic
    elif ELOpop[discord_id][PLAYER_MAP_WIN_INDEX] < 100:
        return get(ctx.message.guild.emojis, name="we4") # Spy
    elif ELOpop[discord_id][PLAYER_MAP_WIN_INDEX] < 250:
        return get(ctx.message.guild.emojis, name="we5") # Sniper
    elif ELOpop[discord_id][PLAYER_MAP_WIN_INDEX] < 500:
        return get(ctx.message.guild.emojis, name="we6") # Engineer
    elif ELOpop[discord_id][PLAYER_MAP_WIN_INDEX] < 750:
        return get(ctx.message.guild.emojis, name="we7") # Soldier
    elif ELOpop[discord_id][PLAYER_MAP_WIN_INDEX] < 1000:
        return get(ctx.message.guild.emojis, name="we8") # Demoman
    else:
        return get(ctx.message.guild.emojis, name="we9") # HWGuy


# Utility function for retrieving the cosmetic ranking number based on ELO for a player ID
def getRank(ID):
    with open("ELOpop.json") as f:
        ELOpop = json.load(f)

    # TODO: Put this in variables.json
    if (ELOpop[ID][PLAYER_MAP_WIN_INDEX] + ELOpop[ID][PLAYER_MAP_LOSS_INDEX] + ELOpop[ID][PLAYER_MAP_DRAW_INDEX]) < 10:
        return "<:questionMark:972369805359337532>"

    if ELOpop[ID][1] < 220:  # 1
        return v["rank1"]
    elif ELOpop[ID][1] < 450:  # 2
        return v["rank2"]
    elif ELOpop[ID][1] < 690:  # 3
        return v["rank3"]
    elif ELOpop[ID][1] < 940:  # 4
        return v["rank4"]
    elif ELOpop[ID][1] < 1200:  # 5
        return v["rank5"]
    elif ELOpop[ID][1] < 1460:  # 6
        return v["rank6"]
    elif ELOpop[ID][1] < 1730:  # 7
        return v["rank7"]
    elif ELOpop[ID][1] < 2010:  # 8
        return v["rank8"]
    elif ELOpop[ID][1] < 2300:  # 9
        return v["rank9"]
    elif ELOpop[ID][1] < 2600:  # 10
        return v["rank10"]
    else:  # S
        return v["rankS"]


# Assign a purely cosmetic ranking number based on ELO assuming they
# have played enough games for one to be stable.
def newRank(ID):
    global ELOpop

    if len(ELOpop[ID][2]) > 9:  # Have they played enough games?
        ELOpop[ID][3] = getRank(ID)
        with open("ELOpop.json", "w") as cd:
            json.dump(ELOpop, cd, indent=4)


@client.command(pass_context=True)
@commands.has_role(v["rater"])
async def avatar(ctx, player: discord.Member, emote):
    async with GLOBAL_LOCK:
        with open("ELOpop.json") as f:
            ELOpop = json.load(f)

        playerID = player.id

        ELOpop[playerID][2] = emote

        with open("ELOpop.json", "w") as cd:
            json.dump(ELOpop, cd, indent=4)


@client.command(pass_context=True)
@commands.has_role(v["rater"])
async def adjustELO(ctx, player, ELO):
    async with GLOBAL_LOCK:
        if ctx.channel.name == v["ratingsChannel"]:
            with open("ELOpop.json") as f:
                ELOpop = json.load(f)
            ELO = int(ELO)

            with open("ELOpop.json") as f:
                ELOpop = json.load(f)
            playerID = None
            for i in ELOpop:
                if ELOpop[i][0] == player:
                    playerID = i
            ELOpop[playerID][1] = ELO

            with open("ELOpop.json", "w") as cd:
                json.dump(ELOpop, cd, indent=4)


@client.command(pass_context=True)
# @commands.has_role(variables['runner'])
async def hello(ctx):
    await ctx.send("bye")


# can swap teams.. this will work as !swap @playerout @playerin and optionally a 3 parameter for if a pickup has already started
# Should reset the ELO points for each team and odds
@client.command(pass_context=True, aliases=["swap"])
@commands.has_role(v["runner"])
async def swapteam(
    ctx, player1: discord.Member, player2: discord.Member, number="None"
):
    async with GLOBAL_LOCK:
        if ctx.channel.name == v["pc"]:
            if number == "None":
                global redTeam
                global blueTeam
                with open("ELOpop.json") as f:
                    ELOpop = json.load(f)
                player1ID = str(player1.id)
                player2ID = str(player2.id)

                blueRank = 0
                redRank = 0

                if player1ID in blueTeam and player2ID in redTeam:
                    redTeam.append(player1ID)
                    blueTeam.remove(player1ID)
                    blueTeam.append(player2ID)
                    redTeam.remove(player2ID)

                elif player1ID in redTeam and player2ID:
                    blueTeam.append(player1ID)
                    redTeam.remove(player1ID)
                    redTeam.append(player2ID)
                    blueTeam.remove(player2ID)

                for j in blueTeam:
                    blueRank += int(ELOpop[j][1])
                for j in redTeam:
                    redRank += int(ELOpop[j][1])

                team1prob = round(1 / (1 + 10 ** ((redRank - blueRank) / 400)), 2)
                team2prob = round(1 / (1 + 10 ** ((blueRank - redRank) / 400)), 2)

                await teamsDisplay(ctx, blueTeam, redTeam, team1prob, team2prob)
            else:
                with open("ELOpop.json") as f:
                    ELOpop = json.load(f)
                with open("activePickups.json") as f:
                    activePickups = json.load(f)
                blueTeam = activePickups[number][2]
                redTeam = activePickups[number][5]
                player1ID = str(player1.id)
                player2ID = str(player2.id)

                blueRank = 0
                redRank = 0

                if player1ID in blueTeam and player2ID in redTeam:
                    redTeam.append(player1ID)
                    blueTeam.remove(player1ID)
                    blueTeam.append(player2ID)
                    redTeam.remove(player2ID)

                elif player1ID in redTeam and player2ID:
                    blueTeam.append(player1ID)
                    redTeam.remove(player1ID)
                    redTeam.append(player2ID)
                    blueTeam.remove(player2ID)

                for j in blueTeam:
                    blueRank += int(ELOpop[j][1])
                for j in redTeam:
                    redRank += int(ELOpop[j][1])

                team1prob = round(1 / (1 + 10 ** ((redRank - blueRank) / 400)), 2)
                team2prob = round(1 / (1 + 10 ** ((blueRank - redRank) / 400)), 2)
                activePickups[number] = [
                    team1prob,
                    blueRank,
                    blueTeam,
                    team2prob,
                    redRank,
                    redTeam,
                    activePickups[number][6],
                    activePickups[number][7],
                    activePickups[number][8],
                ]
                with open("activePickups.json", "w") as cd:
                    json.dump(activePickups, cd, indent=4)
                await teamsDisplay(ctx, blueTeam, redTeam, team1prob, team2prob)


# Saves the pickup into the activepickups json which can be seen with !games
def savePickup():
    global winningMap
    global winningServer
    global blueTeam
    global redTeam
    global captMode
    global vnoELO

    if vnoELO == 0:
        with open("activePickups.json") as f:
            activePickups = json.load(f)
        with open("ELOpop.json") as f:
            ELOpop = json.load(f)

        pSerial = random.randint(0, 10000000)
        while pSerial in list(activePickups):
            pSerial = random.randint(0, 10000000)
        now = round(time.time())
        blueRank = 0
        redRank = 0

        if captMode == 1:
            for i in blueTeam:
                for j in ELOpop:
                    if ELOpop[j][0] == i:
                        blueTeam.append(j)
                        # blueTeam.remove(i)
            for i in redTeam:
                for j in ELOpop:
                    if ELOpop[j][0] == i:
                        redTeam.append(j)
                        # blueTeam.remove(i)

            blueTeam = blueTeam[4:]
            redTeam = redTeam[4:]

        for i in blueTeam:
            blueRank += int(ELOpop[i][1])
        for i in redTeam:
            redRank += int(ELOpop[i][1])

        team1prob = round(1 / (1 + 10 ** ((redRank - blueRank) / 400)), 2)
        team2prob = round(1 / (1 + 10 ** ((blueRank - redRank) / 400)), 2)

        activePickups[pSerial] = [
            team1prob,
            blueRank,
            blueTeam,
            team2prob,
            redRank,
            redTeam,
            f"<t:{now}:f>",
            winningMap,
            winningServer,
        ]
        with open("activePickups.json", "w") as cd:
            json.dump(activePickups, cd, indent=4)


# Utility function for adding a player to the pickup if they aren't already added
def addplayerImpl(playerID, playerDisplayName, cap=None):
    global playersAdded
    global capList
    global ELOpop

    # For simplicity, don't let players add if we are map voting first
    # and still in voting stage.
    if (MAP_VOTE_FIRST == True):
        if (inVote == 1):
            return 2

    if len(playersAdded) <= 19:
        if playerID not in playersAdded:
            if playerID not in list(
                ELOpop
            ):  # Player is not registered, give them a default rating
                with open("ELOpop.json") as f:
                    ELOpop = json.load(f)
                ELOpop[playerID] = [
                    playerDisplayName,
                    800,
                    [],
                    "<:questionMark:972369805359337532>",
                    0,
                    0,
                    0,
                    [],
                    None,
                ]
                # Write the ELO out
                with open("ELOpop.json", "w") as cd:
                    json.dump(ELOpop, cd, indent=4)

            if cap == "cap":
                capList.append(playerID)

            playersAdded.append(playerID)
        else:
            return 1  # Player already added
        return 0  # Player successfully added
    else:
        return 2  # Too many players


# Primary way for players to add themselves to the pickup
# Example: !add
@client.command(pass_context=True, aliases=["+"])
@commands.has_role(v["tfc"])
async def add(ctx, cap=None):
    async with GLOBAL_LOCK:
        try:
            if ctx.channel.name == v["pc"]:
                playerID = str(ctx.author.id)
                playerDisplayName = ctx.author.display_name

                retVal = addplayerImpl(playerID, playerDisplayName, cap)
                if retVal == 1:  # Already added
                    await ctx.author.send(
                        "you are already added to this pickup.."
                    )  # Send PM to player
                if retVal == 0:  # Successfully added
                    await showPickup(ctx)
        except Exception as e:
            logging.error(e)
            await ctx.send(e)


@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def addplayer(ctx, player: discord.Member):
    async with GLOBAL_LOCK:
        if ctx.channel.name == v["pc"]:
            playerID = str(player.id)
            playerDisplayName = player.display_name
            logging.info("Adding player: %s, %s" % (playerID, playerDisplayName))
            retVal = addplayerImpl(playerID, playerDisplayName, None)
            if retVal == 0:  # Successfully added
                await showPickup(ctx)


# Convenience command for testing bot behavior with 7 people added
# Example: !test7
@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def test7(ctx):
    async with GLOBAL_LOCK:
        if ctx.channel.name == v["pc"]:
            cancelImpl()  # Clear out any existing pickup
            addplayerImpl("704204162958753892", "sandro702", None)
            addplayerImpl("303845825476558859", "dougtck", None)
            addplayerImpl("270636499190546432", "CheeseFromGPT", None)
            addplayerImpl("291754504158838784", "AUTHENTIC", None)
            addplayerImpl("194276343540613121", "climax", None)
            addplayerImpl("596225454721990676", "botch", None)
            addplayerImpl("173619058657198082", "Moreno", None)
            # retVal = addplayerImpl("151144734579097601", "EDEdDNEdDYFaN", None)
            # retVal = addplayerImpl("311769927432404994", "Nemsy", None)
            await showPickup(ctx)

# Convenience command for testing bot behavior with 8 people added
# Example: !test8
@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def test8(ctx):
    async with GLOBAL_LOCK:
        if ctx.channel.name == v["pc"]:
            cancelImpl()  # Clear out any existing pickup
            addplayerImpl("704204162958753892", "sandro702", None)
            addplayerImpl("303845825476558859", "dougtck", None)
            addplayerImpl("270636499190546432", "CheeseFromGPT", None)
            addplayerImpl("291754504158838784", "AUTHENTIC", None)
            addplayerImpl("194276343540613121", "climax", None)
            addplayerImpl("596225454721990676", "botch", None)
            addplayerImpl("173619058657198082", "Moreno", None)
            # retVal = addplayerImpl("151144734579097601", "EDEdDNEdDYFaN", None)
            addplayerImpl("311769927432404994", "Nemsy", None)
            await showPickup(ctx)



# Adding player: 704204162958753892, sandro702
# Adding player: 270636499190546432, CheeseFromGPT
# Adding player: 291754504158838784, AUTHENTIC
# Adding player: 194276343540613121, climax
# Adding player: 596225454721990676, botch
# Adding player: 173619058657198082, Moreno
# Adding player: 311769927432404994, Nemsy
# Adding player: 303845825476558859, dougtck


# Convenience multi-threading test function 1.
# Instructions: Run "!testMultithreading1" followed immediately by !testMultithreading2.  If the thread model is working
# correctly, the second function should print only after the first has waited 10 seconds.
@client.command(pass_context=True)
@commands.has_role(v["admin"])
async def testMultithreading1(ctx):
    async with GLOBAL_LOCK:
        await ctx.send("testMultithreading1 sleeping for 10 seconds async")

        # block for a moment
        await asyncio.sleep(10)
        # report a message
        await ctx.send("testMultithreading1 finished")


# Convenience multi-threading test function 2.
# Instructions: Run "!testMultithreading1" followed immediately by !testMultithreading2.  If the thread model is working
# correctly, the second function should print only after the first has waited 10 seconds.
@client.command(pass_context=True)
@commands.has_role(v["admin"])
async def testMultithreading2(ctx):
    async with GLOBAL_LOCK:
        await ctx.send("testMultithreading2 done")


# Utility function for showing the pickup
async def removePlayerImpl(ctx, playerID):
    global playersAdded
    global capList

    # For simplicity, don't let players remove if we are map voting first
    # and still in voting stage.
    if (MAP_VOTE_FIRST == True and inVote == 1):
        return
    if playerID in playersAdded:
        playersAdded.remove(playerID)
        if playerID in capList:
            capList.remove(playerID)
        await showPickup(ctx)
        return

@client.command(pass_context=True, aliases=["-"])
async def remove(ctx):
    async with GLOBAL_LOCK:
        if ctx.channel.name == v["pc"]:
            playerID = str(ctx.author.id)
            await removePlayerImpl(ctx, playerID)

@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def kick(ctx, player: discord.Member):
    async with GLOBAL_LOCK:
        if ctx.channel.name == v["pc"]:
            playerID = str(player.id)
            await removePlayerImpl(ctx, playerID)


@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def noELO(ctx):
    global vnoELO
    async with GLOBAL_LOCK:
        logging.info(vnoELO)
        if vnoELO == 0:
            vnoELO = 1
            await ctx.send("ELO has been turned **OFF** for this game.")
        elif vnoELO == 1:
            vnoELO = 0
            await ctx.send("ELO has been turned **ON** for this game.")


async def doteams(channel2, playerCount=4):
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
    # global pastTeams
    ready = []
    oMsg = None
    DMList = []
    channel2 = await client.fetch_channel(v["pID"])
    logging.info(f"doteams => playersAdded: {playersAdded}, playerCount: {playerCount}")
    if len(playersAdded) >= int(playerCount * 2):
        if inVote == 0:
            if len(capList) < 2:
                with open("ELOpop.json") as f:
                    ELOpop = json.load(f)
                playerCount = int(playerCount)
                if len(playersAdded) == playerCount:
                    eligiblePlayers = playersAdded
                else:
                    eligiblePlayers = playersAdded[0 : playerCount * 2]

                combos = list(
                    itertools.combinations(
                        eligiblePlayers, int(len(eligiblePlayers) / 2)
                    )
                )
                random.shuffle(combos)

                for i in eligiblePlayers:
                    if i in playersAdded:
                        playersAdded.remove(i)
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

                if playerCount <= 8:
                    if (
                        "303845825476558859" in eligiblePlayers
                        and "120411697184768000" in eligiblePlayers
                    ):
                        for i in list(combos):
                            blueRank = 0
                            for j in list(i):
                                blueRank += int(ELOpop[j][1])
                                if (
                                    "303845825476558859" in i
                                    and "120411697184768000" in i
                                ):
                                    rankedOrder.append((list(i), abs(blueRank - half)))
                        rankedOrder = sorted(rankedOrder, key=lambda x: x[1])
                    else:
                        for i in list(combos):
                            blueRank = 0
                            for j in list(i):
                                blueRank += int(ELOpop[j][1])
                            rankedOrder.append((list(i), abs(blueRank - half)))
                        rankedOrder = sorted(rankedOrder, key=lambda x: x[1])
                elif playerCount > 8:
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
                    rankedOrder = sorted(rankedOrder, key=lambda x: x[1])

                logging.info('Outputting list of players in ranked order')
                for i in rankedOrder:
                    logging.info(i)
                blueTeam = list(rankedOrder[0][0])

                for j in eligiblePlayers:
                    if j not in blueTeam:
                        redTeam.append(j)
                blueRank = 0
                for j in blueTeam:
                    blueRank += int(ELOpop[j][1])
                diff = abs(blueRank - half)
                for j in redTeam:
                    redRank += int(ELOpop[j][1])
                diff = abs(redRank - half)

                # Make blue team the favored team as it allows them to be lenient on defense
                # if desired/needed for sportsmanship.
                if (redRank > blueRank):
                    logging.info("Swapping team colors so blue is favored")
                    tempTeam = blueTeam
                    tempRank = blueRank
                    blueTeam = redTeam
                    blueRank = redRank
                    redTeam = tempTeam
                    redRank = tempRank

                logging.info(f"blueTeam: {blueTeam}, diff: {diff}, blueRank: {blueRank}")
                logging.info(f"redTeam: {redTeam}, diff {diff}, redRank: {redRank}")

                team1prob = round(1 / (1 + 10 ** ((redRank - blueRank) / 400)), 2)
                team2prob = round(1 / (1 + 10 ** ((blueRank - redRank) / 400)), 2)
                await teamsDisplay(channel2, blueTeam, redTeam, team1prob, team2prob)
                for i in eligiblePlayers:
                    DMList.append(f"<@{i}> ")

                dmMsg = "".join(DMList)
                await channel2.send(dmMsg)

                if (MAP_VOTE_FIRST == False):
                    # We aren't map voting before teams, so we start the voting after
                    # team are created.
                    # await ctx.send("Please react to the map you want to play on..")
                    await channel2.send("Please react to the server you want to play on..")
                    serverVote = 1
                    await voteSetup()
                    fTimer = 5
                    fVCoolDown.start()
                    inVote = 1

            elif len(capList) >= 2:
                with open("ELOpop.json") as f:
                    ELOpop = json.load(f)
                playerCount = int(playerCount)
                if len(playersAdded) == playerCount:
                    eligiblePlayers = playersAdded
                else:
                    eligiblePlayers = playersAdded[0 : playerCount * 2]
                captMode = 1
                DMList = []
                for i in eligiblePlayers:
                    DMList.append(f"<@{i}> ")

                dmMsg = "".join(DMList)
                await channel2.send(dmMsg)
                # await ctx.send("Please react to the map you want to play on..")
                await channel2.send("Please react to the server you want to play on..")
                serverVote = 1
                await voteSetup()
                fTimer = 5
                fVCoolDown.start()
                inVote = 1
    else:
        await channel2.send("you dont have enough people for that game size..")


# Start the pickup assuming enough players have been added.  This will kick off server and map voting and any other
# flow needed to begin the pickup.
# Example: !teams
@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def teams(ctx, playerCount=4):
    async with GLOBAL_LOCK:
        if ctx.channel.name == v["pc"]:
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
            # global pastTeams
            ready = []
            oMsg = None
            DMList = []
            if len(playersAdded) >= int(playerCount * 2):
                if inVote == 0:
                    if len(capList) < 2:
                        playerCount = int(playerCount)
                        if len(playersAdded) == playerCount:
                            eligiblePlayers = playersAdded
                        else:
                            eligiblePlayers = playersAdded[0 : playerCount * 2]

                        if (MAP_VOTE_FIRST == True):
                            # Prune down the players added
                            playersAdded = eligiblePlayers
                            await showPickup(ctx, False, True)

                        if (MAP_VOTE_FIRST == False):
                            with open("ELOpop.json") as f:
                                ELOpop = json.load(f)

                            combos = list(
                                itertools.combinations(
                                    eligiblePlayers, int(len(eligiblePlayers) / 2)
                                )
                            )
                            random.shuffle(combos)

                            for i in eligiblePlayers:
                                if i in playersAdded:
                                    playersAdded.remove(i)
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

                            if playerCount <= 8:
                                for i in list(combos):
                                    blueRank = 0
                                    for j in list(i):
                                        blueRank += int(ELOpop[j][1])
                                    rankedOrder.append((list(i), abs(blueRank - half)))
                                rankedOrder = sorted(rankedOrder, key=lambda x: x[1])
                            elif playerCount > 8:
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
                                rankedOrder = sorted(rankedOrder, key=lambda x: x[1])

                            #logging.info("Printing players in ranked order")
                            #for i in rankedOrder:
                            #    logging.info(i)
                            blueTeam = list(rankedOrder[0][0])

                            for j in eligiblePlayers:
                                if j not in blueTeam:
                                    redTeam.append(j)
                            blueRank = 0
                            for j in blueTeam:
                                blueRank += int(ELOpop[j][1])
                            diff = abs(blueRank - half)
                            for j in redTeam:
                                redRank += int(ELOpop[j][1])
                            diff = abs(redRank - half)

                            # Make blue team the favored team as it allows them to be lenient on defense
                            # if desired/needed for sportsmanship.
                            if (redRank > blueRank):
                                logging.info("Swapping team colors so blue is favored")
                                tempTeam = blueTeam
                                tempRank = blueRank
                                blueTeam = redTeam
                                blueRank = redRank
                                redTeam = tempTeam
                                redRank = tempRank

                            logging.info(f"blueTeam: {blueTeam}, diff: {diff}, blueRank: {blueRank}")
                            logging.info(f"redTeam: {redTeam}, diff {diff}, redRank: {redRank}")

                            team1prob = round(
                                1 / (1 + 10 ** ((redRank - blueRank) / 400)), 2
                            )
                            team2prob = round(
                                1 / (1 + 10 ** ((blueRank - redRank) / 400)), 2
                            )
                            await teamsDisplay(ctx, blueTeam, redTeam, team1prob, team2prob)
                            for i in eligiblePlayers:
                                DMList.append(f"<@{i}> ")

                            dmMsg = "".join(DMList)
                            await ctx.send(dmMsg)
                            # await ctx.send("Please react to the map you want to play on..")
                            await ctx.send(
                                "Please react to the server you want to play on.."
                            )
                        
                        serverVote = 1
                        await voteSetup()
                        fTimer = 5
                        fVCoolDown.start()
                        inVote = 1

                    elif len(capList) >= 2:
                        with open("ELOpop.json") as f:
                            ELOpop = json.load(f)
                        playerCount = int(playerCount)
                        if len(playersAdded) == playerCount:
                            eligiblePlayers = playersAdded
                        else:
                            eligiblePlayers = playersAdded[0 : playerCount * 2]
                        captMode = 1
                        DMList = []
                        for i in eligiblePlayers:
                            DMList.append(f"<@{i}> ")

                        # remove all players from players added
                        for i in eligiblePlayers:
                            if i in playersAdded:
                                playersAdded.remove(i)

                        dmMsg = "".join(DMList)
                        await ctx.send(dmMsg)
                        await ctx.send(
                            "Please react to the server you want to play on.."
                        )
                        serverVote = 1
                        await voteSetup()
                        fTimer = 5
                        fVCoolDown.start()
                        inVote = 1
            else:
                await ctx.send("you dont have enough people for that game size..")


@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def addp(ctx, number):
    async with GLOBAL_LOCK:
        if ctx.channel.name == v["pc"]:
            global playersAdded
            global capList
            number = int(number)
            with open("ELOpop.json") as f:
                ELOpop = json.load(f)
            pickfrom = list(ELOpop)
            for i in range(number):
                player = random.choice(pickfrom)
                playersAdded.append(player)
                pickfrom.remove(player)

            await showPickup(ctx)


@client.command(pass_context=True)
async def status(ctx):
    async with GLOBAL_LOCK:
        if ctx.channel.name == v["pc"]:
            await showPickup(ctx)


@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def next(ctx, player: discord.Member):
    async with GLOBAL_LOCK:
        if ctx.channel.name == v["pc"]:
            global blueTeam
            global redTeam
            global playersAdded
            global eligiblePlayers

            eligiblePlayers = []
            for i in blueTeam:
                if i != str(player.id):
                    eligiblePlayers.append(i)

            for i in redTeam:
                if i != str(player.id):
                    eligiblePlayers.append(i)

            eligiblePlayers.append(playersAdded[0])
            playerCount = len(eligiblePlayers)
            counter = 0
            teamsPicked = 0
            combos = list(itertools.combinations(eligiblePlayers, int(playerCount / 2)))
            random.shuffle(combos)

            for i in eligiblePlayers:
                if i in playersAdded:
                    playersAdded.remove(i)
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
                        if j not in blueTeam:
                            redTeam.append(j)

                    for j in blueTeam:
                        blueRank += ELOpop[j][1]
                    for j in redTeam:
                        redRank += ELOpop[j][1]

                    diff = abs(blueRank - half)
                    if diff <= counter:
                        if (len(blueTeam) == playerCount / 2) and (
                            len(redTeam) == playerCount / 2
                        ):
                            teamsPicked = 1
                            break
                    else:
                        blueTeam.clear()
                        redTeam.clear()
                        redRank = 0
                        blueRank = 0
                        totalRank = 0
                if playerCount <= 8:
                    counter += 5
                else:
                    counter += 20
            team1prob = round(1 / (1 + 10 ** ((redRank - blueRank) / 400)), 2)
            team2prob = round(1 / (1 + 10 ** ((blueRank - redRank) / 400)), 2)
            await teamsDisplay(ctx, blueTeam, redTeam, team1prob, team2prob)


@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def sub(ctx, playerone: discord.Member, playertwo: discord.Member, number="None"):
    async with GLOBAL_LOCK:
        if ctx.channel.name == v["pc"]:
            with open("activePickups.json") as f:
                activePickups = json.load(f)
            """global eligiblePlayers
            global blueTeam
            global redTeam
            global playersAdded"""
            if number == "None":
                global eligiblePlayers
                global blueTeam
                global redTeam
                global playersAdded
                playeroutid = None
                playerinid = None

                if (MAP_VOTE_FIRST == False):
                    eligiblePlayers = []
                    if str(playerone.id) in blueTeam or str(playerone.id) in redTeam:
                        playeroutid = playerone.id
                        playerinid = playertwo.id
                    elif str(playertwo.id) in blueTeam or str(playertwo.id) in redTeam:
                        playeroutid = playertwo.id
                        playerinid = playerone.id
                    logging.info(f"Subbing player {playerinid} for player {playeroutid}")
                    for i in blueTeam:
                        if i != str(playeroutid):
                            eligiblePlayers.append(i)
                    for i in redTeam:
                        if i != str(playeroutid):
                            eligiblePlayers.append(i)  
                    eligiblePlayers.append(str(playerinid))
                else: # (MAP_VOTE_FIRST == True):
                    # Map voting first, so no teams yet
                    if str(playerone.id) in playersAdded:
                        playeroutid = playerone.id
                        playerinid = playertwo.id
                    elif str(playertwo.id) in playersAdded:
                        playeroutid = playertwo.id
                        playerinid = playerone.id
                    logging.info(f"Subbing player {playerinid} for player {playeroutid}")
                    playersAddedNew = []
                    playersAddedNew.append(str(playerinid))
                    for i in playersAdded:
                        if i != str(playeroutid):
                            playersAddedNew.append(i)
                    playersAdded = playersAddedNew
                    eligiblePlayers = playersAdded
                    await showPickup(ctx, False)

                if (MAP_VOTE_FIRST == False):
                    # Subbing only needs to re-generate teams we aren't map voting first
                    combos = list(
                        itertools.combinations(
                            eligiblePlayers, int(len(eligiblePlayers) / 2)
                        )
                    )
                    random.shuffle(combos)

                    if str(playerinid) in playersAdded:
                        playersAdded.remove(str(playerinid))

                    for i in eligiblePlayers:
                        if i in playersAdded:
                            playersAdded.remove(i)
                    blueTeam = []
                    redTeam = []
                    rankedOrder = []
                    redRank = 0
                    blueRank = 0
                    totalRank = 0
                    half = 0
                    logging.info(eligiblePlayers)
                    for j in eligiblePlayers:
                        totalRank += int(ELOpop[j][1])
                    half = int(totalRank / 2)

                    for i in list(combos):
                        blueRank = 0
                        for j in list(i):
                            blueRank += int(ELOpop[j][1])
                        rankedOrder.append((list(i), abs(blueRank - half)))
                    rankedOrder = sorted(rankedOrder, key=lambda x: x[1])
                    #logging.info("Printing players in ranked order")
                    #for i in rankedOrder:
                    #    logging.info(i)
                    blueTeam = list(rankedOrder[0][0])

                    for j in eligiblePlayers:
                        if j not in blueTeam:
                            redTeam.append(j)
                    blueRank = 0
                    for j in blueTeam:
                        blueRank += int(ELOpop[j][1])
                    diff = abs(blueRank - half)
                    for j in redTeam:
                        redRank += int(ELOpop[j][1])
                    diff = abs(redRank - half)

                    # Make blue team the favored team as it allows them to be lenient on defense
                    # if desired/needed for sportsmanship.
                    if (redRank > blueRank):
                        logging.info("Swapping team colors so blue is favored")
                        tempTeam = blueTeam
                        tempRank = blueRank
                        blueTeam = redTeam
                        blueRank = redRank
                        redTeam = tempTeam
                        redRank = tempRank

                    logging.info(f"blueTeam: {blueTeam}, diff: {diff}, blueRank: {blueRank}")
                    logging.info(f"redTeam: {redTeam}, diff {diff}, redRank: {redRank}")

                    team1prob = round(1 / (1 + 10 ** ((redRank - blueRank) / 400)), 2)
                    team2prob = round(1 / (1 + 10 ** ((blueRank - redRank) / 400)), 2)
                    await teamsDisplay(ctx, blueTeam, redTeam, team1prob, team2prob)
            elif number != "None":
                eligiblePlayers = []
                playerIn = None
                playerOut = None

                blueTeam = activePickups[number][2]
                redTeam = activePickups[number][5]

                if str(playerone.id) in blueTeam or str(playerone.id) in redTeam:
                    playerOut = str(playerone.id)
                    playerIn = str(playertwo.id)
                elif str(playertwo.id) in blueTeam or str(playertwo.id) in redTeam:
                    playerOut = str(playertwo.id)
                    playerIn = str(playerone.id)
                """for i in blueTeam:
                    if(i != str(playerout.id)):
                        eligiblePlayers.append(i)

                for i in redTeam:
                    if(i != str(playerout.id)):
                        eligiblePlayers.append(i)"""
                eligiblePlayers = blueTeam + redTeam
                logging.info(eligiblePlayers)
                eligiblePlayers.remove(playerOut)
                eligiblePlayers.append(playerIn)

                combos = list(
                    itertools.combinations(
                        eligiblePlayers, int(len(eligiblePlayers) / 2)
                    )
                )
                random.shuffle(combos)

                for i in eligiblePlayers:
                    if i in playersAdded:
                        playersAdded.remove(i)

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
                rankedOrder = sorted(rankedOrder, key=lambda x: x[1])
                for i in rankedOrder:
                    logging.info(i)
                blueTeam = list(rankedOrder[0][0])

                for j in eligiblePlayers:
                    if j not in blueTeam:
                        redTeam.append(j)
                blueRank = 0
                for j in blueTeam:
                    blueRank += int(ELOpop[j][1])
                diff = abs(blueRank - half)
                for j in redTeam:
                    redRank += int(ELOpop[j][1])
                diff = abs(redRank - half)

                # Make blue team the favored team as it allows them to be lenient on defense
                # if desired/needed for sportsmanship.
                if (redRank > blueRank):
                    logging.info("Swapping team colors so blue is favored")
                    tempTeam = blueTeam
                    tempRank = blueRank
                    blueTeam = redTeam
                    blueRank = redRank
                    redTeam = tempTeam
                    redRank = tempRank

                logging.info(f"blueTeam: {blueTeam}, diff: {diff}, blueRank: {blueRank}")
                logging.info(f"redTeam: {redTeam}, diff {diff}, redRank: {redRank}")

                team1prob = round(1 / (1 + 10 ** ((redRank - blueRank) / 400)), 2)
                team2prob = round(1 / (1 + 10 ** ((blueRank - redRank) / 400)), 2)
                activePickups[number] = [
                    team1prob,
                    blueRank,
                    blueTeam,
                    team2prob,
                    redRank,
                    redTeam,
                    activePickups[number][6],
                    activePickups[number][7],
                    activePickups[number][8],
                ]
                with open("activePickups.json", "w") as cd:
                    json.dump(activePickups, cd, indent=4)
                await teamsDisplay(ctx, blueTeam, redTeam, team1prob, team2prob)


@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def draw(ctx, pNumber="None"):
    global ELOpop
    dev_channel = await client.fetch_channel(DEV_TESTING_CHANNEL)
    db = mysql.connector.connect(
        host=logins['mysql']['host'],
        user=logins['mysql']['user'],
        passwd=logins['mysql']['passwd'],
        database=logins['mysql']['database'],
    )

    mycursor = db.cursor()
    async with GLOBAL_LOCK:
        if ctx.channel.name == v["pc"]:
            with open("activePickups.json") as f:
                activePickups = json.load(f)
            with open("ELOpop.json") as f:
                ELOpop = json.load(f)
            with open("pastten.json") as f:
                pastTen = json.load(f)

            if pNumber == "None":
                pNumber = list(activePickups)[-1]

            blueTeam = activePickups[pNumber][2]
            redTeam = activePickups[pNumber][5]
            blueProb = activePickups[pNumber][0]
            blueRank = activePickups[pNumber][1]
            redProb = activePickups[pNumber][3]
            redRank = activePickups[pNumber][4]
            pMap = activePickups[pNumber][7]
            adjustTeam1 = 0
            adjustTeam2 = 0

            adjustTeam1 = int(blueRank + 50 * (0.5 - blueProb)) - blueRank
            adjustTeam2 = int(redRank + 50 * (0.5 - redProb)) - redRank

            if "Bot's Choice" in pMap:
                adjustTeam1 = adjustTeam1 * 2
                adjustTeam2 = adjustTeam2 * 2
                logging.info("giving double ELO")

            for i in blueTeam:
                ELOpop[i][1] += adjustTeam1
                # if(int(ELOpop[i][1]) > 2599):
                # ELOpop[i][1] = 2599
                if int(ELOpop[i][1]) < 0:
                    ELOpop[i][1] = 0
                # ELOpop[i][2].append([int(ELOpop[i][1]), pNumber])
                try:
                    input_query = f"MANUAL REPORT: INSERT INTO player_elo (match_id, player_name, player_elos, discord_id) VALUES ({pNumber}, {ELOpop[i][0]}, {ELOpop[i][1]}, {int(i)})"
                    logging.info(input_query)
                    mycursor.execute(
                        "INSERT INTO player_elo (match_id, player_name, player_elos, discord_id) VALUES (%s, %s, %s, %s)",
                        (pNumber, ELOpop[i][0], ELOpop[i][1], int(i)),
                    )
                except Exception as e:
                    await dev_channel.send(f"SQL QUERY DID NOT WORK FOR {ELOpop[i][0]} {e}")
                    await dev_channel.send(input_query)
                ELOpop[i][6] += 1
                if ELOpop[i][3] != "<:norank:1001265843683987487>":
                    newRank(i)
            for i in redTeam:
                ELOpop[i][1] += adjustTeam2
                # if(int(ELOpop[i][1]) > 2599):
                # ELOpop[i][1] = 2599
                if int(ELOpop[i][1]) < 0:
                    ELOpop[i][1] = 0
                # ELOpop[i][2].append([int(ELOpop[i][1]), pNumber])
                try:
                    input_query = f"MANUAL REPORT: INSERT INTO player_elo (match_id, player_name, player_elos, discord_id) VALUES ({pNumber}, {ELOpop[i][0]}, {ELOpop[i][1]}, {int(i)})"
                    logging.info(input_query)
                    mycursor.execute(
                        "INSERT INTO player_elo (match_id, player_name, player_elos, discord_id) VALUES (%s, %s, %s, %s)",
                        (pNumber, ELOpop[i][0], ELOpop[i][1], int(i)),
                    )
                except Exception as e:
                    await dev_channel.send(
                        f"SQL QUERY DID NOT WORK FOR {ELOpop[i][0]}    {e}"
                    )
                    await dev_channel.send(input_query)
                ELOpop[i][6] += 1
                if ELOpop[i][3] != "<:norank:1001265843683987487>":
                    newRank(i)

            if len(list(pastTen)) >= 10:
                while len(list(pastTen)) > 9:
                    ID = list(pastTen)[0]
                    del pastTen[ID]

            pastTen[pNumber] = [
                blueTeam,
                blueProb,
                adjustTeam1,
                blueRank,
                redTeam,
                redProb,
                adjustTeam2,
                redRank,
                0,
                activePickups[pNumber][7],
            ]  # winningTeam, team1prob, adjustmentTeam1, losingteam, team2prob, adjustmentTeam2
            del activePickups[pNumber]
            with open("activePickups.json", "w") as cd:
                json.dump(activePickups, cd, indent=4)
            with open("ELOpop.json", "w") as cd:
                json.dump(ELOpop, cd, indent=4)
            with open("pastten.json", "w") as cd:
                json.dump(pastTen, cd, indent=4)

            await ctx.send("Match reported.. thank you!")


@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def win(ctx, team, pNumber="None"):
    global ELOpop
    dev_channel = await client.fetch_channel(DEV_TESTING_CHANNEL)
    db = mysql.connector.connect(
        host=logins['mysql']['host'],
        user=logins['mysql']['user'],
        passwd=logins['mysql']['passwd'],
        database=logins['mysql']['database'],
    )

    mycursor = db.cursor()
    async with GLOBAL_LOCK:
        if (
            (ctx.channel.name == v["pc"])
            or (ctx.channel.name == "tfc-admins")
            or (ctx.channel.name == "tfc-runners")
        ):
            with open("activePickups.json") as f:
                activePickups = json.load(f)
            with open("ELOpop.json") as f:
                ELOpop = json.load(f)
            with open("pastten.json") as f:
                pastTen = json.load(f)
            if pNumber == "None":
                pNumber = list(activePickups)[-1]

            blueTeam = activePickups[pNumber][2]
            redTeam = activePickups[pNumber][5]
            blueProb = activePickups[pNumber][0]
            blueRank = activePickups[pNumber][1]
            redProb = activePickups[pNumber][3]
            redRank = activePickups[pNumber][4]
            pMap = activePickups[pNumber][7]
            adjustTeam1 = 0
            adjustTeam2 = 0
            winner = 0
            if team == "1":
                adjustTeam1 = int(blueRank + 50 * (1 - blueProb)) - blueRank
                adjustTeam2 = int(redRank + 50 * (0 - redProb)) - redRank
                winner = 1
            if team == "2":
                adjustTeam1 = int(blueRank + 50 * (0 - blueProb)) - blueRank
                adjustTeam2 = int(redRank + 50 * (1 - redProb)) - redRank
                winner = 2
            if team == "draw":
                adjustTeam1 = int(blueRank + 50 * (0.5 - blueProb)) - blueRank
                adjustTeam2 = int(redRank + 50 * (0.5 - redProb)) - redRank
            if "Bot's Choice" in pMap:
                adjustTeam1 = adjustTeam1 * 2
                adjustTeam2 = adjustTeam2 * 2
                logging.info("giving double ELO")

            for i in blueTeam:
                ELOpop[i][1] += adjustTeam1
                # if(int(ELOpop[i][1]) > 2599):
                # ELOpop[i][1] = 2599
                if int(ELOpop[i][1]) < 0:
                    ELOpop[i][1] = 0
                # ELOpop[i][2].append([int(ELOpop[i][1]), pNumber])
                try:
                    input_query = f"MANUAL REPORT: INSERT INTO player_elo (match_id, player_name, player_elos, discord_id) VALUES ({pNumber}, {ELOpop[i][0]}, {ELOpop[i][1]}, {int(i)})"
                    logging.info(input_query)
                    mycursor.execute(
                        "INSERT INTO player_elo (match_id, player_name, player_elos, discord_id) VALUES (%s, %s, %s, %s)",
                        (pNumber, ELOpop[i][0], ELOpop[i][1], int(i)),
                    )
                except Exception as e:
                    await dev_channel.send(
                        f"SQL QUERY DID NOT WORK FOR {ELOpop[i][0]}    {e}"
                    )
                    await dev_channel.send(input_query)
                if team == "1":
                    ELOpop[i][4] += 1
                if team == "2":
                    ELOpop[i][5] += 1
                if team == "draw":
                    ELOpop[i][6] += 1
                if ELOpop[i][3] != "<:norank:1001265843683987487>":
                    newRank(i)
            for i in redTeam:
                ELOpop[i][1] += adjustTeam2
                # if(int(ELOpop[i][1]) > 2599):
                # ELOpop[i][1] = 2599
                if int(ELOpop[i][1]) < 0:
                    ELOpop[i][1] = 0
                # ELOpop[i][2].append([int(ELOpop[i][1]), pNumber])
                try:
                    input_query = f"MANUAL REPORT: INSERT INTO player_elo (match_id, player_name, player_elos, discord_id) VALUES ({pNumber}, {ELOpop[i][0]}, {ELOpop[i][1]}, {int(i)})"
                    logging.info(input_query)
                    mycursor.execute(
                        "INSERT INTO player_elo (match_id, player_name, player_elos, discord_id) VALUES (%s, %s, %s, %s)",
                        (pNumber, ELOpop[i][0], ELOpop[i][1], int(i)),
                    )
                except Exception as e:
                    await dev_channel.send(
                        f"SQL QUERY DID NOT WORK FOR {ELOpop[i][0]}    {e}"
                    )
                    await dev_channel.send(input_query)
                if team == "1":
                    ELOpop[i][5] += 1
                if team == "2":
                    ELOpop[i][4] += 1
                if team == "draw":
                    ELOpop[i][6] += 1
                if ELOpop[i][3] != "<:norank:1001265843683987487>":
                    newRank(i)

            if len(list(pastTen)) >= 10:
                while len(list(pastTen)) > 9:
                    ID = list(pastTen)[0]
                    del pastTen[ID]

            pastTen[pNumber] = [
                blueTeam,
                blueProb,
                adjustTeam1,
                blueRank,
                redTeam,
                redProb,
                adjustTeam2,
                redRank,
                winner,
                activePickups[pNumber][7],
            ]  # winningTeam, team1prob, adjustmentTeam1, losingteam, team2prob, adjustmentTeam2
            del activePickups[pNumber]

            with open("activePickups.json", "w") as cd:
                json.dump(activePickups, cd, indent=4)
            with open("ELOpop.json", "w") as cd:
                json.dump(ELOpop, cd, indent=4)
            with open("pastten.json", "w") as cd:
                json.dump(pastTen, cd, indent=4)

            pastTen[pNumber] = []

            await ctx.send("Match reported.. thank you!")


@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def tfc(ctx, person: discord.Member):
    role = get(person.guild.roles, name="TFC Player")
    await person.add_roles(role)
    await ctx.author.send(
        f"You have given {person.display_name} the TFC Player role and they can now add to pickups"
    )


@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def undo(ctx, pNumber="None"):
    async with GLOBAL_LOCK:
        with open("pastten.json") as f:
            pastTen = json.load(f)
        with open("ELOpop.json") as f:
            ELOpop = json.load(f)
        with open("activePickups.json") as f:
            activePickups = json.load(f)
        db = mysql.connector.connect(
            host=logins['mysql']['host'],
            user=logins['mysql']['user'],
            passwd=logins['mysql']['passwd'],
            database=logins['mysql']['database'],
        )

        mycursor = db.cursor()
        blueTeam = pastTen[pNumber][0]
        redTeam = pastTen[pNumber][4]
        winningTeam = pastTen[pNumber][8]
        team1Adjust = pastTen[pNumber][2]
        team2Adjust = pastTen[pNumber][6]

        for i in blueTeam:
            ELOpop[i][1] += -1 * team1Adjust
            if winningTeam == 1:
                ELOpop[i][4] += -1
            elif winningTeam == 2:
                ELOpop[i][5] += -1
            elif winningTeam == 0:
                ELOpop[i][6] += -1
            """for j in list(ELOpop[i][2]):
                if(j[1] == pNumber):
                    ELOpop[i][2].remove(j)"""
            mycursor.execute(
                "DELETE FROM player_elo WHERE match_id = %s AND discord_id = %s",
                (pNumber, int(i)),
            )

        for i in redTeam:
            ELOpop[i][1] += -1 * team2Adjust
            if winningTeam == 2:
                ELOpop[i][4] += -1
            elif winningTeam == 1:
                ELOpop[i][5] += -1
            elif winningTeam == 0:
                ELOpop[i][6] += -1
            """for j in list(ELOpop[i][2]):
                if(j[1] == pNumber):
                    ELOpop[i][2].remove(j)"""
            mycursor.execute(
                "DELETE FROM player_elo WHERE match_id = %s AND discord_id = %s",
                (pNumber, int(i)),
            )

        # pastTen[pNumber] = [blueTeam, blueProb, adjustTeam1, blueRank, redTeam, redProb, adjustTeam2, redRank, winner, activePickups[pNumber][7]]
        activePickups[pNumber] = [
            pastTen[pNumber][1],
            pastTen[pNumber][3],
            blueTeam,
            pastTen[pNumber][5],
            pastTen[pNumber][7],
            redTeam,
            "None",
            pastTen[pNumber][9],
            "None",
        ]

        await ctx.send(f"Match Number {pNumber} has been undone")
        del pastTen[pNumber]
        with open("activePickups.json", "w") as cd:
            json.dump(activePickups, cd, indent=4)
        with open("ELOpop.json", "w") as cd:
            json.dump(ELOpop, cd, indent=4)
        with open("pastten.json", "w") as cd:
            json.dump(pastTen, cd, indent=4)


@client.command(pass_context=True)
async def games(ctx):
    async with GLOBAL_LOCK:
        if (
            (ctx.channel.name == v["pc"])
            or (ctx.channel.name == "tfc-admins")
            or (ctx.channel.name == "tfc-runners")
        ):
            await openPickups(ctx)


@client.command(pass_context=True)
async def recent(ctx):
    async with GLOBAL_LOCK:
        if (
            (ctx.channel.name == v["pc"])
            or (ctx.channel.name == "tfc-admins")
            or (ctx.channel.name == "tfc-runners")
            or (ctx.channel.id == DEV_TESTING_CHANNEL)
        ):
            await pastGames(ctx)


@client.command(pass_context=True)
async def checkgame(ctx, number):
    async with GLOBAL_LOCK:
        if (
            (ctx.channel.name == v["pc"])
            or (ctx.channel.name == "tfc-admins")
            or (ctx.channel.name == "tfc-runners")
            or (ctx.channel.id == DEV_TESTING_CHANNEL)
        ):
            with open("pastten.json") as f:
                past_ten = json.load(f)
            with open("activePickups.json") as f:
                activePickups = json.load(f)
            with open("ELOpop.json") as f:
                ELOpop = json.load(f)
            msgList = []
            if number in activePickups:
                blueTeam = activePickups[number][2]
                redTeam = activePickups[number][5]
                match_outcome_string = 'Active Game (unreported!)'
            elif number in past_ten:
                blueTeam = past_ten[number][PAST_TEN_BLUE_TEAM_INDEX]
                redTeam = past_ten[number][PAST_TEN_RED_TEAM_INDEX]
                match_outcome_string = "Team " + str(past_ten[number][PAST_TEN_MATCH_OUTCOME_INDEX])
            else:
                await ctx.send(f'Issue finding game number {number} in past 10 or active pickups - check for typo?')
                return

            for i in blueTeam:
                msgList.append(getRank(i) + " " + ELOpop[i][0] + "\n")
            bMsg = "".join(msgList)
            msgList.clear()
            for i in redTeam:
                msgList.append(getRank(i) + " " + ELOpop[i][0] + "\n")
            rMsg = "".join(msgList)
            embed = discord.Embed(title=f"Game Number - {number} - Outcome - {match_outcome_string}")
            embed.add_field(
                name="Blue Team " + v["t1img"], value=bMsg, inline=True
            )
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(
                name="Red Team " + v["t2img"], value=rMsg, inline=True
            )
            await ctx.send(embed=embed)


# Remove a game that you no longer wish to complete or count for ELO.  Use !games to get a
# list of game numbers that are valid to remove.
# Example: !removegame 699670
@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def removegame(ctx, number):
    async with GLOBAL_LOCK:
        if ctx.channel.name == v["pc"]:
            with open("activePickups.json") as f:
                activePickups = json.load(f)

            del activePickups[number]

            with open("activePickups.json", "w") as cd:
                json.dump(activePickups, cd, indent=4)

            await ctx.send("Game has been removed..")


def cancelImpl():
    global playersAdded
    playersAdded.clear()
    DePopulatePickup()


# Completely cancel the pickup
# Example: !cancel
@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def cancel(ctx):
    async with GLOBAL_LOCK:
        if ctx.channel.name == v["pc"]:
            cancelImpl()
            await ctx.send("Queue has been cancelled..")


@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def requeue(ctx):
    global blueTeam
    global redTeam
    global playersAdded
    async with GLOBAL_LOCK:
        if captMode == 1:
            logging.info(blueTeam, redTeam, eligiblePlayers)
            neligibleplayers = eligiblePlayers
            DePopulatePickup()
            playersAdded = neligibleplayers.copy() + playersAdded
            await showPickup(ctx)
        else:
            neligibleplayers = blueTeam + redTeam
            DePopulatePickup()
            playersAdded = neligibleplayers.copy() + playersAdded
            neligibleplayers.clear()
            await showPickup(ctx)


# End the current voting round (server, map, etc) potentially early if not everyone has cast their votes yet.
# Examples: !forceVote
#           !fv
@client.command(aliases=["fv"])
@commands.cooldown(1, 3, commands.BucketType.default)
@commands.has_role(v["runner"])
async def forceVote(channel):
    async with GLOBAL_LOCK:
        channel = await client.fetch_channel(v["pID"])
        if channel.name == v["pc"]:
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
            logging.info("Force Vote Called")
            winningMap = None
            alreadyVoted = []
            if serverVote == 1:
                votes = [
                    len(mapVotes[mapChoice1]),
                    len(mapVotes[mapChoice2]),
                    len(mapVotes[mapChoice3]),
                ]
                windex = votes.index(max(votes))
                if windex == 0:
                    winningIP = "https://tinyurl.com/tfpugseu - connect 78.141.200.198:27015; password letsplay!"
                    winningServer = "EU (London)"
                elif windex == 1:
                    winningIP = "https://tinyurl.com/tfcpugseast - connect coach.game.nfoservers.com; password letsplay!"
                    winningServer = "East (NY)"
                elif windex == 2:
                    winningIP = "https://tinyurl.com/tfcpugscentral - connect coachcent.game.nfoservers.com; password letsplay!"
                    winningServer = "Central (Chi)"
                else:
                    # Just pick one so things aren't completely broken
                    winningIP = "https://tinyurl.com/tfcpugscentral - bot chose this randomly"
                    winningServer = "Central (Chi)"
                serverVote = 0
                fTimer = 3
                await voteSetup()
            elif serverVote == 0:
                # We are currently in map voting round

                # Tally the votes for each choice, putting map choice 4 in the first slot to give precedence for a tie, as it may be the "new maps" special
                # slot which would trigger a new vote in the case of a tie with a real map.
                votes = [
                    len(mapVotes[mapChoice4]),
                    len(mapVotes[mapChoice1]),
                    len(mapVotes[mapChoice2]),
                    len(mapVotes[mapChoice3]),
                ]
                mapNames = [mapChoice4, mapChoice1, mapChoice2, mapChoice3]

                maxVoteCount = max(votes)
                windex = votes.index(maxVoteCount)  # winning index

                # Check for special case of new maps first to trigger new voting round
                if (windex == 0) and (mapChoice4 == "New Maps"):
                    # We need a new voting round
                    reVote = 1
                    # Find the real map with the most votes by deleting the new maps entry
                    del votes[0]  # votes now has 3 entries
                    windex = votes.index(max(votes))
                    if windex == 0:
                        mapChoice4 = mapChoice1
                    if windex == 1:
                        mapChoice4 = mapChoice2
                    if windex == 2:
                        mapChoice4 = mapChoice3
                    # alreadyVoted = []
                    await channel.send("New maps has won, now selecting new maps..")
                    fTimer = 3
                    await voteSetup()
                else:
                    # A real map has won. Gather all maps that had the maximum count
                    voteIndex = 0
                    candidateMapNames = []
                    for count in votes:
                        if count == maxVoteCount:
                            candidateMapNames.append(mapNames[voteIndex])
                        voteIndex = voteIndex + 1

                    logging.info(
                        f"maxVoteCount: {maxVoteCount}, candidateMapNames: {candidateMapNames}"
                    )

                    if captMode == 0:
                        if (MAP_VOTE_FIRST == True):
                            # Create the teams after the map vote
                            inVote = 0
                            await doteams(channel)

                    # Pick a random final winner from the candidate maps
                    winningMap = random.choice(candidateMapNames)
                    if "Bot's Choice" in winningMap:
                        wMap = await pickRandomMap(channel)
                        winningMap = "Bot's Choice - " + wMap
                        await channel.send(
                            f"BOT'S CHOICE! The winning map is **{wMap}** and will be played at {winningIP}"
                        )
                    else:
                        await channel.send(
                            f"The winning map is **{winningMap}** and will be played at {winningIP}"
                        )
                    fVCoolDown.stop()

                    inVote = 0
                    if len(lastFive) >= 5:
                        lastFive.remove(lastFive[0])
                    if "Bot's Choice" in winningMap:
                        lastFive.append(wMap)
                    elif "Bot's Choice" not in winningMap:
                        lastFive.append(winningMap)

                    if captMode == 0:
                        savePickup()
                        DePopulatePickup()

            if inVote == 0 and captMode == 1:
                with open("ELOpop.json") as f:
                    ELOpop = json.load(f)
                for i in eligiblePlayers:
                    if i not in capList:
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
                pMsg = await channel.send(
                    "```"
                    + str(cap1Name)
                    + " and "
                    + str(cap2Name)
                    + " are the captains.\n\n"
                    + msg
                    + "```"
                )
                await pMsg.add_reaction("1️⃣")
                await pMsg.add_reaction("2️⃣")
                await pMsg.add_reaction("3️⃣")
                await pMsg.add_reaction("4️⃣")
                await pMsg.add_reaction("5️⃣")
                await pMsg.add_reaction("6️⃣")


@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def shufflee(ctx, idx=None, game="None"):
    async with GLOBAL_LOCK:
        if idx is None:
            idx = random.randint(1, 11)
        with open("activePickups.json") as f:
            activePickups = json.load(f)
        with open("ELOpop.json") as f:
            ELOpop = json.load(f)
        global rankedOrder
        global blueTeam
        global redTeam
        global team1prob
        global team2prob
        global blueRank
        global redRank
        global tMsg
        if game == "None":
            blueRank = 0
            redRank = 0
            blueTeam = []
            redTeam = []
            logging.info(rankedOrder)
            blueTeam = list(rankedOrder[int(idx)][0])
            for j in eligiblePlayers:
                if j not in blueTeam:
                    redTeam.append(j)
            for j in blueTeam:
                blueRank += int(ELOpop[j][1])
            for j in redTeam:
                redRank += int(ELOpop[j][1])
            team1prob = round(1 / (1 + 10 ** ((redRank - blueRank) / 400)), 2)
            team2prob = round(1 / (1 + 10 ** ((blueRank - redRank) / 400)), 2)
            await teamsDisplay(ctx, blueTeam, redTeam, team1prob, team2prob)
        else:
            nblueTeam = activePickups[game][2]
            nredTeam = activePickups[game][5]
            neligiblePlayers = []
            for i in nblueTeam:
                neligiblePlayers.append(i)
            for i in nredTeam:
                neligiblePlayers.append(i)

            combos = list(
                itertools.combinations(neligiblePlayers, int(len(neligiblePlayers) / 2))
            )
            random.shuffle(combos)
            blueTeam = []
            redTeam = []
            rankedOrder = []
            redRank = 0
            blueRank = 0
            totalRank = 0
            half = 0
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
                if j not in blueTeam:
                    redTeam.append(j)
            blueRank = 0
            for j in blueTeam:
                blueRank += int(ELOpop[j][1])
            for j in redTeam:
                redRank += int(ELOpop[j][1])
            team1prob = round(1 / (1 + 10 ** ((redRank - blueRank) / 400)), 2)
            team2prob = round(1 / (1 + 10 ** ((blueRank - redRank) / 400)), 2)
            await teamsDisplay(ctx, blueTeam, redTeam, team1prob, team2prob)
            activePickups[game][0] = team1prob
            activePickups[game][1] = blueRank
            activePickups[game][2] = blueTeam
            activePickups[game][3] = team2prob
            activePickups[game][4] = redRank
            activePickups[game][5] = redTeam

            with open("activePickups.json", "w") as cd:
                json.dump(activePickups, cd, indent=4)


@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def shuffle(ctx, idx=None, game="None"):
    # global sMsg
    global rankedOrder
    global blueTeam
    global redTeam
    global team1prob
    global team2prob
    global blueRank
    global redRank
    global tMsg
    async with GLOBAL_LOCK:
        # rankedOrder = []
        if ctx.channel.name == v["pc"]:
            if idx is None:
                idx = random.randint(1, 11)
            with open("activePickups.json") as f:
                activePickups = json.load(f)
            with open("ELOpop.json") as f:
                ELOpop = json.load(f)

            if game == "None":
                blueRank = 0
                redRank = 0
                blueTeam = []
                redTeam = []
                logging.info(rankedOrder)
                blueTeam = list(rankedOrder[int(idx)][0])
                for j in eligiblePlayers:
                    if j not in blueTeam:
                        redTeam.append(j)
                for j in blueTeam:
                    blueRank += int(ELOpop[j][1])
                for j in redTeam:
                    redRank += int(ELOpop[j][1])
                team1prob = round(1 / (1 + 10 ** ((redRank - blueRank) / 400)), 2)
                team2prob = round(1 / (1 + 10 ** ((blueRank - redRank) / 400)), 2)
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

                combos = list(
                    itertools.combinations(
                        neligiblePlayers, int(len(neligiblePlayers) / 2)
                    )
                )
                random.shuffle(combos)
                blueTeam = []
                redTeam = []
                rankedOrder = []
                redRank = 0
                blueRank = 0
                totalRank = 0
                half = 0
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
                    if j not in blueTeam:
                        redTeam.append(j)
                blueRank = 0
                for j in blueTeam:
                    blueRank += int(ELOpop[j][1])
                for j in redTeam:
                    redRank += int(ELOpop[j][1])
                team1prob = round(1 / (1 + 10 ** ((redRank - blueRank) / 400)), 2)
                team2prob = round(1 / (1 + 10 ** ((blueRank - redRank) / 400)), 2)
                await teamsDisplay(ctx, blueTeam, redTeam, team1prob, team2prob)
                activePickups[game][0] = team1prob
                activePickups[game][1] = blueRank
                activePickups[game][2] = blueTeam
                activePickups[game][3] = team2prob
                activePickups[game][4] = redRank
                activePickups[game][5] = redTeam

                with open("activePickups.json", "w") as cd:
                    json.dump(activePickups, cd, indent=4)


@client.command(pass_context=True)
@commands.cooldown(1, 300, commands.BucketType.default)
async def notice(ctx, anumber=8):
    async with GLOBAL_LOCK:
        if ctx.channel.name == v["pc"]:
            global playersAdded
            number = len(list(playersAdded))
            role = discord.utils.get(ctx.guild.roles, id=v["TFCPlayer"])

        await ctx.send(f"{role.mention} {number}/{anumber}")


@client.command(pass_context=True)
@commands.cooldown(1, 300, commands.BucketType.default)
async def vote(ctx):
    """
    Nagging message to get people to vote who haven't picked their server or map choice yet
    """
    async with GLOBAL_LOCK:
        if ctx.channel.name == v["pc"] or ctx.channel.id == DEV_TESTING_CHANNEL:
            global players_abstained_discord_id
            if len(players_abstained_discord_id) >= 1:
                nag_list = players_abstained_discord_id
                for index, item in enumerate(nag_list):
                    nag_list[index] = f'<@{item}>'
                nag_message = ("\n💩 " + ", ".join(nag_list) + " need to vote 💩")
                await ctx.send(nag_message)
            else:
                await ctx.author.send("No active vote is happening!")


"""@slash.slash(name="slap")
async def slap(ctx, player: discord.Member):
    await ctx.send(f"{ctx.author.display_name} slapped {player.display_name} around a bit with a large trout")"""


@client.event
async def on_reaction_add(reaction, user):
    async with GLOBAL_LOCK:
        if not user.bot:
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
            global playersAbstained
            global players_abstained_discord_id
            global msg

            if reaction.message == pMsg:
                if (str(user.id) == cap1) or (str(user.id) == cap2):
                    if reaction.emoji == "1️⃣":
                        playerPicked = 1
                    elif reaction.emoji == "2️⃣":
                        playerPicked = 2
                    elif reaction.emoji == "3️⃣":
                        playerPicked = 3
                    elif reaction.emoji == "4️⃣":
                        playerPicked = 4
                    elif reaction.emoji == "5️⃣":
                        playerPicked = 5
                    elif reaction.emoji == "6️⃣":
                        playerPicked = 6

                    if pickCount == 0 and str(user.id) == cap1:
                        for i in pTotalPlayers:
                            if playerPicked in i:
                                pTotalPlayers.remove(i)
                                redTeam.append(i[1])
                                pickCount += 1
                                TeamPickPopulate()
                                await pMsg.edit(content="```" + msg + "```")
                    elif pickCount == 1 and str(user.id) == cap2:
                        for i in pTotalPlayers:
                            if playerPicked in i:
                                pTotalPlayers.remove(i)
                                blueTeam.append(i[1])
                                pickCount += 1
                                TeamPickPopulate()
                                await pMsg.edit(content="```" + msg + "```")
                    elif pickCount == 2 and str(user.id) == cap1:
                        for i in pTotalPlayers:
                            if playerPicked in i:
                                pTotalPlayers.remove(i)
                                redTeam.append(i[1])
                                pickCount += 1
                                TeamPickPopulate()
                                await pMsg.edit(content="```" + msg + "```")
                    elif pickCount == 3 and str(user.id) == cap2:
                        for i in pTotalPlayers:
                            if playerPicked in i:
                                pTotalPlayers.remove(i)
                                blueTeam.append(i[1])
                                pickCount += 1
                                TeamPickPopulate()
                                await pMsg.edit(content="```" + msg + "```")
                                await reaction.message.remove_reaction(reaction, user)
                                await reaction.message.remove_reaction(reaction, pMsg)
                    elif pickCount == 4 and str(user.id) == cap2:
                        for i in pTotalPlayers:
                            if playerPicked in i:
                                pTotalPlayers.remove(i)
                                blueTeam.append(i[1])
                                redTeam.append(pTotalPlayers[0][1])
                                pTotalPlayers.remove(pTotalPlayers[0])
                                pickCount += 1
                                TeamPickPopulate()

                                await reaction.message.channel.send(
                                    "```Teams are done being picked!  Here are the teams:\n\n"
                                    + msg
                                    + "```"
                                )
                                await reaction.message.channel.send(
                                    "Picking has ended.. join the server"
                                )
                                savePickup()
                                DePopulatePickup()
                                inVote = 0
                                reVote = 0

                    else:
                        await user.send("It is not your pick..")
                        await reaction.message.remove_reaction(reaction, user)
            if reaction.message == oMsg:
                if reaction.emoji == "👍":
                    with open("ELOpop.json") as f:
                        ELOpop = json.load(f)
                    if str(user.id) in playersAdded[0:8]:
                        ready.append(str(user.id))
                        if len(ready) < 8:
                            msgList = []
                            for i in playersAdded:
                                if "norank" in ELOpop[i][PLAYER_MAP_VISUAL_RANK_INDEX]:
                                    visualRank = ELOpop[i][PLAYER_MAP_VISUAL_RANK_INDEX]
                                else:
                                    visualRank = getRank(i)
                                if i in capList:
                                    msgList.append(
                                        visualRank
                                        + " "
                                        + ELOpop[i][PLAYER_MAP_VISUAL_NAME_INDEX]
                                        + " "
                                        + v["cptimg"]
                                        + "\n"
                                    )
                                    # msgList.append(ELOpop[i][0] + " " + v['cptimg'] + "\n")
                                else:
                                    msgList.append(
                                        visualRank
                                        + " "
                                        + ELOpop[i][PLAYER_MAP_VISUAL_NAME_INDEX]
                                        + "\n"
                                    )
                                    # msgList.append(ELOpop[i][0] + "\n")
                            msg = "".join(msgList)
                            readyList = []
                            for i in ready:
                                readyList.append(f"{ELOpop[i][0]}\n")
                            rMsg = "".join(readyList)
                            embed = discord.Embed(title="Pickup Has 8 or more Players")
                            if len(playersAdded) > 0:
                                embed.add_field(
                                    name=f"Players Added - {len(playersAdded)} Queued",
                                    value=msg,
                                )
                            elif len(playersAdded) == 0:
                                embed.add_field(
                                    name="Players Added", value="PUG IS EMPTY!"
                                )
                            embed.add_field(name="Players Ready", value=rMsg)

                            await oMsg.edit(embed=embed)
                        elif len(ready) == 8:
                            logging.info("Somehow we got 8 people to hit the thumbs up!")
                            channel2 = await client.fetch_channel(
                                reaction.message.channel.id
                            )
                            await doteams(channel2)
                    else:
                        await reaction.message.remove_reaction(reaction, user)
                        await user.send("You are not among the first 8 added...")

            if reaction.message == vMsg:
                if votable == 1:
                    if (
                        (reaction.emoji == "1️⃣")
                        or (reaction.emoji == "2️⃣")
                        or (reaction.emoji == "3️⃣")
                        or (reaction.emoji == "4️⃣")
                    ):
                        with open("ELOpop.json") as f:
                            ELOpop = json.load(f)
                        playerCount = len(eligiblePlayers)
                        userID = str(user.id)
                        playerName = ELOpop[str(userID)][0]
                        if inVote == 1:
                            if userID in eligiblePlayers:
                                for i in list(mapVotes):
                                    if playerName in mapVotes[i]:
                                        mapVotes[i].remove(playerName)
                                if reaction.emoji == "1️⃣":
                                    mapVotes[mapChoice1].append(playerName)
                                if reaction.emoji == "2️⃣":
                                    mapVotes[mapChoice2].append(playerName)
                                if reaction.emoji == "3️⃣":
                                    mapVotes[mapChoice3].append(playerName)
                                if reaction.emoji == "4️⃣":
                                    mapVotes[mapChoice4].append(playerName)
                                if playerName not in alreadyVoted:
                                    alreadyVoted.append(userID)

                                playersAbstained = []
                                players_abstained_discord_id = []
                                for i in eligiblePlayers:
                                    if i not in alreadyVoted:
                                        playersAbstained.append(ELOpop[str(i)][0])
                                        players_abstained_discord_id.append(i)
                                toVoteString = "```"
                                if len(playersAbstained) != 0:
                                    toVoteString = (
                                        "\n💩 "
                                        + ", ".join(playersAbstained)
                                        + " need to vote 💩```"
                                    )

                                with open("mainmaps.json") as f:
                                    mapList = json.load(f)
                                with open("specmaps.json") as f:
                                    mapList2 = json.load(f)
                                if serverVote == 1:
                                    await vMsg.edit(
                                        content="```Vote for your server! (Please wait for everyone to vote, or sub AFK players)\n\n"
                                        + "1️⃣ "
                                        + mapChoice1
                                        + " " * (70 - len(mapChoice1))
                                        + mapVoteOutput(mapChoice1)
                                        + "\n"
                                        + "2️⃣ "
                                        + mapChoice2
                                        + " " * (70 - len(mapChoice2))
                                        + mapVoteOutput(mapChoice2)
                                        + "\n"
                                        + "3️⃣ "
                                        + mapChoice3
                                        + " " * (70 - len(mapChoice3))
                                        + mapVoteOutput(mapChoice3)
                                        + toVoteString
                                    )
                                elif serverVote == 0:
                                    if reVote == 0:
                                        await vMsg.edit(
                                            content="```Vote up and make sure you hydrate!\n\n"
                                            + "1️⃣ "
                                            + mapChoice1
                                            + " " * (25 - len(mapChoice1))
                                            + "   "
                                            + str(mapList[mapChoice1])
                                            + " mirv"
                                            + " " * 15
                                            + mapVoteOutput(mapChoice1)
                                            + "\n"
                                            + "2️⃣ "
                                            + mapChoice2
                                            + " " * (25 - len(mapChoice2))
                                            + "   "
                                            + str(mapList[mapChoice2])
                                            + " mirv"
                                            + " " * 15
                                            + mapVoteOutput(mapChoice2)
                                            + "\n"
                                            + "3️⃣ "
                                            + mapChoice3
                                            + " " * (25 - len(mapChoice3))
                                            + "   "
                                            + str(mapList2[mapChoice3])
                                            + " mirv"
                                            + " " * 15
                                            + mapVoteOutput(mapChoice3)
                                            + "\n"
                                            + "4️⃣ "
                                            + mapChoice4
                                            + " " * (49 - len(mapChoice4))
                                            + mapVoteOutput(mapChoice4)
                                            + toVoteString
                                        )
                                    elif reVote == 1:
                                        if serverVote == 0:
                                            await vMsg.edit(
                                                content="```Vote up and make sure you hydrate!\n\n"
                                                + "1️⃣ "
                                                + mapChoice1
                                                + " " * (25 - len(mapChoice1))
                                                + "   "
                                                + str(mapList[mapChoice1])
                                                + " mirv"
                                                + " " * 15
                                                + mapVoteOutput(mapChoice1)
                                                + "\n"
                                                + "2️⃣ "
                                                + mapChoice2
                                                + " " * (25 - len(mapChoice2))
                                                + "   "
                                                + str(mapList[mapChoice2])
                                                + " mirv"
                                                + " " * 15
                                                + mapVoteOutput(mapChoice2)
                                                + "\n"
                                                + "3️⃣ "
                                                + mapChoice3
                                                + " " * (25 - len(mapChoice3))
                                                + "   "
                                                + str(mapList2[mapChoice3])
                                                + " mirv"
                                                + " " * 15
                                                + mapVoteOutput(mapChoice3)
                                                + "\n"
                                                + "4️⃣ "
                                                + mapChoice4
                                                + " " * (49 - len(mapChoice4))
                                                + mapVoteOutput(mapChoice4)
                                                + toVoteString
                                            )
                                logging.info(alreadyVoted)
                                logging.info(mapVotes)
                                logging.info(playerCount)
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

    if message.content == "elo":
        with open("ELOpop.json") as f:
            ELOpop = json.load(f)
        user = await client.fetch_user(message.author.id)
        dev_channel = await client.fetch_channel(DEV_TESTING_CHANNEL)
        db = mysql.connector.connect(
            host=logins['mysql']['host'],
            user=logins['mysql']['user'],
            passwd=logins['mysql']['passwd'],
            database=logins['mysql']['database'],
        )

        mycursor = db.cursor()
        try:
            if message.guild is None and message.author != client.user:
                mycursor.execute(
                    f"SELECT player_elos from player_elo WHERE discord_id = {user.id}"
                )
                plotList = []
                for x in mycursor:
                    plotList.append(int(x[0]))
                plt.plot(plotList)
                plt.savefig(message.author.display_name + ".png")

                mycursor.execute(
                    f"""
                        with elo_row_numbered as (
                        select player_name, player_elos, discord_id, row_number() over (partition by player_name order by entryID desc) as row_num from player_elo
                        )

                        select player_elos from elo_row_numbered where row_num = 1 and discord_id = '{user.id}'
                        order by player_elos desc;"""
                )

                if mycursor.rowcount is None:
                    logging.warning('Had to fall-back to local elo file - check for issue query')
                    logging.warning(f"""
                        with elo_row_numbered as (
                        select player_name, player_elos, discord_id, row_number() over (partition by player_name order by entryID desc) as row_num from player_elo
                        )

                        select player_elos from elo_row_numbered where row_num = 1 and discord_id = '{user.id}'
                        order by player_elos desc;""")
                    await dev_channel.send(f"""Query failed for ELO for some reason - check mysql db - with elo_row_numbered as (
                        select player_name, player_elos, discord_id, row_number() over (partition by player_name order by entryID desc) as row_num from player_elo
                        )

                        select player_elos from elo_row_numbered where row_num = 1 and discord_id = '{user.id}'
                        order by player_elos desc;""")
                    await message.author.send(
                        file=discord.File(message.author.display_name + ".png"),
                        content=f"Your ELO is currently {ELOpop[str(user.id)][1]} with a record of W: {ELOpop[str(user.id)][4]} L: {ELOpop[str(user.id)][5]} D: {ELOpop[str(user.id)][6]}",
                    )
                else:
                    current_elo = plotList[-1]
                    previous_game_elo = plotList[-2]
                    elo_difference = current_elo - previous_game_elo
                    if (elo_difference) < 0:
                        elo_difference_message = f"""```diff\n-{abs(elo_difference)}```"""
                    else:
                        elo_difference_message = f"""```diff\n+{elo_difference}```"""
                    await message.author.send(
                        file=discord.File(message.author.display_name + ".png"),
                        content=f"Your ELO is currently {current_elo} with a record of W: {ELOpop[str(user.id)][4]} L: {ELOpop[str(user.id)][5]} D: {ELOpop[str(user.id)][6]}\n Difference from previous game:{elo_difference_message}",
                    )
                os.remove(message.author.display_name + ".png")
                plt.clf()
        except Exception as e:
            await message.author.send("Command failed - Sending error to admins")
            await dev_channel.send(e)

    await client.process_commands(message)


logging.info(v["TOKEN"])

client.run(v["TOKEN"])
# client.run('NzMyMzcyMTcwMzY5NTMxOTc4.G-L8nP.JZ6Gj_AwGnavMYbjW5XU-VVHx6BTeAPUQwEjqI')
