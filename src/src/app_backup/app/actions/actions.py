# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

# from typing import Any, Text, Dict, List
#
# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher
#
#
# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []

#Azione che permette di visualizzare lista dei brand
class GetGenres(Action):
    def name(self) -> Text:
        return "get_genres"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict):
        
        
        query = 'SELECT DISTINCT brands FROM genres'

        cursor.execute(query)
        result = cursor.fetchall()
        if len(result) == 0:
            dispatcher.utter_message("There is no videogame genre in our catalog!")
        else:
            brd='Possible videogame genre are: \n'
            buttons=[]
            for elem in result:
                brd=brd+f' - {elem[0]}\n'
                buttons.append({"title": elem[0], "payload": f'/viewBrandProduct{{"brand":"{elem[0]}"}}'})
            dispatcher.utter_button_message(brd,buttons)
            #dispatcher.utter_message(text=brd)

        return []
# risultato delle informazioni prodotti
class QueryResult(Action):
    def name(self) -> Text:
        return "query_result"

    def run(self,
            #slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        emptyQuery = True
        beofore = False
        BasicQueryString = 'SELECT name,quantity,servin_size,category,ingredients FROM mulino_bianco WHERE '
        title=tracker.get_slot('title')

        print("risultato query")
        #return [{"name":"info_ingredienti","event":"slot","value":None},{"name":"info_serving","event":"slot","value":None},{"name":"info_categoria","event":"slot","value":None},{"name":"info_quantity","event":"slot","value":None}]
        return [{"name":"title","event":"slot","value":None}]
