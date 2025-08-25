import os
import requests
from typing import Dict, Any
import logging
import time
import json
from datetime import datetime, timedelta
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
        
        # Initialize metrics tracking
        self.metrics = {
            'api_calls': {
                'weather': {'total': 0, 'success': 0, 'failed': 0, 'response_times': [], 'last_called': None},
                'news': {'total': 0, 'success': 0, 'failed': 0, 'response_times': [], 'last_called': None},
                'stock': {'total': 0, 'success': 0, 'failed': 0, 'response_times': [], 'last_called': None},
                'google': {'total': 0, 'success': 0, 'failed': 0, 'response_times': [], 'last_called': None}
            },
            'function_calls': {
                'total': 0,
                'by_function': {},
                'success_rate': 0.0
            },
            'system': {
                'start_time': datetime.now(),
                'uptime': None,
                'total_requests': 0
            }
        }
        
        # Load existing metrics if available
        self._load_metrics()

    @staticmethod
    def _setup_logger(level=logging.INFO) -> logging.Logger:
        logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=level)
        return logging.getLogger('FunctionHandler')

    def _load_metrics(self):
        """Load metrics from persistent storage if available."""
        try:
            metrics_file = os.path.join(os.path.dirname(__file__), '..', '..', 'metrics.json')
            if os.path.exists(metrics_file):
                with open(metrics_file, 'r') as f:
                    saved_metrics = json.load(f)
                    # Merge with current metrics, preserving existing data
                    for key in saved_metrics:
                        if key in self.metrics:
                            if isinstance(saved_metrics[key], dict):
                                self.metrics[key].update(saved_metrics[key])
                            else:
                                self.metrics[key] = saved_metrics[key]
                
                # Convert string dates back to datetime objects
                if 'system' in saved_metrics and 'start_time' in saved_metrics['system']:
                    try:
                        if isinstance(saved_metrics['system']['start_time'], str):
                            self.metrics['system']['start_time'] = datetime.fromisoformat(saved_metrics['system']['start_time'])
                    except ValueError:
                        # If conversion fails, use current time
                        self.metrics['system']['start_time'] = datetime.now()
                
                # Convert last_called timestamps back to datetime objects
                for api_name, api_data in self.metrics['api_calls'].items():
                    if 'last_called' in api_data and api_data['last_called']:
                        try:
                            if isinstance(api_data['last_called'], str):
                                api_data['last_called'] = datetime.fromisoformat(api_data['last_called'])
                        except ValueError:
                            api_data['last_called'] = None
                
                self.logger.info("Loaded existing metrics from file")
        except Exception as e:
            self.logger.warning(f"Could not load metrics: {e}")

    def _save_metrics(self):
        """Save metrics to persistent storage."""
        try:
            metrics_file = os.path.join(os.path.dirname(__file__), '..', '..', 'metrics.json')
            # Create a copy for serialization
            metrics_to_save = {}
            for key, value in self.metrics.items():
                if key == 'system':
                    # Handle system metrics specially
                    system_copy = value.copy()
                    if isinstance(system_copy['start_time'], datetime):
                        system_copy['start_time'] = system_copy['start_time'].isoformat()
                    if isinstance(system_copy['uptime'], str):
                        system_copy['uptime'] = str(system_copy['uptime'])
                    metrics_to_save[key] = system_copy
                elif key == 'api_calls':
                    # Handle API calls specially
                    api_calls_copy = {}
                    for api_name, api_data in value.items():
                        api_copy = api_data.copy()
                        if 'last_called' in api_copy and api_copy['last_called']:
                            if isinstance(api_copy['last_called'], datetime):
                                api_copy['last_called'] = api_copy['last_called'].isoformat()
                        api_calls_copy[api_name] = api_copy
                    metrics_to_save[key] = api_calls_copy
                else:
                    metrics_to_save[key] = value
            
            with open(metrics_file, 'w') as f:
                json.dump(metrics_to_save, f, indent=2, default=str)
        except Exception as e:
            self.logger.warning(f"Could not save metrics: {e}")

    def _track_api_call(self, api_name: str, start_time: float, success: bool, error: str = None):
        """Track API call metrics."""
        if api_name not in self.metrics['api_calls']:
            self.metrics['api_calls'][api_name] = {
                'total': 0, 'success': 0, 'failed': 0, 
                'response_times': [], 'last_called': None
            }
        
        api_metrics = self.metrics['api_calls'][api_name]
        api_metrics['total'] += 1
        api_metrics['last_called'] = datetime.now().isoformat()
        
        if success:
            api_metrics['success'] += 1
            response_time = time.time() - start_time
            api_metrics['response_times'].append(response_time)
            # Keep only last 100 response times for performance
            if len(api_metrics['response_times']) > 100:
                api_metrics['response_times'] = api_metrics['response_times'][-100:]
        else:
            api_metrics['failed'] += 1
        
        # Update system metrics
        self.metrics['system']['total_requests'] += 1
        
        # Save metrics periodically
        if self.metrics['system']['total_requests'] % 10 == 0:  # Save every 10 requests
            self._save_metrics()

    def _track_function_call(self, function_name: str, success: bool):
        """Track function call metrics."""
        if function_name not in self.metrics['function_calls']['by_function']:
            self.metrics['function_calls']['by_function'][function_name] = {
                'total': 0, 'success': 0, 'failed': 0
            }
        
        func_metrics = self.metrics['function_calls']['by_function'][function_name]
        func_metrics['total'] += 1
        
        if success:
            func_metrics['success'] += 1
        else:
            func_metrics['failed'] += 1
        
        # Update overall function call metrics
        self.metrics['function_calls']['total'] += 1
        total_success = sum(f['success'] for f in self.metrics['function_calls']['by_function'].values())
        self.metrics['function_calls']['success_rate'] = (total_success / self.metrics['function_calls']['total']) * 100

    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics overview."""
        # Update uptime - ensure start_time is a datetime object
        if isinstance(self.metrics['system']['start_time'], str):
            try:
                self.metrics['system']['start_time'] = datetime.fromisoformat(self.metrics['system']['start_time'])
            except ValueError:
                self.metrics['system']['start_time'] = datetime.now()
        
        # Calculate uptime
        if isinstance(self.metrics['system']['start_time'], datetime):
            self.metrics['system']['uptime'] = str(datetime.now() - self.metrics['system']['start_time'])
        else:
            self.metrics['system']['uptime'] = "Unknown"
        
        # Calculate API success rates and average response times
        for api_name, api_data in self.metrics['api_calls'].items():
            if api_data['total'] > 0:
                api_data['success_rate'] = (api_data['success'] / api_data['total']) * 100
                if api_data['response_times']:
                    api_data['avg_response_time'] = sum(api_data['response_times']) / len(api_data['response_times'])
                    api_data['min_response_time'] = min(api_data['response_times'])
                    api_data['max_response_time'] = max(api_data['response_times'])
                else:
                    api_data['avg_response_time'] = 0
                    api_data['min_response_time'] = 0
                    api_data['max_response_time'] = 0
            else:
                api_data['success_rate'] = 0
                api_data['avg_response_time'] = 0
                api_data['min_response_time'] = 0
                api_data['max_response_time'] = 0
        
        return self.metrics

    def print_metrics(self) -> None:
        """Print formatted metrics to console."""
        metrics = self.get_metrics()
        
        print("\n" + "="*60)
        print("AXIOM API USAGE METRICS")
        print("="*60)
        
        # System Overview
        print(f"\n📊 SYSTEM OVERVIEW:")
        print(f"   Start Time: {metrics['system']['start_time']}")
        print(f"   Uptime: {metrics['system']['uptime']}")
        print(f"   Total Requests: {metrics['system']['total_requests']}")
        
        # API Usage Summary
        print(f"\n🌐 API USAGE SUMMARY:")
        total_api_calls = sum(api['total'] for api in metrics['api_calls'].values())
        total_api_success = sum(api['success'] for api in metrics['api_calls'].values())
        overall_api_success_rate = (total_api_success / total_api_calls * 100) if total_api_calls > 0 else 0
        
        print(f"   Total API Calls: {total_api_calls}")
        print(f"   Overall Success Rate: {overall_api_success_rate:.1f}%")
        
        # Individual API Metrics
        print(f"\n🔍 DETAILED API METRICS:")
        for api_name, api_data in metrics['api_calls'].items():
            if api_data['total'] > 0:
                print(f"\n   📡 {api_name.upper()} API:")
                print(f"      Total Calls: {api_data['total']}")
                print(f"      Success: {api_data['success']} ({api_data['success_rate']:.1f}%)")
                print(f"      Failed: {api_data['failed']}")
                print(f"      Avg Response Time: {api_data['avg_response_time']:.3f}s")
                print(f"      Min/Max Response Time: {api_data['min_response_time']:.3f}s / {api_data['max_response_time']:.3f}s")
                if api_data['last_called']:
                    if isinstance(api_data['last_called'], str):
                        try:
                            last_called = datetime.fromisoformat(api_data['last_called'])
                            time_ago = datetime.now() - last_called
                            print(f"      Last Called: {time_ago.total_seconds():.0f}s ago")
                        except ValueError:
                            print(f"      Last Called: {api_data['last_called']}")
                    elif isinstance(api_data['last_called'], datetime):
                        time_ago = datetime.now() - api_data['last_called']
                        print(f"      Last Called: {time_ago.total_seconds():.0f}s ago")
                    else:
                        print(f"      Last Called: Unknown")
            else:
                print(f"\n   📡 {api_name.upper()} API: No calls yet")
        
        # Function Call Metrics
        print(f"\n⚙️ FUNCTION CALL METRICS:")
        print(f"   Total Function Calls: {metrics['function_calls']['total']}")
        print(f"   Overall Success Rate: {metrics['function_calls']['success_rate']:.1f}%")
        
        for func_name, func_data in metrics['function_calls']['by_function'].items():
            if func_data['total'] > 0:
                func_success_rate = (func_data['success'] / func_data['total']) * 100
                print(f"      {func_name}: {func_data['total']} calls, {func_success_rate:.1f}% success")
        
        print("\n" + "="*60)
        
        # Save metrics after displaying
        self._save_metrics()

    def get_api_usage_summary(self) -> str:
        """Get a brief API usage summary as a string."""
        metrics = self.get_metrics()
        
        summary = []
        summary.append("API Usage Summary:")
        
        for api_name, api_data in metrics['api_calls'].items():
            if api_data['total'] > 0:
                success_rate = (api_data['success'] / api_data['total']) * 100
                avg_time = sum(api_data['response_times']) / len(api_data['response_times']) if api_data['response_times'] else 0
                summary.append(f"  {api_name}: {api_data['total']} calls, {success_rate:.1f}% success, {avg_time:.2f}s avg")
            else:
                summary.append(f"  {api_name}: No calls yet")
        
        return "\n".join(summary)

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
            self._track_function_call('get_weather', False)
            return

        start_time = time.time()
        success = False
        error = None
        
        try:
            url = f"https://api.weatherstack.com/current?access_key={self.WEATHER_API_KEY}"
            query = {"query": location}

            response = requests.get(url, params=query)
            response.raise_for_status()
            data = response.json()

            if "success" in data and not data["success"]:
                error = f"API Error: {data.get('error', {}).get('info', 'Unknown error')}"
                self.logger.error(f"Error fetching weather data: {error}")
                self._track_api_call('weather', start_time, False, error)
                self._track_function_call('get_weather', False)
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
            
            success = True

        except requests.exceptions.RequestException as e:
            error = f"Network or API error: {e}"
            self.logger.error(f"Network or API error while fetching weather: {e}")
        except KeyError as e:
            error = f"Data parsing error: Missing key {e}"
            self.logger.error(f"Error parsing weather data: Missing key {e}. Response: {data}")
        except Exception as e:
            error = f"Unexpected error: {e}"
            self.logger.error(f"Unexpected error in get_weather: {e}")
        finally:
            self._track_api_call('weather', start_time, success, error)
            self._track_function_call('get_weather', success)

    def get_stock(self, **kwargs) -> None:
        stock_name = kwargs.get("stock_name")
        if not stock_name:
            self.logger.error("Stock name is required for get_stock.")
            self._track_function_call('get_stock', False)
            return

        start_time = time.time()
        success = False
        
        try:
            self.logger.info(f"Getting stock data for {stock_name} (Functionality not yet implemented)")
            success = True  # Mark as success since it's not an API failure, just unimplemented
        except Exception as e:
            self.logger.error(f"Error in get_stock: {e}")
        finally:
            self._track_api_call('stock', start_time, success)
            self._track_function_call('get_stock', success)

    def get_news(self, **kwargs) -> None:
        topic = kwargs.get("topic")
        if not topic:
            self.logger.error("Topic is required for get_news.")
            self._track_function_call('get_news', False)
            return

        start_time = time.time()
        success = False
        error = None
        
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
            
            success = True

        except Exception as e:
            error = f"News API error: {e}"
            self.logger.error(f"Error fetching news: {e}")
        finally:
            self._track_api_call('news', start_time, success, error)
            self._track_function_call('get_news', success)

    def schedule(self, **kwargs) -> None:
        user = kwargs.get("user")
        event_title = kwargs.get("event")
        event_time = kwargs.get("time")

        if not all([user, event_title, event_time]):
            self.logger.error("'user', 'event', and 'time' are required for schedule.")
            self._track_function_call('schedule', False)
            return

        start_time = time.time()
        success = False
        
        try:
            self.logger.info(f"Scheduling '{event_title}' for {user} at {event_time} (Calendar integration not active)")
            success = True  # Mark as success since it's not an API failure, just unimplemented
        except Exception as e:
            self.logger.error(f"Error in schedule: {e}")
        finally:
            self._track_api_call('google', start_time, success)
            self._track_function_call('schedule', success)

    def notify(self, **kwargs) -> None:
        recipient = kwargs.get("recipient")
        message = kwargs.get("message")

        if not all([recipient, message]):
            self.logger.error("'recipient' and 'message' are required for notify.")
            self._track_function_call('notify', False)
            return

        start_time = time.time()
        success = False
        
        try:
            self.logger.info(f"Notifying {recipient}: '{message}' (Notification system not active)")
            success = True  # Mark as success since it's not an API failure, just unimplemented
        except Exception as e:
            self.logger.error(f"Error in notify: {e}")
        finally:
            self._track_function_call('notify', success)

    def create_resident(self, **kwargs) -> None:
        name = kwargs.get("name")
        weight = kwargs.get("weight")
        height = kwargs.get("height")

        if not all([name, weight, height]):
            self.logger.error("'name', 'weight', and 'height' are required for create_resident.")
            self._track_function_call('create_resident', False)
            return

        start_time = time.time()
        success = False
        
        try:
            self.logger.info(f"Creating resident {name} with weight {weight} and height {height}")
            success = True
        except Exception as e:
            self.logger.error(f"Error in create_resident: {e}")
        finally:
            self._track_function_call('create_resident', success)

    def create_staff(self, **kwargs) -> None:
        name = kwargs.get("name")
        weight = kwargs.get("weight")
        height = kwargs.get("height")
        temp = kwargs.get("temp")

        if not all([name, weight, height, temp]):
            self.logger.error("'name', 'weight', 'height', and 'temp' are required for create_staff.")
            self._track_function_call('create_staff', False)
            return

        start_time = time.time()
        success = False
        
        try:
            self.logger.info(f"Creating staff {name} with weight {weight}, height {height}, and temperature {temp}")
            success = True
        except Exception as e:
            self.logger.error(f"Error in create_staff: {e}")
        finally:
            self._track_function_call('create_staff', success)

    def create_visitor(self, **kwargs) -> None:
        name = kwargs.get("name")
        purpose = kwargs.get("purpose")

        if not all([name, purpose]):
            self.logger.error("'name' and 'purpose' are required for create_visitor.")
            self._track_function_call('create_visitor', False)
            return

        start_time = time.time()
        success = False
        
        try:
            self.logger.info(f"Creating visitor {name} for purpose: {purpose}")
            success = True
        except Exception as e:
            self.logger.error(f"Error in create_visitor: {e}")
        finally:
            self._track_function_call('create_visitor', success)
