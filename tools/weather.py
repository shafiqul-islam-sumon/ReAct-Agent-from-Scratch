import os

import requests
from dotenv import load_dotenv

from .base_tool import BaseTool


class WeatherTool(BaseTool):
    def __init__(self):
        load_dotenv()
        super().__init__(
            name="weather",
            description="Fetches weather information for a given city. Input is only the name of the city. e.g. 'Tokyo'.",
        )

        self.base_url = "http://api.openweathermap.org/data/2.5/weather"
        self.api_key = os.getenv("OPENWEATHER_API_KEY")

        if not self.api_key:
            raise ValueError("Missing API Key: Please set 'OPENWEATHER_API_KEY' in the .env file.")

    def run(self, query):
        """Fetches weather data for a given city"""
        if not query or not query.strip():
            return "Error: City name cannot be empty."

        url = f"{self.base_url}?q={query}&appid={self.api_key}&units=metric"
        # print('###### weather url : ', url)

        try:
            response = requests.get(url, timeout=5)

            # ✅ Checking HTTP status manually
            if response.status_code != 200:
                return f"Error: Unable to fetch weather data. Server responded with {response.status_code}: {response.json().get('message', 'Unknown error')}"

            data = response.json()

            # ✅ Ensuring response contains required data
            if "main" not in data or "weather" not in data:
                return f"Could not find weather data for '{query}'. Please check the city name."

            temperature = data["main"]["temp"]
            description = data["weather"][0]["description"]
            humidity = data["main"]["humidity"]
            wind_speed = data["wind"]["speed"]

            return f"The temperature in {query} is {temperature}°C. " f"The weather is {description}. " f"The humidity is {humidity}%. " f"The wind speed is {wind_speed} m/s."

        except requests.exceptions.RequestException as req_err:
            return f"Request failed: {str(req_err)}"


# === For standalone testing ===
if __name__ == "__main__":

    weather_tool = WeatherTool()
    city = "Dhaka"

    result = weather_tool.run(city)
    print(result)
