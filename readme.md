# Discord Data Bot

Discord Data Bot is a tool used to analyze thousands of pieces of data and return organized data specified by the user

### Project Description

* Grabs data from a third party tool in json format, then organize data to user specifications
* Copies file location of json and moves it to a new directory
* Stores data onto MySQL for later access using mysql connector, and viewing on Discord with tabulate formating
* Writes data onto Excel, using openpyxl, for other users to download through Discord

### Available Commands

* stats: Displays current winrate and remaining attacks for each team
* match: Displays winrate of members from highest to lowest wins
* record: Uploads an Excel sheet of all the matches in this season
* completed: Records the match onto an Excel sheet
* add": Adds units onto the MySQL database
* counter": Displays the units from the MySQL database
* tick": Computes input with preset formula 
* register": Adds users to the MySQL database
* player": Displays player history of matches
* player_vs": Displays player history of matches versus specified team
* player_season": Displays player history of matches in a given season

#### Stats Command
![stats command](./images/stats.png)

#### Match Command
![match command](./images/match.png)

#### Register Commamnd
![register command](./images/register.png)

#### Player Command
![player command](./images/history.png)

#### Webscrap Monster ID and Name
![Webscrap](./images/webscrape.png)

this box of code uses open source tool BeautifulSoup to extract information from a website to get monster ID and Name, then it adds the data into the Monster table in MySQL database.

#### Grabbing User Data, storing onto Database
![playerjson](./images/playerjson.png)
![monstedata](./images/monsterdata.png)

The first image is a sample of users json Data that gets read by the Discord Bot, the second image displays a small sample of information the bot reads through and adds into the database for user interaction.

#### Displaying Data
![defense](./images/playermonsters.png)

This image displays the usage of -defense command which displays the number of specified monsters each user has, while showing only the users who have atleast one of each specified monster.

#### Data Visualization
![Visualization](./images/plot.png)

this image displays a users performance in comparison with the best worst player in that day, as well as their performance from day to day.

#### MySQL ER Diagram
![mysql ER diagram](./images/mysqldiagram.png)


### Thoughts

The decision to make this Data Bot accessible through discord is for a community of players to use the Bot with ease of access, as well as having the ability to converse through discord voice chatting system, while using the Data Bot to help them identify issues in their play styles, or to highlight areas of improvement.

The Bot is currently only available to a closed but growing community currently, with a suggestions text channel for other users to express what features would help them improve, or if there are bugs that need to be fixed. 









