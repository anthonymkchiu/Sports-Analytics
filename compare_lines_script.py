import requests
from bs4 import BeautifulSoup
import datetime
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from operator import itemgetter


def sportsline_get_team_data(url, home_team):
    """
    Takes gathers player projection data on a game given a URL

    Inputs:
        url [str]: The URL of the game that will me used to generate data
        home_team [str]: The name of the home team of the game

    Returns [List[Tup[str, [List]]]]: Returns a list tuples with the first element
    of the tuples being the name of the player and the second element being a
    list of stats
    """
    away_page = requests.get(url)
    away_info = BeautifulSoup(away_page.text, 'html.parser')
    away_info_prettify = away_info.prettify()
    away_stats = sportsline_gather(away_info_prettify)   

    driver = webdriver.Chrome()
    driver.get(url)
    button_name = f'//button[text()="{home_team}"]'
    home_button = driver.find_element(By.XPATH, button_name)
    home_button.click()
    home_content = driver.page_source
    home_info = BeautifulSoup(home_content, 'html.parser')
    home_info_prettify = home_info.prettify()
    home_stats = sportsline_gather(home_info_prettify) 
    
    return away_stats + home_stats


def sportsline_gather(info_prettify):
    """
    Takes prettified HTML code and returns player projected data

    Inputs:
        info_prettify [str]:The prettified HTML source code
    
    Returns [List[Tup[str, [List]]]]: Returns a list tuples with the first element
    of the tuples being the name of the player and the second element being a
    list of stats
    """
    name_start_index = info_prettify.find('<table class="sc-af84713a-1 lcrxDg"')
    name_end_index = info_prettify.find("sc-cb8dd678-1 iknkQC")
    name_lines = info_prettify[name_start_index:name_end_index].splitlines()
    names = []
    for line in name_lines:
        stripped_line = line.strip() 
        if stripped_line[0] != "<":
            names.append(stripped_line)
    names.pop(0)

    stats_start_index = info_prettify.find('<table class="sc-cb8dd678-1 iknkQC"')
    stats_end_index = info_prettify.find("sc-ed7d8b84-0 iqOEpP no-padding")
    stats_lines = info_prettify[stats_start_index:stats_end_index].splitlines()

    stats = []
    for line in stats_lines:
        stripped_line = line.strip() 
        if stripped_line[0] != "<":
            stats.append(stripped_line)
    for _ in range(0,6):
        stats.pop(0)

    player_stats = []
    for start in range(0,round(len(stats) / 6)):
        player_index = start * 6
        stat_lst = []
        for stat_index in range(player_index, player_index + 6):
            stat_lst.append(float(stats[stat_index]))
        player_tup = names[start], stat_lst
        player_stats.append(player_tup)

    return player_stats  

def not_start_with_num(str):
    """
    Checks to make sure that a string does not start with a number

    Inputs:
        str [str]: The string to be checked

    Returns [bool]: True if the string does not start with a number,
    returns Talse otherwise 
    """
    nums = ["0","1","2","3","4","5","6","7","8","9"]
    for val in nums:
        if str.startswith(val):
            return False
    return True
    
    

def get_matchups():
    """
    Checks the current NBA games that sportsLine has data for and
    reports the matchups

    Inputs: None

    Returns [List[Tuple[str, str]]]: Returns a List of Tuples, with each tuple
    containing the names of the two teams in the matchup as strings
    """
    page = requests.get("https://www.sportsline.com/nba/picks/")
    info = BeautifulSoup(page.text, 'html.parser')
    info_prettify = info.prettify()
    
    teams_start_index = info_prettify.find('<div class="sc-5780ff56-0 fhgbQJ sc-9e842b7e-0 eAePBl"')
    teams_end_index = info_prettify.find("sc-5780ff56-0 sc-ab308bf4-1 eqambb")
    teams_lines = info_prettify[teams_start_index:teams_end_index].splitlines()
    
    teams = []
    for line in teams_lines:
        stripped_line = line.strip()
        if stripped_line[0] != "<":
            teams.append(stripped_line)
    refined_teams = []

    for team in teams:
        if not team.startswith("+") and not team.startswith("-"):
            if not team.startswith("O/U") and not team.startswith("Matchup"):
                if not_start_with_num(team) and not team.endswith("UTC"):
                    refined_teams.append(team)


    matchups = []
    for index in range(0, round(len(refined_teams) / 3)):
        matchup_index = index * 3

        name_start_index = refined_teams[matchup_index].find('"name":')
        name_end_index = refined_teams[matchup_index].find('"startDate":')
        game_tag = refined_teams[matchup_index][name_start_index + 8: name_end_index - 2]
        time_start_index = refined_teams[matchup_index].find('"startDate":')
        time_end_index = refined_teams[matchup_index].find('"location":')
        game_time = refined_teams[matchup_index][time_start_index + 13: time_end_index - 9]
        
        tag_time_and_home = game_tag, game_time, refined_teams[matchup_index + 2]
        matchups.append(tag_time_and_home)

    return matchups

    
    
def time_to_string(time):
    """
    Takes a positive number and turns it into a string. If the number
    is less than 10, it adds a 0 to the front

    Inputs
        tine [int]: the number to be turned into a string

    Returns [str]: the input number represented as a string
    """
    if time < 10:
        return f"0{time}"
    else:
        return str(time)

def get_stats_from_sportsline():
    """
    Retrieves NBA stats from sportsline

    Input: None 

    Returns [Dict[str, [List]]]: A dictionary that maps a player's name to
    the list of stats associated with that player
    """
    player_dictionary = {}
    matchups = get_matchups()
    
    url_front = f"https://www.sportsline.com/nba/game-forecast/NBA_"
    url_back = "/daily-fantasy-projections/"

    for matchup in matchups: 
        tag, time, home = matchup 
        home = modify_home(home)
        correct_year, correct_month, correct_day = correct_time(time)
        correct_year_string = time_to_string(correct_year)
        correct_month_string = time_to_string(correct_month)
        correct_day_string = time_to_string(correct_day)
        formatted_time = correct_year_string + correct_month_string + correct_day_string
        url = url_front + formatted_time + "_" + tag + url_back
        at_index = tag.find("@")
        data = sportsline_get_team_data(url, home)
        for player in data:
            name, stats = player
            player_dictionary[name] = stats

    return player_dictionary

def modify_home(home):
    """
    Modifies the home team name if it is not formatted the same way as the
    name on the button

    Inputs:
        home [str]: the name of the home team
    
    Returns [str]: the newly formatted string, if formatting is necessary
    """
    if home == "Golden St.":
        return "Golden State"
    if home == "L.A. Clippers":
        return "Los Angeles"
    if home == "L.A. Lakers":
        return "Los Angeles"
    return home

      
def correct_time(time):
    """
    Takes a string that represents UTC time as yyyy-mm-dd-hh-mm and gives
    CDT time values

    Inputs:
        time [str]: The string representation of the UTC time
    
    Returns [Tup[int, int, int]]: The year, month, and day of the CDT time
    """
    year = int(time[0:4])
    month = int(time[5:7])
    day = int(time[8:10])
    hour = int(time[11:13])
    minute = int(time[14:16])
    date = datetime(year, month, day, hour, minute)
    cdt_time = date + timedelta(hours = -5)

    return cdt_time.year, cdt_time.month, cdt_time.day

'''
def convert_prizepicks_source(source):
    """
    Takes source HTML and derives the player props

    Inputs:
        source [str]: The source HTML from prizepicks
    
    Returns [Dict[str, int]]: A dictionary with the keys being the player
    names and the values being the prop for that player
    """
    
    prizepicks_info = BeautifulSoup(source, 'html.parser')
    raw_names = prizepicks_info.find_all(class_="name")
    raw_scores = prizepicks_info.find_all(class_="score-container")
    prettified_scores = []
    for score in raw_scores:
        prettified_scores.append(score.prettify())
    
    names = []
    scores = []  
    for index, prettified_score in enumerate(prettified_scores):
        if not "Goblin" in prettified_score and not "Demon" in prettified_score:
            if raw_scores[index].text.count(".") < 2:
                names.append(raw_names[index].text)
                scores.append(float(raw_scores[index].text))

    prop_dict = {}
    for index, player in enumerate(names):
        prop_dict[player] = scores[index]
    
    return prop_dict
'''


def prop_type(prop):
    possible_props = ["Pts + Rebs + Asts", "Points", "Assists", "Rebounds", "Points + Rebounds", "Points + Assists", "Rebounds + Assists"]
    possible_prop_index = -1
    for index, possible_prop in enumerate(possible_props):
        if prop == possible_prop:
            possible_prop_index = index
    key_stats = []
    if possible_prop_index == 0:
        key_stats = [1, 2, 3]
    elif possible_prop_index == 1:
        key_stats = [1]
    elif possible_prop_index == 2:
        key_stats = [3]
    elif possible_prop_index == 3:
        key_stats = [2]
    elif possible_prop_index == 5:
        key_stats = [1, 2]
    elif possible_prop_index == 6:
        key_stats = [1, 3]
    elif possible_prop_index == 7:
        key_stats = [2, 3]
    return key_stats


def gather_underdog():
    """
    Gets players and their respective stat props from Underdog

    Inputs: 
        None

    Returns [Dict[str, Dict[str, int]]]: Returns a dictionary that with players
    and a dictionary of stats.
    """
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)
    driver.get("https://underdogfantasy.com/")
    login_button = driver.find_element(By.XPATH, '//button[text()="Log in"]')
    login_button.click()
    email = driver.find_element(By.CSS_SELECTOR, "#root > div > div.styles__modalBackground__7IQ1P > div > div > div > div.styles__content__AeGUr > div > form > div:nth-child(1) > label > div.styles__field__Q6LKF > input")
    email.send_keys("ep1dude1@gmail.com")
    password = driver.find_element(By.CSS_SELECTOR, "#root > div > div.styles__modalBackground__7IQ1P > div > div > div > div.styles__content__AeGUr > div > form > div:nth-child(2) > label > div.styles__field__Q6LKF > input")
    password.send_keys("Kalebchan122904!")
    sign_in_button = driver.find_element(By.CSS_SELECTOR, '#root > div > div.styles__modalBackground__7IQ1P > div > div > div > div.styles__content__AeGUr > div > form > button.styles__button__gmYRZ.styles__green__aqzHf.styles__small___s6i5.styles__solid__BthGK.styles__intrinsic__OkkMQ.styles__button__JBB9c')
    sign_in_button.click()
    nba_button = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='sport-selector-button-nba']")))
    nba_button.click()
    prop_boxes = wait.until(EC.visibility_of_all_elements_located((By.CLASS_NAME, "styles__overUnderCell__KgzNn")))
    more_prop_buttons = wait.until(EC.visibility_of_all_elements_located((By.CLASS_NAME, "styles__toggleButton__jrfS7")))
    for button in more_prop_buttons:
        button.click()
    player_lines = {}
    for prop_box in prop_boxes:
        name = prop_box.find_element(By.CLASS_NAME, "styles__playerName__jW6mb")
        props = prop_box.find_elements(By.CLASS_NAME, "styles__overUnderListCell__tbRod")
        valid_props = []
        for prop in props:
            choices = prop.find_elements(By.CLASS_NAME, "styles__pickEmButton__OS_iW")
            if len(choices) == 2:
                valid_props.append(prop)
        statlines = []
        for valid_prop in valid_props:
            prop_statline = valid_prop.find_element(By.CLASS_NAME, "styles__statLine__K1NYh")
            statline = prop_statline.find_element(By.TAG_NAME, "p")
            statlines.append(statline.text)
        prop_dict = {}
        for index, statline_string in enumerate(statlines): 
            stat_index = statline_string.find(" ")
            line = float(statline_string[:stat_index])
            stat = statline_string[stat_index + 1:]
            prop_dict[stat] = line, valid_props[index]
        player_lines[name.text] = prop_dict
    driver.close()
    return player_lines

underdog_dict = gather_underdog()
sportsline_dict = get_stats_from_sportsline()

def give_best_lines(prop):
    """
    Creats a list of props sorted by line discrepancy 

    Inputs: 
        props [str]: The prop that is being analyzed
    
    Returns [List]: A sorted list of the desired props
    """
    key_stats = prop_type(prop)
    best_lines = []
    for player in underdog_dict:
        if prop in underdog_dict[player]:
            if player in sportsline_dict:
                stat_sum = 0
                for stat in key_stats:
                    stat_sum += sportsline_dict[player][stat] 
                stat_difference = abs(stat_sum - underdog_dict[player][prop][0]) 
                line = stat_difference, player,underdog_dict[player][prop][0], stat_sum
                best_lines.append(line)
    sorted_list = sorted(best_lines, key=lambda x: x[0], reverse=True)
    return sorted_list

def return_best():
    """
    Prints the best lines for Points Rebounds, Assists and PRA

    Inputs: None

    Returns: None
    """
    points = give_best_lines("Points")
    print("Points:")
    print(points[0])
    print(points[1])
    print(points[2])
    print(points[3])
    print(points[4])
    print("\n")
    rebounds = give_best_lines("Rebounds")
    print("Rebounds:")
    print(rebounds[0])
    print(rebounds[1])
    print(rebounds[2])
    print(rebounds[3])
    print(rebounds[4])
    print("\n")
    assists = give_best_lines("Assists")
    print("Assists:")
    print(assists[0])
    print(assists[1])
    print(assists[2])
    print(assists[3])
    print(assists[4])
    print("\n")
    pra = give_best_lines("Pts + Rebs + Asts")
    print("Pts + Rebs + Asts:")
    print(pra[0])
    print(pra[1])
    print(pra[2])
    print(pra[3])
    print(pra[4])
    print("\n")

return_best()
