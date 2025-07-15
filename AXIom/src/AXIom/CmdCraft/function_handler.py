import os
import requests
from typing import Dict, Any
# my IDE was being weird, still works just an IDE thing
# noinspection PyUnresolvedReferences
from dotenv import load_dotenv
# noinspection PyUnresolvedReferences
from newsapi import NewsApiClient

load_dotenv()

# Map of function names to their required parameters.
# Parameters can be a single string or a list of strings.
"""
Module: Function Handler
Manages a collection of callable functions and their associated parameters.
It also handles API key initialization for external services.
NOTE: FUNCTIONS ARE NOT CALLED HERE, THEY ARE CALLED FROM THE CMD-HANDLER
"""

class FunctionHandler:

    def __init__(self):
        """
        Initializes the FunctionHandler with API keys and an empty list
        to track function calls.
        """
        self.function_name = None
        self.function_params = None
        self.function_calls = []

        # Load API keys from environment variables
        self.WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
        self.NEWS_API_KEY = os.getenv("NEWS_API_KEY")

        # Initialize News API client
        self.newsapi = NewsApiClient(api_key=self.NEWS_API_KEY)

    def set_function_call(self, function_name: str, function_params: Dict[str, Any]) -> None:
        """
        Sets the current function call details and appends it to the history of calls.

        Args:
            function_name (str): The name of the function to be called.
            function_params (Dict[str, Any]): A dictionary of parameters for the function.
        """
        self.function_name = function_name
        self.function_params = function_params
        self.function_calls.append(self._get_function_call_dict())

    def _get_function_call_dict(self) -> Dict:
        """
        Returns the current function call details as a dictionary.

        Returns:
            Dict: A dictionary containing the function name and its parameters.
        """
        return {
            "function_name": self.function_name,
            "function_params": self.function_params
        }

    def print_function_calls(self) -> None:
        """
        Prints a formatted list of all recorded function calls.
        """
        for function_call in self.function_calls:
            print("=" * 50)
            print(f"Function Call:")
            print(f"  Called Function: {function_call['function_name']}")
            print(f"  Function Parameters: {function_call['function_params']}")
            print("=" * 50)

    def get_weather(self, **kwargs) -> None:
        """
        Retrieves and prints current weather data for a specified location.

        Args:
            **kwargs: Expected to contain 'location' (str).
        """
        location = kwargs.get("location")
        if not location:
            print("Error: Location is required for get_weather.")
            return

        url = f"https://api.weatherstack.com/current?access_key={self.WEATHER_API_KEY}"
        query = {"query": location}

        try:
            response = requests.get(url, params=query)
            response.raise_for_status()  # Raise an exception for HTTP errors
            data = response.json()

            if "success" in data and not data["success"]:
                print(f"Error fetching weather data: {data.get('error', {}).get('info', 'Unknown error')}")
                return

            location_data = data.get("location", {})
            current_weather = data.get("current", {})

            print(f"\n{'=' * 75}")
            print(f"Getting weather for {location}")
            print(f"\nLocation: {location_data.get('name', 'N/A')}, "
                  f"{location_data.get('region', 'N/A')}, "
                  f"{location_data.get('country', 'N/A')}")
            print(f"Local Time: {location_data.get('localtime', 'N/A')}")
            print(f"Weather: {current_weather.get('weather_descriptions', ['N/A'])[0]}")
            print(f"Temperature: {current_weather.get('temperature', 'N/A')}°C "
                  f"(Feels like {current_weather.get('feelslike', 'N/A')}°C)")
            print(f"Humidity: {current_weather.get('humidity', 'N/A')}%")
            print(f"Wind: {current_weather.get('wind_speed', 'N/A')} km/h "
                  f"from {current_weather.get('wind_dir', 'N/A')}")
            print(f"Visibility: {current_weather.get('visibility', 'N/A')} km")
            print(f"Cloud Cover: {current_weather.get('cloudcover', 'N/A')}%")
            print(f"UV Index: {current_weather.get('uv_index', 'N/A')}")
            print(f"Precipitation: {current_weather.get('precip', 'N/A')} mm")
            print(f"Pressure: {current_weather.get('pressure', 'N/A')} hPa")
            print(f"\n{'=' * 75}")

        except requests.exceptions.RequestException as e:
            print(f"Network or API error while fetching weather: {e}")
        except KeyError as e:
            print(f"Error parsing weather data: Missing key {e}. Response: {data}")

    def get_stock(self, **kwargs) -> None:
        """
        Placeholder function to simulate getting stock data.

        Args:
            **kwargs: Expected to contain 'stock_name' (str).
        """
        stock_name = kwargs.get("stock_name")
        if not stock_name:
            print("Error: Stock name is required for get_stock.")
            return

        print(f"\n{'=' * 75}\n")
        print(f"Getting stock data for {stock_name} (Functionality not yet implemented)")
        print(f"\n{'=' * 75}\n")

    def get_news(self, **kwargs) -> None:
        """
        Retrieves and prints top news headlines for a specified topic.

        Args:
            **kwargs: Expected to contain 'topic' (str).
        """
        topic = kwargs.get("topic")
        if not topic:
            print("Error: Topic is required for get_news.")
            return

        try:
            top_headlines = self.newsapi.get_top_headlines(q=topic, language='en', country='us', category='business')

            articles = top_headlines.get('articles', [])
            status = top_headlines.get('status', 'N/A')

            print(f"\n{'=' * 75}\n")
            print(f"Getting news for '{topic}'")
            print(f"Status: {status}")

            if articles:
                print("Articles:")
                for i, article in enumerate(articles):
                    title = article.get('title', 'No Title')
                    author = article.get('author', 'Unknown Author')
                    content = article.get('content', 'No content available.')
                    source = article.get('source', {}).get('name', 'Unknown Source')
                    url = article.get('url', '#')

                    print(f"\n{i+1}. {title}")
                    print(f"   By {author} from {source}")
                    print(f"   Content: {content.split(' [+')[0]}...") # Truncate "[+... chars]"
                    print(f"   Read more: {url}")
            else:
                print("No articles found for this topic.")
            print(f"\n{'=' * 75}\n")

        except Exception as e:
            print(f"Error fetching news: {e}")

    def schedule(self, **kwargs) -> None:
        """
        Placeholder function to simulate scheduling an event.

        Args:
            **kwargs: Expected to contain 'user' (str), 'event' (str), and 'time' (str).
                      'time' should be in RFC3339 format (e.g., "2025-06-01T15:00:00-05:00").
        """
        user = kwargs.get("user")
        event_title = kwargs.get("event")
        event_time = kwargs.get("time")

        if not all([user, event_title, event_time]):
            print("Error: 'user', 'event', and 'time' are required for schedule.")
            return

        print(f"\n{'=' * 75}\n")
        print(f"Scheduling '{event_title}' for {user} at {event_time} (Calendar integration not active)")
        print(f"\n{'=' * 75}\n")

    def notify(self, **kwargs) -> None:
        """
        Placeholder function to simulate sending a notification.

        Args:
            **kwargs: Expected to contain 'recipient' (str) and 'message' (str).
        """
        recipient = kwargs.get("recipient")
        message = kwargs.get("message")

        if not all([recipient, message]):
            print("Error: 'recipient' and 'message' are required for notify.")
            return

        print(f"\n{'=' * 75}\n")
        print(f"Notifying {recipient}: '{message}' (Notification system not active)")
        print(f"\n{'=' * 75}\n")

    def create_resident(self, **kwargs) -> None:
        """
        Placeholder function to simulate creating a resident entry.

        Args:
            **kwargs: Expected to contain 'name' (str), 'weight' (Any), and 'height' (Any).
        """
        name = kwargs.get("name")
        weight = kwargs.get("weight")
        height = kwargs.get("height")

        if not all([name, weight, height]):
            print("Error: 'name', 'weight', and 'height' are required for create_resident.")
            return

        print(f"\n{'=' * 75}\n")
        print(f"Creating resident {name} with weight {weight} and height {height}")
        print(f"\n{'=' * 75}\n")

    def create_staff(self, **kwargs) -> None:
        """
        Placeholder function to simulate creating a staff entry.

        Args:
            **kwargs: Expected to contain 'name' (str), 'weight' (Any),
                      'height' (Any), and 'temp' (Any).
        """
        name = kwargs.get("name")
        weight = kwargs.get("weight")
        height = kwargs.get("height")
        temp = kwargs.get("temp")

        if not all([name, weight, height, temp]):
            print("Error: 'name', 'weight', 'height', and 'temp' are required for create_staff.")
            return

        print(f"\n{'=' * 75}\n")
        print(f"Creating staff {name} with weight {weight}, height {height}, and temperature {temp}")
        print(f"\n{'=' * 75}\n")

    def create_visitor(self, **kwargs) -> None:
        """
        Placeholder function to simulate creating a visitor entry.

        Args:
            **kwargs: Expected to contain 'name' (str) and 'purpose' (str).
        """
        name = kwargs.get("name")
        purpose = kwargs.get("purpose")

        if not all([name, purpose]):
            print("Error: 'name' and 'purpose' are required for create_visitor.")
            return

        print(f"\n{'=' * 75}\n")
        print(f"Creating visitor {name} for purpose: {purpose}")
        print(f"\n{'=' * 75}\n")



