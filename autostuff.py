import discord
from discord.ext import commands
import json
from ftplib import FTP
import os
import traceback
import zipfile
import mysql.connector
import logging

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

intents = discord.Intents.all()
client = commands.Bot(
    command_prefix=["!", "+", "-"], case_insensitive=True, intents=intents
)
DEV_TESTING_CHANNEL = 1139762727275995166


with open("ELOpop.json") as f:
    ELOpop = json.load(f)
with open("variables.json") as f:
    v = json.load(f)


def pruneDict(dictk):
    for i in list(dictk):
        if i != "totalgame":
            if dictk["totalgame"] != 0:
                percent = dictk[i][0] / dictk["totalgame"] * 100
            else:
                percent = 0
            if percent < 5.0:
                # print(i)
                del dictk[i]
    return dictk


def newRank(ID):
    global ELOpop

    if len(ELOpop[ID][2]) > 9:
        if ELOpop[ID][1] < 240:  # 1
            ELOpop[ID][3] = v["rank1"]
        if ELOpop[ID][1] >= 240:  # 2
            ELOpop[ID][3] = v["rank2"]
        if ELOpop[ID][1] > 720:  # 3
            ELOpop[ID][3] = v["rank3"]
        if ELOpop[ID][1] > 960:  # 4
            ELOpop[ID][3] = v["rank4"]
        if ELOpop[ID][1] > 1200:  # 5
            ELOpop[ID][3] = v["rank5"]
        if ELOpop[ID][1] > 1440:  # 6
            ELOpop[ID][3] = v["rank6"]
        if ELOpop[ID][1] > 1680:  # 7
            ELOpop[ID][3] = v["rank7"]
        if ELOpop[ID][1] > 1920:  # 8
            ELOpop[ID][3] = v["rank8"]
        if ELOpop[ID][1] > 2160:  # 9
            ELOpop[ID][3] = v["rank9"]
        if ELOpop[ID][1] > 2300:  # 10
            ELOpop[ID][3] = v["rank10"]
        if ELOpop[ID][1] > 2600:  # 10
            ELOpop[ID][3] = v["rankS"]

    with open("ELOpop.json", "w") as cd:
        json.dump(ELOpop, cd, indent=4)


def simplifyDict(dictfrom, idx, pergame="No"):
    newDict = {}
    for i in list(dictfrom):
        if i != "totalgame":
            if pergame == "No":
                newDict[i] = dictfrom[i][idx]
            else:
                if dictfrom[i][0] != 0:
                    newDict[i] = round(dictfrom[i][idx] / dictfrom[i][0], 2)
                else:
                    newDict[i] = 0
    return newDict


def find(haystack, needle, n):
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start + len(needle))
        n -= 1
    return start


def stat_log_file_handler(ftp, region):
    # Note: We are taking a dependency on newer logs having a higher ascending name
    logListNameAsc = ftp.nlst()  # Get list of logs sorted in ascending order by name.
    logListNameDesc = reversed(
        logListNameAsc
    )  # We want to evaluate most recent first for efficiency, so reverse it

    lastTwoBigLogList = []
    for logFile in logListNameDesc:
        size = ftp.size(logFile)
        # Do a simple heuristic check to see if this is a "real" round.  TODO: maybe use a smarter heuristic
        # if we find any edge cases.
        if (size > 100000) and (
            ".log" in logFile
        ):  # Rounds with logs of players and time will be big
            print("passed heuristic!")
            lastTwoBigLogList.append(logFile)
            if len(lastTwoBigLogList) >= 2:
                break

    logToParse1 = lastTwoBigLogList[1]
    logToParse2 = lastTwoBigLogList[0]

    try:
        ftp.retrbinary("RETR " + logToParse1, open(logToParse1, "wb").write)
        ftp.retrbinary("RETR " + logToParse2, open(logToParse2, "wb").write)
    except Exception:
        logging.warning(f"Issue Downloading logfiles from FTP - {Exception}")

    os.rename(logToParse1, f"{logToParse1[0:-4]}-coach{region}.log")
    os.rename(logToParse2, f"{logToParse2[0:-4]}-coach{region}.log")

    logToParse1 = f"{logToParse1[0:-4]}-coach{region}.log"
    logToParse2 = f"{logToParse2[0:-4]}-coach{region}.log"
    f = open(logToParse1)
    pickup_date = None
    pickup_map = None
    for line in f:
        if "Loading map" in line:
            mapstart = line.find('map "') + 5
            mapend = line.find('"', mapstart)
            datestart = line.find("L ") + 2
            dateend = line.find("-", datestart)
            pickup_date = line[datestart:dateend]
            pickup_map = line[mapstart:mapend]
    blarghalyzer_fallback = None
    hampalyzer_output = None
    newCMD = (
        "curl -X POST -F force=on -F logs[]=@"
        + logToParse1
        + " -F logs[]=@"
        + logToParse2
        + " http://app.hampalyzer.com/api/parseGame"
    )
    output3 = os.popen(newCMD).read()
    if "nginx" not in output3 or output3 is None:
        hampalyzer_output = "http://app.hampalyzer.com/" + output3[21:-3]
    else:
        # newCMD = 'curl --connection-timeout 10 -v -F "process=true" -F "inptImage=@' + logToParse1 + '" -F "language=en" -F "blarghalyze=Blarghalyze!" http://blarghalyzer.com/Blarghalyzer.php'
        newCMD = (
            'curl -v -m 5 -F "process=true" -F "inptImage=@'
            + logToParse1
            + '" -F "language=en" -F "blarghalyze=Blarghalyze!" http://blarghalyzer.com/Blarghalyzer.php'
        )
        output = os.popen(newCMD).read()
        # newCMD = 'curl --connection-timeout 10 -v -F "process=true" -F "inptImage=@' + logToParse2 + '" -F "language=en" -F "blarghalyze=Blarghalyze!" http://blarghalyzer.com/Blarghalyzer.php'
        newCMD = (
            'curl -v -m 5 -F "process=true" -F "inptImage=@'
            + logToParse2
            + '" -F "language=en" -F "blarghalyze=Blarghalyze!" http://blarghalyzer.com/Blarghalyzer.php'
        )
        output2 = os.popen(newCMD).read()
        blarghalyzer_fallback = (
            "**Round 1:** https://blarghalyzer.com/parsedlogs/"
            + logToParse1[:-4].lower()
            + "/ **Round 2:** https://blarghalyzer.com/parsedlogs/"
            + logToParse2[:-4].lower()
            + "/"
        )

    os.remove(logToParse1)
    os.remove(logToParse2)
    return pickup_date, pickup_map, hampalyzer_output, blarghalyzer_fallback


def hltv_file_handler(ftp, pickup_date, pickup_map):
    try:
        output_filename = None
        # getting lists
        HLTVListNameAsc = (
            ftp.nlst()
        )  # Get list of demos sorted in ascending order by name.
        HLTVListNameDesc = list(reversed(HLTVListNameAsc))
        lastTwoBigHLTVList = []
        for HLTVFile in HLTVListNameDesc:
            size = ftp.size(HLTVFile)
            # Do a simple heuristic check to see if this is a "real" round.  TODO: maybe use a smarter heuristic
            # if we find any edge cases.
            if (size > 11000000) and (
                ".dem" in HLTVFile
            ):  # Rounds with logs of players and time will be big
                print("passed heuristic!")
                lastTwoBigHLTVList.append(HLTVFile)
                if len(lastTwoBigHLTVList) >= 2:
                    break

        if len(lastTwoBigHLTVList) >= 2:
            HLTVToZip1 = lastTwoBigHLTVList[1]
            HLTVToZip2 = lastTwoBigHLTVList[0]

            # zip file stuff.. get rid of slashes so we dont error.
            formatted_date = pickup_date.replace("/", "")
            ftp.retrbinary("RETR " + HLTVToZip1, open(HLTVToZip1, "wb").write)
            ftp.retrbinary("RETR " + HLTVToZip2, open(HLTVToZip2, "wb").write)
            try:
                mode = zipfile.ZIP_DEFLATED
            except:
                mode = zipfile.ZIP_STORED
            output_filename = pickup_map + "-" + formatted_date + ".zip"
            zip = zipfile.ZipFile(output_filename, "w", mode)
            zip.write(HLTVToZip1)
            zip.write(HLTVToZip2)
            zip.close()
            os.remove(HLTVToZip1)
            os.remove(HLTVToZip2)
        return output_filename
    except Exception as e:
        logging.warning(traceback.format_exc())
        logging.warning(f"error here. {e}")
        return None


@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def stats(
    ctx, region=None, match_number=None, winning_score=None, losing_score=None
):
    with open("login.json") as f:
        logins = json.load(f)
    schannel = await client.fetch_channel(
        1000847501194174675
    )  # 1000847501194174675 original channelID
    region_formatted = region.lower()
    output_zipfile = None
    if region_formatted == "none" or region_formatted is None:
        await ctx.send("please specify region..")
    elif region_formatted in ("east", "east2", "eu", "central", "west", "southeast"):
        try:
            ftp = FTP(logins[region_formatted]["server_ip"])
            ftp.login(
                user=logins[region_formatted]["ftp_username"],
                passwd=logins[region_formatted]["ftp_password"],
            )
            ftp.cwd("logs")

            pickup_date, pickup_map, hampalyzer_output, blarghalyzer_fallback = (
                stat_log_file_handler(ftp, region)
            )
            ftp.cwd("..")
            ftp.cwd(f"HLTV{region.upper()}")
            output_zipfile = hltv_file_handler(ftp, pickup_date, pickup_map)

            if hampalyzer_output is not None:
                if output_zipfile is None:
                    await schannel.send(
                        f"**Hampalyzer:** {hampalyzer_output} {pickup_map} {pickup_date} {region} {match_number} {winning_score} {losing_score}"
                    )
                elif output_zipfile is not None:
                    await schannel.send(
                        file=discord.File(output_zipfile),
                        content=f"**Hampalyzer:** {hampalyzer_output} {pickup_map} {pickup_date} {region} {match_number} {winning_score} {losing_score}",
                    )
                    os.remove(output_zipfile)
            else:
                if output_zipfile is None:
                    await schannel.send(
                        f"**Blarghalyzer:** {blarghalyzer_fallback} {pickup_map} {pickup_date} {region} {match_number} {winning_score} {losing_score}"
                    )
                elif output_zipfile is not None:
                    await schannel.send(
                        file=discord.File(output_zipfile),
                        content=f"**Blarghalyzer:** {blarghalyzer_fallback} {pickup_map} {pickup_date} {region} {match_number} {winning_score} {losing_score}",
                    )
                    os.remove(output_zipfile)

            ftp.close()
        except ZeroDivisionError:
            print(traceback.format_exc())


@client.command(pass_context=True)
@commands.has_role(v["runner"])
async def bwin(ctx, team, pNumber="None"):
    global ELOpop
    dev_channel = await client.fetch_channel(DEV_TESTING_CHANNEL)
    with open("login.json") as f:
        logins = json.load(f)
    db = mysql.connector.connect(
        host=logins["mysql"]["host"],
        user=logins["mysql"]["user"],
        passwd=logins["mysql"]["passwd"],
        database=logins["mysql"]["database"],
    )

    mycursor = db.cursor()
    if (
        (ctx.name == v["pc"])
        or (ctx.name == "tfc-admins")
        or (ctx.name == "tfc-runners")
    ):
        with open("activePickups.json") as f:
            activePickups = json.load(f)
        with open("ELOpop.json") as f:
            ELOpop = json.load(f)
        with open("pastten.json") as f:
            pastTen = json.load(f)
        if pNumber == "None":
            pNumber = list(activePickups)[0]

        # print(activePickups[pNumber][2])
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
            print("giving double ELO")
        for i in blueTeam:
            ELOpop[i][1] += adjustTeam1
            # if(int(ELOpop[i][1]) > 2599):
            # ELOpop[i][1] = 2599
            if int(ELOpop[i][1]) < 0:
                ELOpop[i][1] = 0
            # ELOpop[i][2].append([int(ELOpop[i][1]), pNumber])
            try:
                input_query = f"AUTO REPORT: INSERT INTO player_elo (match_id, player_name, player_elos, discord_id) VALUES ({pNumber}, {ELOpop[i][0]}, {ELOpop[i][1]}, {int(i)})"
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
            # print(ELOpop[i][2])
        for i in redTeam:
            # print(type(ELOpop[i][1]))
            # print(ELOpop)
            ELOpop[i][1] += adjustTeam2
            # if(int(ELOpop[i][1]) > 2599):
            # ELOpop[i][1] = 2599
            if int(ELOpop[i][1]) < 0:
                ELOpop[i][1] = 0
            # ELOpop[i][2].append([int(ELOpop[i][1]), pNumber])
            try:
                input_query = f"AUTO REPORT: INSERT INTO player_elo (match_id, player_name, player_elos, discord_id) VALUES ({pNumber}, {ELOpop[i][0]}, {ELOpop[i][1]}, {int(i)})"
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
                print(i)
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

        await ctx.send("**AUTO-REPORTING** CONFIRMED")


@client.event
async def on_message(message):
    channel = await client.fetch_channel(v["pID"])
    if (
        message.content == "!draw"
        or message.content == "!win 1"
        or message.content == "!win 2"
    ):
        user = await client.fetch_user(message.author.id)
        if user.bot:
            if "!draw" in message.content:
                await bwin(channel, "draw")
            if "!win 1" in message.content:
                await bwin(channel, "1")
            if "!win 2" in message.content:
                await bwin(channel, "2")
    if "!stats" in message.content:
        user = await client.fetch_user(message.author.id)
        if user.bot:
            #!stats {region.lower()} {reported_match} {winningScore} {losingScore}
            split_message = str(message.content).split(" ")

            l = len(split_message)
            print("len: " + str(l))
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

            # content = str(message.content)
            # content = content[7:]
            await stats(channel, region, match_number, winning_score, losing_score)

    await client.process_commands(message)


# resetlb()
client.run(v["TOKEN"])
# client.run('NzMyMzcyMTcwMzY5NTMxOTc4.GPL0pm.iRN9voORDs1haOXvmlhZu26tWOtS-e7Xpmf7LM')
