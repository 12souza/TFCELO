import asyncio
import datetime
import itertools
import json
import logging
import os
import random
import re
import time
import typing
import urllib.request
import zipfile
from ftplib import FTP
import traceback
import discord
import matplotlib.pyplot as plt
import mplcyberpunk
import mysql.connector
from discord.ext import commands, tasks
from discord.utils import get
from discord import TextChannel
from PIL import Image, ImageFont, ImageDraw, ImageEnhance
from datetime import timezone
from pathlib import Path
import boto3
from discord.ext.commands import Context
import aiohttp
from bs4 import BeautifulSoup
import aioftp
import aiofiles
import aiomysql

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

intents = discord.Intents.all()
client = commands.Bot(
    command_prefix=["!", "+", "-"], case_insensitive=True, intents=intents
)
client.remove_command("help")


async def load_extensions():
    await client.load_extension("cogs.dm_commands")


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send("This command is on a %.2fs cooldown" % error.retry_after)
    elif isinstance(error, commands.MissingRole):
        await ctx.send(
            "This command requires you to have a certain role that you don't have"
        )
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("The command that you entered was not found")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(error)
    elif isinstance(error, commands.CommandInvokeError):
        await ctx.send(
            "The command that you sent failed with an error on the backend. Sending debug-output to admins!"
        )
        dev_channel = await client.fetch_channel(DEV_TESTING_CHANNEL)
        exception_string = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        await dev_channel.send(exception_string[:2000])
        raise error
    else:
        raise error  # re-raise the error so all the errors will still show up in console


# Load in ELO configuration
with open("ELOpop.json") as f:
    ELOpop = json.load(f)

# Load in main script configuration
with open("variables.json") as f:
    v = json.load(f)

# TODO: Update login to work differently..

with open("login.json") as f:
    logins = json.load(f)

filename = Path('mute_list.json')
filename.touch(exist_ok=True)
with open(filename) as f:
    mute_list = json.load(f)

filename = Path('hellban_list.json')
filename.touch(exist_ok=True)
with open(filename) as f:
    hellban_list = json.load(f)

# =====================================
# =========== DEFINE GLOBALS ==========
# =====================================

GLOBAL_LOCK = None

# ELOpop scheme
# ELOpop contains at the root a map of player ID (i.e. str(ctx.author.id)) to a list of variables metadata slots
# TODO: Move to fixtures file
PLAYER_MAP_VISUAL_NAME_INDEX = 0  # Player's visual name
PLAYER_MAP_CURRENT_ELO_INDEX = 1  # Player's current ELO number
PLAYER_MAP_VISUAL_RANK_INDEX = 3  # current visual rank icon
PLAYER_MAP_WIN_INDEX = 4
PLAYER_MAP_LOSS_INDEX = 5
PLAYER_MAP_DRAW_INDEX = 6
PLAYER_MAP_ACHIEVEMENT_INDEX = 7  # list of achievement icons
PLAYER_MAP_DUNCE_FLAG_INDEX = 8  # Is this player a dunce or not?
PLAYER_MAP_STEAM_ID_INDEX = 9
PLAYER_MAP_DM_WIN_INDEX = 10
PLAYER_MAP_DM_LOSS_INDEX = 11
PAST_TEN_BLUE_TEAM_INDEX = 0
PAST_TEN_RED_TEAM_INDEX = 4
PAST_TEN_MATCH_OUTCOME_INDEX = 8
PAST_TEN_MAP_INDEX = 9
LOCAL_DEV_ENABLED = bool(os.getenv("TFCELO_LOCAL_DEV")) is True
DEV_TESTING_CHANNEL = 1139762727275995166
MAP_VOTE_FIRST = True
RANK_BOUNDARIES_LIST = [720, 950, 1190, 1440, 1700, 1960, 2230, 2510, 2800, 3100]
MAIN_MAPS_FILE = "classic_maps.json"
SECONDARY_MAPS_FILE = "spring_2024_maps.json"
SHOW_VISUAL_RANKS = False
SERVER_VOTE_TIME_LIMIT = 181
MAP_VOTE_TIME_LIMIT = 61
SHOW_MAP_VOTE_COUNTS = True

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
map_choice_1 = None
map_choice_2 = None
map_choice_3 = None
map_choice_4 = None
map_choice_5 = None
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
inVote = 0
eligiblePlayers = []
reVote = 0
captMode = 0
vMsg = None
server_vote = 0
mapVote = 0
pickCount = 0
msg = None
pTotalPlayers = []
winningMap = None
winningServer = None
last_add_timestamp = datetime.datetime.utcnow()
last_add_context = None
map_url_dictionary = {}
server_vote_message_view = None
map_vote_message_view = None

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


async def get_mvp_steam_id(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html = await response.text()
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find the MVP by looking for the span with class="mvp"
    mvp_span = soup.find('span', class_='mvp')
    if not mvp_span:
        return None
        
    # Get the parent td element that contains both the MVP span and the player link
    player_td = mvp_span.find_parent('td', class_='player-name')
    if not player_td:
        return None
        
    # Find the player link within this td
    player_link = player_td.find('a')
    if not player_link:
        return None
    
    # Get the MVP's player ID
    player_id = player_link.get('href').replace('p', '').replace('.html', '')
    
    # Find all catacombs tracker links
    catacombs_links = soup.find_all('a', href=lambda href: href and 'steamid=' in href)
    
    # Find the catacombs link that matches our player ID
    for link in catacombs_links:
        if player_id in link['href']:
            # Extract Steam ID from the URL
            match = re.search(r'steamid=(\d:\d:\d+)', link['href'])
            if match:
                steam_id = "STEAM_" + match.group(1)
                return steam_id
    
    return None


async def get_db_pool():
    return await aiomysql.create_pool(
        host=logins["mysql"]["host"],
        user=logins["mysql"]["user"],
        password=logins["mysql"]["passwd"],
        db=logins["mysql"]["database"],
        autocommit=True
    )


async def setup_global_lock():
    global GLOBAL_LOCK
    GLOBAL_LOCK = asyncio.Lock()

async def generate_teams(playerCount):
    global playersAdded
    global capList
    global inVote
    global blueTeam
    global redTeam
    global eligiblePlayers
    global oMsg
    global captMode
    global server_vote
    global rankedOrder
    global ready
    dev_channel = await client.fetch_channel(DEV_TESTING_CHANNEL)
    with open("ELOpop.json") as f:
        ELOpop = json.load(f)
    logging.info(f"eligiblePlayers: {eligiblePlayers}")
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
            # Check if the corresponding opposite team is already in the list before adding
            # This prevents duplicate lineups from being inserted
            current_team = list(i)
            opposing_team = []
            already_inserted = False
            for j in eligiblePlayers:
                if j not in current_team:
                    opposing_team.append(j)
            opposing_team = sorted(opposing_team)
            for index, team in enumerate(rankedOrder):
                if (
                    sorted(rankedOrder[index][0])
                    == opposing_team
                ):
                    already_inserted = True
                    break
            if not already_inserted:
                rankedOrder.append(
                    (list(i), abs(blueRank - half))
                )
                rankedOrder = sorted(
                    rankedOrder, key=lambda x: x[1]
                )
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

    blueTeam = list(rankedOrder[0][0])

    for j in eligiblePlayers:
        if j not in blueTeam:
            redTeam.append(j)
    blueRank = 0
    for j in blueTeam:
        blueRank += int(ELOpop[j][1])
    blue_diff = abs(blueRank - half)
    for j in redTeam:
        redRank += int(ELOpop[j][1])
    red_diff = abs(redRank - half)

    # Make blue team the favored team as it allows them to be lenient on defense
    # if desired/needed for sportsmanship.
    if redRank > blueRank:
        logging.info("Swapping team colors so blue is favored")
        tempTeam = blueTeam
        tempRank = blueRank
        blueTeam = redTeam
        blueRank = redRank
        redTeam = tempTeam
        redRank = tempRank

    team1prob = round(
        1 / (1 + 10 ** ((redRank - blueRank) / 400)), 2
    )
    team2prob = round(
        1 / (1 + 10 ** ((blueRank - redRank) / 400)), 2
    )
    blue_team_info_string = f"blueTeam: {blueTeam}, diff: {blue_diff}, blueRank: {blueRank}, blue_win_probability: {team1prob}"
    red_team_info_string = f"redTeam: {redTeam}, diff {red_diff}, redRank: {redRank}, red_win_probability {team2prob}"
    logging.info(blue_team_info_string)
    logging.info(red_team_info_string)

    await dev_channel.send(
        "Outputting top 5 possible games by absolute ELO difference sorted ascending"
    )
    debug_embeds = []
    for index, item in enumerate(rankedOrder):
        if index > 4:
            break
        dev_blue_team = rankedOrder[index][0]
        dev_blue_rank = 0
        dev_red_team = []
        dev_red_rank = 0
        for j in eligiblePlayers:
            if j not in dev_blue_team:
                dev_red_team.append(j)
        for j in dev_blue_team:
            dev_blue_rank += int(ELOpop[j][1])
        dev_blue_diff = abs(dev_blue_rank - half)
        for j in dev_red_team:
            dev_red_rank += int(ELOpop[j][1])
        dev_red_diff = abs(dev_red_rank - half)

        # Make blue team the favored team as it allows them to be lenient on defense
        # if desired/needed for sportsmanship.
        if dev_red_rank > dev_blue_rank:
            logging.info(
                "DEV LOGGING: Swapping team colors so blue is favored"
            )
            tempTeam = dev_blue_team
            tempRank = dev_blue_rank
            dev_blue_team = dev_red_team
            dev_blue_rank = dev_red_rank
            dev_red_team = tempTeam
            dev_red_rank = tempRank

        logging.info(
            f"blueTeam: {dev_blue_team}, diff: {dev_blue_diff}, blueRank: {dev_blue_rank}"
        )
        logging.info(
            f"redTeam: {dev_red_team}, diff {dev_red_diff}, redRank: {dev_red_rank}"
        )

        dev_team1prob = round(
            1
            / (
                1 + 10 ** ((dev_red_rank - dev_blue_rank) / 400)
            ),
            2,
        )
        dev_team2prob = round(
            1
            / (
                1 + 10 ** ((dev_blue_rank - dev_red_rank) / 400)
            ),
            2,
        )
        debug_embeds.append(
            teamsDisplay(
                dev_blue_team,
                dev_red_team,
                dev_team1prob,
                dev_team2prob,
                dev_blue_rank,
                dev_red_rank,
                True,
                True,
            )
        )
    await dev_channel.send(embeds=debug_embeds)


def process_vote(player: discord.Member = None, vote=None):
    global eligiblePlayers
    global inVote
    global mapVotes
    global playersAbstained
    global players_abstained_discord_id

    with open("ELOpop.json") as f:
        ELOpop = json.load(f)
    playerCount = len(eligiblePlayers)
    userID = str(player.id)
    playerName = ELOpop[str(userID)][0]
    # TODO: inVote check for == 0?
    if inVote == 1:
        if userID in eligiblePlayers:
            # If the player has already voted for a map, remove their vote so they can change their decision
            # TODO: Seems sub-optimal if they just click the same option twice?
            for i in list(mapVotes):
                if playerName in mapVotes[i]:
                    mapVotes[i].remove(playerName)
            if vote == map_choice_1:
                mapVotes[map_choice_1].append(playerName)
            if vote == map_choice_2:
                mapVotes[map_choice_2].append(playerName)
            if vote == map_choice_3:
                mapVotes[map_choice_3].append(playerName)
            if vote == map_choice_4:
                mapVotes[map_choice_4].append(playerName)
            if vote == map_choice_5:
                mapVotes[map_choice_5].append(playerName)
            if userID not in alreadyVoted:
                alreadyVoted.append(userID)

            playersAbstained = []
            players_abstained_discord_id = []
            for i in eligiblePlayers:
                if i not in alreadyVoted:
                    playersAbstained.append(ELOpop[str(i)][0])
                    players_abstained_discord_id.append(i)
            logging.info(alreadyVoted)
            logging.info(mapVotes)
        # TODO: Consider giving error message to player who hits button who isn't in pickup?


def drawProgressBar(d, x, y, w, h, progress, bg="black", fg="gold"):
    # draw background
    d.ellipse((x + w, y, x + h + w, y + h), fill=bg)
    d.ellipse((x, y, x + h, y + h), fill=bg)
    d.rectangle((x + (h / 2), y, x + w + (h / 2), y + h), fill=bg)

    # draw progress bar
    w *= progress
    d.ellipse((x + w, y, x + h + w, y + h), fill=fg)
    d.ellipse((x, y, x + h, y + h), fill=fg)
    d.rectangle((x + (h / 2), y, x + w + (h / 2), y + h), fill=fg)

    return d


def generate_map_vote_embed(vote_round, time_remaining=MAP_VOTE_TIME_LIMIT):
    global map_choice_1
    global map_choice_2
    global map_choice_3
    global map_choice_4
    global map_choice_5
    global playersAbstained

    with open(MAIN_MAPS_FILE) as f:
        main_maps = json.load(f)
    with open(SECONDARY_MAPS_FILE) as f:
        secondary_maps = json.load(f)

    main_embed = discord.Embed(
        title="Vote for map!",
        description=f"Time remaining in vote - {time_remaining} Seconds",
        color=0xF1C40F,
        url="https://tfpugs.online/",
    )

    main_embed.add_field(
        name="",
        value="1️⃣ "
        + map_choice_1
        + " " * (25 - len(map_choice_1))
        + "   "
        + str(main_maps[map_choice_1]["mirv_count"])
        + " mirv <:mirv:1242078860611158106>"
        + " " * 15
        + "\n"
        + mapVoteOutput(map_choice_1),
        inline=False,
    )
    main_embed.add_field(
        name="",
        value="2️⃣ "
        + map_choice_2
        + " " * (25 - len(map_choice_2))
        + "   "
        + str(main_maps[map_choice_2]["mirv_count"])
        + " mirv <:mirv:1242078860611158106>"
        + " " * 15
        + "\n"
        + mapVoteOutput(map_choice_2),
        inline=False,
    )
    main_embed.add_field(
        name="",
        value="3️⃣ "
        + map_choice_3
        + " " * (25 - len(map_choice_3))
        + "   "
        + str(secondary_maps[map_choice_3]["mirv_count"])
        + " mirv <:mirv:1242078860611158106>"
        + " " * 15
        + "\n"
        + mapVoteOutput(map_choice_3),
        inline=False,
    )
    main_embed.add_field(
        name="",
        value="4️⃣ "
        + map_choice_4
        + " " * (25 - len(map_choice_4))
        + "   "
        + str(secondary_maps[map_choice_4]["mirv_count"])
        + " mirv <:mirv:1242078860611158106>"
        + " " * 15
        + "\n"
        + mapVoteOutput(map_choice_4),
        inline=False,
    )
    if vote_round == 0:
        # New Maps
        main_embed.add_field(
            name="",
            value="5️⃣ "
            + map_choice_5
            + " " * (49 - len(map_choice_5))
            + "\n"
            + mapVoteOutput(map_choice_5),
            inline=False,
        )
    elif vote_round == 1:
        # Weird edge-case handling - need to look up mirv count for the carry-over map
        if (
            main_maps.get(map_choice_5) is not None
            and main_maps.get(map_choice_5) != "New Maps"
        ):
            carryover_mirv_count = str(main_maps[map_choice_5]["mirv_count"])
        else:
            carryover_mirv_count = str(secondary_maps[map_choice_5]["mirv_count"])
        main_embed.add_field(
            name="",
            value="5️⃣ "
            + map_choice_5
            + " " * (25 - len(map_choice_5))
            + "   "
            + carryover_mirv_count
            + " mirv <:mirv:1242078860611158106>"
            + " " * 15
            + "\n"
            + mapVoteOutput(map_choice_5),
            inline=False,
        )
    unvoted_string = "💩" + ", ".join(playersAbstained) + " need to vote! 💩"
    main_embed.set_footer(text=unvoted_string)

    # create image or load your existing image with out=Image.open(path)
    out = Image.new("RGBA", (150, 13), (255, 255, 255, 0))
    d = ImageDraw.Draw(out)

    # draw the progress bar to given location, width, progress and color
    d = drawProgressBar(d, 10, 4, 100, 6.25, (8 - len(playersAbstained)) / 8)
    out.save("pickup_progress_bar.png", "PNG")
    image_file = discord.File("pickup_progress_bar.png")
    main_embed.set_image(url="attachment://pickup_progress_bar.png")
    # TODO: add past 5 maps like inhouse?
    return main_embed, image_file


def generate_server_vote_embed(time_remaining=SERVER_VOTE_TIME_LIMIT):
    global map_choice_1
    global map_choice_2
    global map_choice_3
    global map_choice_4
    global map_choice_5
    global playersAbstained

    main_embed = discord.Embed(
        title="Vote for server!",
        description=f"Time remaining in vote - {time_remaining} Seconds",
        color=0xF1C40F,
        url="https://tfpugs.online/",
    )

    main_embed.add_field(
        name="",
        value="1️⃣ " + map_choice_1 + "\n" + server_vote_output(map_choice_1),
        inline=False,
    )
    main_embed.add_field(
        name="",
        value="2️⃣ " + map_choice_2 + "\n" + server_vote_output(map_choice_2),
        inline=False,
    )
    main_embed.add_field(
        name="",
        value="3️⃣ " + map_choice_3 + "\n" + server_vote_output(map_choice_3),
        inline=False,
    )

    unvoted_string = "💩" + ", ".join(playersAbstained) + " need to vote! 💩"
    main_embed.set_footer(text=unvoted_string)

    out = Image.new("RGBA", (150, 13), (255, 255, 255, 0))
    d = ImageDraw.Draw(out)

    # draw the progress bar to given location, width, progress and color
    d = drawProgressBar(d, 10, 4, 100, 6.25, (8 - len(playersAbstained)) / 8)
    out.save("pickup_progress_bar.png", "PNG")
    image_file = discord.File("pickup_progress_bar.png")
    main_embed.set_image(url="attachment://pickup_progress_bar.png")
    # TODO: add past 5 maps like inhouse?
    return main_embed, image_file


async def handle_map_button_callback(
    self, interaction: discord.Interaction, button: discord.ui.Button
):
    global reVote
    process_vote(interaction.user, button.custom_id)
    time_remaining = f"{MAP_VOTE_TIME_LIMIT - map_vote_timer.current_loop}"
    embed, progress_bar = generate_map_vote_embed(reVote, time_remaining)
    await interaction.response.edit_message(embed=embed, attachments=[progress_bar])


async def handle_server_button_callback(
    self, interaction: discord.Interaction, button: discord.ui.Button
):
    global SERVER_VOTE_TIME_LIMIT
    process_vote(interaction.user, button.custom_id)
    time_remaining = f"{SERVER_VOTE_TIME_LIMIT - server_vote_timer.current_loop}"
    embed, progress_bar = generate_server_vote_embed(time_remaining)
    await interaction.response.edit_message(embed=embed, attachments=[progress_bar])


class ServerVoteView(discord.ui.View):
    global map_choice_1
    global map_choice_2
    global map_choice_3
    global map_choice_4
    global map_choice_5

    def __init__(self):
        super().__init__(timeout=SERVER_VOTE_TIME_LIMIT)
        self.add_buttons()

    def add_buttons(self):
        self.add_item(
            self.create_button(label=f"1️⃣ {map_choice_1}", custom_id=map_choice_1)
        )
        self.add_item(
            self.create_button(label=f"2️⃣ {map_choice_2}", custom_id=map_choice_2)
        )
        self.add_item(
            self.create_button(label=f"3️⃣ {map_choice_3}", custom_id=map_choice_3)
        )

    def create_button(self, label, custom_id):
        button = discord.ui.Button(
            label=label, custom_id=custom_id, style=discord.ButtonStyle.blurple
        )

        async def server_button_callback(interaction: discord.Interaction):
            await handle_server_button_callback(self, interaction, button)

        button.callback = server_button_callback
        return button


class MapVoteView(discord.ui.View):
    global map_choice_1
    global map_choice_2
    global map_choice_3
    global map_choice_4
    global map_choice_5

    def __init__(self):
        super().__init__(timeout=MAP_VOTE_TIME_LIMIT)
        self.add_buttons()

    def add_buttons(self):
        self.add_item(
            self.create_button(label=f"1️⃣ {map_choice_1}", custom_id=map_choice_1)
        )
        self.add_item(
            self.create_button(label=f"2️⃣ {map_choice_2}", custom_id=map_choice_2)
        )
        self.add_item(
            self.create_button(label=f"3️⃣ {map_choice_3}", custom_id=map_choice_3)
        )
        self.add_item(
            self.create_button(label=f"4️⃣ {map_choice_4}", custom_id=map_choice_4)
        )
        self.add_item(
            self.create_button(label=f"5️⃣ {map_choice_5}", custom_id=map_choice_5)
        )

    def create_button(self, label, custom_id):
        button = discord.ui.Button(
            label=label, custom_id=custom_id, style=discord.ButtonStyle.blurple
        )

        async def map_button_callback(interaction: discord.Interaction):
            await handle_map_button_callback(self, interaction, button)

        button.callback = map_button_callback
        return button


def teamsDisplay(
    blueTeam,
    redTeam,
    team1prob,
    team2prob,
    team1_elo=None,
    team2_elo=None,
    show_probability=False,
    show_visual_rank=False,
):
    msgList = []

    for i in blueTeam:
        if show_visual_rank:
            msgList.append(
                getRank(i)
                + " "
                + ELOpop[i][PLAYER_MAP_VISUAL_NAME_INDEX]
                + " "
                + str(ELOpop[i][PLAYER_MAP_CURRENT_ELO_INDEX])
                + "\n"
            )
        else:
            msgList.append(ELOpop[i][PLAYER_MAP_VISUAL_NAME_INDEX] + "\n")
    bMsg = "".join(msgList)
    msgList.clear()
    for i in redTeam:
        if show_visual_rank:
            msgList.append(
                getRank(i)
                + " "
                + ELOpop[i][PLAYER_MAP_VISUAL_NAME_INDEX]
                + " "
                + str(ELOpop[i][PLAYER_MAP_CURRENT_ELO_INDEX])
                + "\n"
            )
        else:
            msgList.append(ELOpop[i][PLAYER_MAP_VISUAL_NAME_INDEX] + "\n")
    rMsg = "".join(msgList)
    embed = discord.Embed(title="Teams Sorted!", color=0xF1C40F)
    if show_probability:
        embed.add_field(
            name="Blue Team "
            + v["t1img"]
            + " "
            + str(int(team1prob * 100))
            + "% "
            + str(int(team1_elo)),
            value=bMsg,
            inline=True,
        )
    else:
        embed.add_field(name="Blue Team " + v["t1img"], value=bMsg, inline=True)
    embed.add_field(name="\u200b", value="\u200b")
    if show_probability:
        embed.add_field(
            name="Red Team "
            + v["t2img"]
            + " "
            + str(int(team2prob * 100))
            + "% "
            + str(int(team2_elo)),
            value=rMsg,
            inline=True,
        )
    else:
        embed.add_field(name="Red Team " + v["t2img"], value=rMsg, inline=True)
    return embed


def get_map_vote_output(reVote, map_list, map_list_2, unvoted_string):
    global map_choice_1
    global map_choice_2
    global map_choice_3
    global map_choice_4
    global map_choice_5
    output = "Something went wrong"
    if reVote == 0:
        output = (
            "```1️⃣ "
            + map_choice_1
            + " " * (25 - len(map_choice_1))
            + "   "
            + str(map_list[map_choice_1]["mirv_count"])
            + " mirv <:mirv:1242078860611158106>"
            + " " * 15
            + mapVoteOutput(map_choice_1)
            + "\n"
            + "2️⃣ "
            + map_choice_2
            + " " * (25 - len(map_choice_2))
            + "   "
            + str(map_list[map_choice_2]["mirv_count"])
            + " mirv <:mirv:1242078860611158106>"
            + " " * 15
            + mapVoteOutput(map_choice_2)
            + "\n"
            + "3️⃣ "
            + map_choice_3
            + " " * (25 - len(map_choice_3))
            + "   "
            + str(map_list_2[map_choice_3]["mirv_count"])
            + " mirv <:mirv:1242078860611158106>"
            + " " * 15
            + mapVoteOutput(map_choice_3)
            + "\n"
            + "4️⃣ "
            + map_choice_4
            + " " * (25 - len(map_choice_4))
            + "   "
            + str(map_list_2[map_choice_4]["mirv_count"])
            + " mirv <:mirv:1242078860611158106>"
            + " " * 15
            + mapVoteOutput(map_choice_4)
            + "\n"
            + "5️⃣ "
            + map_choice_5
            + " " * (49 - len(map_choice_5))
            + mapVoteOutput(map_choice_5)
            + unvoted_string
        )
    elif reVote == 1:
        # Weird edge-case handling - need to look up mirv count for the carry-over map
        if (
            map_list.get(map_choice_5) is not None
            and map_list.get(map_choice_5) != "New Maps"
        ):
            carryover_mirv_count = str(map_list[map_choice_5]["mirv_count"])
        else:
            carryover_mirv_count = str(map_list_2[map_choice_5]["mirv_count"])
        output = (
            "```Vote up and make sure you hydrate!\n\n"
            + "1️⃣ "
            + map_choice_1
            + " " * (25 - len(map_choice_1))
            + "   "
            + str(map_list[map_choice_1]["mirv_count"])
            + " mirv <:mirv:1242078860611158106>"
            + " " * 15
            + mapVoteOutput(map_choice_1)
            + "\n"
            + "2️⃣ "
            + map_choice_2
            + " " * (25 - len(map_choice_2))
            + "   "
            + str(map_list[map_choice_2]["mirv_count"])
            + " mirv <:mirv:1242078860611158106>"
            + " " * 15
            + mapVoteOutput(map_choice_2)
            + "\n"
            + "3️⃣ "
            + map_choice_3
            + " " * (25 - len(map_choice_3))
            + "   "
            + str(map_list_2[map_choice_3]["mirv_count"])
            + " mirv <:mirv:1242078860611158106>"
            + " " * 15
            + mapVoteOutput(map_choice_3)
            + "\n"
            + "4️⃣ "
            + map_choice_4
            + " " * (25 - len(map_choice_4))
            + "   "
            + str(map_list_2[map_choice_4]["mirv_count"])
            + " mirv <:mirv:1242078860611158106>"
            + " " * 15
            + mapVoteOutput(map_choice_4)
            + "\n"
            + "5️⃣ 🔄 "
            + map_choice_5
            + " " * (25 - len(map_choice_5))
            + "   "
            + carryover_mirv_count
            + " mirv <:mirv:1242078860611158106>"
            + " " * 15
            + mapVoteOutput(map_choice_5)
            + unvoted_string
        )
    return output


def find(haystack, needle, n):
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start + len(needle))
        n -= 1
    return start


async def stat_log_file_handler(region):
    async with aioftp.Client.context(
        logins[region]["server_ip"],
        user=logins[region]["ftp_username"],
        password=logins[region]["ftp_password"]
    ) as ftp_client:
        await ftp_client.change_directory("logs")
        
        # Get list of logs and sort them
        log_files = await ftp_client.list()
        # Extract filenames from tuples and sort
        log_files = sorted(log_files, key=lambda x: x[0], reverse=True)  # Most recent first
        
        last_two_big_logs = []
        for log_file in log_files:
            file_size = int(log_file[1]['size'])  # Access size from the dictionary
            if file_size > 100000 and ".log" in log_file[0].name:
                last_two_big_logs.append(log_file[0])
                if len(last_two_big_logs) >= 2:
                    break

        if len(last_two_big_logs) < 2:
            raise Exception("Could not find enough log files")

        log_to_parse1 = last_two_big_logs[1]
        log_to_parse2 = last_two_big_logs[0]

        # Download logs asynchronously
        for log_file in [log_to_parse1, log_to_parse2]:
            async with aiofiles.open(str(log_file), mode='wb') as f:
                try:
                    async with ftp_client.download_stream(log_file) as stream:
                        data = await stream.read()
                        await f.write(data)
                except aioftp.StatusCodeError as e:
                    if '226' in str(e):  # Transfer complete
                        logging.info(f"Successfully downloaded {log_file}")
                    else:
                        raise

        # Rename files
        await asyncio.to_thread(os.rename, str(log_to_parse1), f"{str(log_to_parse1)[0:-4]}-coach{region}.log")
        await asyncio.to_thread(os.rename, str(log_to_parse2), f"{str(log_to_parse2)[0:-4]}-coach{region}.log")

        log_to_parse1 = f"{str(log_to_parse1)[0:-4]}-coach{region}.log"
        log_to_parse2 = f"{str(log_to_parse2)[0:-4]}-coach{region}.log"

        # Read log file asynchronously
        pickup_date = None
        pickup_map = None
        async with aiofiles.open(log_to_parse1, mode='r') as f:
            async for line in f:
                if "Loading map" in line:
                    mapstart = line.find('map "') + 5
                    mapend = line.find('"', mapstart)
                    datestart = line.find("L ") + 2
                    dateend = line.find("-", datestart)
                    pickup_date = line[datestart:dateend]
                    pickup_map = line[mapstart:mapend]
                    break

        # Make HTTP requests asynchronously
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field('force', 'on')
            data.add_field('logs[]', open(log_to_parse1, 'rb'))
            data.add_field('logs[]', open(log_to_parse2, 'rb'))
            
            async with session.post('https://www.tfcstats.com/api/parsePickup', data=data) as response:
                api_output = await response.text()

        log_output = None
        hampalyzer_output = None
        blarghalyzer_fallback = None

        tfc_stats_output = json.loads(api_output)
        if tfc_stats_output.get('success') is not None:
            log_output = tfc_stats_output["success"]["path"]
        else:
            logging.error(f"Error in tfc_stats_output: {tfc_stats_output}")
        if hampalyzer_output is None:
            # Additional output to hampalyzer
            async with aiohttp.ClientSession() as session:
                data = aiohttp.FormData()
                data.add_field('force', 'on')
                data.add_field('logs[]', open(log_to_parse1, 'rb'))
                data.add_field('logs[]', open(log_to_parse2, 'rb'))
                
                async with session.post('http://app.hampalyzer.com/api/parseGame', data=data) as response:
                    output3 = await response.text()

            if "nginx" not in output3 and output3:
                hampalyzer_output = "http://app.hampalyzer.com/" + output3[21:-3]
            # Fallback to blarghalyzer
            else:
                async with aiohttp.ClientSession() as session:
                    for log_file in [log_to_parse1, log_to_parse2]:
                        data = aiohttp.FormData()
                        data.add_field('process', 'true')
                        data.add_field('inptImage', open(log_file, 'rb'))
                        data.add_field('language', 'en')
                        data.add_field('blarghalyze', 'Blarghalyze!')
                        
                        async with session.post('http://blarghalyzer.com/Blarghalyzer.php', data=data) as response:
                            await response.text()

                blarghalyzer_fallback = (
                    f"**Round 1:** https://blarghalyzer.com/parsedlogs/{log_to_parse1[:-4].lower()}/ "
                    f"**Round 2:** https://blarghalyzer.com/parsedlogs/{log_to_parse2[:-4].lower()}/"
                )

        # Clean up files asynchronously
        await asyncio.to_thread(os.remove, log_to_parse1)
        await asyncio.to_thread(os.remove, log_to_parse2)

        return pickup_date, pickup_map, log_output, hampalyzer_output, blarghalyzer_fallback

async def hltv_file_handler(region, pickup_date, pickup_map):
    try:
        async with aioftp.Client.context(
            logins[region]["server_ip"],
            user=logins[region]["ftp_username"],
            password=logins[region]["ftp_password"]
        ) as ftp_client:
            await ftp_client.change_directory(f"HLTV{region.upper()}")
            
            # Get list of demos
            hltv_files = await ftp_client.list()
            # Extract filenames from tuples and sort
            hltv_files = sorted(hltv_files, key=lambda x: x[0], reverse=True)  # Most recent first

            last_two_big_hltvs = []
            for hltv_file in hltv_files:
                file_size = int(hltv_file[1]['size'])
                if file_size > 11000000 and ".dem" in hltv_file[0].name:
                    last_two_big_hltvs.append(hltv_file[0])
                    if len(last_two_big_hltvs) >= 2:
                        break

            if len(last_two_big_hltvs) < 2:
                return None

            hltv_to_zip1 = last_two_big_hltvs[1]
            hltv_to_zip2 = last_two_big_hltvs[0]

            # Download HLTV files asynchronously
            for hltv_file in [hltv_to_zip1, hltv_to_zip2]:
                async with aiofiles.open(str(hltv_file), mode='wb') as f:
                    try:
                        async with ftp_client.download_stream(hltv_file) as stream:
                            data = await stream.read()
                            await f.write(data)
                    except aioftp.StatusCodeError as e:
                        if '226' in str(e):  # Transfer complete
                            logging.info(f"Successfully downloaded {hltv_file}")
                        else:
                            raise

            # Create zip file
            formatted_date = pickup_date.replace("/", "")
            output_filename = f"{pickup_map}-{formatted_date}.zip"
            
            # Zip files asynchronously
            await asyncio.to_thread(
                lambda: zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED).write(str(hltv_to_zip1))
            )
            await asyncio.to_thread(
                lambda: zipfile.ZipFile(output_filename, 'a', zipfile.ZIP_DEFLATED).write(str(hltv_to_zip2))
            )

            # Clean up files asynchronously
            await asyncio.to_thread(os.remove, str(hltv_to_zip1))
            await asyncio.to_thread(os.remove, str(hltv_to_zip2))

            return output_filename
    except Exception as e:
        logging.warning(traceback.format_exc())
        logging.warning(f"Error in HLTV handling: {e}")
        return None

@client.event
async def on_ready():
    global GLOBAL_LOCK
    logging.info("on_ready!")
    await load_extensions()
    # Remake the global lock to try to get it compatible with the bot's event loop
    # TODO: I don't fully understand why or if this helps exactly.
    if GLOBAL_LOCK is None:
        await setup_global_lock()


@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def search(ctx, searchkey):
    """
    Allow users with "rater" role to search for a player's ELO

    Example usage: "!search kix" in the #tfc-ratings channel
    ctx: Discord context object
    searchkey: string to search for in list of players
    """
    global GLOBAL_LOCK
    if GLOBAL_LOCK is None:
        await setup_global_lock()
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

            if len(searchList) == 0:
                await ctx.send("No results with that search string")

            for i in searchList:
                player_id = None
                for j in list(ELOpop):
                    if i == ELOpop[j][0]:
                        player_id = j
                # really stupid hack incoming to handle people who have never actually played a game
                if (
                    ELOpop[player_id][PLAYER_MAP_WIN_INDEX]
                    + ELOpop[player_id][PLAYER_MAP_LOSS_INDEX]
                    + ELOpop[player_id][PLAYER_MAP_DRAW_INDEX]
                ) == 0:
                    await ctx.send(
                        f"Player has no games reported yet - ELO is {ELOpop[player_id][PLAYER_MAP_CURRENT_ELO_INDEX]}"
                    )
                    continue
                user = await client.fetch_user(player_id)
                file, embed = await generate_elo_chart(user)
                if file is None:
                    await ctx.send(embed=embed)
                else:
                    await ctx.send(embed=embed, file=file)


# Allow all players to toggle their rank being private or hidden
# Example: !private
@client.command(pass_context=True)
async def private(ctx):
    global ELOpop
    global GLOBAL_LOCK
    if GLOBAL_LOCK is None:
        await setup_global_lock()
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


"""@client.command(pass_context=True)
async def load_player_database(ctx):
    global ELOpop

    async with GLOBAL_LOCK:
        with open("ELOpop.json") as f:
            ELOpop = json.load(f)

        db = mysql.connector.connect(
            host=logins["mysql"]["host"],
            user=logins["mysql"]["user"],
            passwd=logins["mysql"]["passwd"],
            database=logins["mysql"]["database"],
        )
        mycursor = db.cursor()
        columns = "discord_id, created_at, updated_at, deleted_at, player_name, current_elo, visual_rank_override, pug_wins, pug_losses, pug_draws, dm_wins, dm_losses, achievements, dunce, steam_id"
        placeholders = ", ".join(["%s"] * 15)

        sql = "INSERT INTO %s ( %s ) VALUES ( %s )" % (
            "matches",
            columns,
            placeholders,
        )
        logging.info(sql)
        logging.info(list(current_game.values()))
        player_rows = []
        current_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        for player in ELOpop:
            current_row = [player, current_timestamp, current_timestamp, None,
                            ELOpop[player]]
        cursor.execute(sql, list(current_game.values()))"""


@client.command(pass_context=True, aliases=["leaderboard"])
async def top15(ctx):
    """ "
    Show the list of top, non-private players in the discord

    Example usage: "!top15"
    ctx: Discord context object
    """
    await ctx.send("https://tfpugs.online/leaderboard")


# Toggle the "dunce" on a player (for being naughty) at admin discretion
# Example: !dunce @MILOS chopping
@client.command(pass_context=True)
@commands.has_role(v["admin"])
async def dunce(ctx, player: discord.Member, reason=None):
    global PLAYER_MAP_DUNCE_FLAG_INDEX
    global GLOBAL_LOCK
    if GLOBAL_LOCK is None:
        await setup_global_lock()
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
    global blueTeam
    global redTeam
    global winner
    global oMsg
    global map_choice_1
    global map_choice_2
    global map_choice_3
    global map_choice_4
    global map_choice_5
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
    global ready
    global inVote
    global vnoELO
    global eligiblePlayers
    global reVote
    global server_vote
    global mapVote
    global pickCount
    global msg
    global pTotalPlayers
    global server_vote_message_view
    global map_vote_message_view
    global map_vote_timer
    global server_vote_timer

    cap1 = None
    cap1Name = None
    cap2 = None
    cap2Name = None
    capList = []
    blueTeam = []
    ready = []
    redTeam = []
    winner = None
    vnoELO = 0
    map_choice_1 = None
    map_choice_2 = None
    map_choice_3 = None
    map_choice_4 = None
    map_choice_5 = None
    loveMaps = []
    hateMaps = []
    mapVotes = {}
    alreadyVoted = []
    pMsg = None
    mapSelected = []
    oMsg = None
    winningIP = "None"
    votePhase = 0
    inVote = 0
    eligiblePlayers = []
    reVote = 0
    captMode = 0
    vMsg = None
    server_vote = 0
    mapVote = 0
    pickCount = 0
    msg = None
    pTotalPlayers = []
    if server_vote_message_view is not None:
        server_vote_message_view.stop()
    if map_vote_message_view is not None:
        map_vote_message_view.stop()
    if map_vote_timer.is_running():
        map_vote_timer.cancel()
    if server_vote_timer.is_running():
        server_vote_timer.cancel()


# Populates a list of players whom have voted for a particular map
def mapVoteOutput(mapChoice):
    global mapVotes
    whoVoted = []
    for i in mapVotes[mapChoice]:
        # whoVoted.append(ELOpop[i][0])
        whoVoted.append(i)
    numVotes = len(whoVoted)
    if SHOW_MAP_VOTE_COUNTS == False:
        return ""
    if numVotes == 0:
        return "0 votes"

    whoVoted = "**" + ", ".join(whoVoted) + "**"
    if numVotes == 1:
        return "1 vote (%s)" % whoVoted
    else:
        return "%d votes (%s)" % (numVotes, whoVoted)
    

def server_vote_output(mapChoice):
    global mapVotes
    whoVoted = []
    for i in mapVotes[mapChoice]:
        # whoVoted.append(ELOpop[i][0])
        whoVoted.append(i)
    numVotes = len(whoVoted)

    if numVotes == 0:
        return "0 votes"

    whoVoted = "**" + ", ".join(whoVoted) + "**"
    if numVotes == 1:
        return "1 vote (%s)" % whoVoted
    else:
        return "%d votes (%s)" % (numVotes, whoVoted)


@tasks.loop(minutes=30)
async def idle_cancel():
    global last_add_timestamp
    global last_add_context
    global pickupActive
    global playersAdded
    global inVote

    if len(playersAdded) >= 1 and inVote == 0:
        # check if 2 hours since last add
        last_add_time_diff = (
            datetime.datetime.utcnow() - last_add_timestamp
        ).total_seconds()
        logging.info("last add was %d minutes ago" % (last_add_time_diff / 60))

        if last_add_time_diff > (2 * 60 * 60):
            logging.info("stopping pickup for being idle for 2 hours")

            await last_add_context.send(
                "Pickup idle for more than two hours, canceling. Durden was too slow"
            )
            cancelImpl()


# TODO: Vote timer loop that shows amount of time left, calls a separate function via after_loop at the end that checks if the length of players_abstained is > 2 and if it does it requeues and kicks the non-voters
@tasks.loop(seconds=1, count=SERVER_VOTE_TIME_LIMIT)
async def server_vote_timer(vote_message):
    global inVote
    global server_vote

    # Double check if we are in a map-vote
    if inVote == 0:
        logging.info("Bailing out of vote timer because we aren't in a vote anymore")
        server_vote_timer.cancel()
        return
    if vote_message is None:
        # TODO: Figure out _when_ this is happening, but vMsg is None AFTER a pickup started. We shouldn't even be here if this is the case!
        logging.info(
            "The vote message global was none, check why we are in the loop here"
        )
        server_vote_timer.cancel()
        return
    time_remaining = f"{SERVER_VOTE_TIME_LIMIT - server_vote_timer.current_loop}"
    vote_embed, progress_bar = generate_server_vote_embed(time_remaining)
    vote_message = await vote_message.edit(embed=vote_embed)


@tasks.loop(seconds=1, count=MAP_VOTE_TIME_LIMIT)
async def map_vote_timer(vote_message):
    global inVote
    global server_vote

    # Double check if we are in a map-vote
    if inVote == 0:
        logging.info("Bailing out of vote timer because we aren't in a vote anymore")
        map_vote_timer.cancel()
        return
    if vote_message is None:
        # TODO: Figure out _when_ this is happening, but vMsg is None AFTER a pickup started. We shouldn't even be here if this is the case!
        logging.info(
            "The vote message global was none, check why we are in the loop here"
        )
        map_vote_timer.cancel()
        return

    time_remaining = f"{MAP_VOTE_TIME_LIMIT - map_vote_timer.current_loop}"
    vote_embed, progress_bar = generate_map_vote_embed(reVote, time_remaining)
    vote_message = await vote_message.edit(embed=vote_embed)


@server_vote_timer.after_loop
async def handle_slow_voters():
    global players_abstained_discord_id

    if server_vote_timer.is_being_cancelled():
        return

    logging.info(f"Kicking idle users: {players_abstained_discord_id}")
    channel = await client.fetch_channel(v["pID"])
    kicked_players_pretty = []
    for player in players_abstained_discord_id:
        current_user = await client.fetch_user(player)
        kicked_players_pretty.append(current_user.display_name)
    await channel.send(
        f"Kicked the following players who didn't vote in time - {kicked_players_pretty}"
    )
    await requeue(channel, False)
    await removePlayerImpl(channel, players_abstained_discord_id)


@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def timeout(
    ctx,
    user: discord.Member,
    input_duration: typing.Optional[str] = None,
    reason=None,
):
    adminChannel = await client.fetch_channel(836999458431434792)
    if input_duration is None and reason is None:
        await ctx.send("User must be given a reason for timeout..")
        return
    elif input_duration is not None and reason is None:
        # User didn't put a length for the timeout
        reason = input_duration
        duration = datetime.timedelta(seconds=0, minutes=0, hours=0, days=1)
        print(reason)
    else:
        digits = []
        for char in input_duration:
            if char.isdigit():
                digits.append(char)
        converted_duration = int("".join(digits))
        logging.info(f"Input Duration: {input_duration}")
        logging.info(f"Converted Duration: {converted_duration}")
        if "m" in input_duration.lower():
            duration = datetime.timedelta(
                seconds=0, minutes=int(converted_duration), hours=0, days=0
            )
        elif "s" in input_duration.lower():
            duration = datetime.timedelta(
                seconds=int(converted_duration), minutes=0, hours=0, days=0
            )
        elif "h" in input_duration.lower():
            duration = datetime.timedelta(
                seconds=0, minutes=0, hours=int(converted_duration), days=0
            )
        elif "d" in input_duration.lower():
            duration = datetime.timedelta(
                seconds=0, minutes=0, hours=0, days=int(converted_duration)
            )
        else:
            await ctx.send(
                "Incorrect duration value set. Use <numbervalue>[d,h,m,s] or set no number for 1 day."
            )
            return
    await user.timeout(duration, reason=reason)
    await ctx.send(f"Successfully timed out {user.name} for {duration}")
    await user.send(f"You have been timed out for {duration} for {reason}")
    await adminChannel.send(
        f"**{user.display_name}** has been timed out by **{ctx.author.display_name}** for **{reason}** for {duration}"
    )


# use_voice_activation
@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def forcePTT(ctx, user: discord.Member, *, reason=None):
    if reason is None:
        await ctx.send("User must be given a reason")
    else:
        adminChannel = await client.fetch_channel(836999458431434792)
        channels = [
            836633744902586378,
            836633820849373184,
            840065112484085771,
            840065140489060363,
        ]
        for id in channels:
            vchannel = await client.fetch_channel(id)
            perms = vchannel.overwrites_for(user)
            perms.use_voice_activation = False
            # await vchannel.set_permissions(user, use_voice_activation=not perms.use_voice_activation)
            await vchannel.set_permissions(user, overwrite=perms)
        await ctx.send(f"Successfully set {user.name}'s permission to PTT only")
        await user.send(f"You have been put on PTT for {reason}")
        await adminChannel.send(
            f"**{user.display_name}** has been forced to PPT by **{ctx.author.display_name}** for **{reason}**"
        )


# Selects maps from two different json files.  options 1/2 are from classic_maps.json and option 3/4 is from spring_2024_maps.json
def PickMaps():
    global map_choice_1
    global map_choice_2
    global map_choice_3
    global map_choice_4
    global map_choice_5
    global loveMaps
    global hateMaps
    global mapVotes
    global alreadyVoted
    global votePhase
    global lastFive
    with open(MAIN_MAPS_FILE) as f:
        mapList = json.load(f)

    mapVotes = {}
    alreadyVoted = []
    mapPick = []
    # Seed lastFive from the last 5 pickups played so that this value is never empty
    with open("pastten.json") as f:
        past_ten = json.load(f)
        logging.info(past_ten)
        past_ten_keys_list = list(past_ten.keys())
        past_ten_keys_list.reverse()
        for match in past_ten_keys_list:
            if len(lastFive) >= 5:
                break
            map = past_ten[match][PAST_TEN_MAP_INDEX]
            lastFive.append(map)

    for i in list(mapList):
        if i not in mapSelected:
            if (i not in lastFive) and (i not in hateMaps):
                mapPick.append(i)
    mapPick2 = []
    with open(SECONDARY_MAPS_FILE) as f:
        mapList = json.load(f)

    for i in list(mapList):
        if i not in mapSelected:
            if (i not in lastFive) and (i not in hateMaps):
                mapPick2.append(i)

    map_choice_1 = random.choice(mapPick)
    while map_choice_1 in mapPick:
        mapPick.remove(map_choice_1)
    mapVotes[map_choice_1] = []
    mapSelected.append(map_choice_1)
    map_choice_2 = random.choice(mapPick)
    while map_choice_2 in mapPick:
        mapPick.remove(map_choice_2)
    mapVotes[map_choice_2] = []
    mapSelected.append(map_choice_2)
    map_choice_3 = random.choice(mapPick2)
    while map_choice_3 in mapPick2:
        mapPick2.remove(map_choice_3)
    mapVotes[map_choice_3] = []
    mapSelected.append(map_choice_3)
    map_choice_4 = random.choice(mapPick2)
    while map_choice_4 in mapPick2:
        mapPick2.remove(map_choice_4)
    mapVotes[map_choice_4] = []
    mapSelected.append(map_choice_4)
    mapVotes[map_choice_5] = []

    logging.info(f"Map Lists: {mapPick} {mapPick2}")
    logging.info(f"Maps Selected: {mapSelected}")
    logging.info(f"Love Maps: {loveMaps}")
    logging.info(f"Hate Maps: {hateMaps}")
    logging.info(f"Last Five: {lastFive}")


# function for testing visualizing map choices without needing a full game
# !pick_maps_test
@client.command(pass_context=True, aliases=["pmtest"])
@commands.has_role(v["admin"])
async def pick_maps_test(ctx):
    PickMaps()


# TODO: Add steam_id registation for players
@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def register_steamid(ctx, player: discord.Member, steam_id):
    print("foo")


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
    global GLOBAL_LOCK
    if GLOBAL_LOCK is None:
        await setup_global_lock()
    async with GLOBAL_LOCK:
        channel = await client.fetch_channel(v["pID"])
        if channel.name == v["pc"]:
            global vMsg
            await vMsg.reply("Click the link above to go the current vote!")
            # await channel.send(vMsg)


# Sets up voting and manages the voting process
async def voteSetup(ctx):
    global map_choice_1
    global map_choice_2
    global map_choice_3
    global map_choice_4
    global map_choice_5
    global mapVotes
    global server_vote
    global reVote
    global alreadyVoted
    global vMsg
    global votable
    global playersAbstained
    global players_abstained_discord_id
    global eligiblePlayers
    global server_vote_message_view
    global map_vote_message_view

    with open("ELOpop.json") as f:
        ELOpop = json.load(f)

    alreadyVoted = []
    mapVotes = {}
    playersAbstained = []
    players_abstained_discord_id = []
    for i in eligiblePlayers:
        if i not in alreadyVoted:
            playersAbstained.append(ELOpop[i][0])
            players_abstained_discord_id.append(i)
    PickMaps()

    with open(MAIN_MAPS_FILE) as f:
        mapList = json.load(f)
    with open(SECONDARY_MAPS_FILE) as f:
        mapList2 = json.load(f)

    map_vote_timer.cancel()
    server_vote_timer.cancel()

    if server_vote == 1:
        map_choice_1 = "Central - Dallas"
        mapVotes[map_choice_1] = []
        map_choice_2 = "South East - Miami"
        mapVotes[map_choice_2] = []
        map_choice_3 = "East2 - New York City"
        mapVotes[map_choice_3] = []
        vote_embed, progress_bar = generate_server_vote_embed()
        server_vote_message_view = ServerVoteView()
        vMsg = await ctx.send(
            embed=vote_embed, view=server_vote_message_view, file=progress_bar
        )
        if not server_vote_timer.is_running():
            server_vote_timer.start(vMsg)
    elif server_vote == 0:
        vote_image_embed_1 = discord.Embed(
            url="https://tfpugs.online/", title="Vote up and make sure you hydrate!"
        )
        vote_image_embed_1.set_image(url=mapList[map_choice_1]["image_url"])
        vote_image_embed_2 = discord.Embed(
            url="https://tfpugs.online/", title="Vote up and make sure you hydrate!"
        )
        vote_image_embed_2.set_image(url=mapList[map_choice_2]["image_url"])
        vote_image_embed_3 = discord.Embed(
            url="https://tfpugs.online/", title="Vote up and make sure you hydrate!"
        )
        vote_image_embed_3.set_image(url=mapList2[map_choice_3]["image_url"])
        vote_image_embed_4 = discord.Embed(
            url="https://tfpugs.online/", title="Vote up and make sure you hydrate!"
        )
        vote_image_embed_4.set_image(url=mapList2[map_choice_4]["image_url"])
        vote_image_embed_5 = discord.Embed(
            url="https://tfpugs.online/", title="Vote up and make sure you hydrate!"
        )
        vote_image_embed_5.set_image(url=mapList2[map_choice_4]["image_url"])
        vote_embed, progress_bar = generate_map_vote_embed(reVote)
        map_vote_message_view = MapVoteView()
        await ctx.send(
            embeds=[
                vote_image_embed_1,
                vote_image_embed_2,
                vote_image_embed_3,
                vote_image_embed_4,
                vote_image_embed_5,
            ]
        )
        vMsg = await ctx.send(
            embed=vote_embed, view=map_vote_message_view, file=progress_bar
        )
        tag_list = []
        for i in eligiblePlayers:
            tag_list.append(f"<@{i}> ")
        tag_msg = "".join(tag_list)
        await ctx.send(tag_msg)
        if not map_vote_timer.is_running():
            map_vote_timer.start(vMsg)
    votable = 1
    logging.info("Starting vote timer NOW")


@client.command(pass_context=True)
@commands.has_role(v["admin"])
async def addach(ctx, key, value):
    global GLOBAL_LOCK
    if GLOBAL_LOCK is None:
        await setup_global_lock()
    async with GLOBAL_LOCK:
        with open("emotes.json") as f:
            e = json.load(f)

        e[key] = value

        with open("emotes.json", "w") as cd:
            json.dump(e, cd, indent=4)
        await ctx.send("value has been added to the list of achievements")


@client.command(pass_context=True)
@commands.has_role(v["admin"])
async def ach(ctx, player: discord.Member, ach):
    global GLOBAL_LOCK
    if GLOBAL_LOCK is None:
        await setup_global_lock()
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


@client.command(pass_context=True)
@commands.has_role(v["admin"])
async def sync_players(ctx):
    with open("ELOpop.json") as f:
        ELOpop = json.load(f)
    
    db = mysql.connector.connect(
        host=logins["mysql"]["host"],
        user=logins["mysql"]["user"],
        passwd=logins["mysql"]["passwd"],
        database=logins["mysql"]["database"],
        autocommit=True,
    )

    columns = "id, discord_id, created_at, updated_at, deleted_at, player_name, current_elo, visual_rank_override, pug_wins, pug_losses, pug_draws, dm_wins, dm_losses, achievements, dunce, steam_id"
    placeholders = ", ".join(["%s"] * 16)

    players = []

    for index, player in enumerate(ELOpop):
        row = (index+1,player,'2024-11-11 20:00:00','2024-11-11 20:00:00',None,ELOpop[player][PLAYER_MAP_VISUAL_NAME_INDEX],ELOpop[player][PLAYER_MAP_CURRENT_ELO_INDEX],ELOpop[player][PLAYER_MAP_VISUAL_RANK_INDEX],ELOpop[player][PLAYER_MAP_WIN_INDEX],ELOpop[player][PLAYER_MAP_LOSS_INDEX],ELOpop[player][PLAYER_MAP_DRAW_INDEX],0,0,';'.join(ELOpop[player][PLAYER_MAP_ACHIEVEMENT_INDEX]),None,None)
        players.append(row)

    sql = "INSERT INTO %s ( %s ) VALUES ( %s )" % (
        "players",
        columns,
        placeholders,
    )

    cursor = db.cursor()
    cursor.execute("TRUNCATE TABLE players")
    cursor.executemany(sql, players)


# Utility function for showing the pickup
async def showPickup(ctx, showReact=False, mapVoteFirstPickupStarted=False):
    global playersAdded
    global capList
    global oMsg
    global ready
    global PLAYER_MAP_DUNCE_FLAG_INDEX
    global PLAYER_MAP_VISUAL_NAME_INDEX
    global PLAYER_MAP_VISUAL_RANK_INDEX
    global inVote
    global MAP_VOTE_FIRST
    with open("ELOpop.json") as f:
        ELOpop = json.load(f)

    isMapVoteFirstPickupStarted = False
    if (inVote == 1 or mapVoteFirstPickupStarted) and MAP_VOTE_FIRST is True:
        isMapVoteFirstPickupStarted = True

    msgList = []
    for i in playersAdded:
        achList = ELOpop[i][7]
        if "norank" in ELOpop[i][3]:
            visualRank = ELOpop[i][3]
        else:
            visualRank = getRank(i)  # ELOpop[i][PLAYER_MAP_VISUAL_RANK_INDEX]
            # await ctx.send(f"{ELOpop[i][3]}")
        if not SHOW_VISUAL_RANKS:
            visualRank = ""

        if (
            ELOpop[i][PLAYER_MAP_DUNCE_FLAG_INDEX] is not None
        ):  # Is player a naughty dunce?
            ach = (
                v["dunce"]
                + "- Dunce cap for: "
                + ELOpop[i][PLAYER_MAP_DUNCE_FLAG_INDEX]
            )  # Achievements get wiped and replaced with the dunce cap
            if SHOW_VISUAL_RANKS:
                visualRank = getRank(
                    i
                )  # Always show the rank of the dunce as a punishment
            else:
                visualRank = ""
            win_emblem = ""  # Dunces don't get an emblem to show off
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
    msg = "".join(msgList)

    if len(playersAdded) >= 8:
        # Create the ready message
        readyList = []
        for i in ready:
            readyList.append(f"{ELOpop[i][0]}\n")
        readyMsg = "".join(readyList)

        # Create the emebd
        embed = None
        if isMapVoteFirstPickupStarted is True:
            embed = discord.Embed(title="Pickup Voting Phase!")
        else:
            embed = discord.Embed(title=f"Pickup Has 8 or more Players - {len(playersAdded)} Queued")

        if len(playersAdded) > 0:
            embed.description = msg
        elif len(playersAdded) == 0:
            embed.description = "Nobody..."

        oMsg = await ctx.send(embed=embed)

        if showReact is True:
            await oMsg.add_reaction("👍")
        notiflist = []
        for i in playersAdded[0:8]:
            notiflist.append(f"<@{i}> ")
        if showReact is True:
            notiflist.append(
                "... React with 👍 when ready to teams if no runner available."
            )
        msg = "".join(notiflist)
        await ctx.send(msg)

    elif len(playersAdded) < 8:
        oMsg = None
        embed = discord.Embed(title=f"Players Added - {len(playersAdded)} Queued")
        if len(playersAdded) > 0:
            embed.description = msg
        elif len(playersAdded) == 0:
            embed.description = "Nobody..."
        await ctx.send(embed=embed)

    if inVote == 1 and vMsg is not None:
        await vMsg.reply("Click the link above to go the current vote!")


async def pastGames(ctx):
    with open("pastten.json") as f:
        past_ten_matches = json.load(f)
    msgList = []
    for i in past_ten_matches:
        match_outcome_string = "Team " + str(
            past_ten_matches[i][PAST_TEN_MATCH_OUTCOME_INDEX]
        )
        msgList.append(
            f"{i:.<8}|{match_outcome_string:.^10}|{past_ten_matches[i][PAST_TEN_MAP_INDEX]:.>25}\n"
        )
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

    if type(ctx) is TextChannel:
        emoji_comparison = ctx.guild.emojis
    else:
        emoji_comparison = ctx.message.guild.emojis

    if ELOpop[discord_id][PLAYER_MAP_WIN_INDEX] < 10:
        return get(emoji_comparison, name="we0")  # Civilian
    elif ELOpop[discord_id][PLAYER_MAP_WIN_INDEX] < 25:
        return get(emoji_comparison, name="we1")  # Scout
    elif ELOpop[discord_id][PLAYER_MAP_WIN_INDEX] < 50:
        return get(emoji_comparison, name="we2")  # Pyro
    elif ELOpop[discord_id][PLAYER_MAP_WIN_INDEX] < 75:
        return get(emoji_comparison, name="we3")  # Medic
    elif ELOpop[discord_id][PLAYER_MAP_WIN_INDEX] < 100:
        return get(emoji_comparison, name="we4")  # Spy
    elif ELOpop[discord_id][PLAYER_MAP_WIN_INDEX] < 250:
        return get(emoji_comparison, name="we5")  # Sniper
    elif ELOpop[discord_id][PLAYER_MAP_WIN_INDEX] < 500:
        return get(emoji_comparison, name="we6")  # Engineer
    elif ELOpop[discord_id][PLAYER_MAP_WIN_INDEX] < 750:
        return get(emoji_comparison, name="we7")  # Soldier
    elif ELOpop[discord_id][PLAYER_MAP_WIN_INDEX] < 1000:
        return get(emoji_comparison, name="we8")  # Demoman
    else:
        return get(emoji_comparison, name="we9")  # HWGuy


# Utility function for retrieving the cosmetic ranking number based on ELO for a player ID
def getRank(ID):
    with open("ELOpop.json") as f:
        ELOpop = json.load(f)

    # TODO: Put this in variables.json
    if (
        ELOpop[ID][PLAYER_MAP_WIN_INDEX]
        + ELOpop[ID][PLAYER_MAP_LOSS_INDEX]
        + ELOpop[ID][PLAYER_MAP_DRAW_INDEX]
    ) < 10:
        return "<:questionMark:972369805359337532>"

    if ELOpop[ID][1] < RANK_BOUNDARIES_LIST[0]:  # 1
        return v["rank1"]
    elif ELOpop[ID][1] < RANK_BOUNDARIES_LIST[1]:  # 2
        return v["rank2"]
    elif ELOpop[ID][1] < RANK_BOUNDARIES_LIST[2]:  # 3
        return v["rank3"]
    elif ELOpop[ID][1] < RANK_BOUNDARIES_LIST[3]:  # 4
        return v["rank4"]
    elif ELOpop[ID][1] < RANK_BOUNDARIES_LIST[4]:  # 5
        return v["rank5"]
    elif ELOpop[ID][1] < RANK_BOUNDARIES_LIST[5]:  # 6
        return v["rank6"]
    elif ELOpop[ID][1] < RANK_BOUNDARIES_LIST[6]:  # 7
        return v["rank7"]
    elif ELOpop[ID][1] < RANK_BOUNDARIES_LIST[7]:  # 8
        return v["rank8"]
    elif ELOpop[ID][1] < RANK_BOUNDARIES_LIST[8]:  # 9
        return v["rank9"]
    elif ELOpop[ID][1] < RANK_BOUNDARIES_LIST[9]:  # 10
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
    global GLOBAL_LOCK
    if GLOBAL_LOCK is None:
        await setup_global_lock()
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
    global GLOBAL_LOCK
    if GLOBAL_LOCK is None:
        await setup_global_lock()
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
            ELOpop[playerID][PLAYER_MAP_CURRENT_ELO_INDEX] = ELO
            await ctx.send(
                f"Player {ELOpop[playerID][PLAYER_MAP_VISUAL_NAME_INDEX]} updated to ELO {ELOpop[playerID][PLAYER_MAP_CURRENT_ELO_INDEX]}"
            )

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
    global GLOBAL_LOCK
    if GLOBAL_LOCK is None:
        await setup_global_lock()
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

                await ctx.send(
                    embed=teamsDisplay(blueTeam, redTeam, team1prob, team2prob)
                )
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
                await ctx.send(
                    embed=teamsDisplay(blueTeam, redTeam, team1prob, team2prob)
                )


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
        current_timestamp = datetime.datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        current_game = {
            "match_id": pSerial,
            "created_at": current_timestamp,
            "updated_at": current_timestamp,
            "deleted_at": None,
            "blue_probability": team1prob,
            "blue_rank": blueRank,
            "blue_team": ','.join(blueTeam),
            "red_probability": team2prob,
            "red_rank": redRank,
            "red_team": ','.join(redTeam),
            "map": winningMap,
            "server": winningServer,
            "game_type": "4v4",
            "match_outcome": None,
        }
        # Write to db
        placeholders = ", ".join(["%s"] * len(current_game))
        columns = ", ".join(current_game.keys())
        sql = "INSERT INTO %s ( %s ) VALUES ( %s )" % (
            "matches",
            columns,
            placeholders,
        )
        logging.info(sql)
        logging.info(list(current_game.values()))
        db = mysql.connector.connect(
            host=logins["mysql"]["host"],
            user=logins["mysql"]["user"],
            passwd=logins["mysql"]["passwd"],
            database=logins["mysql"]["database"],
            autocommit=True,
        )
        cursor = db.cursor()
        cursor.execute(sql, list(current_game.values()))


# Utility function for adding a player to the pickup if they aren't already added
def addplayerImpl(playerID, playerDisplayName, cap=None):
    global playersAdded
    global capList
    global ELOpop
    global inVote

    # For simplicity, don't let players add if we are map voting first
    # and still in voting stage.
    if MAP_VOTE_FIRST is True:
        if inVote == 1:
            return 2
        
    with open("activePickups.json") as f:
        active_pickups = json.load(f)
    
    for game in active_pickups:
        if playerID in active_pickups[game][2] or playerID in active_pickups[game][5]:
            return 3

    if len(playersAdded) <= 19:
        if playerID not in playersAdded:
            if playerID not in list(
                ELOpop
            ):  # Player is not registered, give them a default rating
                with open("ELOpop.json") as f:
                    ELOpop = json.load(f)
                ELOpop[playerID] = [
                    playerDisplayName,
                    400,
                    [],
                    "<:questionMark:972369805359337532>",
                    0,
                    0,
                    0,
                    [],
                    None,
                    None,
                    0,
                    0,
                ]
                # Write the ELO out
                with open("ELOpop.json", "w") as cd:
                    json.dump(ELOpop, cd, indent=4)

            if cap == "cap" and len(capList) < 2:
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
    global last_add_timestamp
    global last_add_context
    global GLOBAL_LOCK
    if GLOBAL_LOCK is None:
        await setup_global_lock()

    async with GLOBAL_LOCK:
        try:
            if ctx.channel.name == v["pc"] or (ctx.channel.id == DEV_TESTING_CHANNEL):
                playerID = str(ctx.author.id)
                playerDisplayName = ctx.author.display_name

                retVal = addplayerImpl(playerID, playerDisplayName, cap)
                if retVal == 3:
                    await ctx.send(f"{playerDisplayName} is currently in an unreported pickup - wait for report before adding!")
                if retVal == 2:
                    await ctx.send("Currently in a mapvote for a pickup, please wait for that to finish before adding!")
                if retVal == 1:  # Already added
                    await ctx.author.send(
                        "you are already added to this pickup.."
                    )  # Send PM to player
                if retVal == 0:  # Successfully added
                    last_add_timestamp = datetime.datetime.utcnow()
                    if not idle_cancel.is_running():
                        idle_cancel.start()
                        last_add_context = ctx
                    await showPickup(ctx)
        except Exception as e:
            logging.error(e)
            await ctx.send(e)


@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def addplayer(ctx, player: discord.Member):
    global GLOBAL_LOCK
    if GLOBAL_LOCK is None:
        await setup_global_lock()
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
    global GLOBAL_LOCK
    if GLOBAL_LOCK is None:
        await setup_global_lock()
    async with GLOBAL_LOCK:
        if (ctx.channel.name == v["pc"]) or (ctx.channel.id == DEV_TESTING_CHANNEL):
            cancelImpl()  # Clear out any existing pickup
            addplayerImpl("704204162958753892", "sandro702", None)
            addplayerImpl("303845825476558859", "dougtck", None)
            addplayerImpl("270636499190546432", "CheeseFromGPT", None)
            addplayerImpl("291754504158838784", "AUTHENTIC", None)
            addplayerImpl("194276343540613121", "climax", None)
            addplayerImpl("596225454721990676", "botch", None)
            addplayerImpl("173619058657198082", "Moreno", None)
            addplayerImpl("151144734579097601", "EDEdDNEdDYFaN", None)
            await showPickup(ctx)


# Convenience command for testing bot behavior with 8 people added
# Example: !test8
@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def test8(ctx):
    global GLOBAL_LOCK
    if GLOBAL_LOCK is None:
        await setup_global_lock()
    async with GLOBAL_LOCK:
        if (ctx.channel.name == v["pc"]) or (ctx.channel.id == DEV_TESTING_CHANNEL):
            cancelImpl()  # Clear out any existing pickup
            addplayerImpl("704204162958753892", "sandro702", None)
            addplayerImpl("303845825476558859", "dougtck", None)
            addplayerImpl("270636499190546432", "CheeseFromGPT", None)
            addplayerImpl("291754504158838784", "AUTHENTIC", None)
            addplayerImpl("194276343540613121", "climax", None)
            addplayerImpl("596225454721990676", "botch", None)
            addplayerImpl("173619058657198082", "Moreno", None)
            addplayerImpl("151144734579097601", "EDEdDNEdDYFaN", None)
            await showPickup(ctx)


# Adding player: 704204162958753892, sandro702
# Adding player: 270636499190546432, CheeseFromGPT
# Adding player: 291754504158838784, AUTHENTIC
# Adding player: 194276343540613121, climax
# Adding player: 596225454721990676, botch
# Adding player: 173619058657198082, Moreno
# Adding player: 311769927432404994, Nemsy
# Adding player: 303845825476558859, dougtck


# Utility function for showing the pickup
async def removePlayerImpl(ctx, player_id_list):
    global playersAdded
    global capList
    global MAP_VOTE_FIRST
    global inVote

    # For simplicity, don't let players remove if we are map voting first
    # and still in voting stage.
    if MAP_VOTE_FIRST is True and inVote == 1:
        return
    playersAdded = [player for player in playersAdded if player not in player_id_list]
    capList = [player for player in capList if player not in player_id_list]
    await showPickup(ctx)
    return


@client.command(pass_context=True, aliases=["-"])
async def remove(ctx):
    global GLOBAL_LOCK
    if GLOBAL_LOCK is None:
        await setup_global_lock()
    async with GLOBAL_LOCK:
        if ctx.channel.name == v["pc"]:
            playerID = str(ctx.author.id)
            await removePlayerImpl(ctx, [playerID])


@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def kick(ctx, player: discord.Member):
    global GLOBAL_LOCK
    if GLOBAL_LOCK is None:
        await setup_global_lock()
    async with GLOBAL_LOCK:
        if ctx.channel.name == v["pc"]:
            playerID = str(player.id)
            await removePlayerImpl(ctx, [playerID])


@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def noELO(ctx):
    global vnoELO
    global GLOBAL_LOCK
    if GLOBAL_LOCK is None:
        await setup_global_lock()
    async with GLOBAL_LOCK:
        logging.info(vnoELO)
        if vnoELO == 0:
            vnoELO = 1
            await ctx.send("ELO has been turned **OFF** for this game.")
        elif vnoELO == 1:
            vnoELO = 0
            await ctx.send("ELO has been turned **ON** for this game.")


# Start the pickup assuming enough players have been added.  This will kick off server and map voting and any other
# flow needed to begin the pickup.
# Example: !teams
@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def teams(ctx, playerCount=4):
    global GLOBAL_LOCK
    if GLOBAL_LOCK is None:
        await setup_global_lock()
    async with GLOBAL_LOCK:
        dev_channel = await client.fetch_channel(DEV_TESTING_CHANNEL)
        if (ctx.channel.name == v["pc"]) or (ctx.channel.id == DEV_TESTING_CHANNEL):
            global playersAdded
            global capList
            global inVote
            global blueTeam
            global redTeam
            global eligiblePlayers
            global oMsg
            global captMode
            global server_vote
            global rankedOrder
            global ready
            # global pastTeams
            ready = []
            oMsg = None
            if len(playersAdded) >= int(playerCount * 2):
                if inVote == 0:
                    if len(capList) < 2:
                        playerCount = int(playerCount)
                        if len(playersAdded) == playerCount:
                            eligiblePlayers = playersAdded.copy()
                        else:
                            eligiblePlayers = playersAdded[0 : playerCount * 2]

                        if MAP_VOTE_FIRST is True:
                            # Prune down the players added
                            playersAdded = playersAdded[0 : playerCount * 2]
                            await showPickup(ctx, False, True)

                        if MAP_VOTE_FIRST is False:
                            with open("ELOpop.json") as f:
                                ELOpop = json.load(f)

                            await generate_teams(playerCount)
                    elif len(capList) >= 2:
                        with open("ELOpop.json") as f:
                            ELOpop = json.load(f)
                        playerCount = int(playerCount)
                        if len(playersAdded) == playerCount:
                            eligiblePlayers = playersAdded.copy()
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
                    server_vote = 1
                    inVote = 1
                    await voteSetup(ctx)
                    if idle_cancel.is_running():
                        idle_cancel.stop()
            else:
                await ctx.send("you dont have enough people for that game size..")


@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def stats(
    ctx, region=None, match_number=None, winning_score=None, losing_score=None
):
    global GLOBAL_LOCK
    if GLOBAL_LOCK is None:
        await setup_global_lock()
    async with GLOBAL_LOCK:
        if not region or region.lower() == "none":
            await ctx.send("Please specify region..")
            return
            
        region = region.lower()
        if region not in ("east", "east2", "eu", "central", "west", "southeast"):
            await ctx.send("Invalid region specified")
            return

        try:
            # Get stats channel
            schannel = await client.fetch_channel(1000847501194174675)

            # Process log files
            pickup_date, pickup_map, log_output, hampalyzer_output, blarghalyzer_fallback = await stat_log_file_handler(region)
            
            # Process HLTV files
            output_zipfile = await hltv_file_handler(region, pickup_date, pickup_map)

            # Get MVP steam ID
            # mvp_steam_id = await get_mvp_steam_id(hampalyzer_output)
            mvp_steam_id = ''

            # Update database
            current_timestamp = datetime.datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            
            async with aiomysql.connect(
                host=logins["mysql"]["host"],
                user=logins["mysql"]["user"],
                password=logins["mysql"]["passwd"],
                db=logins["mysql"]["database"],
                autocommit=True
            ) as conn:
                async with conn.cursor() as cursor:
                    if log_output:
                        update_query = """
                            UPDATE matches 
                            SET winning_score = %s, losing_score = %s, stats_url = %s, mvp = %s, updated_at = %s 
                            WHERE match_id = %s
                        """
                        await cursor.execute(
                            update_query, 
                            (winning_score, losing_score, log_output, mvp_steam_id, current_timestamp, match_number)
                        )

            # Send results
            if output_zipfile:
                if log_output and hampalyzer_output:
                    await schannel.send(
                            file=discord.File(output_zipfile),
                            content=f"**TFCStats:** {log_output}\n**Hampalyzer:** {hampalyzer_output}\n{pickup_map} {pickup_date} {region} {match_number} {winning_score} {losing_score}",
                        )
                elif blarghalyzer_fallback:

                    await schannel.send(
                        file=discord.File(output_zipfile),
                        content=f"**Blarghalyzer:** {blarghalyzer_fallback} {pickup_map} {pickup_date} {region} {match_number} {winning_score} {losing_score}",
                    )
                else:
                    await ctx.send("Could not generate stats URLs")
                await asyncio.to_thread(os.remove, output_zipfile)
            else:
                if log_output and hampalyzer_output:
                    await schannel.send(
                        f"**TFCStats:** {log_output}\n**Hampalyzer:** {hampalyzer_output}\n{pickup_map} {pickup_date} {region} {match_number} {winning_score} {losing_score}"
                    )
                elif blarghalyzer_fallback:
                    await schannel.send(
                        f"**Blarghalyzer:** {blarghalyzer_fallback} {pickup_map} {pickup_date} {region} {match_number} {winning_score} {losing_score}"
                    )
                else:
                    await ctx.send("Could not generate stats URLs")
        except Exception as e:
            logging.error(traceback.format_exc())
            await ctx.send(f"Error processing stats: {str(e)}")


@client.command(pass_context=True)
async def status(ctx):
    global GLOBAL_LOCK
    if GLOBAL_LOCK is None:
        await setup_global_lock()
    async with GLOBAL_LOCK:
        if ctx.channel.name == v["pc"]:
            await showPickup(ctx)


@client.command(aliases=["map"], pass_context=True)
async def tfcmap(ctx, map_name_string):
    global GLOBAL_LOCK
    if GLOBAL_LOCK is None:
        await setup_global_lock()
    async with GLOBAL_LOCK:
        map = map_name_string.lower()
        with urllib.request.urlopen(r"http://mrclan.com/tfcmaps/") as mapIndex:
            response = mapIndex.read().decode("utf-8")
            matches = re.findall('<a href="/tfcmaps/%s.zip' % (map), response, re.I)
            if len(matches) != 0:
                await ctx.send("Found map: http://mrclan.com/tfcmaps/%s.zip" % (map))
            else:
                await ctx.send(f"https://tfcmaps.net/?filterMap={map_name_string}")


@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def startserver(ctx, region: str):
    global GLOBAL_LOCK
    if GLOBAL_LOCK is None:
        await setup_global_lock()
    async with GLOBAL_LOCK:
        boto_region = "us-east-1" if region != 'west' else 'us-west-1'
        boto_client = boto3.client('ec2', region_name=boto_region)
        instance_state = boto_client.describe_instance_status(InstanceIds=[logins[region]["instance_id"]])['InstanceStatuses'][0]['InstanceState']['Name']
        if instance_state == 'running':
            await ctx.send(f"{region} server is already running!")
            return
        boto_client.start_instances(InstanceIds=[logins[region]["instance_id"]])
        await ctx.send(f"Starting {region} server...")
        waiter = boto_client.get_waiter('instance_running')
        waiter.wait(InstanceIds=[logins[region]["instance_id"]]) # TODO: this might not jive with async
        await ctx.send(f"{region} server started!")

@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def sub(ctx, playerone: discord.Member, playertwo: discord.Member, number=None):
    global inVote
    global eligiblePlayers
    global blueTeam
    global redTeam
    global playersAdded
    global MAP_VOTE_FIRST

    global GLOBAL_LOCK
    if GLOBAL_LOCK is None:
        await setup_global_lock()
    async with GLOBAL_LOCK:
        dev_channel = await client.fetch_channel(DEV_TESTING_CHANNEL)
        if (ctx.channel.name == v["pc"]) or (ctx.channel.id == DEV_TESTING_CHANNEL):
            with open("activePickups.json") as f:
                activePickups = json.load(f)
            if number is None:
                if inVote == 0:
                    await ctx.send(
                        "ERROR: Tried calling !sub without a game number outside of voting!"
                    )
                    return
                playeroutid = None
                playerinid = None

                if MAP_VOTE_FIRST is False:
                    eligiblePlayers = []
                    if str(playerone.id) in blueTeam or str(playerone.id) in redTeam:
                        playeroutid = playerone.id
                        playerinid = playertwo.id
                    elif str(playertwo.id) in blueTeam or str(playertwo.id) in redTeam:
                        playeroutid = playertwo.id
                        playerinid = playerone.id
                    logging.info(
                        f"Subbing player {playerinid} for player {playeroutid}"
                    )
                    for i in blueTeam:
                        if i != str(playeroutid):
                            eligiblePlayers.append(i)
                    for i in redTeam:
                        if i != str(playeroutid):
                            eligiblePlayers.append(i)
                    eligiblePlayers.append(str(playerinid))
                else:  # (MAP_VOTE_FIRST is True):
                    # Map voting first, so no teams yet
                    if str(playerone.id) in playersAdded:
                        playeroutid = playerone.id
                        playerinid = playertwo.id
                    elif str(playertwo.id) in playersAdded:
                        playeroutid = playertwo.id
                        playerinid = playerone.id
                    logging.info(
                        f"Subbing player {playerinid} for player {playeroutid}"
                    )
                    playersAddedNew = []
                    playersAddedNew.append(str(playerinid))
                    for i in playersAdded:
                        if i != str(playeroutid):
                            playersAddedNew.append(i)
                    playersAdded = playersAddedNew
                    eligiblePlayers = playersAdded.copy()
                    await showPickup(ctx, False)

                if MAP_VOTE_FIRST is False:
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
                    dev_channel.send(
                        "Outputting top 5 possible games by absolute ELO difference sorted ascending"
                    )
                    for index, item in enumerate(rankedOrder):
                        if index > 4:
                            break
                        blueTeam = rankedOrder[index][0]
                        for j in eligiblePlayers:
                            if j not in blueTeam:
                                redTeam.append(j)
                        blueRank = 0
                        for j in blueTeam:
                            blueRank += int(ELOpop[j][1])
                        blue_diff = abs(blueRank - half)
                        for j in redTeam:
                            redRank += int(ELOpop[j][1])
                        red_diff = abs(redRank - half)

                        # Make blue team the favored team as it allows them to be lenient on defense
                        # if desired/needed for sportsmanship.
                        if redRank > blueRank:
                            logging.info("Swapping team colors so blue is favored")
                            tempTeam = blueTeam
                            tempRank = blueRank
                            blueTeam = redTeam
                            blueRank = redRank
                            redTeam = tempTeam
                            redRank = tempRank

                        logging.info(
                            f"blueTeam: {blueTeam}, diff: {blue_diff}, blueRank: {blueRank}"
                        )
                        logging.info(
                            f"redTeam: {redTeam}, diff {red_diff}, redRank: {redRank}"
                        )

                        team1prob = round(
                            1 / (1 + 10 ** ((redRank - blueRank) / 400)), 2
                        )
                        team2prob = round(
                            1 / (1 + 10 ** ((blueRank - redRank) / 400)), 2
                        )
                        await dev_channel.send(
                            embed=teamsDisplay(
                                blueTeam,
                                redTeam,
                                team1prob,
                                team2prob,
                                blueRank,
                                redRank,
                                True,
                                True,
                            )
                        )
                        redTeam = []
                        redRank = 0
                        totalRank = 0
                    blueTeam = list(rankedOrder[0][0])

                    for j in eligiblePlayers:
                        if j not in blueTeam:
                            redTeam.append(j)
                    blueRank = 0
                    for j in blueTeam:
                        blueRank += int(ELOpop[j][1])
                    blue_diff = abs(blueRank - half)
                    for j in redTeam:
                        redRank += int(ELOpop[j][1])
                    red_diff = abs(redRank - half)

                    # Make blue team the favored team as it allows them to be lenient on defense
                    # if desired/needed for sportsmanship.
                    if redRank > blueRank:
                        logging.info("Swapping team colors so blue is favored")
                        tempTeam = blueTeam
                        tempRank = blueRank
                        blueTeam = redTeam
                        blueRank = redRank
                        redTeam = tempTeam
                        redRank = tempRank

                    team1prob = round(1 / (1 + 10 ** ((redRank - blueRank) / 400)), 2)
                    team2prob = round(1 / (1 + 10 ** ((blueRank - redRank) / 400)), 2)
                    blue_team_info_string = f"blueTeam: {blueTeam}, diff: {blue_diff}, blueRank: {blueRank}, blue_win_probability: {team1prob}"
                    red_team_info_string = f"redTeam: {redTeam}, diff {red_diff}, redRank: {redRank}, red_win_probability {team2prob}"
                    logging.info(blue_team_info_string)
                    logging.info(red_team_info_string)

                    await ctx.send(
                        embed=teamsDisplay(blueTeam, redTeam, team1prob, team2prob)
                    )
            elif number is not None:
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
                dev_channel.send(
                    "Outputting top 5 possible games by absolute ELO difference sorted ascending"
                )
                for index, item in enumerate(rankedOrder):
                    if index > 4:
                        break
                    blueTeam = rankedOrder[index][0]
                    for j in eligiblePlayers:
                        if j not in blueTeam:
                            redTeam.append(j)
                    blueRank = 0
                    for j in blueTeam:
                        blueRank += int(ELOpop[j][1])
                    blue_diff = abs(blueRank - half)
                    for j in redTeam:
                        redRank += int(ELOpop[j][1])
                    red_diff = abs(redRank - half)

                    # Make blue team the favored team as it allows them to be lenient on defense
                    # if desired/needed for sportsmanship.
                    if redRank > blueRank:
                        logging.info("Swapping team colors so blue is favored")
                        tempTeam = blueTeam
                        tempRank = blueRank
                        blueTeam = redTeam
                        blueRank = redRank
                        redTeam = tempTeam
                        redRank = tempRank

                    logging.info(
                        f"blueTeam: {blueTeam}, diff: {blue_diff}, blueRank: {blueRank}"
                    )
                    logging.info(
                        f"redTeam: {redTeam}, diff {red_diff}, redRank: {redRank}"
                    )

                    team1prob = round(1 / (1 + 10 ** ((redRank - blueRank) / 400)), 2)
                    team2prob = round(1 / (1 + 10 ** ((blueRank - redRank) / 400)), 2)
                    await dev_channel.send(
                        embed=teamsDisplay(
                            blueTeam,
                            redTeam,
                            team1prob,
                            team2prob,
                            blueRank,
                            redRank,
                            True,
                            True,
                        )
                    )
                    redTeam = []
                    redRank = 0
                    totalRank = 0
                blueTeam = list(rankedOrder[0][0])

                for j in eligiblePlayers:
                    if j not in blueTeam:
                        redTeam.append(j)
                blueRank = 0
                for j in blueTeam:
                    blueRank += int(ELOpop[j][1])
                blue_diff = abs(blueRank - half)
                for j in redTeam:
                    redRank += int(ELOpop[j][1])
                red_diff = abs(redRank - half)

                # Make blue team the favored team as it allows them to be lenient on defense
                # if desired/needed for sportsmanship.
                if redRank > blueRank:
                    logging.info("Swapping team colors so blue is favored")
                    tempTeam = blueTeam
                    tempRank = blueRank
                    blueTeam = redTeam
                    blueRank = redRank
                    redTeam = tempTeam
                    redRank = tempRank

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
                blue_team_info_string = f"blueTeam: {blueTeam}, diff: {blue_diff}, blueRank: {blueRank}, blue_win_probability: {team1prob}"
                red_team_info_string = f"redTeam: {redTeam}, diff {red_diff}, redRank: {redRank}, red_win_probability {team2prob}"
                logging.info(blue_team_info_string)
                logging.info(red_team_info_string)

                with open("activePickups.json", "w") as cd:
                    json.dump(activePickups, cd, indent=4)
                async with await get_db_pool() as pool:
                    async with pool.acquire() as conn:
                        async with conn.cursor() as cursor:
                            try:
                                current_timestamp = datetime.datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                                blueTeamString = ','.join(blueTeam)
                                redTeamString = ','.join(redTeam)
                                await cursor.execute(
                                    "UPDATE matches SET blue_probability = %s, blue_team = %s, blue_rank = %s, red_probability = %s, red_team = %s, red_rank = %s, updated_at = %s WHERE match_id = %s",
                                    (team1prob, blueTeamString, blueRank, team2prob, redTeamString, redRank, current_timestamp, number)
                                )
                            except Exception as e:
                                await dev_channel.send(f"SQL QUERY ERROR: {e}")
                await ctx.send(
                    embed=teamsDisplay(blueTeam, redTeam, team1prob, team2prob)
                )


@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def draw(ctx, pNumber="None"):
    global ELOpop
    dev_channel = await client.fetch_channel(DEV_TESTING_CHANNEL)

    global GLOBAL_LOCK
    if GLOBAL_LOCK is None:
        await setup_global_lock()
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

            # Prepare player data for bulk insert
            player_elo_data = []
            
            # Process blue team
            for i in blueTeam:
                ELOpop[i][1] += adjustTeam1
                if int(ELOpop[i][1]) < 0:
                    ELOpop[i][1] = 0
                player_elo_data.append((pNumber, ELOpop[i][0], ELOpop[i][1], int(i)))
                ELOpop[i][6] += 1
                if ELOpop[i][3] != "<:norank:1001265843683987487>":
                    newRank(i)

            # Process red team
            for i in redTeam:
                ELOpop[i][1] += adjustTeam2
                if int(ELOpop[i][1]) < 0:
                    ELOpop[i][1] = 0
                player_elo_data.append((pNumber, ELOpop[i][0], ELOpop[i][1], int(i)))
                ELOpop[i][6] += 1
                if ELOpop[i][3] != "<:norank:1001265843683987487>":
                    newRank(i)

            # Perform database operations
            async with await get_db_pool() as pool:
                async with pool.acquire() as conn:
                    async with conn.cursor() as cursor:
                        try:
                            # Bulk insert player ELO data
                            await cursor.executemany(
                                "INSERT INTO player_elo (match_id, player_name, player_elos, discord_id) VALUES (%s, %s, %s, %s)",
                                player_elo_data
                            )
                            
                            # Update match outcome
                            current_timestamp = datetime.datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                            await cursor.execute(
                                "UPDATE matches SET match_outcome = %s, updated_at = %s WHERE match_id = %s",
                                ('0', current_timestamp, pNumber)
                            )
                        except Exception as e:
                            await dev_channel.send(f"SQL QUERY ERROR: {e}")

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
            ]
            del activePickups[pNumber]
            
            with open("activePickups.json", "w") as cd:
                json.dump(activePickups, cd, indent=4)
            with open("ELOpop.json", "w") as cd:
                json.dump(ELOpop, cd, indent=4)
            with open("pastten.json", "w") as cd:
                json.dump(pastTen, cd, indent=4)

            await ctx.send("Match reported.. thank you!")
            await sync_players(ctx)

@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def win(ctx, team, pNumber="None"):
    global ELOpop
    dev_channel = await client.fetch_channel(DEV_TESTING_CHANNEL)
    
    global GLOBAL_LOCK
    if GLOBAL_LOCK is None:
        await setup_global_lock()
    async with GLOBAL_LOCK:
        if ((ctx.channel.name == v["pc"]) or 
            (ctx.channel.name == "tfc-admins") or 
            (ctx.channel.name == "tfc-runners")):
            
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

            if "Bot's Choice" in pMap:
                adjustTeam1 = adjustTeam1 * 2
                adjustTeam2 = adjustTeam2 * 2
                logging.info("giving double ELO")

            # Prepare player data for bulk insert
            player_elo_data = []
            
            # Process blue team
            for i in blueTeam:
                ELOpop[i][1] += adjustTeam1
                if int(ELOpop[i][1]) < 0:
                    ELOpop[i][1] = 0
                player_elo_data.append((pNumber, ELOpop[i][0], ELOpop[i][1], int(i)))
                if team == "1":
                    ELOpop[i][4] += 1
                if team == "2":
                    ELOpop[i][5] += 1
                if ELOpop[i][3] != "<:norank:1001265843683987487>":
                    newRank(i)

            # Process red team
            for i in redTeam:
                ELOpop[i][1] += adjustTeam2
                if int(ELOpop[i][1]) < 0:
                    ELOpop[i][1] = 0
                player_elo_data.append((pNumber, ELOpop[i][0], ELOpop[i][1], int(i)))
                if team == "2":
                    ELOpop[i][4] += 1
                if team == "1":
                    ELOpop[i][5] += 1
                if ELOpop[i][3] != "<:norank:1001265843683987487>":
                    newRank(i)

            # Perform database operations
            async with await get_db_pool() as pool:
                async with pool.acquire() as conn:
                    async with conn.cursor() as cursor:
                        try:
                            # Bulk insert player ELO data
                            await cursor.executemany(
                                "INSERT INTO player_elo (match_id, player_name, player_elos, discord_id) VALUES (%s, %s, %s, %s)",
                                player_elo_data
                            )
                            
                            # Update match outcome
                            current_timestamp = datetime.datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                            await cursor.execute(
                                "UPDATE matches SET match_outcome = %s, updated_at = %s WHERE match_id = %s",
                                (team, current_timestamp, pNumber)
                            )
                        except Exception as e:
                            await dev_channel.send(f"SQL QUERY ERROR: {e}")

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
            ]
            del activePickups[pNumber]

            with open("activePickups.json", "w") as cd:
                json.dump(activePickups, cd, indent=4)
            with open("ELOpop.json", "w") as cd:
                json.dump(ELOpop, cd, indent=4)
            with open("pastten.json", "w") as cd:
                json.dump(pastTen, cd, indent=4)

            await ctx.send("Match reported!")
            await sync_players(ctx)


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
    global GLOBAL_LOCK
    if GLOBAL_LOCK is None:
        await setup_global_lock()
    async with GLOBAL_LOCK:
        with open("pastten.json") as f:
            pastTen = json.load(f)
        with open("ELOpop.json") as f:
            ELOpop = json.load(f)
        with open("activePickups.json") as f:
            activePickups = json.load(f)
        db = mysql.connector.connect(
            host=logins["mysql"]["host"],
            user=logins["mysql"]["user"],
            passwd=logins["mysql"]["passwd"],
            database=logins["mysql"]["database"],
            autocommit=True,
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

        sql = "UPDATE matches SET updated_at = %s, deleted_at = %s WHERE match_id = %s"
        current_timestamp = datetime.datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        logging.info(sql)
        logging.info((current_timestamp, current_timestamp, pNumber))
        mycursor.execute(
            sql,
            (current_timestamp, current_timestamp, pNumber),
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
        await sync_players(ctx)


@client.command(pass_context=True)
async def games(ctx):
    global GLOBAL_LOCK
    if GLOBAL_LOCK is None:
        await setup_global_lock()
    async with GLOBAL_LOCK:
        if (
            (ctx.channel.name == v["pc"])
            or (ctx.channel.name == "tfc-admins")
            or (ctx.channel.name == "tfc-runners")
        ):
            await openPickups(ctx)


@client.command(pass_context=True)
async def recent(ctx):
    global GLOBAL_LOCK
    if GLOBAL_LOCK is None:
        await setup_global_lock()
    async with GLOBAL_LOCK:
        if (
            (ctx.channel.name == v["pc"])
            or (ctx.channel.name == "tfc-admins")
            or (ctx.channel.name == "tfc-runners")
            or (ctx.channel.id == DEV_TESTING_CHANNEL)
        ):
            await pastGames(ctx)


@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def checkgame(ctx, number):
    global GLOBAL_LOCK
    if GLOBAL_LOCK is None:
        await setup_global_lock()
    async with GLOBAL_LOCK:
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
            match_outcome_string = "Active Game (unreported!)"
        elif number in past_ten:
            blueTeam = past_ten[number][PAST_TEN_BLUE_TEAM_INDEX]
            redTeam = past_ten[number][PAST_TEN_RED_TEAM_INDEX]
            match_outcome_string = "Team " + str(
                past_ten[number][PAST_TEN_MATCH_OUTCOME_INDEX]
            )
        else:
            await ctx.send(
                f"Issue finding game number {number} in past 10 or active pickups - check for typo?"
            )
            return

        for i in blueTeam:
            msgList.append(getRank(i) + " " + ELOpop[i][0] + "\n")
        bMsg = "".join(msgList)
        msgList.clear()
        for i in redTeam:
            msgList.append(getRank(i) + " " + ELOpop[i][0] + "\n")
        rMsg = "".join(msgList)
        embed = discord.Embed(
            title=f"Game Number - {number} - Outcome - {match_outcome_string}"
        )
        embed.add_field(name="Blue Team " + v["t1img"], value=bMsg, inline=True)
        embed.add_field(name="\u200b", value="\u200b")
        embed.add_field(name="Red Team " + v["t2img"], value=rMsg, inline=True)
        await ctx.send(embed=embed)


# Remove a game that you no longer wish to complete or count for ELO.  Use !games to get a
# list of game numbers that are valid to remove.
# Example: !removegame 699670
@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def removegame(ctx, number):
    global GLOBAL_LOCK
    if GLOBAL_LOCK is None:
        await setup_global_lock()
    async with GLOBAL_LOCK:
        with open("activePickups.json") as f:
            activePickups = json.load(f)

        with open("pastten.json") as f:
            pastTen = json.load(f)

        if number in activePickups:
            del activePickups[number]
        elif number in pastTen:
            await ctx.send(
                f"ERROR: Game {number} needs to be undone via !undo first!"
            )
            return
        else:
            await ctx.send(
                f"ERROR: Game {number} not found in active games nor in past ten games!"
            )
            return
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
    global GLOBAL_LOCK
    if GLOBAL_LOCK is None:
        await setup_global_lock()
    async with GLOBAL_LOCK:
        if (ctx.channel.name == v["pc"]) or (ctx.channel.id == DEV_TESTING_CHANNEL):
            cancelImpl()
            await ctx.send("Queue has been cancelled..")


@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def requeue(ctx, show_queue=True):
    global blueTeam
    global redTeam
    global playersAdded
    global inVote

    global GLOBAL_LOCK
    if GLOBAL_LOCK is None:
        await setup_global_lock()
    async with GLOBAL_LOCK:
        if inVote == 0:
            await ctx.send("ERROR: Tried calling !requeue outside of mapvote!")
            return
        if captMode == 1:
            logging.info(blueTeam, redTeam, eligiblePlayers)
            neligibleplayers = eligiblePlayers.copy()
            DePopulatePickup()
            playersAdded = neligibleplayers.copy() + playersAdded
            if show_queue:
                await showPickup(ctx)
        else:
            if MAP_VOTE_FIRST is False:
                neligibleplayers = blueTeam + redTeam
                DePopulatePickup()
                playersAdded = neligibleplayers.copy() + playersAdded
                neligibleplayers.clear()
            else:
                DePopulatePickup()
            if show_queue:
                await showPickup(ctx)


@map_vote_timer.after_loop
async def force_vote_timer_version():
    if map_vote_timer.is_being_cancelled():
        return

    # ctx = await client.get_context(vMsg)
    # command = client.get_command("forceVote")
    # await ctx.invoke(command)
    channel = await client.fetch_channel(v["pID"])
    # await channel.send("Time's up! Auto-Force Voting!")
    await channel.send("!fv")


# End the current voting round (server, map, etc) potentially early if not everyone has cast their votes yet.
# Examples: !forceVote
#           !fv
@client.command(aliases=["fv"], pass_context=True)
@commands.cooldown(1, 10, commands.BucketType.channel)
@commands.has_role(v["runner"])
async def forceVote(ctx):
    global mapVotes
    global map_choice_4
    global map_choice_3
    global map_choice_2
    global map_choice_1
    global map_choice_5
    global winningIP
    global server_vote
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
    global alreadyVoted
    global lastFive
    global vMsg
    global blueTeam
    global redTeam
    global server_vote_message_view
    global map_vote_message_view

    global GLOBAL_LOCK
    if GLOBAL_LOCK is None:
        await setup_global_lock()
    async with GLOBAL_LOCK:
        channel = await client.fetch_channel(v["pID"])
        if channel.name == v["pc"]:
            if inVote == 0:
                await ctx.send("ERROR: Tried calling force vote outside of a vote!")
                return

            winningMap = None
            alreadyVoted = []
            if server_vote == 1:
                server_vote_message_view.stop()
                server_vote_timer.cancel()
                votes = [
                    len(mapVotes[map_choice_1]),
                    len(mapVotes[map_choice_2]),
                    len(mapVotes[map_choice_3]),
                ]
                server_names = [
                    map_choice_1,
                    map_choice_2,
                    map_choice_3,
                    map_choice_4,
                    map_choice_5,
                ]
                vote_index = 0
                max_vote_count = max(votes)
                candidate_server_names = []
                for count in votes:
                    if count == max_vote_count:
                        candidate_server_names.append(server_names[vote_index])
                    vote_index = vote_index + 1

                if len(candidate_server_names) > 1:
                    winning_server = random.choice(candidate_server_names)
                    await ctx.send(
                        f"There was a tie in server votes! Making a random selection between them... - {winning_server}"
                    )
                else:
                    winning_server = candidate_server_names[0]
                # Pick a random final winner from the candidate maps

                winningServer = winning_server  # keeping this random variable around til I refactor it into oblivion
                if winning_server == "Central - Dallas":
                    winningIP = f"https://tinyurl.com/tfpcentralvultr2 - {winning_server} connect {logins['central']['server_ip']}:27015; password letsplay!"
                elif winning_server == "South East - Miami":
                    winningIP = f"http://tinyurl.com/tfpsoutheastvultr - {winning_server} connect {logins['southeast']['server_ip']}:27015; password letsplay!"
                elif winning_server == "East2 - New York City":
                    winningIP = f"http://tinyurl.com/tfpeast2vultr - {winning_server} connect {logins['east2']['server_ip']}:27015; password letsplay!"
                else:
                    # Just pick one so things aren't completely broken
                    winningIP = f"http://tinyurl.com/tfpeast2vultr - {winning_server} connect {logins['east2']['server_ip']}:27015; password letsplay!"
                    winningServer = "East2 - New York City"
                server_vote = 0
                map_choice_5 = "New Maps"
                if winningIP.find('aws') != -1:
                    boto_region = "us-east-1" if winningIP.find('west') == -1 else 'us-west-1'
                    boto_client = boto3.client('ec2', region_name=boto_region)
                    server = winning_server.split(' - ')[0].lower()
                    instance_state_raw = boto_client.describe_instance_status(InstanceIds=[logins[server]["instance_id"]])['InstanceStatuses']
                    if instance_state_raw == []:
                        instance_state = 'stopped'
                    else:
                        instance_state = instance_state_raw[0]['InstanceState']['Name']
                    if instance_state != 'running':
                        await ctx.send(f"{server} server is not running! Starting it up now")
                        boto_client.start_instances(InstanceIds=[logins[server]["instance_id"]])
                await voteSetup(ctx)
            elif server_vote == 0:
                map_vote_message_view.stop()
                map_vote_timer.cancel()
                # We are currently in map voting round
                if reVote == 0:
                    # Tally the votes for each choice, putting new maps in the first slot to give precedence for a tie
                    # This will trigger a new vote in the case of a tie with a real map.
                    votes = [
                        len(mapVotes[map_choice_5]),
                        len(mapVotes[map_choice_1]),
                        len(mapVotes[map_choice_2]),
                        len(mapVotes[map_choice_3]),
                        len(mapVotes[map_choice_4]),
                    ]
                    mapNames = [
                        map_choice_5,
                        map_choice_1,
                        map_choice_2,
                        map_choice_3,
                        map_choice_4,
                    ]
                elif reVote == 1:
                    votes = [
                        len(mapVotes[map_choice_1]),
                        len(mapVotes[map_choice_2]),
                        len(mapVotes[map_choice_3]),
                        len(mapVotes[map_choice_4]),
                        len(mapVotes[map_choice_5]),
                    ]
                    mapNames = [
                        map_choice_1,
                        map_choice_2,
                        map_choice_3,
                        map_choice_4,
                        map_choice_5,
                    ]
                maxVoteCount = max(votes)
                windex = votes.index(maxVoteCount)  # winning index

                # Check for special case of new maps first to trigger new voting round
                if (windex == 0) and ("New Maps" in mapNames):
                    # We need a new voting round
                    reVote = 1
                    del votes[0]  # votes now has 4 entries
                    windex = votes.index(max(votes))
                    if windex == 0:
                        map_choice_5 = map_choice_1
                    if windex == 1:
                        map_choice_5 = map_choice_2
                    if windex == 2:
                        map_choice_5 = map_choice_3
                    if windex == 3:
                        map_choice_5 = map_choice_4
                    await ctx.send("New maps has won, now selecting new maps..")
                    await voteSetup(ctx)
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
                        if MAP_VOTE_FIRST is True:
                            # Create the teams after the map vote
                            inVote = 0
                            player_count = len(eligiblePlayers) // 2
                            await generate_teams(player_count)

                    # Pick a random final winner from the candidate maps
                    winningMap = random.choice(candidateMapNames)
                    await ctx.send(
                            embed=teamsDisplay(
                                blueTeam,
                                redTeam,
                                None,
                                None,
                                None,
                                None,
                                False,
                                False,
                            )
                        )
                    await ctx.send(
                        f"The winning map is **{winningMap}** and will be played at {winningIP}"
                    )
                    inVote = 0
                    if len(lastFive) >= 5:
                        lastFive.remove(lastFive[0])
                    lastFive.append(winningMap)
                    if map_vote_timer.is_running():
                        map_vote_timer.cancel()
                    edited_content = "\n".join(vMsg.content.split("\n")[:-1])
                    await vMsg.edit(
                        content=edited_content + "\n" + "Voting is finished!"
                    )

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
                pMsg = await ctx.send(
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
async def shuffle(ctx, idx=None, game="None"):
    global rankedOrder
    global blueTeam
    global redTeam
    global team1prob
    global team2prob
    global blueRank
    global redRank
    global tMsg
    
    global GLOBAL_LOCK
    if GLOBAL_LOCK is None:
        await setup_global_lock()
    async with GLOBAL_LOCK:
        dev_channel = await client.fetch_channel(DEV_TESTING_CHANNEL)
        if (ctx.channel.name == v["pc"]) or (ctx.channel.id == DEV_TESTING_CHANNEL):
            if idx is None:
                idx = random.randint(1, 11)
            with open("activePickups.json") as f:
                activePickups = json.load(f)
            with open("ELOpop.json") as f:
                ELOpop = json.load(f)

            if game == "None":
                game = list(activePickups)[-1]
            
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
            blue_team_info_string = f"blueTeam: {blueTeam}, blueRank: {blueRank}, blue_win_probability: {team1prob}"
            red_team_info_string = f"redTeam: {redTeam}, redRank: {redRank}, red_win_probability {team2prob}"
            logging.info(blue_team_info_string)
            logging.info(red_team_info_string)

            await ctx.send(
                embed=teamsDisplay(blueTeam, redTeam, team1prob, team2prob)
            )
            activePickups[game][0] = team1prob
            activePickups[game][1] = blueRank
            activePickups[game][2] = blueTeam
            activePickups[game][3] = team2prob
            activePickups[game][4] = redRank
            activePickups[game][5] = redTeam

            with open("activePickups.json", "w") as cd:
                json.dump(activePickups, cd, indent=4)
            async with await get_db_pool() as pool:
                async with pool.acquire() as conn:
                    async with conn.cursor() as cursor:
                        try:
                            current_timestamp = datetime.datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                            blueTeamString = ','.join(blueTeam)
                            redTeamString = ','.join(redTeam)
                            await cursor.execute(
                                "UPDATE matches SET blue_probability = %s, blue_team = %s, blue_rank = %s, red_probability = %s, red_team = %s, red_rank = %s, updated_at = %s WHERE match_id = %s",
                                (team1prob, blueTeamString, blueRank, team2prob, redTeamString, redRank, current_timestamp, game)
                            )
                        except Exception as e:
                            await dev_channel.send(f"SQL QUERY ERROR: {e}")


@client.command(pass_context=True)
@commands.cooldown(1, 30, commands.BucketType.channel)
async def notice(ctx, anumber=8):
    global GLOBAL_LOCK
    if GLOBAL_LOCK is None:
        await setup_global_lock()
    async with GLOBAL_LOCK:
        if ctx.channel.name == v["pc"]:
            global playersAdded
            number = len(list(playersAdded))
            role = discord.utils.get(ctx.guild.roles, id=v["TFCPlayer"])

        await ctx.send(f"{role.mention} {number}/{anumber}")
        await showPickup(ctx)


@client.command(pass_context=True, aliases=["v"])
@commands.cooldown(1, 30, commands.BucketType.channel)
async def vote(ctx):
    """
    Nagging message to get people to vote who haven't picked their server or map choice yet
    """
    global GLOBAL_LOCK
    if GLOBAL_LOCK is None:
        await setup_global_lock()
    async with GLOBAL_LOCK:
        if ctx.channel.name == v["pc"] or ctx.channel.id == DEV_TESTING_CHANNEL:
            global players_abstained_discord_id
            if len(players_abstained_discord_id) >= 1:
                nag_list = players_abstained_discord_id
                for index, item in enumerate(nag_list):
                    nag_list[index] = f"<@{item}>"
                nag_message = "\n💩 " + ", ".join(nag_list) + " need to vote 💩"
                await ctx.send(nag_message)
            else:
                await ctx.author.send("No active vote is happening!")


"""@slash.slash(name="slap")
async def slap(ctx, player: discord.Member):
    await ctx.send(f"{ctx.author.display_name} slapped {player.display_name} around a bit with a large trout")"""


@client.event
async def on_reaction_add(reaction, user):
    global GLOBAL_LOCK
    if GLOBAL_LOCK is None:
        await setup_global_lock()
    async with GLOBAL_LOCK:
        if not user.bot:
            global vMsg
            global mapVotes
            global server_vote
            global inVote
            global eligiblePlayers
            global map_choice_1
            global map_choice_2
            global map_choice_3
            global map_choice_4
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
                                if not SHOW_VISUAL_RANKS:
                                    visualRank = ""
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

                            await oMsg.edit(embed=embed)
                        elif len(ready) == 8:
                            logging.info(
                                "Somehow we got 8 people to hit the thumbs up!"
                            )
                            channel2 = await client.fetch_channel(
                                reaction.message.channel.id
                            )
                            await teams(channel2)
                    else:
                        await reaction.message.remove_reaction(reaction, user)
                        await user.send("You are not among the first 8 added...")
            # TODO: Remove dead code branch
            if reaction.message == vMsg:
                if votable == 1:
                    if (
                        (reaction.emoji == "1️⃣")
                        or (reaction.emoji == "2️⃣")
                        or (reaction.emoji == "3️⃣")
                        or (reaction.emoji == "4️⃣")
                        or (reaction.emoji == "5️⃣")
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
                                    mapVotes[map_choice_1].append(playerName)
                                if reaction.emoji == "2️⃣":
                                    mapVotes[map_choice_2].append(playerName)
                                if reaction.emoji == "3️⃣":
                                    mapVotes[map_choice_3].append(playerName)
                                if reaction.emoji == "4️⃣":
                                    mapVotes[map_choice_4].append(playerName)
                                if reaction.emoji == "5️⃣":
                                    mapVotes[map_choice_5].append(playerName)
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

                                with open(MAIN_MAPS_FILE) as f:
                                    mapList = json.load(f)
                                with open(SECONDARY_MAPS_FILE) as f:
                                    mapList2 = json.load(f)
                                if server_vote == 1:
                                    vMsg = await vMsg.edit(
                                        content="```Vote for your server! (Please wait for everyone to vote, or sub AFK players)\n\n"
                                        + "1️⃣ "
                                        + map_choice_1
                                        + " " * (70 - len(map_choice_1))
                                        + server_vote_output(map_choice_1)
                                        + "\n"
                                        + "2️⃣ "
                                        + map_choice_2
                                        + " " * (70 - len(map_choice_2))
                                        + server_vote_output(map_choice_2)
                                        + "\n"
                                        + "3️⃣ "
                                        + map_choice_3
                                        + " " * (70 - len(map_choice_3))
                                        + server_vote_output(map_choice_3)
                                    )
                                elif server_vote == 0:
                                    vMsg = await vMsg.edit(
                                        content=get_map_vote_output(
                                            reVote, mapList, mapList2, toVoteString
                                        )
                                    )
                                logging.info(alreadyVoted)
                                logging.info(mapVotes)
                                logging.info(playerCount)
                            else:
                                await reaction.message.remove_reaction(reaction, user)
                                await user.send("You are not in this pickup..")
                    else:
                        await reaction.message.remove_reaction(reaction, user)


async def generate_elo_chart(discord_user):
    with open("ELOpop.json") as f:
        ELOpop = json.load(f)
    dev_channel = await client.fetch_channel(DEV_TESTING_CHANNEL)
    db = mysql.connector.connect(
        host=logins["mysql"]["host"],
        user=logins["mysql"]["user"],
        passwd=logins["mysql"]["passwd"],
        database=logins["mysql"]["database"],
        autocommit=True,
    )

    mycursor = db.cursor()
    try:
        mycursor.execute(
            f"SELECT player_elos from player_elo WHERE discord_id = {discord_user.id} order by entryID"
        )
        elo_history = mycursor.fetchall()

        if len(elo_history) < 1:
            logging.warning(
                "Had to fall-back to local elo file - check for issue query"
            )
            logging.warning(
                f"""
                with elo_row_numbered as (
                select player_name, player_elos, discord_id, row_number() over (partition by player_name order by entryID desc) as row_num from player_elo
                )

                select player_elos from elo_row_numbered where row_num = 1 and discord_id = '{discord_user.id}'
                order by player_elos desc;"""
            )
            await dev_channel.send(
                f"""Query failed for ELO for some reason - check mysql db - with elo_row_numbered as (
                select player_name, player_elos, discord_id, row_number() over (partition by player_name order by entryID desc) as row_num from player_elo
                )

                select player_elos from elo_row_numbered where row_num = 1 and discord_id = '{discord_user.id}'
                order by player_elos desc;"""
            )
            embed = discord.Embed(title=f"{discord_user.display_name}")
            message_formatted = f"ELO is currently {ELOpop[str(discord_user.id)][1]} with a record of W: {ELOpop[str(discord_user.id)][PLAYER_MAP_WIN_INDEX]} L: {ELOpop[str(discord_user.id)][PLAYER_MAP_LOSS_INDEX]} D: {ELOpop[str(discord_user.id)][PLAYER_MAP_DRAW_INDEX]}"
            embed.add_field(name="ELO & Stats", value=message_formatted)
            return None, embed
        elif len(elo_history) == 1:
            # TODO: Need to store diffs of elo before and after somewhere instead of only having the final value persisted
            embed = discord.Embed(title=f"{discord_user.display_name}")
            message_formatted = f"ELO is currently {ELOpop[str(discord_user.id)][1]} with a record of W: {ELOpop[str(discord_user.id)][PLAYER_MAP_WIN_INDEX]} L: {ELOpop[str(discord_user.id)][PLAYER_MAP_LOSS_INDEX]} D: {ELOpop[str(discord_user.id)][PLAYER_MAP_DRAW_INDEX]}"
            embed.add_field(name="ELO & Stats", value=message_formatted)
            return None, embed
        else:
            plotList = []
            for x in elo_history:
                plotList.append(int(x[0]))
            plt.style.use("cyberpunk")
            plt.plot(plotList)
            mplcyberpunk.add_glow_effects()
            plt.savefig(discord_user.display_name + ".png")

            mycursor.execute(
                f"""SELECT max(player_elos) from player_elo WHERE discord_id = {discord_user.id}"""
            )
            max_elo = mycursor.fetchone()[0]
            current_elo = plotList[-1]
            previous_game_elo = plotList[-2]
            elo_difference = current_elo - previous_game_elo
            if (elo_difference) < 0:
                elo_difference_message = f"""```diff\n-{abs(elo_difference)}```"""
            else:
                elo_difference_message = f"""```diff\n+{elo_difference}```"""
            embed = discord.Embed(title=f"{discord_user.display_name}")
            message_formatted = f"Your ELO is currently {current_elo} with a record of W: {ELOpop[str(discord_user.id)][4]} L: {ELOpop[str(discord_user.id)][5]} D: {ELOpop[str(discord_user.id)][6]}\n Difference from previous game:{elo_difference_message}"
            embed.add_field(name="ELO & Stats", value=message_formatted)
            needed_for_next_rank = "N/A"
            # TODO: Put this into a function outside of this code
            for index, elo_group in enumerate(RANK_BOUNDARIES_LIST):
                if current_elo > elo_group:
                    continue
                else:
                    needed_for_next_rank = RANK_BOUNDARIES_LIST[index] - current_elo
                    break
            embed.add_field(
                name="Amount of ELO needed for next rank", value=needed_for_next_rank
            )
            embed.add_field(name="Peak ELO", value=max_elo)
            # TODO: Add a field that has the past 10 games, like neatqueue
            filename = discord_user.display_name + ".png"
            file = discord.File(filename)
            os.remove(filename)
            plt.clf()
            return file, embed
    except Exception as e:
        await dev_channel.send(e)


#command to mute a player
@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def mute(ctx, player: discord.Member):
    global mute_list

    filename = Path('mute_list.json')
    filename.touch(exist_ok=True)
    with open(filename) as f:
        mute_list = json.load(f)
    if(str(player.id) not in list(mute_list)):  
        mute_list[str(player.id)] = [0, 0]
        await player.send("You have been muted from posting links and attachments. Further doing so could result in a timeout.")
        await ctx.send(f"{player.display_name} has been muted from posting links and attachments. Further doing so could result in a timeout.")
    else:
        await ctx.send("Player already on the mute list.")

    with open(filename, "w") as cd:
        json.dump(mute_list, cd, indent=4)


#command to unmute a player
@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def unmute(ctx, player: discord.Member):
    global mute_list

    filename = Path('mute_list.json')
    filename.touch(exist_ok=True)
    with open(filename) as f:
        mute_list = json.load(f)
    if(str(player.id) in list(mute_list)):  
        del mute_list[str(player.id)]
        await player.send("You have been unmuted from posting links and attachments. Don't fuck up again")
        await ctx.send(f"{player.display_name} has been unmuted from posting links and attachments.")
    else:
        await ctx.send("Player was not in the mute list.")

    with open(filename, "w") as cd:
        json.dump(mute_list, cd, indent=4)


@client.command(pass_context=True)
@commands.has_role(v["admin"])
async def hellban(ctx, player: discord.Member):
    global hellban_list

    filename = Path('hellban_list.json')
    filename.touch(exist_ok=True)
    with open(filename) as f:
        hellban_list = json.load(f)
    if(str(player.id) not in list(hellban_list)):  
        hellban_list[str(player.id)] = [0, 0]
        await player.send("You have been hellbanned. You may only add or remove from pickups, other messages will be deleted.")
        await ctx.send(f"{player.display_name} has been hellbanned - all messages not related to pickups will be deleted.")
    else:
        await ctx.send("Player already on the hellban list.")

    with open(filename, "w") as cd:
        json.dump(hellban_list, cd, indent=4)


@client.command(pass_context=True)
@commands.has_role(v["admin"])
async def unhellban(ctx, player: discord.Member):
    global hellban_list

    filename = Path('hellban_list.json')
    filename.touch(exist_ok=True)
    with open(filename) as f:
        hellban_list = json.load(f)
    if(str(player.id) in list(hellban_list)):  
        del hellban_list[str(player.id)]
        await player.send("You have been unhellbanned. Don't fuck up again")
        await ctx.send(f"{player.display_name} has been unhellbanned.")
    else:
        await ctx.send("Player was not in the hellban list.")

    with open(filename, "w") as cd:
        json.dump(hellban_list, cd, indent=4)


def is_link(message):
    test_list = ['.com', '.ru', '.net', '.org', '.info', '.biz', '.io', '.co', "https://", "http://"]
    return [ele for ele in test_list if(ele in message)]


@client.event
async def on_message(message):
    global eligiblePlayers
    global alreadyVoted
    global server_vote
    global reVote
    global vMsg
    global mapVotes
    global map_choice_1
    global map_choice_2
    global map_choice_3
    global map_choice_4
    global mute_list
    global hellban_list

    if message.content == "elo":
        user = await client.fetch_user(message.author.id)
        file, embed = await generate_elo_chart(user)
        await message.author.send(embed=embed, file=file)
    # Check for auto-report
    user = await client.fetch_user(message.author.id)

    user_id = str(message.author.id)
    # TODO: Move to function
    if user_id in mute_list and (is_link(message.content) or message.attachments):
        await message.delete()
        await message.author.send("You are banned from sending links, images, or attachments. Further messages will result in a timeout.") 
        mute_list[user_id][0] += 1
        duration = datetime.timedelta(seconds=0, minutes=5, hours= 0, days=0)
        #apply timeout if user is trying to spam images.  Was giving me a "Missing Permissions" in my test server but could be because I am owner in test server.  Timeout lasts for 5 minutes and can be changed.
        if (mute_list[user_id][0] > 2):
            await message.author.timeout(duration, reason="Muted on GIFs")
        with open("mute_list.json", "w") as cd:
            json.dump(mute_list, cd, indent=4)
    
    if user_id in hellban_list and (not message.content.startswith("!")):
        await message.delete()

    ctx = await client.get_context(message)
    if user.bot:
        if "!fv" in message.content:
            command = client.get_command("forceVote")
            await ctx.invoke(command)
        if "!stats1v1" in message.content:
            command = client.get_command("stats1v1")
            await ctx.invoke(command)
        elif "!win1v1" in message.content:
            split_message = str(message.content).split(" ")
            command = client.get_command("win1v1")
            await ctx.invoke(command, split_message[1])
        elif "!win" in message.content:
            split_message = str(message.content).split(" ")
            await win(ctx, split_message[1])
        elif "!draw" in message.content:
            await draw(ctx)
        elif "!stats" in message.content:
            split_message = str(message.content).split(" ")

            if len(split_message) == 5:
                tokens = str(message.content).split(" ")
                region = tokens[1]
                match_number = tokens[2]
                winning_score = tokens[3]
                losing_score = tokens[4]
            else:  # Assume 4
                tokens = str(message.content).split(" ")
                region = tokens[1]
                match_number = tokens[2]
                winning_score = tokens[3]
                losing_score = winning_score

            await stats(ctx, region, match_number, winning_score, losing_score)
    await client.process_commands(message)


client.run(v["TOKEN"])
