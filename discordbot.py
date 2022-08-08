import discord
import requests
import json
import glob
import os.path
import shutil
import youtube_dl
import random

import pandas as pd
import numpy as np
from openpyxl import load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from tabulate import tabulate

from discord.ext import commands
from requests_html import HTMLSession


client = commands.Bot(command_prefix = "-")


##
##with open("siege.json", 'r', encoding='utf=8') as json_file:
##    json_load = json.load(json_file)
##    match_id = json_load["matchup_info"]["match_info"]["match_id"]

##with open("siege.json", 'r', encoding='utf=8') as json_file:
        
##    data = json.loads(json_file.read())
##
##
##    guild_list = pd.json_normalize(data['matchup_info'], record_path =['guild_list'])
##    match_info = pd.DataFrame.from_dict(data['matchup_info']['match_info'],orient='index').transpose()
##    wizard_info_list = pd.json_normalize(data['matchup_info'], record_path =['wizard_info_list'])
##    attack_log_battle_log_list = pd.json_normalize(data['attack_log']['log_list'], record_path =['battle_log_list'])
##    defense_log_battle_log_list = pd.json_normalize(data['defense_log']['log_list'], record_path =['battle_log_list'])
##    current_attack_log = attack_log_battle_log_list.merge(match_info, how="inner",on=['match_id','siege_id'])
##
##    attack_stats_temp = current_attack_log.groupby(['wizard_name','win_lose']).size().reset_index(name='counts')
##    attack_stats_by_wizard = attack_stats_temp.pivot(index='wizard_name', columns='win_lose', values='counts').rename_axis(None,axis=1).reset_index()
##    attack_stats_by_wizard = attack_stats_by_wizard.rename(columns={'wizard_name': 'name',1:'win',2:'lose'})
##
##    attack_stats_by_wizard = attack_stats_by_wizard.fillna(0)
##    attack_stats_by_wizard['attack_win_rate'] = round(attack_stats_by_wizard['win']/ (attack_stats_by_wizard['win'] + attack_stats_by_wizard['lose'])*100)
##
####    await message.send("```{}```".format(attack_stats_by_wizard))
##    print(type(attack_stats_by_wizard))
####    df = attack_stats_by_wizard.reindex(sorted(attack_stats_by_wizard.columns))
####    print(df)
##    print(tabulate((attack_stats_by_wizard)))

        
comm = {
    "-stats": "Displays current winrate and remaining attacks for each guild",
    "-match": "Displays winrate of our guild members from highest to lowest",
    "-record": "excel file of each siege match",
    "-counter": "This command displays the 3 unit defence",
    "-helpadd": "explains clearly on how to use -add command",
    "-add": "This command adds new counter arg2 to the defence arg1 with kill order as arg3",
    "-defrate": "Displays total defense winrate",
    "-atkmade": "Displays percentage of attacks each guild used on us",
    "-completed": "Use this command immediately after the siege match has concluded",
    "-atkleft": "DISCONTINUED. Displays remaining attacks for each guild",
    "-winrate": "DISCONTINUED. Displays current winrate"  
    }
def helper():
    folder_path = r'C:\Users\Geo\Desktop\Summoners War Exporter Files'
    file_type = '\*json'
    files = glob.glob(folder_path + file_type)
    max_file = max(files, key=os.path.getctime)
    target = r'C:\Users\Geo\Desktop\Python project\siege.json'
    shutil.copyfile(max_file, target)
    with open("siege.json", 'r', encoding='utf=8') as json_file:
        
        data = json.loads(json_file.read())


        guild_list = pd.json_normalize(data['matchup_info'], record_path =['guild_list'])
        match_info = pd.DataFrame.from_dict(data['matchup_info']['match_info'],orient='index').transpose()
        wizard_info_list = pd.json_normalize(data['matchup_info'], record_path =['wizard_info_list'])
        attack_log_battle_log_list = pd.json_normalize(data['attack_log']['log_list'], record_path =['battle_log_list'])
        defense_log_battle_log_list = pd.json_normalize(data['defense_log']['log_list'], record_path =['battle_log_list'])
        current_attack_log = attack_log_battle_log_list.merge(match_info, how="inner",on=['match_id','siege_id'])
        print(guild_list)

            
        attack_stats_temp = current_attack_log.groupby(['wizard_name','win_lose']).size().reset_index(name='counts')
        attack_stats_by_wizard = attack_stats_temp.pivot(index='wizard_name', columns='win_lose', values='counts').rename_axis(None,axis=1).reset_index()
        attack_stats_by_wizard = attack_stats_by_wizard.rename(columns={'wizard_name': 'name',1:'win',2:'lose'})

        attack_stats_by_wizard = attack_stats_by_wizard.fillna(0)
        attack_stats_by_wizard['attack_win_rate'] = round(attack_stats_by_wizard['win']/ (attack_stats_by_wizard['win'] + attack_stats_by_wizard['lose'])*100)

        return attack_stats_by_wizard
@client.event
async def on_ready():
    print("now online")

@client.command()
async def commands(message):
    command_list = pd.DataFrame(list(comm.values()), index=comm)

    headers = ["Commands", "Description"]
    await message.send("```{}```".format(tabulate(command_list, headers, tablefmt="github")))


@client.command()
async def helpadd(message):
    await message.send("```With the -add command, you must encapsulate three arguments in qoutations, example 'argument1' 'argument 2' 'argument 3', 'harmonia vigor roid' 'triana roid rina' 'Description'. The first argument is the defence you want to make the counter for, the second argument is the team used to counter the first argument defence, the third argument is the kill order and any other descriptions necessary.```") 

@client.command()
async def match(message):
        attack_stats_by_wizard = helper()

        attack_stats_by_wizard.sort_values(by=['attack_win_rate'])

        
        await message.send("```{}```".format(attack_stats_by_wizard.sort_values(by=['attack_win_rate'], ascending =False)))


@client.command()
async def completed(message):
        attack_stats_by_wizard = helper()


        ExcelWorkbook = load_workbook('siege_record.xlsx')
        writer = pd.ExcelWriter('siege_record.xlsx', if_sheet_exists="replace", engine = 'openpyxl', mode='a')
        writer.book = ExcelWorkbook
        writer.sheets = dict((ws.title, ws) for ws in ExcelWorkbook.worksheets)
##        attack_stats_by_wizard.to_excel(writer, sheet_name=str(match_id))
        writer.save()

        print(guild_list)

        await message.send("```Match has been recorded!```")

@client.command()
async def record(message):
    await message.send(file=discord.File("siege_record.xlsx"))

@client.command()
async def stats(message):
    folder_path = r'C:\Users\Geo\Desktop\Summoners War Exporter Files'
    file_type = '\*json'
    files = glob.glob(folder_path + file_type)
    max_file = max(files, key=os.path.getctime)
    target = r'C:\Users\Geo\Desktop\Python project\siege.json'
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
async def counter(message, arg1=None, arg2=None, arg3=None):

    ExcelWorkbook = load_workbook('counters.xlsx', read_only=True)

    writer = pd.ExcelWriter('counters.xlsx', if_sheet_exists='overlay', engine = 'openpyxl', mode='a')
    writer.book = ExcelWorkbook
    writer.sheets = dict((ws.title, ws) for ws in ExcelWorkbook.worksheets)
    title = {"Counters"}
    if arg1 is None:
        counter_list = pd.DataFrame(list(writer.sheets.keys()), index=None, columns=title)
        counter_list = counter_list.sort_values("Counters")
        
        
##        await message.send("```{}```".format(counter_list))
        await message.send("```{}```".format(tabulate(counter_list, title, showindex=False, tablefmt="plain")))
        

    else:
        defense_team = arg1.lower() + " " + arg2.lower() + " " + arg3.lower()
        if defense_team not in ExcelWorkbook.sheetnames:
            await message.send("```There are currently no posted counters for {}```".format(defense_team))
        else:
            sheet = pd.read_excel('counters.xlsx', sheet_name = defense_team)
            headers = list(sheet.columns.values)
            await message.send("```{}```".format(tabulate(sheet, headers, showindex=False, maxcolwidths=[None, None, 50])))
    
@client.command()
async def add(message, arg, arg2, arg3):
    arg = arg.lower()
    arg2 = arg2.lower()
    arg3 = arg3.lower()
    header = ["Counter", "Kill Order"]
    new_row = {'Counter': [arg2], 'Kill Order': [arg3]}

    data = pd.DataFrame(new_row, columns=header)


    ExcelWorkbook = load_workbook('counters.xlsx')
    writer = pd.ExcelWriter('counters.xlsx', if_sheet_exists='overlay', engine = 'openpyxl', mode='a')
    writer.book = ExcelWorkbook
    writer.sheets = dict((ws.title, ws) for ws in ExcelWorkbook.worksheets)

    
    if arg in writer.sheets:
        print("test")
        sheet_data = pd.read_excel('counters.xlsx', sheet_name = arg)
        if arg2 in sheet_data["Counter"].values:
            print("test2")
            await message.send("```{} already exists as a counter for the defence {}```".format(arg2, arg))
        else:
            print("test3")
            data.to_excel(writer, sheet_name=arg, startrow=writer.sheets[arg].max_row, header=False)
            await message.send("```{} Has been added to the list of counters for {}```".format(arg2, arg))
    else:
        print("test4")
        data.to_excel(writer, sheet_name=arg, header=header)
        await message.send("```{} Has been added to the list of counters for {}```".format(arg2, arg))
        
    writer.save()
    
##@client.command()
##async def delete(message):

##Discontinued function, displays remaining atks for each guild
##
##@client.command()
##async def atkleft(message):
##    folder_path = r'C:\Users\Geo\Desktop\Summoners War Exporter Files'
##    file_type = '\*json'
##    files = glob.glob(folder_path + file_type)
##    max_file = max(files, key=os.path.getctime)
##    target = r'C:\Users\Geo\Desktop\Python project\siege.json'
##    shutil.copyfile(max_file, target)
##    with open("siege.json", 'r', encoding='utf=8') as json_file:
##        json_load = json.load(json_file)
##        json_match = json_load["matchup_info"]["guild_list"]
##        siege_dict = {}
##        guilds = []
##
##        for line in json_match:
##            siege_dict[line.get("guild_name")] = 250-line.get("attack_count")
##        title = [""]
##        
##        atks = pd.DataFrame(list(siege_dict.values()), index=siege_dict, columns=title)
##        print(atks)
##        await message.send("{}".format(atks))


##Discontinued function, displays winrate for each guild
        
##@client.command()
##async def winrate(message):
##    folder_path = r'C:\Users\Geo\Desktop\Summoners War Exporter Files'
##    file_type = '\*json'
##    files = glob.glob(folder_path + file_type)
##    max_file = max(files, key=os.path.getctime)
##    target = r'C:\Users\Geo\Desktop\Python project\siege.json'
##    shutil.copyfile(max_file, target)
##    with open("siege.json", 'r', encoding='utf=8') as json_file:
##        siege_dict = {}
##        json_load = json.load(json_file)
##        total = 0
##        win = 0
##        win2 =0
##        total2=0
##        win3=0
##        total3=0
##        teams = []
##
##
##        for line in json_load["matchup_info"]["guild_list"]:
##            if "guild_id" in line:
##                siege_dict[line["guild_name"]] = 0
##                if "Hurt" not in line["guild_name"]:
##                    teams.append(line["guild_name"])
##        for line in json_load["attack_log"]["log_list"][0]["battle_log_list"]:
##            if line["win_lose"] == 1:
##                win+=1
##            total+= 1
##            siege_dict["Hurt"] = round(win/total,2)*100
##    
##        for line in json_load["defense_log"]["log_list"][0]["battle_log_list"]:
##            if teams[0] in line["opp_guild_name"]:
##                if line["win_lose"] == 1:
##                    win2+=1
##                total2+=1
##
##                siege_dict[line["opp_guild_name"]] = round(1 - win2/total2,2)*100;
##            if teams[1] in line["opp_guild_name"]:
##                if line["win_lose"] == 1:
##                    win3+=1
##                total3+=1
##                siege_dict[line["opp_guild_name"]] = round(1 - win3/total3,2)*100 ;
##        
##
##        title = [""]
##        
##        winrate = pd.DataFrame(list(siege_dict.values()), index=siege_dict, columns=title)
##        print(winrate)
##        await message.send(winrate)
##
@client.command()
async def defrate(message):
    folder_path = r'C:\Users\Geo\Desktop\Summoners War Exporter Files'
    file_type = '\*json'
    files = glob.glob(folder_path + file_type)
    max_file = max(files, key=os.path.getctime)
    target = r'C:\Users\Geo\Desktop\Python project\siege.json'
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

##@client.command()
##async def atkmade(message):
##    folder_path = r'C:\Users\Geo\Desktop\Summoners War Exporter Files'
##    file_type = '\*json'
##    files = glob.glob(folder_path + file_type)
##    max_file = max(files, key=os.path.getctime)
##    target = r'C:\Users\Geo\Desktop\Python project\siege.json'
##    shutil.copyfile(max_file, target)
##    teams = []
##    siege_dict = {}
##    total1 = 0
##    total2 = 0
##    with open("siege.json", 'r', encoding='utf=8') as json_file:
##        
##        json_load = json.load(json_file)
##        for line in json_load["matchup_info"]["guild_list"]:
##            if "guild_id" in line:
##                siege_dict[line["guild_name"]] = 0
##                if "Hurt" not in line["guild_name"]:
##                    teams.append(line["guild_name"])
##
##
##        for line in json_load["defense_log"]["log_list"][0]["battle_log_list"]:
##            if teams[0] in line["opp_guild_name"]:
##                total1+=1
##                siege_dict[line["opp_guild_name"]] = round(total1/250,2)*100;
##                
##            if teams[1] in line["opp_guild_name"]:
##                total2+=1
##                siege_dict[line["opp_guild_name"]] = round(total2/250,2)*100;
##                
##        for i in siege_dict:
##            
##            await message.send("{}: {}%".format(i, siege_dict.get(i)))


##Discontinued function, updates json file            
##@client.command()
##async def update(message):
##    folder_path = r'C:\Users\Geo\Desktop\Summoners War Exporter Files'
##    file_type = '\*json'
##    files = glob.glob(folder_path + file_type)
##    max_file = max(files, key=os.path.getctime)
##    target = r'C:\Users\Geo\Desktop\Python project\siege.json'
##    shutil.copyfile(max_file, target)
##    await message.send("Json file updated!")

            
##@client.command()
##async def league(message):
    
    
    
@client.command()
async def join(message):
    if message.author.voice is None:
        await message.send("Please enter a voice channel")
    voice_channel = message.author.voice.channel
    if message.voice_client is None:
        await voice_channel.connect()
    else:
        await message.voice_client.move_to(voice_channel)

@client.command()
async def leave(message):
    if message.author.voice.channel is not message.voice_client.channel:
        await message.send("You must be in the same channel")
    else:
        await message.voice_client.disconnect()

@client.command()
async def tm(message, arg):
    if arg == "join":
        if len(members) >= 10:
            await message.send("lobby is full")
        else:
            members.append(message.author.name)
            await message.send("You have been added")
            await message.send(members)
    if arg == "start":
        if len(members) < 10:
            await message.send("you require more members")
        else:
            random.shuffle(members)
            
            await message.send("Blue Team {}".format(members[:5]))
            await message.send("Red Team {}".format(members[5:]))
            

@client.command()
async def liar(message, arg):
    if arg == "join":
        if len(lm) >= 2:
            await message.send("lobby is full")
        else:
            lm.append(message.author.name)
            await message.send("You have been added")
    if arg == "start":
        dice = []
        for i in range(0, len(lm)):
            dice.clear()
            for j in range(0,5):
                dice.append(random.randint(1,6))
                
            lm[i] = dice
        await message.send(lm)
        lm.clear()



#work in progres
####@client.command()
####async def opgg(message, arg):
##    html = HTMLSession()
##    #query = arg
##    url = f'https://u.gg/lol/champions/Diana/build'
##    req = html.get(url, headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36'})
##    print(url)
##    for line in req.html.find('img'):
##    print(line)
##    print(type(req.html.find('img')[0]))



##
client.run('OTQwNDQzNjg1ODY1MjkxODE2.YgHebw.N9eu1c6Uz0jeKsHOgpMopqZj7rg')


#https://discord.com/api/oauth2/authorize?client_id=940443685865291816&permissions=517543947328&scope=bot
