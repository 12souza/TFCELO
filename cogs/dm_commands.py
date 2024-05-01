import json
import discord
import logging
import mysql.connector
import os
import random
from datetime import datetime, timezone
from ftplib import FTP
from pathlib import Path
from discord.ext import commands
from discord.utils import get

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

"""Players can add to 1v1 queue via !add1v1 in this channel, game will start when either both players thumbs up react the game message or a runner does !start1v1 - this creates a 1v1 match with a game number
Server will be the old east 2 (which will also be the conc server at some point in the future) - I'll rename it later
I am thinking of adding a 1v1 plugin that will detect whoever gets first to 50 kills (or whatever number we think of later) as the win condition
Match will get auto-reported if this is implemented, otherwise either player can report the game (which can be undone by a runner/admin if necessary) via !win1v1 (game number optional)
Ladder rankings will just be based purely off of wins, but wins and losses will be tracked. """

DM_CHANNEL_ID = 1230852204567597186
DEV_TESTING_CHANNEL = 1139762727275995166
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
dm_queue = []

# Load in ELO configuration
base_path = Path(__file__).parent
ELOpop_file_path = (base_path / "../ELOpop.json").resolve()
with open(ELOpop_file_path) as f:
    ELOpop = json.load(f)

# Load in main script configuration
variables_file_path = (base_path / "../variables.json").resolve()
with open(variables_file_path) as f:
    v = json.load(f)

login_file_path = (base_path / "../login.json").resolve()
with open(login_file_path) as f:
    logins = json.load(f)


class DMCommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def check_message_channel(ctx):
        return ctx.channel.id in (DEV_TESTING_CHANNEL, DM_CHANNEL_ID)

    def stat_log_file_handler(self, ftp, region):
        # Note: We are taking a dependency on newer logs having a higher ascending name
        logListNameAsc = (
            ftp.nlst()
        )  # Get list of logs sorted in ascending order by name.
        logListNameDesc = reversed(
            logListNameAsc
        )  # We want to evaluate most recent first for efficiency, so reverse it

        log_to_parse = None
        for logFile in logListNameDesc:
            size = ftp.size(logFile)
            # Do a simple heuristic check to see if this is a "real" round.  TODO: maybe use a smarter heuristic
            # if we find any edge cases.
            if (size > 100000) and (
                ".log" in logFile
            ):  # Rounds with logs of players and time will be big
                log_to_parse = logFile
                break

        try:
            ftp.retrbinary("RETR " + log_to_parse, open(log_to_parse, "wb").write)
        except Exception:
            logging.warning(f"Issue Downloading logfiles from FTP - {Exception}")
        renamed_log = f"{log_to_parse[0:-4]}-coach{region}.log"
        os.rename(log_to_parse, renamed_log)

        hampalyzer_output = None
        newCMD = (
            "curl -X POST -F force=on -F logs[]=@"
            + renamed_log
            + " http://app.hampalyzer.com/api/parseLog"
        )
        output3 = os.popen(newCMD).read()
        if "nginx" not in output3 or output3 is None:
            hampalyzer_output = "http://app.hampalyzer.com/" + output3[21:-3]

        os.remove(renamed_log)
        return hampalyzer_output

    def addplayerImpl(self, playerID, playerDisplayName):
        global dm_queue
        global ELOpop

        with open("ELOpop.json") as f:
            ELOpop = json.load(f)
        if len(dm_queue) <= 2:
            if playerID not in dm_queue:
                if playerID not in list(
                    ELOpop
                ):  # Player is not registered, give them a default rating
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
                # Handle setting starting win/loss count for 1v1s to 0 for existing players
                if len(ELOpop[playerID]) == 9:
                    ELOpop[playerID].append(None)
                    ELOpop[playerID].append(0)
                    ELOpop[playerID].append(0)

                    with open("ELOpop.json", "w") as cd:
                        json.dump(ELOpop, cd, indent=4)

                dm_queue.append(playerID)
            else:
                return 1  # Player already added
            return 0  # Player successfully added
        else:
            return 2  # Too many players

    # TODO: This should be based off of 1v1 wins, not pug wins
    def get_win_emblem(self, ctx, discord_id):
        """Return the corresponding emblem for a player given their win count"""

        if ELOpop[discord_id][PLAYER_MAP_WIN_INDEX] < 10:
            return get(ctx.message.guild.emojis, name="we0")  # Civilian
        elif ELOpop[discord_id][PLAYER_MAP_WIN_INDEX] < 25:
            return get(ctx.message.guild.emojis, name="we1")  # Scout
        elif ELOpop[discord_id][PLAYER_MAP_WIN_INDEX] < 50:
            return get(ctx.message.guild.emojis, name="we2")  # Pyro
        elif ELOpop[discord_id][PLAYER_MAP_WIN_INDEX] < 75:
            return get(ctx.message.guild.emojis, name="we3")  # Medic
        elif ELOpop[discord_id][PLAYER_MAP_WIN_INDEX] < 100:
            return get(ctx.message.guild.emojis, name="we4")  # Spy
        elif ELOpop[discord_id][PLAYER_MAP_WIN_INDEX] < 250:
            return get(ctx.message.guild.emojis, name="we5")  # Sniper
        elif ELOpop[discord_id][PLAYER_MAP_WIN_INDEX] < 500:
            return get(ctx.message.guild.emojis, name="we6")  # Engineer
        elif ELOpop[discord_id][PLAYER_MAP_WIN_INDEX] < 750:
            return get(ctx.message.guild.emojis, name="we7")  # Soldier
        elif ELOpop[discord_id][PLAYER_MAP_WIN_INDEX] < 1000:
            return get(ctx.message.guild.emojis, name="we8")  # Demoman
        else:
            return get(ctx.message.guild.emojis, name="we9")  # HWGuy

    async def show_dm_pickup(self, ctx):
        global oMsg
        global ready

        embed_player_list = []
        for i in dm_queue:
            achList = ELOpop[i][7]

            if (
                ELOpop[i][PLAYER_MAP_DUNCE_FLAG_INDEX] is not None
            ):  # Is player a naughty dunce?
                ach = (
                    v["dunce"]
                    + "- Dunce cap for: "
                    + ELOpop[i][PLAYER_MAP_DUNCE_FLAG_INDEX]
                )  # Achievements get wiped and replaced with the dunce cap
                win_emblem = ""  # Dunces don't get an emblem to show off
            else:
                ach = "".join(achList)  # Not a dunce, use their real achievements
                # TODO: This should be based off of 1v1 wins, not pug wins
                self.get_win_emblem(ctx, i)
                win_emblem = str(self.get_win_emblem(ctx, i))

            embed_player_list.append(
                win_emblem
                + " "
                + ELOpop[i][PLAYER_MAP_VISUAL_NAME_INDEX]
                + " "
                + ach
                + "\n"
            )
        msg = "".join(embed_player_list)

        if len(dm_queue) <= 2:
            embed = discord.Embed(title="DM Queue")
            if len(dm_queue) > 0:
                embed.add_field(
                    name=f"Players Added - {len(dm_queue)} Queued", value=msg
                )
            elif len(dm_queue) == 0:
                embed.add_field(name="Players Added", value="PUG IS EMPTY!")
            await ctx.send(embed=embed)

    # Utility function for showing the pickup
    async def removePlayerImpl(self, ctx, playerID):
        global dm_queue
        if playerID in dm_queue:
            dm_queue.remove(playerID)
            await self.show_dm_pickup(ctx)
            return

    @commands.command(pass_context=True)
    @commands.check(check_message_channel)
    async def remove1v1(self, ctx):
        playerID = str(ctx.author.id)
        await self.removePlayerImpl(ctx, playerID)

    @commands.command(pass_context=True)
    @commands.has_role(v["runner"])
    @commands.check(check_message_channel)
    async def kick1v1(self, ctx, player: discord.Member):
        playerID = str(player.id)
        await self.removePlayerImpl(ctx, playerID)

    @commands.command(pass_context=True)
    @commands.has_role(v["tfc"])
    @commands.check(check_message_channel)
    async def add1v1(self, ctx):
        global dm_queue
        playerID = str(ctx.author.id)
        playerDisplayName = ctx.author.display_name

        retVal = self.addplayerImpl(playerID, playerDisplayName)
        if retVal == 1:  # Already added
            await ctx.send(
                f"{ctx.author.display_name} - you are already added to the 1v1 queue"
            )
        if retVal == 0:  # Successfully added
            await self.show_dm_pickup(ctx)

    @commands.command(pass_context=True)
    @commands.has_role(v["tfc"])
    @commands.check(check_message_channel)
    async def test1v1(self, ctx, player: discord.Member):
        playerID = str(player.id)
        playerDisplayName = player.display_name
        retVal = self.addplayerImpl(playerID, playerDisplayName)
        if retVal == 0:  # Successfully added
            await self.show_dm_pickup(ctx)

    @commands.command(pass_context=True)
    @commands.has_role(v["tfc"])
    @commands.check(check_message_channel)
    async def start1v1(self, ctx):
        global dm_queue
        if len(dm_queue) != 2:
            await ctx.send(
                "Not the correct number of players for the queue. Must be exactly 2!"
            )
            return
        db = mysql.connector.connect(
            host=logins["mysql"]["host"],
            user=logins["mysql"]["user"],
            passwd=logins["mysql"]["passwd"],
            database=logins["mysql"]["database"],
            autocommit=True,
        )
        cursor = db.cursor()

        # Create match, remove players from queue
        if not os.path.exists("active_1v1_matches.json"):
            with open("active_1v1_matches.json", "w") as f:
                f.write("{}")
            active_1v1_matches = {}
        else:
            with open("active_1v1_matches.json", "r") as f:
                active_1v1_matches = json.load(f)
        match_id = random.randint(10000001, 20000000)
        # In the rare scenario that we happen to pick a game id that we already have we need to regenerate
        # TODO: Handle reported games with the same logic, too
        while match_id in active_1v1_matches:
            match_id = random.randint(10000001, 20000000)
        current_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        current_game = {
            "match_id": match_id,
            "created_at": current_timestamp,
            "updated_at": current_timestamp,
            "deleted_at": None,
            "blue_probability": None,
            "blue_rank": None,
            "blue_team": dm_queue[0],
            "red_probability": None,
            "red_rank": None,
            "red_team": dm_queue[1],
            "map": "ass_dm",
            "server": "east2",
            "game_type": "1v1",
            "match_outcome": None,
        }
        # Write to local json
        active_1v1_matches[match_id] = current_game
        with open("active_1v1_matches.json", "w") as f:
            json.dump(active_1v1_matches, f, indent=4)
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
        cursor.execute(sql, list(current_game.values()))
        embed = discord.Embed(title=f"Game Number - {match_id} - Started!")
        embed.add_field(
            name="Blue Team " + v["t1img"],
            value=ELOpop[dm_queue[0]][PLAYER_MAP_VISUAL_NAME_INDEX],
            inline=True,
        )
        embed.add_field(name="\u200b", value="\u200b")
        embed.add_field(
            name="Red Team " + v["t2img"],
            value=ELOpop[dm_queue[1]][PLAYER_MAP_VISUAL_NAME_INDEX],
            inline=True,
        )
        await ctx.send(embed=embed)
        await ctx.send(
            f"http://tinyurl.com/tfpeast2aws - connect {logins['east2']['server_ip']}:27015; password letsplay!"
        )
        # Remove players from queue
        dm_queue.clear()

    @commands.command(pass_context=True)
    @commands.has_role(v["tfc"])
    @commands.check(check_message_channel)
    async def check1v1game(self, ctx, match_id):
        if match_id is None:
            await ctx.send("You must enter a match_id number to look up from database!")
        db = mysql.connector.connect(
            host=logins["mysql"]["host"],
            user=logins["mysql"]["user"],
            passwd=logins["mysql"]["passwd"],
            database=logins["mysql"]["database"],
            autocommit=True,
        )
        cursor = db.cursor(dictionary=True)

        # Check if match is in active 1v1s, otherwise fall-back to database to look up
        with open("active_1v1_matches.json", "r") as f:
            active_1v1_matches = json.load(f)
        if active_1v1_matches.get(match_id) is not None:
            blue_team = active_1v1_matches[match_id]["blue_team"]
            red_team = active_1v1_matches[match_id]["red_team"]
            match_outcome_string = "Active Game (unreported!)"
        else:
            cursor.execute(
                "SELECT * FROM matches WHERE match_id = %s and deleted_at is NULL",
                [match_id],
            )
            query_output = cursor.fetchall()
            if len(query_output) < 1:
                await ctx.send(
                    f"Could not find match with ID {match_id}, check for typos"
                )
                return
            match_row = query_output[0]
            blue_team = match_row["blue_team"]
            red_team = match_row["red_team"]
            match_outcome_string = "Winner - Team " + str(match_row["match_outcome"])

        embed = discord.Embed(
            title=f"Game Number - {match_id} - Outcome - {match_outcome_string}"
        )
        embed.add_field(
            name="Blue Team " + v["t1img"],
            value=ELOpop[blue_team][PLAYER_MAP_VISUAL_NAME_INDEX],
            inline=True,
        )
        embed.add_field(name="\u200b", value="\u200b")
        embed.add_field(
            name="Red Team " + v["t2img"],
            value=ELOpop[red_team][PLAYER_MAP_VISUAL_NAME_INDEX],
            inline=True,
        )
        await ctx.send(embed=embed)

    @commands.command(pass_context=True)
    @commands.has_role(v["tfc"])
    @commands.check(check_message_channel)
    async def win1v1(self, ctx, winning_team, match_id=None):
        global ELOpop

        db = mysql.connector.connect(
            host=logins["mysql"]["host"],
            user=logins["mysql"]["user"],
            passwd=logins["mysql"]["passwd"],
            database=logins["mysql"]["database"],
            autocommit=True,
        )
        cursor = db.cursor()

        with open("active_1v1_matches.json", "r") as f:
            active_1v1_matches = json.load(f)
        with open("ELOpop.json") as f:
            ELOpop = json.load(f)

        if match_id is None:
            reported_match_id = list(active_1v1_matches)[-1]
        else:
            reported_match_id = match_id

        # TODO: Check if one of the players was the one who called this function, bot, or runner
        if winning_team == "1":
            ELOpop[active_1v1_matches[reported_match_id]["blue_team"]][
                PLAYER_MAP_DM_WIN_INDEX
            ] += 1
            ELOpop[active_1v1_matches[reported_match_id]["red_team"]][
                PLAYER_MAP_DM_LOSS_INDEX
            ] += 1
        elif winning_team == "2":
            ELOpop[active_1v1_matches[reported_match_id]["red_team"]][
                PLAYER_MAP_DM_WIN_INDEX
            ] += 1
            ELOpop[active_1v1_matches[reported_match_id]["blue_team"]][
                PLAYER_MAP_DM_LOSS_INDEX
            ] += 1
        else:
            await ctx.send("Incorrect usage of win1v1 detected, bailing out.")
            return
        current_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        if active_1v1_matches[reported_match_id]["deleted_at"] is None:
            sql = "UPDATE matches SET match_outcome = %s, updated_at = %s WHERE match_id = %s"
        else:
            sql = "UPDATE matches SET match_outcome = %s, updated_at = %s, deleted_at = NULL WHERE match_id = %s"
        cursor.execute(sql, (winning_team, current_timestamp, reported_match_id))

        del active_1v1_matches[reported_match_id]
        with open("active_1v1_matches.json", "w") as f:
            json.dump(active_1v1_matches, f, indent=4)
        with open("ELOpop.json", "w") as cd:
            json.dump(ELOpop, cd, indent=4)

        await ctx.send(
            f"Match {reported_match_id} reported with winning side {winning_team}"
        )

    @commands.command(pass_context=True)
    @commands.has_role(v["runner"])
    @commands.check(check_message_channel)
    async def undo1v1(self, ctx, match_id=None):
        if match_id is None:
            await ctx.send("Need to set a match id value to undo it")
            return
        global ELOpop

        db = mysql.connector.connect(
            host=logins["mysql"]["host"],
            user=logins["mysql"]["user"],
            passwd=logins["mysql"]["passwd"],
            database=logins["mysql"]["database"],
            autocommit=True,
        )
        cursor = db.cursor(dictionary=True)

        with open("active_1v1_matches.json", "r") as f:
            active_1v1_matches = json.load(f)
        with open("ELOpop.json") as f:
            ELOpop = json.load(f)

        # Recreate match to put into active games
        cursor.execute("SELECT * FROM matches WHERE match_id = %s", [match_id])
        match_row = cursor.fetchall()[0]
        # This column is just the primary key from the MySQL db but isn't used
        del match_row["id"]
        active_1v1_matches[match_id] = match_row
        active_1v1_matches[match_id]["created_at"] = active_1v1_matches[match_id][
            "created_at"
        ].strftime("%Y-%m-%d %H:%M:%S")
        active_1v1_matches[match_id]["updated_at"] = active_1v1_matches[match_id][
            "updated_at"
        ].strftime("%Y-%m-%d %H:%M:%S")
        active_1v1_matches[match_id]["deleted_at"] = active_1v1_matches[match_id][
            "deleted_at"
        ].strftime("%Y-%m-%d %H:%M:%S")
        with open("active_1v1_matches.json", "w") as f:
            json.dump(active_1v1_matches, f, indent=4)
        current_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        sql = "UPDATE matches SET updated_at = %s, deleted_at = %s WHERE match_id = %s"
        logging.info(sql)
        logging.info((current_timestamp, current_timestamp, match_id))
        cursor.execute(
            sql,
            (current_timestamp, current_timestamp, match_id),
        )
        await ctx.send(f"Match {match_id} un-reported.")

    # TODO: 1v1 Stats, can be called by anyone
    @commands.command(aliases=["stats1v"], pass_context=True)
    @commands.has_role(v["tfc"])
    @commands.check(check_message_channel)
    async def stats1v1(self, ctx):
        ftp = FTP(logins["east2"]["server_ip"])
        ftp.login(
            user=logins["east2"]["ftp_username"],
            passwd=logins["east2"]["ftp_password"],
        )
        ftp.cwd("logs")

        hampalyzer_output = self.stat_log_file_handler(ftp, "east2")
        await ctx.send(f"Hampalyzer Stats: {hampalyzer_output}")

    # TODO: Leaderboard, can be called by anyone
    @commands.command(pass_context=True)
    @commands.has_role(v["tfc"])
    @commands.check(check_message_channel)
    async def leaderboard(self, ctx):
        db = mysql.connector.connect(
            host=logins["mysql"]["host"],
            user=logins["mysql"]["user"],
            passwd=logins["mysql"]["passwd"],
            database=logins["mysql"]["database"],
            autocommit=True,
        )
        cursor = db.cursor(dictionary=True)

        # TODO: Reported matches should update players table


async def setup(bot):
    await bot.add_cog(DMCommandsCog(bot))
