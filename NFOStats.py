import socket
import discord
from discord.ext import commands
import json
import logging

intents = discord.Intents.all()
client = commands.Bot(
    command_prefix=["!", "+", "-"], case_insensitive=True, intents=intents
)
UDP_IP_ADDRESS = "0.0.0.0"
UDP_PORT_NO = 6789
DM_CHANNEL_ID = 1230852204567597186
serverSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
serverSock.bind((UDP_IP_ADDRESS, UDP_PORT_NO))

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

with open("login.json") as f:
    logins = json.load(f)
with open("variables.json") as f:
    v = json.load(f)


@client.event
async def on_ready():
    pChannel = await client.fetch_channel(v["pID"])  # 836633689248104518
    logging.info("Auto Report Starting!")
    while True:
        # TODO: This is a blocking operation and should be updated to leverage asyncio instead of socket
        # This is blocks the discord heartbeat, but otherwise works
        data, addr = serverSock.recvfrom(1024)
        logging.info((str(data)))
        # L 01/05/2025 - 20:19:45: [MATCH RESULT] Team 1 Wins <70> (60) EAST phantom_lg
        if "[MATCH RESULT]" in str(data):
            with open("activePickups.json") as f:
                activePickups = json.load(f)
            string = str(data)
            begin = string.find("<") + 1
            end = string.find(">")
            winningScore = string[begin:end]
            begin = string.find("(") + 1
            end = string.find(")")
            losingScore = string[begin:end]
            # Lazy way to get region and map
            final_part = string[string.find(")") + 2:].split(" ")
            region = final_part[0]
            map = final_part[1][:-2]

            if losingScore == "0":
                print("Ignoring match result due to 0")
            else:
                if len(activePickups) > 0:
                    logging.info(str(activePickups))
                    reported_match = None
                    for game in activePickups:
                        if map == activePickups[game][7]:
                            logging.info(f"Found match {game} for map {map}")
                            reported_match = game
                            break
                    # if we can't find the map in the active pickups, use the most recent one
                    if reported_match is None:
                        logging.info("No match found for map, using most recent match")
                        reported_match = list(activePickups)[-1]
                    if "Team 1 Wins" in (str(data)):
                        # team 1 wins
                        await pChannel.send(f"!win 1 {reported_match}")
                        # [MATCH RESULT] Team 1 Wins <10> (0) EAST phantom_lg
                        await pChannel.send(
                            f"**AUTO-REPORTING** Team 1 wins {winningScore} to {losingScore} for game {reported_match}"
                        )
                        await pChannel.send(
                            f"!stats {region.lower()} {reported_match} {winningScore} {losingScore}"
                        )
                    elif "Team 2 Wins" in (str(data)):
                        await pChannel.send(f"!win 2 {reported_match}")
                        # [MATCH RESULT] Team 2 Wins <10> (0) EAST phantom_lg
                        await pChannel.send(
                            f"**AUTO-REPORTING** Team 2 wins {winningScore} to {losingScore} for game {reported_match}"
                        )
                        await pChannel.send(
                            f"!stats {region.lower()} {reported_match} {winningScore} {losingScore}"
                        )
                    elif "DRAW" in (str(data)):
                        await pChannel.send(f"!draw {reported_match}")
                        # [MATCH RESULT] DRAW at (50) CENTRAL phantom_lg
                        await pChannel.send(f"**AUTO-REPORTING** DRAW at {losingScore} for game {reported_match}")
                        await pChannel.send(
                            f"!stats {region.lower()} {reported_match} {losingScore}"
                        )
                else:
                    print("!! NO ACTIVE PICKUPS!")
        if "[1v1 MATCH RESULT]" in str(data):
            with open("active_1v1_matches.json", "r") as f:
                active_1v1_matches = json.load(f)
            if len(active_1v1_matches) > 0:
                reported_1v1_match = list(active_1v1_matches)[-1]
                dm_channel = await client.fetch_channel(DM_CHANNEL_ID)
                # TODO: This is copy-paste of above logic
                if "Team 1 Wins" in (str(data)):
                    # team 1 wins
                    await dm_channel.send("!win1v1 1")
                    # [MATCH RESULT] Team 1 Wins <10> (0)
                    await dm_channel.send(
                        f"**AUTO-REPORTING** Team 1 wins {reported_1v1_match}"
                    )
                elif "Team 2 Wins" in (str(data)):
                    await dm_channel.send("!win1v1 2")
                    # [MATCH RESULT] Team 2 Wins <10> (0)
                    await dm_channel.send(
                        f"**AUTO-REPORTING** Team 2 wins {reported_1v1_match}"
                    )
                await dm_channel.send("!stats1v1")


client.run(v["TOKEN"])
