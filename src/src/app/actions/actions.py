# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List

from pandas.core.generic import T

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

from rasa_sdk.forms import FormValidationAction

from rasa_sdk.events import SlotSet, AllSlotsReset

import pandas as pd
import re

from rapidfuzz import process 

df = pd.read_csv("./actions/new_games.csv")

GENRES_DEFAULT_NEGATIVE = ["NO"]
TEAMS_DEFAULT_NEGATIVE = ["NO"]

def extract_unique_items_from_list_column(column_name):
    test_df = df.copy()
    test_df[column_name] = test_df[column_name].apply(lambda x: eval(x) if isinstance(x, str) else x)
    all_items = set(item for sublist in test_df[column_name] if isinstance(sublist, list) for item in sublist )
    all_items_list = list(all_items)
    return all_items_list

# Metodo per trovare risultati in modo fuzzy 
def fuzzy_find(query_term, column):
    similar_title = process.extractOne(query_term, df[column])[0]
    return similar_title

# Metodo per trovare risultati in modo fuzzy su colonne che contengono liste
def fuzzy_find_in_list(item, column):
    items_list = extract_unique_items_from_list_column(column)
    lowercase_item_list = [s.lower() for s in items_list]

    similar_item_index = process.extractOne(
                item.lower(),
                lowercase_item_list)[2]

    similar_item = items_list[similar_item_index]

    return similar_item

def filter_df_by_column_single(dataset, item, column, msg=None):
    return dataset[dataset[column].apply(
        lambda items: item.lower() in 
        [ s.lower() for s in re.findall(r"'(.*?)'", items)]
        if isinstance(items, str) else False)]

def filter_df_by_column_batch(dataset, items, column, msg=None):
    filtered_df = pd.DataFrame(columns=dataset.columns)
    for i in range(len(items)):
        similar_item = fuzzy_find_in_list(items[i], column)

        if similar_item is None:
            if msg is not None:
                msg+= f"Didn't find {items[i]}"
                msg+= f"Didn't find really anything actually"
            continue
        else:
            if msg is not None and similar_item.lower() != items[i].lower():
                msg += f"Didn't find {items[i]}, searching for {similar_item} intstead.\n"
            items[i] = similar_item

        if msg is not None: 
            msg += f"Filtering for {similar_item}\n"
        games = filter_df_by_column_single(dataset, items[i], column, msg)

        if not games.empty:
            filtered_df = pd.concat([filtered_df, games]).drop_duplicates()
        
    return filtered_df


# Action that queries available genres
class GetGenres(Action):
    def name(self) -> Text:
        return "action_get_genres"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict):

        msg = 'Available videogame genres are:\n'
        genres = extract_unique_items_from_list_column("Genres")
        for genre in genres:
            msg += f'- {genre}\n'
        
        dispatcher.utter_message(msg)
        return []

# Action that queries info about given game 
class GetGameData(Action):
    def name(self) -> Text:
        return "action_get_game_data"

    def run(self,
            #slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        slots=tracker.slots
        title=tracker.get_slot('title')
        result = df[df['Title'].str.lower() == title.lower()]

        msg = f"Searching details about game: {title}...\n"
        dispatcher.utter_message(text=f"{msg}")
        msg = ""

        if result.empty:
            similar_title = process.extractOne(title.lower(),
                                      df['Title'].str.lower())[0]
            result = df[df['Title'].str.lower()==similar_title.lower()]
            msg += f"Didn't find {title}, searching for {similar_title} instead.\n"
                
        if not result.empty :
            row = result.iloc[0]
            msg += f"Here's some details about {row['Title']}:\n"
            msg += f"Release date: {row['Release Date']}\n"
            msg += f"Developed by: {row['Team']}\n"
            msg += f"Rating: {row['Rating']}/5\n"
            msg += f"Genres: {row['Genres']}\n"
            msg += " \n"
            msg += "Here's a brief summary:\n"
            msg += " \n"
            msg += f"{row['Summary']}"
        else:
            msg += f'No game named {title} was found.\n'
                

        print("risultato query")
        dispatcher.utter_message(text=f"{msg}")

        return [SlotSet("title", None)]

# risultato delle informazioni prodotti
class GetGameReviews(Action):
    def name(self) -> Text:
        return "action_get_game_reviews"

    def run(self,
            #slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        slots=tracker.slots
        title=tracker.get_slot('title')

        msg = f"Searching reviews for game: {title}...\n"
        similar_title = fuzzy_find(title, 'Title')
        
        if similar_title is not None and title.lower() != similar_title.lower():
            msg += f"Didn't find {title}, searching for {similar_title} intstead.\n"
            title=similar_title

        result = df[df['Title'].str.lower() == title.lower()]

        if result is not None and not result.empty:
            row = result.iloc[0]
            msg += f"Here's some reviews about {row['Title']}:\n"
            reviews = re.findall(r"'(.*?)'", row["Reviews"])
            counter = 0
            msg += "------------------------------------------------------------------------\n"
            msg += " \n"
            for review in reviews:
                msg += " \n"
                msg += f'{review}\n'
                msg += " \n"
                msg += "------------------------------------------------------------------------\n"
                counter += 1
                if(counter==5):
                    break
        else:
            msg += f'No game named {title} was found.\n'
            msg += f'{slots}'

        dispatcher.utter_message(text=f"{msg}")
        return [SlotSet("title", None)]

class GetTeamGames(Action):
    def name(self) -> Text:
        return "action_get_team_games"

    def run(self,
            #slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:


        team=tracker.get_slot('teams')[0]
        msg = f"Searching for team: {team}...\n"

        similar_team = fuzzy_find_in_list(team, "Team")

        if similar_team is not None and similar_team.lower() != team.lower():
            msg += f"Didn't find {team}, searching for {similar_team} intstead.\n"
            team = similar_team

        result = filter_df_by_column_batch(df,[team], 'Team', msg)

        if result is not None and not result.empty:
            msg += f"Here's a list of games made by {team}:\n"
            for title in result['Title']:
                msg += '\n'
                msg += f"- {title}"
        else:
            msg += f'No game made by {team} was found porcodio.\n'
            slots=tracker.slots
            msg += f'{slots}'

        dispatcher.utter_message(text=f"{msg}")
        result = None
        return [SlotSet("teams", None)]

class GetGamesRecommendaton(Action):
    def name(self) -> Text:
        return "action_get_games_recommendation"

    def run(self,
            #slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        result = df.copy()
        teams=tracker.get_slot('teams')
        genres=tracker.get_slot('genres')
        msg = ""

        if teams and teams != ["NO"]:
            #msg += f'Filtering for team\n'
            result = filter_df_by_column_batch(result, teams, "Team", msg)
            #msg += f'{result}\n'

        if genres and genres != ["NO"]:
            #msg += f'Filtering for genres\n'
            result = filter_df_by_column_batch(result, genres, "Genres", msg)
            #msg += f'{result}\n'


        if not result.empty:
            result = result.sort_values(by='Rating', ascending=False)
            msg += f"Here's a list of games that follow your recommendations by:\n"
            counter = 0
            for index, game in result.iterrows():
                msg += '\n'
                msg += f"- {game['Title']} ({game['Rating']}/5)"
                counter+=1
                if counter == 10:
                    break
            slots=tracker.slots
            #msg += f"{slots}"
        else:
            msg += f'No games were found.\n'
            slots=tracker.slots
            #msg += f'{slots}'

        dispatcher.utter_message(text=f"{msg}")
        result = None
        return [SlotSet("genres_filter", None), SlotSet("teams_filter", None), SlotSet("teams", None), SlotSet("genres", None)]

class ValidateGamesRecommendationForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_games_recommendation_form"

    def validate_genres_filter(
        self,
        value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> Dict[Text, Any]:

        if tracker.get_intent_of_latest_message() == "affirm_genres_filter":
            return {"genres_filter": True}
        elif tracker.get_intent_of_latest_message() == "deny_genres_filter":
            dispatcher.utter_message(text="Ok, I won't filter by genre.")
            return {"genres_filter": False, "genres": ["NO"]}
        #dispatcher.utter_message(text="I didn't get that")
        return {"genres_filter": None}


    def validate_genres(
        self,
        value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> Dict[Text, Any]:
        if not tracker.get_slot("genres_filter"):
            dispatcher.utter_message(text="Ok, I won't search for a specific genre!")
            return {"genres": ["NO"]}
        else:
            dispatcher.utter_message(text=f"Ok, I will filter by {tracker.get_slot('genres')}")
            return {"genres": value}
    
    def validate_teams_filter(
        self,
        value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> Dict[Text, Any]:
        if tracker.get_intent_of_latest_message() == "affirm_teams_filter":
            return {"teams_filter": True}
        elif tracker.get_intent_of_latest_message() == "deny_teams_filter":
            dispatcher.utter_message(text="Ok, I won't filter by team.")
            return {"teams_filter": False, "teams": ["NO"]}
        #dispatcher.utter_message(text="I didn't get that")
        return {"teams_filter": None}

    def validate_teams(
        self,
        value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> Dict[Text, Any]:
        if not tracker.get_slot("teams_filter"):
            dispatcher.utter_message(text="Ok, I won't search for a specific dev team!")
            return {"teams": ["NO"]}
        else:
            dispatcher.utter_message(text=f"Ok, I will filter by {tracker.get_slot('teams')}")
            return {"teams": value}

class AskForGenresFiler(Action):
    def name(self) -> Text:
        return "action_ask_genres_filter"
    
    def run(self,
            #slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="Would you like to filter by genre?",
                                 buttons=[
                                     {"title": "yes", "payload": "/affirm_genres_filter"},
                                     {"title": "no", "payload": "/deny_genres_filter"}
                                 ],
                                 button_type="inline")
        return []

class AskForTeamsFiler(Action):
    def name(self) -> Text:
        return "action_ask_teams_filter"
    
    def run(self,
            #slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="Woult you like to filter by dev team?",
                                 buttons=[
                                     {"title": "yes", "payload": "/affirm_teams_filter"},
                                     {"title": "no", "payload": "/deny_teams_filter"}
                                 ],
                                 button_type="inline")
        return []

class AskForGenres(Action):
    def name(self) -> Text:
        return "action_ask_genres"
    
    def run(self,
            #slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        if tracker.get_slot("genres_filter"):
            dispatcher.utter_message("What kind of genre do you prefer?")
        else:
            SlotSet("genres", ["NO"])
        return []

class AskForTeams(Action):
    def name(self) -> Text:
        return "action_ask_teams"
    
    def run(self,
            #slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        if tracker.get_slot("teams_filter"):
            dispatcher.utter_message("What development team do you prefer?")
        else:
            SlotSet("teams", ["NO"])
        return []
