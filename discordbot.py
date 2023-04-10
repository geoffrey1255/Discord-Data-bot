import discord
import requests
import json
import glob
import os.path
import shutil
import random
import re
import math
import os
import time


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from openpyxl import load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from tabulate import tabulate
from dotenv import load_dotenv, find_dotenv
from collections import OrderedDict

from discord.ext import commands
from requests_html import HTMLSession
import requests
from bs4 import BeautifulSoup

from datetime import datetime, date

import mysql.connector

load_dotenv(find_dotenv())



client = commands.Bot(command_prefix = "-")
spd = {'3': 477, '4':358, '5':286, '6':239, '7':205, '8':179}

# with open("Pies-29550280.json", 'r', encoding='utf=8') as json_file:
#     json_load = json.load(json_file)
#     for i in json_load["unit_list"]:
#         print(i)
# "wizard_info"
# "wizard_id"
# "wizard_name"

comm = {
    "-stats": "Displays current winrate and remaining attacks for each guild",
    "-match": "Displays winrate of our guild members from highest to lowest",
    "-record": "excel file of each siege match",    
    "-completed": "Use this command immediately after the siege match has concluded",
    "-add": "'[3 unit defence]' '[3 unit offence]' '[description]'",
    "-counter": "[Unit 1] [Unit 2] [Unit 3]",
    "-tick": "[base spd] [additional spd] [desired spd tick] [leave blank if no lead]",
    "-register": "[summoners_name]",
    "-player": "[summoners_name]",
    "-player_vs": "[summoners_name] [enemy_guild]",
    "-player_season": "[summoners_name] [season_number]",
    "-history": "[season_number]",
    "updatepmonster" : "Updates monster database"
    }
# change back to with open("siege.json", 'r', encoding='utf=8') as json_file: later
def grabjson():
    folder_path = os.environ.get("YOUR_FOLDER_PATH")
    file_type = '\SiegeMatch*json'
    files = glob.glob(folder_path + file_type)
    max_file = max(files, key=os.path.getctime)
    target = os.environ.get("YOUR_TARGET")
    shutil.copyfile(max_file, target)
    # with open("SiegeMatch-to-test-with.json", 'r', encoding='utf=8')
    with open("siege.json", 'r', encoding='utf=8') as json_file:
        json_load = json.load(json_file)
    return json_load


def helper():       
    data = grabjson()


    guild_list = pd.json_normalize(data['matchup_info'], record_path =['guild_list'])
    match_info = pd.DataFrame.from_dict(data['matchup_info']['match_info'],orient='index').transpose()
    wizard_info_list = pd.json_normalize(data['matchup_info'], record_path =['wizard_info_list'])
    attack_log_battle_log_list = pd.json_normalize(data['attack_log']['log_list'], record_path =['battle_log_list'])
    defense_log_battle_log_list = pd.json_normalize(data['defense_log']['log_list'], record_path =['battle_log_list'])
    current_attack_log = attack_log_battle_log_list.merge(match_info, how="inner",on=['match_id','siege_id'])
    current_defense_log = defense_log_battle_log_list.merge(match_info, how="inner",on=['match_id','siege_id'])
    print(guild_list)

        
    attack_stats_temp = current_attack_log.groupby(['wizard_name','win_lose']).size().reset_index(name='counts')
    attack_stats_by_wizard = attack_stats_temp.pivot(index='wizard_name', columns='win_lose', values='counts').rename_axis(None,axis=1).reset_index()
    attack_stats_by_wizard = attack_stats_by_wizard.rename(columns={'wizard_name': 'name',1:'win',2:'lose'})

    attack_stats_by_wizard = attack_stats_by_wizard.fillna(0)
    attack_stats_by_wizard['winrate'] = round(attack_stats_by_wizard['win']/ (attack_stats_by_wizard['win'] + attack_stats_by_wizard['lose'])*100)

    defense_stats_temp = current_defense_log.groupby(['wizard_name','win_lose']).size().reset_index(name='counts')
    defense_stats_by_wizard = defense_stats_temp.pivot(index='wizard_name', columns='win_lose', values='counts').rename_axis(None,axis=1).reset_index()
    defense_stats_by_wizard = defense_stats_by_wizard.rename(columns={'wizard_name': 'name',1:'defense_win', 2: 'defense_lose'})

    defense_stats_by_wizard = defense_stats_by_wizard.fillna(0)
    defense_stats_by_wizard['defense_winrate'] = round(defense_stats_by_wizard['defense_win']/ (defense_stats_by_wizard['defense_win'] + defense_stats_by_wizard['defense_lose'])*100)

    merged_table = pd.merge(attack_stats_by_wizard, defense_stats_by_wizard, on='name', how='left')
    merged_table = merged_table.fillna(0)
    print(merged_table)

    return merged_table


def getguildexcel():
    json_load = grabjson()
    guild_list = ""
    for i in json_load["matchup_info"]["guild_list"]:
        if i["guild_name"] != "Hurt":
            guild_list += str(i["guild_name"]) + "   "
    guild_list = re.sub("[\/:*?!]", "", guild_list)
    return guild_list

def getguildsql():
    json_load = grabjson()
    guild_list = []
    for i in json_load["matchup_info"]["guild_list"]:
        if i["guild_name"] != "Hurt":
            guild_list.append(i["guild_name"])
    print(guild_list)
    return guild_list

def getplacement():
    json_load = grabjson()
    guild_list = getguildsql()
    placement = {}
    for i in range(3):
        placement[json_load["attack_log"]["log_list"][0]["guild_info_list"][i]["guild_name"]] = json_load["attack_log"]["log_list"][0]["guild_info_list"][i]["match_score"]
    print(placement["Hurt"]) 
    if placement["Hurt"] > placement[guild_list[0]] and placement["Hurt"] > placement[guild_list[1]]:
        return "First"
    elif placement["Hurt"] < placement[guild_list[0]] and placement["Hurt"] < placement[guild_list[1]]:
        return "Third"
    else:
        return "Second"

def member(message):
    disc_id = str(message)
    try:
        
        sql_db = mysql.connector.connect(
            host=os.getenv('YOUR_HOST'),
            user=os.getenv('YOUR_USER'),
            passwd=os.getenv('YOUR_PASSWD'),
            database=os.getenv('YOUR_DATABASE')
            )

        sql_cursor = sql_db.cursor()

        sql_cursor.callproc('checkPlayer', [disc_id])
        for result in sql_cursor.stored_results():
            sql_return = result.fetchall()

        if len(sql_return) == 0:
            return 0
        else:
            return 1
    except mysql.connector.Error as e:
        print("Error occurred while connecting to MySQL database: ", e)
    finally:
        sql_cursor.close()
        sql_db.close()



@client.event
async def on_ready():
    print("now online")

@client.command()
async def commands(message):
    command_list = pd.DataFrame(list(comm.values()), index=comm)

    headers = ["Commands", "Description"]
    await message.send("```{}```".format(tabulate(command_list, headers, tablefmt="github", maxcolwidths=[None, 75])))

    
@client.command()
async def tick(message, arg1=None, arg2=None, arg3=None, arg4=None):
    arg1 = float(arg1)
    arg2 = float(arg2)
    arg3 = int(arg3)

    if arg4 == None:
        total = math.ceil((arg1 * 0.15) + arg1 + arg2)
        if total > spd.get(str(arg3)):
            await message.send("```Your total spd is: {}, you have {} more than {} tick, with no spd leader```".format(total, total - spd.get(str(arg3)), arg3))
        else:
            await message.send("```Your total spd is: {}, you need {} spd to reach {} tick, with no spd leader```".format(total, spd.get(str(arg3)) - total, arg3))
    else:
        total = math.ceil((arg1 * 0.15) + arg1 + arg2 + (float(arg1) * float(arg4) * 0.01))
        if total > spd.get(str(arg3)):
            await message.send("```Your total spd is: {}, you have {} more than {} tick, with {}% spd leader```".format(total, total - spd.get(str(arg3)), arg3, arg4))
        else:
            await message.send("```Your total spd is: {}, you need {} spd to reach {} tick, with {}% spd leader```".format(total, spd.get(str(arg3)) - total, arg3, arg4))     

    

@client.command()
async def match(message):
    if message.channel.id != int(os.getenv('YOUR_SIEGE_CHANNEL')):
        await message.send("```this command does not work in this text channel```")
        return 0
    attack_stats_by_wizard = helper()

    attack_stats_by_wizard.sort_values(by=['winrate'])
    sign = []
    start = 0
    end = 0

    # print(attack_stats_by_wizard)
    attack_stats_by_wizard = attack_stats_by_wizard.set_index("name")
    # print(attack_stats_by_wizard)
    attack_stats_by_wizard = attack_stats_by_wizard.sort_values(by=['winrate', 'win'], ascending = [False, False])
    print(attack_stats_by_wizard)
    for index, i in enumerate(attack_stats_by_wizard.values):
        print(index, i)
        temp = list(i)
        print(type(i))
        
        if temp[2] < 80.0 and end == 0:
            print(type(attack_stats_by_wizard.index[index]))
            print(attack_stats_by_wizard.index[index])
            sign.append("\u001b[0;40m\u001b[1;31m" + attack_stats_by_wizard.index[index])
            # sign.append("test" + attack_stats_by_wizard.index[index])
            # sign.append("\u001b[0;40m\u001b[1;31m")
            print("test")             
            end = 1
            
            print(sign[index])
        elif temp[2] > 80.0 and start == 0:
            sign.append("\u001b[0;40m\u001b[1;34m" + attack_stats_by_wizard.index[index])
            # sign.append("test" + attack_stats_by_wizard.index[index])
            # sign.append("\u001b[0;40m\u001b[1;34m")
            start = 1

            print("test")
            print(sign[index])
        else:
            sign.append(attack_stats_by_wizard.index[index])
            # sign.append("")
            print(sign[index])

    
    print(attack_stats_by_wizard.values[0])
    print(attack_stats_by_wizard)
    attack_stats_by_wizard = attack_stats_by_wizard.set_index(pd.Index(sign))
    attack_stats_by_wizard = attack_stats_by_wizard.drop(['defense_lose', 'defense_winrate'], axis =1)
    print(attack_stats_by_wizard)
    await message.send("```ansi\n{}```".format(attack_stats_by_wizard))


@client.command()
async def completed(message):
    if message.channel.id != int(os.getenv('YOUR_SIEGE_CHANNEL')):
        await message.send("```this command does not work in this text channel```")
        return 0
    attack_stats_by_wizard = helper()
    guilds_name = getguildexcel()

    
    ExcelWorkbook = load_workbook('siege_records11.xlsx')
    writer = pd.ExcelWriter('siege_records12.xlsx', if_sheet_exists="replace", engine = 'openpyxl', mode='a')
    writer.book = ExcelWorkbook
    writer.sheets = dict((ws.title, ws) for ws in ExcelWorkbook.worksheets)
    attack_stats_by_wizard.to_excel(writer, sheet_name=str(guilds_name))
##        guild_stats.to_excel(writer, startcol=0, startrow=30, sheet_name=str(guilds_name))
    writer.save()
    
    print(guilds_name)

    await message.send("```Match has been recorded!```")

# @client.command()
def complete():
    attack_stats_by_wizard = helper()
    guilds_name = getguildsql()
    attack_stats_by_wizard["Enemy_Guild_One"] = guilds_name[0]
    attack_stats_by_wizard["Enemy_Guild_Two"] = guilds_name[1]
    attack_stats_by_wizard["Placement"] = getplacement()
    attack_stats_by_wizard["Season"] = 11
    attack_stats_by_wizard["Date"] = date.today()
    print(attack_stats_by_wizard)
    # message.send("```Match has been recorded!```")


@client.command()
async def record(message):
    await message.send(file=discord.File("siege_records12.xlsx"))
    #make option to search past records, keep in separate folder

@client.command()
async def stats(message):
    if message.channel.id != int(os.getenv('YOUR_SIEGE_CHANNEL')):
        await message.send("```this command does not work in this text channel```")
        return 0
    siege_atk = {}
    siege_winrate = {}
    win = {}
    loss = {}
    total = {}
    json_load = grabjson()
    teams = []


    for line in json_load["matchup_info"]["guild_list"]:
        siege_atk[line.get("guild_name")] = 250-line.get("attack_count")
        if "guild_id" in line:
            siege_winrate[line["guild_name"]] = 0
            win[line["guild_name"]] = 0
            loss[line["guild_name"]] = 0
            total[line["guild_name"]] = 0
            if "Hurt" not in line["guild_name"]:
                teams.append(line["guild_name"])

    for line in json_load["attack_log"]["log_list"][0]["battle_log_list"]:
        if line["win_lose"] == 1:
            win["Hurt"] += 1
        else:
            loss["Hurt"] += 1
        total["Hurt"] += 1
        siege_winrate["Hurt"] = round((win["Hurt"]/total["Hurt"]*100),2)


    for line in json_load["defense_log"]["log_list"][0]["battle_log_list"]:
        if teams[0] in line["opp_guild_name"]:
            if line["win_lose"] == 1:
                loss[teams[0]] += 1
            else:
                win[teams[0]] += 1
            total[teams[0]] += 1

            siege_winrate[line["opp_guild_name"]] = round((1 - loss[teams[0]]/total[teams[0]])*100,2)

        if teams[1] in line["opp_guild_name"]:
            if line["win_lose"] == 1:
                loss[teams[1]] += 1
            else:
                win[teams[1]] += 1
            total[teams[1]] += 1
            siege_winrate[line["opp_guild_name"]] = round((1 - loss[teams[1]]/total[teams[1]])*100,2)

    print(teams)
    print(total)
    print(win)
    print(loss)
    print(siege_winrate)
    print(siege_atk)

    title = [""]
    wins = pd.DataFrame(list(win.values()), index=siege_winrate, columns=title)
    losses = pd.DataFrame(list(loss.values()), index=siege_winrate, columns=title)
    totals = pd.DataFrame(list(total.values()), index=siege_winrate, columns=title)
    atks = pd.DataFrame(list(siege_atk.values()), index=siege_winrate, columns=title)

    winrate = pd.DataFrame(list(siege_winrate.values()), index=siege_winrate, columns=title)
    result = {}

    for i in siege_atk.keys():
        print(i)
        print(total[i])
        print(siege_atk[i])
        if siege_atk[i] == 250:
            result[i] = 0
        else:
            result[i] =  round((total[i] / (250 - siege_atk[i])*100),2)

    used = pd.DataFrame(list(result.values()), index = siege_winrate, columns = title)
    print(wins)
    print(losses)
    print(totals)
    print(atks)
    print(winrate)    
    stat = pd.concat([wins, losses, winrate, atks, totals, used], axis=1)
    print(stat)
    stat.columns = ["Wins", "Losses", "Winrate", "Remaining Atks", "Total", "Used On Us"]
    header = ["", "Wins", "Losses", "Winrate", "Remaining Atks", "Total", "Used On Us"]

    await message.send("```{}```".format(tabulate(stat, header, tablefmt ="github")))


@client.command()
async def counter(message, unit_one=None, unit_two=None, unit_three=None):
    if message.channel.id != int(os.getenv('YOUR_CHANNEL_ID')):
        await message.send("```this command does not work in this text channel```")
        return 0
    unit_one = unit_one.lower()
    unit_two = unit_two.lower()
    unit_three = unit_three.lower()
    print(unit_one, unit_two, unit_three)
    if not member(message.author):
        await message.send("```You must be a member of Hurt to use this command```")
        return 0

    if unit_two is not None and unit_three is not None:
        temp = ""
        print("test")
        if unit_two > unit_three:
            unit_two, unit_three = unit_three, unit_two
    else:
        await message.send("```Please enter 3 unit defense```")
        return 0
        
    defense_team = unit_one + " " + unit_two + " " + unit_three
    print(defense_team)
    sql_arg1 = [unit_one, unit_two, unit_three]

    args = [defense_team]
    

    try:
        sql_db = mysql.connector.connect(
            host=os.getenv('YOUR_HOST'),
            user=os.getenv('YOUR_USER'),
            passwd=os.getenv('YOUR_PASSWD'),
            database=os.getenv('YOUR_DATABASE')
            )

        sql_cursor = sql_db.cursor()

        sql_cursor.callproc('getwinlosscombatlog', sql_arg1)

        for result in sql_cursor.stored_results():
            sql_return = result.fetchall()
        print(sql_return)

        sql_cursor.callproc('GetCounter', args)

        for result in sql_cursor.stored_results():
            sql_return = result.fetchall()

        print(sql_return)

        if len(sql_return) == 0:
            await message.send("```There are currently no posted counters for {}```".format(defense_team))
            return 0

        headers = ["Counter", "Kill Order"]
        await message.send("```{}```".format(tabulate(sql_return, headers, showindex=False, maxcolwidths=[None, 70])))

    except mysql.connector.Error as e:
        await message.send("```Error occurred while connecting to MySQL database: {}```", e)

    finally:
        sql_cursor.close()
        sql_db.close()
    
@client.command()
async def add(message, defense_team, offense_team, description):
    if message.channel.id != int(os.getenv('YOUR_CHANNEL_ID')):
        await message.send("```This command does not work in this text channel```")
        return 0

    if not member(message.author):
        await message.send("```You must be a member of Hurt to use this command```")
        return 0

    defense_team = defense_team.lower()
    offense_team = offense_team.lower()
    description = description.lower()

    defense_order = defense_team.split()
    temp = ""

    if defense_order[1] > defense_order[2]:
        temp = defense_order[1]
        defense_order[1] = defense_order[2]
        defense_order[2] = temp
        
        defense_team = " ".join(defense_order)

    offense_order = offense_team.split()
    temp = ""

    if offense_order[1] > offense_order[2]:
        temp = offense_order[1]
        offense_order[1] = offense_order[2]
        offense_order[2] = temp

        offense_team = " ".join(offense_order)

    now=datetime.now()
    dt_string = now.strftime("%Y-%m-%d %H:%M:%S")

    args = [defense_team, offense_team, description, str(message.author), dt_string]
    

    try:
        sql_db = mysql.connector.connect(
            host=os.getenv('YOUR_HOST'),
            user=os.getenv('YOUR_USER'),
            passwd=os.getenv('YOUR_PASSWD'),
            database=os.getenv('YOUR_DATABASE')
            )

        sql_cursor = sql_db.cursor()
        sql_cursor.callproc('checkCounter', [defense_team, offense_team])

        for result in sql_cursor.stored_results():
            sql_return = result.fetchall()
            
        if len(sql_return) == 0:
            sql_cursor.callproc('inputCounter', args)
            sql_db.commit()
            await message.send("```{} Has been added to the list of counters for {}```".format(offense_team, defense_team))
        else:
            await message.send("```{} already exists as a counter for the defence {}```".format(offense_team, defense_team))
            return 0
        
    except mysql.connector.Error as e:
        await message.send("```Error occurred while connecting to MySQL database: {}```", e)

    finally:
        sql_cursor.close()
        sql_db.close()

#maybe something you can do here check logic in the morning
@client.command()
async def register(message, summoners_id=None, reg_date = date.today()):
    if message.channel.id != int(os.getenv('YOUR_REGISTER_CHANNEL')):
        await message.send("```this command does not work in this text channel```")
        return 0

    print(message.author, message.author.display_name, summoners_id)

    disc_id = str(message.author)
    disc_display_name = message.author.display_name

    try:
        sql_db = mysql.connector.connect(
            host=os.getenv('YOUR_HOST'),
            user=os.getenv('YOUR_USER'),
            passwd=os.getenv('YOUR_PASSWD'),
            database=os.getenv('YOUR_DATABASE')
            )
        sql_cursor = sql_db.cursor()

        folder_path = os.getenv('YOUR_FOLDER_PATH')
        file_name = os.getenv('YOUR_JSON_FILE')
        file_path = os.path.join(folder_path,file_name)

        with open(file_path, 'r', encoding='UTF-8') as json_file:
            json_load = json.load(json_file)
            for i in json_load["guild"]["guild_members"]:
                name = json_load["guild"]["guild_members"][i]["wizard_name"]
                id = i
                # print(json_load["guild"]["guild_members"][i]["wizard_name"])

                args = [id, name]
                sql_cursor.callproc('checkplayerregister', args)
                for results in sql_cursor.stored_results():
                    sql_return = results.fetchall()
                # print(sql_return)
                if len(sql_return) == 0:

                    sql_cursor.callproc('addregister', args)
                    print(id, name)
            sql_db.commit()
        
        sql_cursor.callproc('checkregister', [summoners_id])

        for result in sql_cursor.stored_results():
            sql_return = result.fetchall()
        if len(sql_return) == 0:
            await message.send("```{} is not a member of Hurt```".format(summoners_id))
            return 0
        print(sql_return)

        uuid = sql_return[0][0]
        print(uuid)

        args = [disc_id, disc_display_name, reg_date, uuid]

        print(args)

        sql_cursor.callproc('checkdiscordid', [uuid])
        for result in sql_cursor.stored_results():
            sql_return = result.fetchall()

        if sql_return[0][0] == None:
            sql_cursor.callproc('addPlayer', args)
            sql_db.commit()
            
            await message.send("```{} has been added to the player database```".format(disc_display_name))
        else:
            await message.send("```{} is already in the player database```".format(disc_display_name))
            return 0
        
    except mysql.connector.Error as e:
        await message.send("```Error occurred while connecting to MySQL database: {}```", e)

    finally:
        sql_cursor.close()
        sql_db.close()

@client.command()
async def history(message, season=None):
    if message.channel.id != int(os.getenv('YOUR_HISTORY_CHANNEL')):
        await message.send("```this command does not work in this text channel```")
        return 0
    args = [season]

    try:
        sql_db = mysql.connector.connect(
            host=os.getenv('YOUR_HOST'),
            user=os.getenv('YOUR_USER'),
            passwd=os.getenv('YOUR_PASSWD'),
            database=os.getenv('YOUR_DATABASE')
            )

        sql_cursor = sql_db.cursor()

        sql_cursor.callproc('GetSeasonWinrate', args)
        for result in sql_cursor.stored_results():
            sql_return = result.fetchall()

        result = []
        start = 0
        end = 0
        print(sql_return)
        # sorted_list = sorted(sql_return, key=lambda x: (float(x[1].strip('%')), -x[2]), reverse=True)
        sorted_list = sorted(sql_return, key=lambda x: (float(x[1].strip('%')), -float(x[1].strip('%')) if x[1] is not None else 0), reverse=True)

        print(type(sql_return))
        for index, i in enumerate(sorted_list):
            print(i)
            if float(i[1].strip(' \t\n\r%')) < 85.00 and end == 0:
                test = ("\u001b[0;40m\u001b[1;31m", i[0], i[1], i[2])
                result.append(test)
                end = 1
            elif float(i[1].strip(' \t\n\r%')) > 85.00 and start == 0:
                test = ("\u001b[0;40m\u001b[1;34m", i[0], i[1], i[2])
                result.append(test)
                start = 1
            else:
                test = (" ", i[0], i[1], i[2])
                result.append(test)

        print(result)
        headers = [" ", "Summoner", "Winrate", "Season"]
        await message.send("```ansi\n{}```".format(tabulate(result, headers, showindex=False)))
            
    except mysql.connector.Error as e:
        await message.send("```Error occurred while connecting to MySQL database: {}```", e)

    finally:
        sql_cursor.close()
        sql_db.close()

@client.command()
async def active(message, season = None):
    if message.channel.id != int(os.getenv('YOUR_HISTORY_CHANNEL')):
        await message.send("```this command does not work in this text channel```")
        return 0
    args = [season]

    try:
        sql_db = mysql.connector.connect(
            host=os.getenv('YOUR_HOST'),
            user=os.getenv('YOUR_USER'),
            passwd=os.getenv('YOUR_PASSWD'),
            database=os.getenv('YOUR_DATABASE')
            )

        sql_cursor = sql_db.cursor()

        sql_cursor.callproc('GetActiveWinrate', args)
        for result in sql_cursor.stored_results():
            sql_return = result.fetchall()

        result = []
        start = 0
        end = 0
        print(sql_return)
        # sorted_list = sorted(sql_return, key=lambda x: (float(x[1].strip('%')), -x[2]), reverse=True)
        sorted_list = sorted(sql_return, key=lambda x: (float(x[1].strip('%')), -float(x[2].strip('%')) if x[2] is not None else 0), reverse=True)

        print(type(sql_return))
        for index, i in enumerate(sorted_list):
            print(i)
            if float(i[1].strip(' \t\n\r%')) < 85.00 and end == 0:
                test = ("\u001b[0;40m\u001b[1;31m", i[0], i[1], i[2], i[3])
                result.append(test)
                end = 1
            elif float(i[1].strip(' \t\n\r%')) > 85.00 and start == 0:
                test = ("\u001b[0;40m\u001b[1;34m", i[0], i[1], i[2], i[3])
                result.append(test)
                start = 1
            else:
                test = (" ", i[0], i[1], i[2], i[3])
                result.append(test)

        print(result)
        headers = [" ", "Summoner", "Winrate", "Defense_Winrate", "Season"]
        await message.send("```ansi\n{}```".format(tabulate(result, headers, showindex=False)))
            
    except mysql.connector.Error as e:
        await message.send("```Error occurred while connecting to MySQL database: {}```", e)

    finally:
        sql_cursor.close()
        sql_db.close()



@client.command()
async def player(message, user=None):
    if message.channel.id != int(os.getenv('YOUR_HISTORY_CHANNEL')):
        await message.send("```this command does not work in this text channel```")
        return 0
    args = [user]
    print(args)

    try:
        print("testersstart")
        sql_db = mysql.connector.connect(
            host=os.getenv('YOUR_HOST'),
            user=os.getenv('YOUR_USER'),
            passwd=os.getenv('YOUR_PASSWD'),
            database=os.getenv('YOUR_DATABASE')
            )

        sql_cursor = sql_db.cursor()
    
        sql_cursor.callproc('GetUserSiege', args)
        for result in sql_cursor.stored_results():
            sql_return = result.fetchall()
        wins = 0
        loss = 0
        for rows in sql_return:
            wins += rows[0]
            loss += rows[1]
        winrate = (wins / (wins + loss))* 100

        sql_cursor.callproc('GetUserSiege20', args)
        for result in sql_cursor.stored_results():
            sql_return = result.fetchall()

        # print(sql_return)
        headers = ["Wins", "Losses", "Winrate", "Enemy_Guild_One", "Enemy_Guild_Two", "Season"]
        await message.send("```{}```".format(tabulate(sql_return, headers, showindex=False)))
        await message.send("```Your winrate is {}```".format(round(winrate,2)))
                
    except mysql.connector.Error as e:
        await message.send("```Error occurred while connecting to MySQL database: {}```", e)

    finally:
        print("testersfinal")
        sql_cursor.close()
        sql_db.close()

@client.command()
async def player_vs(message, user=None, user_input=None):
    if message.channel.id != int(os.getenv('YOUR_HISTORY_CHANNEL')):
        await message.send("```this command does not work in this text channel```")
        return 0

    args = [user,user_input]

    try:
        sql_db = mysql.connector.connect(
            host=os.getenv('YOUR_HOST'),
            user=os.getenv('YOUR_USER'),
            passwd=os.getenv('YOUR_PASSWD'),
            database=os.getenv('YOUR_DATABASE')
            )

        sql_cursor = sql_db.cursor()
    
        sql_cursor.callproc('GetUserVSGuild', args)
        for result in sql_cursor.stored_results():
            sql_return = result.fetchall()

        wins = 0
        loss = 0

        for rows in sql_return:
            wins += rows[0]
            loss += rows[1]

        winrate = (wins / (wins + loss)) * 100
        print(sql_return)

        headers = ["Wins", "Losses", "Winrate", "Enemy_Guild_One", "Enemy_Guild_Two", "Season"]
        await message.send("```{}```".format(tabulate(sql_return, headers, showindex=False)))
        await message.send("```Your winrate is {}```".format(round(winrate,2)))

    except mysql.connector.Error as e:
        await message.send("```Error occurred while connecting to MySQL database: {}```", e)

    finally:
        sql_cursor.close()
        sql_db.close()

@client.command()
async def player_season(message, user=None, user_input=None):
    if message.channel.id != int(os.getenv('YOUR_HISTORY_CHANNEL')):
        await message.send("```this command does not work in this text channel```")
        return 0
    args = [user, user_input]

    try:
        print("testerstart")
        sql_db = mysql.connector.connect(
            host=os.getenv('YOUR_HOST'),
            user=os.getenv('YOUR_USER'),
            passwd=os.getenv('YOUR_PASSWD'),
            database=os.getenv('YOUR_DATABASE')
            )

        sql_cursor = sql_db.cursor()
    
        sql_cursor.callproc('GetUserSiegeSeason', args)
        for result in sql_cursor.stored_results():
            sql_return = result.fetchall()



        wins = 0
        loss = 0
        print(sql_return)
        for rows in sql_return:
            wins += rows[0]
            loss += rows[1]

        # print(wins)
        # print(wins+loss)
        winrate = (wins / (wins + loss)) * 100
        print(winrate)
        print(sql_return)
        sql_cursor.callproc('GetUserSiegeSeason20', args)
        for result in sql_cursor.stored_results():
            sql_return = result.fetchall()
               
        result = []
        start = 0
        end = 0
        for index, i in enumerate(sql_return):
            if i[2] < 80 and end == 0:
                test = ("\u001b[0;40m\u001b[1;31m", i[0], i[1], i[2], i[3], i[4], i[5])
                result.append(test)
                end = 1
            elif i[2] >= 80 and start == 0:
                test = ("\u001b[0;40m\u001b[1;34m", i[0], i[1], i[2], i[3], i[4], i[5])
                result.append(test)
                start = 1
            else:
                test = ("", i[0], i[1], i[2], i[3], i[4], i[5])
                result.append(test)
        print(result)

        headers = ["Wins", "Losses", "Winrate", "Enemy_Guild_One", "Enemy_Guild_Two", "Season"]
        await message.send("```ansi\n{}```".format(tabulate(result, headers, showindex=False)))
        if winrate < 85.00:
            await message.send("```ansi\n \u001b[0;37mYour winrate is\u001b[0;0m \u001b[1;31m{}%\u001b[0;0m```".format(round(winrate,2)))
        else:
            await message.send("```ansi\n \u001b[0;37mYour winrate is\u001b[0;0m \u001b[1;34m{}%\u001b[0;0m```".format(round(winrate,2)))

    except mysql.connector.Error as e:
        await message.send("```Error occurred while connecting to MySQL database: {}```", e)

    finally:
        print("testerclose")
        sql_cursor.close()
        sql_db.close()



@client.command()
async def progress(message, user=None, season=None):
    if message.channel.id != int(os.getenv('YOUR_HISTORY_CHANNEL')):
        await message.send("```this command does not work in this text channel```")
        return 0
    args = [user, season]

    try:
        sql_db = mysql.connector.connect(
            host=os.getenv('YOUR_HOST'),
            user=os.getenv('YOUR_USER'),
            passwd=os.getenv('YOUR_PASSWD'),
            database=os.getenv('YOUR_DATABASE')
            )

        sql_cursor = sql_db.cursor()
        
        sql_cursor.callproc('test', args)

        for result in sql_cursor.stored_results():
            sql_return = result.fetchall()
            print("test")
            print(sql_return)

        print(sql_return)

        namehigh = [row[0] for row in sql_return]
        high = [row[1] for row in sql_return]
        z = [row[2] for row in sql_return]
        namelow = [row[3] for row in sql_return]
        low = [row[4] for row in sql_return]
        nameplay = [row[6] for row in sql_return]
        play = [row[7] for row in sql_return]
        y = high + low + play


        fig, ax = plt.subplots(figsize=(15, 8))
        ax.set_title("Overall Performance in season " + season)
        ax.scatter(z * 3, y, c='black')

        for i, txt in enumerate(namehigh):
            ax.annotate(txt, (z[i], high[i]), xytext=(-10, 10), textcoords='offset points', ha='center', va='bottom')

        for i, txt in enumerate(nameplay):
            ax.annotate(txt, (z[i], play[i]), xytext=(-10, 10), textcoords='offset points', ha='center', va='bottom')
        
        for i, txt in enumerate(namelow):
            ax.annotate(txt, (z[i], low[i]), xytext=(-10, 10), textcoords='offset points', ha='center', va='bottom')

        plt.plot(z, high, c='green', label = "Best Performance")
        plt.plot(z, play, c='blue', label = "Your Performance")
        plt.plot(z, low, c='red', label="Worst Performance")
        ax.legend(loc='upper left', bbox_to_anchor=(-0.16, 1.15))
        plt.grid(True)
        
        plt.scatter(z * 3, y, c = 'black')

        plt.xticks(rotation=45, ha='center')


        plt.savefig("plot.png")



        await message.send(file=discord.File("plot.png"))

    except mysql.connector.Error as e:
        await message.send("```Error occurred while connecting to MySQL database: {}```", e)

    finally:
        sql_cursor.close()
        sql_db.close()

@client.command()
async def updatepmonster(message):
    try:
        sql_db = mysql.connector.connect(
            host=os.getenv('YOUR_HOST'),
            user=os.getenv('YOUR_USER'),
            passwd=os.getenv('YOUR_PASSWD'),
            database=os.getenv('YOUR_DATABASE')
            )

        sql_cursor = sql_db.cursor()
        json_dir = os.environ.get("YOUR_MEMBER_JSON")
        name = ''
        id = ''
        mon_dict = {}
        # Loop through all the files in the directory
        for filename in os.listdir(json_dir):
            if filename.endswith('.json'):  # Check if the file is a JSON file
                filepath = os.path.join(json_dir, filename)  # Get the full path to the file
                with open(filepath, 'r', encoding='utf=8') as json_file:
                    json_load = json.load(json_file)

                    id = json_load["wizard_info"]["wizard_id"]

                    name = json_load["wizard_info"]["wizard_name"]

                    mon_dict[name] = {}
                    mon_dict[name][id] = {}

                    for i in json_load["unit_list"]:
                        if mon_dict[name][id].get(i["unit_master_id"]) is not None:
                            mon_dict[name][id][i["unit_master_id"]] += 1
                        else:
                            mon_dict[name][id][i["unit_master_id"]] = 1

        for name, id in mon_dict.items():
            for i in mon_dict[name][list(id.keys())[0]]:

                args = [list(id.keys())[0], i]
                # print(i)
                # print(name, list(id.keys())[0], i)
                # print(mon_dict[name][list(id.keys())[0]][i])
                sql_cursor.callproc('checkmon', args)
                for result in sql_cursor.stored_results():
                    isMonster = result.fetchall()
                # print(i, isMonster)
                if isMonster:
                    upmargs = [list(id.keys())[0], i, mon_dict[name][list(id.keys())[0]][i]]
                    sql_cursor.callproc('updateplayersmonster', upmargs)
                    # print("exists in table")
                else:
                    apmargs = [list(id.keys())[0], i, mon_dict[name][list(id.keys())[0]][i]]
                    sql_cursor.callproc('addplayersmonster', apmargs)
                    # print(apmargs)
                    # print("does not exist")
            sql_db.commit()

        await message.send("```Database has been updated with guild members monsters```")

    except mysql.connector.Error as e:
        await message.send("```Error occurred while connecting to MySQL database: {}```", e)

    finally:
        sql_cursor.close()
        sql_db.close()

@client.command()
async def updateactive(message):
    if message.channel.id != int(os.getenv('YOUR_SIEGE_CHANNEL')):
        await message.send("```this command does not work in this text channel```")
        return 0
    try:
        sql_db = mysql.connector.connect(
            host=os.getenv('YOUR_HOST'),
            user=os.getenv('YOUR_USER'),
            passwd=os.getenv('YOUR_PASSWD'),
            database=os.getenv('YOUR_DATABASE')
            )

        sql_cursor = sql_db.cursor()
        args = []
        folder_path = os.getenv('YOUR_FOLDER_PATH')
        file_name = os.getenv('YOUR_JSON_FILE')
        file_path = os.path.join(folder_path,file_name)
        sql_cursor.callproc('setinactive', args)

        with open(file_path, 'r', encoding='UTF-8') as json_file:
            json_load = json.load(json_file)
            for i in json_load["guild"]["guild_members"]:
                name = json_load["guild"]["guild_members"][i]["wizard_name"]
                id = i
                # print(json_load["guild"]["guild_members"][i]["wizard_name"])

                args = [id, name]
                sql_cursor.callproc('setactive', args)
                print(id, name)
            sql_db.commit()
        await message.send("```Active guild members have been updated!```")


    except mysql.connector.Error as e:
        await message.send("```Error occurred while connecting to MySQL database: {}```", e)

    finally:
        sql_cursor.close()
        sql_db.close()


@client.command()
async def defense(message, mon1 = None, mon2 = None, mon3 = None):
    if message.channel.id != int(os.getenv('YOUR_SIEGE_CHANNEL')):
        await message.send("```this command does not work in this text channel```")
        return 0
    try:
        sql_db = mysql.connector.connect(
            host=os.getenv('YOUR_HOST'),
            user=os.getenv('YOUR_USER'),
            passwd=os.getenv('YOUR_PASSWD'),
            database=os.getenv('YOUR_DATABASE')
            )

        sql_cursor = sql_db.cursor()

        mon1 = mon1.title()
        mon2 = mon2.title()
        if mon3 != None:
            mon3 = mon3.title()
        print(mon1, mon2, mon3)
        args = [mon1, mon2, mon3]

        sql_cursor.callproc('getplayermonster', args)
        for result in sql_cursor.stored_results():
            sql_return = result.fetchall()
        print(sql_return)
        result = []
        result2 = []
        count = 0
        test = ()
        test2 = ()
        sql_return = list(OrderedDict.fromkeys(sql_return))
        

        first, second, third = 0, 0 ,0
        nametrack = []
        mark = 0
        for i in sql_return:
            print(i)
            if i[2] == mon1:
                first = i[1]
                mark+=1
                nametrack.append(i[0])
                print("test1")
            elif i[2] == mon2:
                second = i[1]
                mark+=1
                nametrack.append(i[0])
                print("test2")
            elif i[2] == mon3:
                third = i[1]
                mark+=1
                nametrack.append(i[0])
                print("test3")
            
            print(nametrack)
            count+=1
            print(count)
            print(mark)
            if mon3 == None:
                if count == 2 and mark == 2 and (nametrack[0] == nametrack[1]):
                    test2 = (i[0], first, second)
                    print("test2 " + str(test2))
                    result2.append(test2)
                    count = 0
                    mark = 0
                    nametrack.clear() 
                elif count == 2 and  (nametrack[0] != nametrack[1]):
                    count = 1
                    mark = 1
                    nametrack.clear()
                    nametrack.append(i[0])
                    continue
            else:
                if count == 3 and mark == 3 and (nametrack[0] == nametrack[2]):
                    test = (i[0], first, second, third)
                    print("test1 " + str(test))
                    result.append(test)
                    count = 0
                    mark = 0
                    nametrack.clear()
                elif count == 3 and (nametrack[0] != nametrack[2]):
                    count = 1
                    mark = 1
                    nametrack.clear()
                    nametrack.append(i[0])
                    continue
            
        print(result)
        print(result2)
        if mon3 == None:
            headers = ["players", mon1, mon2]
            await message.send("```{}```".format(tabulate(result2, headers, showindex="always", tablefmt="github",)))
        else:
            headers = ["players", mon1, mon2, mon3]
            await message.send("```{}```".format(tabulate(result, headers, showindex="always", tablefmt="github")))
    
    except mysql.connector.Error as e:
        await message.send("```Error occurred while connecting to MySQL database: {}```", e)

    finally:
        sql_cursor.close()
        sql_db.close()

@client.command()
async def webscrape(message):
    try:
        sql_db = mysql.connector.connect(
            host=os.getenv('YOUR_HOST'),
            user=os.getenv('YOUR_USER'),
            passwd=os.getenv('YOUR_PASSWD'),
            database=os.getenv('YOUR_DATABASE')
            )
        
        sql_cursor = sql_db.cursor()

        url = "https://github.com/Xzandro/sw-exporter/blob/master/app/mapping.js"
        response = requests.get(url)

        
        soup = BeautifulSoup(response.content, 'html.parser')
        rows = soup.select("table.js-file-line-container tr")

        for i, row in enumerate(rows):
            name_tag = row.select_one("span.pl-s") 
            number_tag = row.select_one("span.pl-c1") 
            if i > 1186:
                break
            if i < 18:
                continue
            if name_tag and number_tag: # Only print if both name and number are found
                name = name_tag.text.strip()
                name = re.sub(r'[^a-zA-Z0-9\s]', '', name)
                number = number_tag.text.strip()
                print(i, name, number)
                sql = "INSERT INTO monster (UUID, Name) VALUES (%s, %s)"
                values = (number, name)
                sql_cursor.execute(sql, values)
            sql_db.commit()

        
    except mysql.connector.Error as e:
        await message.send("```Error occurred while connecting to MySQL database: {}```", e)

    finally:
        sql_cursor.close()
        sql_db.close()

client.run(os.getenv('YOUR_TOKEN_ID'))



