import os
import requests
from typing import Dict, Any
import logging
# noinspection PyUnresolvedReferences
from dotenv import load_dotenv
# noinspection PyUnresolvedReferences
from newsapi import NewsApiClient

load_dotenv()


class FunctionHandler:

    def __init__(self):
        self.function_name = None
        self.function_params = None
        self.function_calls = []
        
        self.WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
        self.NEWS_API_KEY = os.getenv("NEWS_API_KEY")

        self.newsapi = NewsApiClient(api_key=self.NEWS_API_KEY)
        self.logger = self._setup_logger()

    @staticmethod
    def _setup_logger(level=logging.INFO) -> logging.Logger:
        logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=level)
        return logging.getLogger('FunctionHandler')

    def set_function_call(self, function_name: str, function_params: Dict[str, Any]) -> None:
        self.function_name = function_name
        self.function_params = function_params
        self.function_calls.append(self._get_function_call_dict())

    def _get_function_call_dict(self) -> Dict:
        return {
            "function_name": self.function_name,
            "function_params": self.function_params
        }

    def print_function_calls(self) -> None:
        for function_call in self.function_calls:
            self.logger.info("=" * 50)
            self.logger.info(f"Function Call:")
            self.logger.info(f"  Called Function: {function_call['function_name']}")
            self.logger.info(f"  Function Parameters: {function_call['function_params']}")
            self.logger.info("=" * 50)

    def get_weather(self, **kwargs) -> None:
        location = kwargs.get("location")
        if not location:
            self.logger.error("Location is required for get_weather.")
            return

        url = f"https://api.weatherstack.com/current?access_key={self.WEATHER_API_KEY}"
        query = {"query": location}

        try:
            response = requests.get(url, params=query)
            response.raise_for_status()
            data = response.json()

            if "success" in data and not data["success"]:
                self.logger.error(f"Error fetching weather data: {data.get('error', {}).get('info', 'Unknown error')}")
                return

            location_data = data.get("location", {})
            current_weather = data.get("current", {})

            self.logger.info(f"Getting weather for {location}")
            self.logger.info(f"Location: {location_data.get('name', 'N/A')}, "
                             f"{location_data.get('region', 'N/A')}, "
                             f"{location_data.get('country', 'N/A')}")
            self.logger.info(f"Local Time: {location_data.get('localtime', 'N/A')}")
            self.logger.info(f"Weather: {current_weather.get('weather_descriptions', ['N/A'])[0]}")
            self.logger.info(f"Temperature: {current_weather.get('temperature', 'N/A')} °C "
                             f"(Feels like {current_weather.get('feelslike', 'N/A')} °C)")
            self.logger.info(f"Humidity: {current_weather.get('humidity', 'N/A')}%")
            self.logger.info(f"Wind: {current_weather.get('wind_speed', 'N/A')} km/h from {current_weather.get('wind_dir', 'N/A')}")
            self.logger.info(f"Visibility: {current_weather.get('visibility', 'N/A')} km")
            self.logger.info(f"Cloud Cover: {current_weather.get('cloudcover', 'N/A')}%")
            self.logger.info(f"UV Index: {current_weather.get('uv_index', 'N/A')}")
            self.logger.info(f"Precipitation: {current_weather.get('precip', 'N/A')} mm")
            self.logger.info(f"Pressure: {current_weather.get('pressure', 'N/A')} hPa")

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network or API error while fetching weather: {e}")
        except KeyError as e:
            self.logger.error(f"Error parsing weather data: Missing key {e}. Response: {data}")

    def get_stock(self, **kwargs) -> None:
        stock_name = kwargs.get("stock_name")
        if not stock_name:
            self.logger.error("Stock name is required for get_stock.")
            return

        self.logger.info(f"Getting stock data for {stock_name} (Functionality not yet implemented)")

    def get_news(self, **kwargs) -> None:
        topic = kwargs.get("topic")
        if not topic:
            self.logger.error("Topic is required for get_news.")
            return

        try:
            top_headlines = self.newsapi.get_top_headlines(q=topic, language='en', country='us', category='business')

            articles = top_headlines.get('articles', [])
            status = top_headlines.get('status', 'N/A')

            self.logger.info(f"Getting news for '{topic}'")
            self.logger.info(f"Status: {status}")

            if articles:
                for i, article in enumerate(articles):
                    title = article.get('title', 'No Title')
                    author = article.get('author', 'Unknown Author')
                    content = article.get('content', 'No content available.')
                    source = article.get('source', {}).get('name', 'Unknown Source')
                    url = article.get('url', '#')

                    self.logger.info(f"{i + 1}. {title}")
                    self.logger.info(f"   By {author} from {source}")
                    self.logger.info(f"   Content: {content.split(' [+')[0]}...")
                    self.logger.info(f"   Read more: {url}")
            else:
                self.logger.info("No articles found for this topic.")

        except Exception as e:
            self.logger.error(f"Error fetching news: {e}")

    def schedule(self, **kwargs) -> None:
        user = kwargs.get("user")
        event_title = kwargs.get("event")
        event_time = kwargs.get("time")

        if not all([user, event_title, event_time]):
            self.logger.error("'user', 'event', and 'time' are required for schedule.")
            return

        self.logger.info(f"Scheduling '{event_title}' for {user} at {event_time} (Calendar integration not active)")

    def notify(self, **kwargs) -> None:
        recipient = kwargs.get("recipient")
        message = kwargs.get("message")

        if not all([recipient, message]):
            self.logger.error("'recipient' and 'message' are required for notify.")
            return

        self.logger.info(f"Notifying {recipient}: '{message}' (Notification system not active)")

    def create_resident(self, **kwargs) -> None:
        name = kwargs.get("name")
        weight = kwargs.get("weight")
        height = kwargs.get("height")

        if not all([name, weight, height]):
            self.logger.error("'name', 'weight', and 'height' are required for create_resident.")
            return

        self.logger.info(f"Creating resident {name} with weight {weight} and height {height}")

    def create_staff(self, **kwargs) -> None:
        name = kwargs.get("name")
        weight = kwargs.get("weight")
        height = kwargs.get("height")
        temp = kwargs.get("temp")

        if not all([name, weight, height, temp]):
            self.logger.error("'name', 'weight', 'height', and 'temp' are required for create_staff.")
            return

        self.logger.info(f"Creating staff {name} with weight {weight}, height {height}, and temperature {temp}")

    def create_visitor(self, **kwargs) -> None:
        name = kwargs.get("name")
        purpose = kwargs.get("purpose")

        if not all([name, purpose]):
            self.logger.error("'name' and 'purpose' are required for create_visitor.")
            return

        self.logger.info(f"Creating visitor {name} for purpose: {purpose}")
