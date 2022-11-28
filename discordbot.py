import discord
import requests
import json
import glob
import os.path
import shutil
import youtube_dl
import random
import time
import re
import math
import os


import pandas as pd
import numpy as np
from openpyxl import load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from tabulate import tabulate
from dotenv import load_dotenv, find_dotenv

from discord.ext import commands
from requests_html import HTMLSession

from datetime import datetime

import mysql.connector

load_dotenv(find_dotenv())


sql_db = mysql.connector.connect(
    host=os.getenv('YOUR_HOST'),
    user=os.getenv('YOUR_USER'),
    passwd=os.getenv('YOUR_PASSWD'),
    database=os.getenv('YOUR_DATABASE')
    )

sql_cursor = sql_db.cursor()


client = commands.Bot(command_prefix = "-")
spd = {'3': 477, '4':358, '5':286, '6':239, '7':205, '8':179}


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
    "-player_season": "[summoners_name] [season_number]"
    }
def helper():
    folder_path = os.getenv('YOUR_FOLDER_PATH')
    file_type = '\*json'
    files = glob.glob(folder_path + file_type)
    max_file = max(files, key=os.path.getctime)
    target = os.getenv('YOUR_TARGET')
    shutil.copyfile(max_file, target)
    with open("siege.json", 'r', encoding='utf=8') as json_file:
        
        data = json.loads(json_file.read())


        guild_list = pd.json_normalize(data['matchup_info'], record_path =['guild_list'])
        match_info = pd.DataFrame.from_dict(data['matchup_info']['match_info'],orient='index').transpose()
        wizard_info_list = pd.json_normalize(data['matchup_info'], record_path =['wizard_info_list'])
        attack_log_battle_log_list = pd.json_normalize(data['attack_log']['log_list'], record_path =['battle_log_list'])
        defense_log_battle_log_list = pd.json_normalize(data['defense_log']['log_list'], record_path =['battle_log_list'])
        current_attack_log = attack_log_battle_log_list.merge(match_info, how="inner",on=['match_id','siege_id'])

            
        attack_stats_temp = current_attack_log.groupby(['wizard_name','win_lose']).size().reset_index(name='counts')
        attack_stats_by_wizard = attack_stats_temp.pivot(index='wizard_name', columns='win_lose', values='counts').rename_axis(None,axis=1).reset_index()
        attack_stats_by_wizard = attack_stats_by_wizard.rename(columns={'wizard_name': 'name',1:'win',2:'lose'})

        attack_stats_by_wizard = attack_stats_by_wizard.fillna(0)
        attack_stats_by_wizard['attack_win_rate'] = round(attack_stats_by_wizard['win']/ (attack_stats_by_wizard['win'] + attack_stats_by_wizard['lose'])*100)

        return attack_stats_by_wizard

def getguild():
    with open("siege.json", 'r', encoding='utf=8') as json_file:
        json_load = json.load(json_file)
        guild_list = ""
        for i in json_load["matchup_info"]["guild_list"]:
            if i["guild_name"] != "Hurt":
                guild_list += str(i["guild_name"]) + "   "
        guild_list = re.sub("[\/:*?!]", "", guild_list)
        return guild_list
    
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
        attack_stats_by_wizard = helper()

        attack_stats_by_wizard.sort_values(by=['attack_win_rate'])

        
        await message.send("```{}```".format(attack_stats_by_wizard.sort_values(by=['attack_win_rate'], ascending =False)))


@client.command()
async def completed(message):
        attack_stats_by_wizard = helper()
        guilds_name = getguild()

        ExcelWorkbook = load_workbook('siege_records11.xlsx')
        writer = pd.ExcelWriter('siege_records11.xlsx', if_sheet_exists="replace", engine = 'openpyxl', mode='a')
        writer.book = ExcelWorkbook
        writer.sheets = dict((ws.title, ws) for ws in ExcelWorkbook.worksheets)
        attack_stats_by_wizard.to_excel(writer, sheet_name=str(guilds_name))
        writer.save()
        
        await message.send("```Match has been recorded!```")



@client.command()
async def record(message):
    await message.send(file=discord.File("siege_records10.xlsx"))
    #make option to search past records, keep in separate folder

@client.command()
async def stats(message):
    folder_path = os.getenv('YOUR_FOLDER_PATH')
    file_type = '\*json'
    files = glob.glob(folder_path + file_type)
    max_file = max(files, key=os.path.getctime)
    target = os.getenv('YOUR_TARGET')
    shutil.copyfile(max_file, target)
    with open("siege.json", 'r', encoding='utf=8') as json_file:
        siege_atk = {}
        siege_winrate = {}
        json_load = json.load(json_file)
        total = 0
        win = 0
        win2 =0
        total2=0
        win3=0
        total3=0
        teams = []


        for line in json_load["matchup_info"]["guild_list"]:
            siege_atk[line.get("guild_name")] = 250-line.get("attack_count")
            if "guild_id" in line:
                siege_winrate[line["guild_name"]] = 0
                if "Hurt" not in line["guild_name"]:
                    teams.append(line["guild_name"])
                    
        for line in json_load["attack_log"]["log_list"][0]["battle_log_list"]:
            if line["win_lose"] == 1:
                win+=1
            total+= 1
            siege_winrate["Hurt"] = round(win/total,2)*100

    
        for line in json_load["defense_log"]["log_list"][0]["battle_log_list"]:
            if teams[0] in line["opp_guild_name"]:
                if line["win_lose"] == 1:
                    win2+=1
                total2+=1

                siege_winrate[line["opp_guild_name"]] = round(1 - win2/total2,2)*100

            if teams[1] in line["opp_guild_name"]:
                if line["win_lose"] == 1:
                    win3+=1
                total3+=1
                siege_winrate[line["opp_guild_name"]] = round(1 - win3/total3,2)*100



        title = [""]
        atks = pd.DataFrame(list(siege_atk.values()), index=siege_atk, columns=title)
      
        winrate = pd.DataFrame(list(siege_winrate.values()), index=siege_winrate, columns=title)
         
        stat = pd.concat([winrate, atks], axis=1)
        stat.columns = ["Winrate", "Remaining Atks"]
        header = ["", "Winrate", "Remaining Atks"]

        await message.send("```{}```".format(tabulate(stat, header, tablefmt ="github")))


@client.command()
async def counter(message, unit_one=None, unit_two=None, unit_three=None):
    if message.channel.id != int(os.getenv('YOUR_CHANNEL_ID')):
        await message.send("```this command does not work in this text channel```")
        return 0

    disc_id = str(message.author)

    sql_cursor.callproc('checkPlayer', [disc_id])
    for result in sql_cursor.stored_results():
        sql_return = result.fetchall()

    if len(sql_return) == 0:
        await message.send("```You must be a member of Hurt to use this command```")
        return 0

    if unit_two is not None and unit_three is not None:
        temp = ""
        if unit_two > unit_three:
            unit_two, unit_three = unit_three, unit_two
    else:
        await message.send("```Please enter 3 unit defense```")
        return 0
        
    defense_team = unit_one.lower() + " " + unit_two.lower() + " " + unit_three.lower()

    args = [defense_team]
    sql_cursor.callproc('GetCounter', args)

    for result in sql_cursor.stored_results():
        sql_return = result.fetchall()

    if len(sql_return) == 0:
        await message.send("```There are currently no posted counters for {}```".format(defense_team))
        return 0

    headers = ["Counter", "Kill Order"]
    await message.send("```{}```".format(tabulate(sql_return, headers, showindex=False, maxcolwidths=[None, 75])))
    
@client.command()
async def add(message, defense_team, offense_team, description):
    if message.channel.id != int(os.getenv('YOUR_CHANNEL_ID')):
        await message.send("```This command does not work in this text channel```")
        return 0

    disc_id = str(message.author)

    sql_cursor.callproc('checkPlayer', [disc_id])
    for result in sql_cursor.stored_results():
        sql_return = result.fetchall()

    if len(sql_return) == 0:
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

    args = [defense_team, offense_team, description, disc_id, dt_string]

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

@client.command()
async def defrate(message):
    folder_path = os.getenv('YOUR_FOLDER_PATH')
    file_type = '\*json'
    files = glob.glob(folder_path + file_type)
    max_file = max(files, key=os.path.getctime)
    target = os.getenv('YOUR_TARGET')
    shutil.copyfile(max_file, target)

    win = 0
    total =0
    with open("siege.json", 'r', encoding='utf=8') as json_file:
        json_load = json.load(json_file)
        for line in json_load["defense_log"]["log_list"][0]["battle_log_list"]:
            if line["win_lose"] == 1:
                win+=1
            total+=1
    drate = round(win/total,2)*100
    
    await message.send("```defense winrate is {}%```".format(drate))


@client.command()
async def register(message, summoners_id=None):
    if message.channel.id != int(os.getenv('YOUR_REGISTER_CHANNEL')):
        await message.send("```this command does not work in this text channel```")
        return 0



    disc_id = str(message.author)
    disc_display_name = message.author.display_name
    sql_cursor.callproc('checkPlayer', [disc_id])

    for result in sql_cursor.stored_results():
        sql_return = result.fetchall()
    args = [disc_id, disc_display_name, summoners_id]

 
    if len(sql_return) == 0:
        sql_cursor.callproc('addPlayer', args)
        sql_db.commit()
        
        await message.send("```{} has been added to the player database```".format(disc_display_name))
    else:
        await message.send("```{} is already in the player database```".format(disc_display_name))
        return 0
        

@client.command()
async def player(message, user=None):
    if message.channel.id != int(os.getenv('YOUR_HISTORY_CHANNEL')):
        await message.send("```this command does not work in this text channel```")
        return 0
    args = [user]

    sql_cursor.callproc('GetUserSiege', args)
    for result in sql_cursor.stored_results():
        sql_return = result.fetchall()
    wins = 0
    loss = 0
    for rows in sql_return:
        wins += rows[0]
        loss += rows[1]
    winrate = wins / (wins + loss)

  
    headers = ["Wins", "Losses", "Winrate", "Enemy_Guild_One", "Enemy_Guild_Two", "Season"]
    await message.send("```{}```".format(tabulate(sql_return, headers, showindex=False)))
    await message.send("```Your winrate is {}```".format(round(winrate,2)))


@client.command()
async def player_vs(message, user=None, user_input=None):
    if message.channel.id != int(os.getenv('YOUR_HISTORY_CHANNEL')):
        await message.send("```this command does not work in this text channel```")
        return 0

    args = [user,user_input]
    sql_cursor.callproc('GetUserVSGuild', args)
    for result in sql_cursor.stored_results():
        sql_return = result.fetchall()

    wins = 0
    loss = 0

    for rows in sql_return:
        wins += rows[0]
        loss += rows[1]

    winrate = wins / (wins + loss)

    headers = ["Wins", "Losses", "Winrate", "Enemy_Guild_One", "Enemy_Guild_Two", "Season"]
    await message.send("```{}```".format(tabulate(sql_return, headers, showindex=False)))
    await message.send("```Your winrate is {}```".format(round(winrate,2)))

@client.command()
async def player_season(message, user=None, user_input=None):
    if message.channel.id != int(os.getenv('YOUR_HISTORY_CHANNEL')):
        await message.send("```this command does not work in this text channel```")
        return 0
    args = [user, user_input]
    sql_cursor.callproc('GetUserSiegeSeason', args)
    for result in sql_cursor.stored_results():
        sql_return = result.fetchall()

    wins = 0
    loss = 0

    for rows in sql_return:
        wins += rows[0]
        loss += rows[1]

    winrate = wins / (wins + loss)


    headers = ["Wins", "Losses", "Winrate", "Enemy_Guild_One", "Enemy_Guild_Two", "Season"]
    await message.send("```{}```".format(tabulate(sql_return, headers, showindex=False)))
    await message.send("```Your winrate is {}```".format(round(winrate,2)))


client.run(os.getenv('YOUR_TOKEN_ID'))



