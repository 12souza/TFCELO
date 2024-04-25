import json
import discord
from pathlib import Path
from discord.ext import commands
from discord.utils import get

"""Players can add to 1v1 queue via !add1v1 in this channel, game will start when either both players thumbs up react the game message or a runner does !start1v1 - this creates a 1v1 match with a game number
Server will be the old east 2 (which will also be the conc server at some point in the future) - I'll rename it later
I am thinking of adding a 1v1 plugin that will detect whoever gets first to 50 kills (or whatever number we think of later) as the win condition
Match will get auto-reported if this is implemented, otherwise either player can report the game (which can be undone by a runner/admin if necessary) via !win1v1 (game number optional)
Ladder rankings will just be based purely off of wins, but wins and losses will be tracked. """

DM_CHANNEL_ID = 1230852204567597186
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

    def addplayerImpl(self, playerID, playerDisplayName):
        global dm_queue
        global ELOpop

        if len(dm_queue) <= 2:
            if playerID not in dm_queue:
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

        if len(dm_queue) < 2:
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
    async def remove1v1(self, ctx):
        if ctx.channel.id == DM_CHANNEL_ID:
            playerID = str(ctx.author.id)
            await self.removePlayerImpl(ctx, playerID)

    @commands.command(pass_context=True)
    @commands.has_role(v["tfc"])
    async def add1v1(self, ctx):
        global dm_queue
        if ctx.channel.id == DM_CHANNEL_ID:
            playerID = str(ctx.author.id)
            playerDisplayName = ctx.author.display_name

            retVal = self.addplayerImpl(playerID, playerDisplayName)
            if retVal == 1:  # Already added
                await ctx.send(
                    f"{ctx.author.display_name} - you are already added to the 1v1 queue"
                )
            if retVal == 0:  # Successfully added
                await self.show_dm_pickup(ctx)

    async def on_message(self, message):
        print(message.content)


async def setup(bot):
    await bot.add_cog(DMCommandsCog(bot))
