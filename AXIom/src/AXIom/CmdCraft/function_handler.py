# function_handler.py
import os
import requests
from typing import Dict, Any
from dotenv import load_dotenv
from newsapi import  NewsApiClient
from scheduler import get_calendar_service

load_dotenv()
# environment variables

"""
Module: Function Handler
Handles all functions that need to be call and 
the functions parameters
NOTE: The functions are NOT called here, they are call from the cmd_handler
"""

class FunctionHandler:

    # map of function names to function parameters
    FUNCTION_MAP = {
        "get_weather": "location",
        "get_news": "topic",
        "get_stock": "stock_name",
        "schedule": ["user", "event", "time"],
        "notify": ["recipient", "message"],
        "create_resident": ["name", "weight", "height"],
        "create_staff": ["name", "weight", "height", "temp"],
        "create_visitor": ["name", "purpose"],
    }


    def __init__(self):

        self.function_name = None
        self.function_params = None
        self.function_calls = []
        # Set API keussssss
        self.WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
        self.NEWS_API_KEY = os.getenv("NEWS_API_KEY")

        # initialize news api client
        self.newsapi = NewsApiClient(api_key=self.NEWS_API_KEY)

    def set_function_call(self, function_name: str, function_params: Dict[str, Any]) -> None:
        self.function_name = function_name
        self.function_params = function_params
        self.function_calls.append(self.get_function_call())

    def get_function_call(self) -> Dict:
        """
        Returns the name of the function and its parameters as a dictionary
        :return: function call as a dictionary
        """
        return {
            "function_name": self.function_name,
            "function_params": self.function_params
        }
    def print_function_calls(self):

        for function_call in self.function_calls:
            print("="*50)
            print(f"Function Call: \nCalled Function: {function_call['function_name']} \nFunction Parameters: {function_call['function_params']}")
            print("=" * 50)

    def get_weather(self, **kwargs):

        # unpack the arguments
        location = kwargs.get("location")
        # get the weather data from the API
        url = f"https://api.weatherstack.com/current?access_key={self.WEATHER_API_KEY}"
        query = {"query": location}
        response = requests.get(url, params=query)
        data = response.json()

        # save location data
        location_data = data["location"]
        # save current weather stats
        current = data["current"]

        # print the formatted results
        print(f"\n{'=' * 75}")
        print(f"Getting weather for {location}")
        print(f"\nLocation: {location_data['name']}, {location_data['region']}, {location_data['country']}")
        print(f"Local Time: {location_data['localtime']}")
        print(f"Weather: {current['weather_descriptions'][0]}")
        print(f"Temperature: {current['temperature']}°C (Feels like {current['feelslike']}°C)")
        print(f"Humidity: {current['humidity']}%")
        print(f"Wind: {current['wind_speed']} km/h from {current['wind_dir']}")
        print(f"Visibility: {current['visibility']} km")
        print(f"Cloud Cover: {current['cloudcover']}%")
        print(f"UV Index: {current.get('uv_index', 'N/A')}")
        print(f"Precipitation: {current['precip']} mm")
        print(f"Pressure: {current['pressure']} hPa")
        print(f"\n{'=' * 75}")

    def get_stock(self, **kwargs):
        stock = kwargs.get("topic")
        print(f"\n{'=' * 75}\n")
        print(f"Getting stock data for {stock}")
        print(f"\n{'=' * 75}\n")

    def get_news(self, **kwargs):
        # unpack args
        topic = kwargs.get("topic")
        # get news articles
        top_headlines = self.newsapi.get_top_headlines(q=topic,language='en', country='us', category='business')

        articles = top_headlines['articles']
        titles = [article['title'] for article in articles]
        authors = [article['author'] for article in articles]
        status = top_headlines['status']

        # print the shit
        print(f"\n{'=' * 75}\n")
        print(f"Getting news for {topic}")
        print(f"Status: {status}")
        print(f"Articles:")
        for i in range(len(titles)):
            print(f"{i+1}. {titles[i]} by {authors[i]}")
            # print any content
            print(f"{articles[i]['content']}")
        print(f"\n{'=' * 75}\n")

    def schedule(self, **kwargs):
        user = kwargs.get("user")
        event_title = kwargs.get("event")
        event_time = kwargs.get("time")  # Expected in RFC3339 format: "2025-06-01T15:00:00-05:00"

        print(f"\n{'=' * 75}\n")
        print(f"Scheduling {event_title} for {user} at {event_time}")

        service = get_calendar_service()

        event = {
            'summary': event_title,
            'description': f"Scheduled by ARA for {user}",
            'start': {
                'dateTime': event_time,
                'timeZone': 'America/Chicago',
            },
            'end': {
                'dateTime': event_time,  # Ideally add duration
                'timeZone': 'America/Chicago',
            }
        }

        created_event = service.events().insert(calendarId='primary', body=event).execute()
        print(f"Event created: {created_event.get('htmlLink')}")
        print(f"\n{'=' * 75}\n")

    def notify(self, **kwargs):
        recipient = kwargs.get("recipient")
        message = kwargs.get("message")
        print(f"\n{'=' * 75}\n")
        print(f"Notifying {recipient} of {message}")
        print(f"\n{'=' * 75}\n")

    def create_resident(self, **kwargs):
        name = kwargs.get("name")
        weight = kwargs.get("weight")
        height = kwargs.get("height")
        print(f"\n{'=' * 75}\n")
        print(f"Creating resident {name} with weight {weight} and height {height}")
        print(f"\n{'=' * 75}\n")

    def create_staff(self, **kwargs):
        name = kwargs.get("name")
        weight = kwargs.get("weight")
        height = kwargs.get("height")
        temp = kwargs.get("temp")
        print(f"\n{'=' * 75}\n")
        print(f"Creating staff {name} with weight {weight} and height {height} and temperature {temp}")
        print(f"\n{'=' * 75}\n")

    def create_visitor(self, **kwargs):
        name = kwargs.get("name")
        purpose = kwargs.get("purpose")
        print(f"\n{'=' * 75}\n")
        print(f"Creating visitor {name} for {purpose}")
        print(f"\n{'=' * 75}\n")




