"""
OpenWeatherMap integration for MLB stadium weather monitoring
Provides real-time weather data for home run probability analysis
"""

import os
import logging
import requests
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import math

class WeatherIntegration:
    def __init__(self):
        """Initialize weather integration with API key"""
        # Check if weather is enabled
        self.enabled = os.environ.get("WEATHER_ENABLED", "true").lower() == "true"
        
        # Get API key (support both OWM_API_KEY and OPENWEATHER_API_KEY)
        self.api_key = os.environ.get("OWM_API_KEY") or os.environ.get("OPENWEATHER_API_KEY")
        
        if not self.enabled:
            logging.info("Weather integration disabled by configuration")
        elif not self.api_key:
            logging.warning("OpenWeatherMap API key not found - weather features disabled")
            self.enabled = False
        else:
            logging.info("Weather integration initialized successfully")
        
        # Stadium coordinates (latitude, longitude)
        # Using both short and full team names for compatibility
        self.stadium_coordinates = {
            # American League East
            "Yankees": (40.8296, -73.9262),  # Yankee Stadium
            "New York Yankees": (40.8296, -73.9262),
            "Red Sox": (42.3467, -71.0972),  # Fenway Park  
            "Boston Red Sox": (42.3467, -71.0972),
            "Blue Jays": (43.6414, -79.3894),  # Rogers Centre
            "Toronto Blue Jays": (43.6414, -79.3894),
            "Orioles": (39.2838, -76.6218),  # Oriole Park
            "Baltimore Orioles": (39.2838, -76.6218),
            "Rays": (27.7682, -82.6534),  # Tropicana Field
            "Tampa Bay Rays": (27.7682, -82.6534),
            
            # American League Central
            "White Sox": (41.8299, -87.6338),  # Guaranteed Rate Field
            "Chicago White Sox": (41.8299, -87.6338),
            "Guardians": (41.4962, -81.6852),  # Progressive Field
            "Cleveland Guardians": (41.4962, -81.6852),
            "Tigers": (42.3390, -83.0485),  # Comerica Park
            "Detroit Tigers": (42.3390, -83.0485),
            "Royals": (39.0517, -94.4803),  # Kauffman Stadium
            "Kansas City Royals": (39.0517, -94.4803),
            "Twins": (44.9818, -93.2775),  # Target Field
            "Minnesota Twins": (44.9818, -93.2775),
            
            # American League West
            "Astros": (29.7573, -95.3555),  # Minute Maid Park
            "Houston Astros": (29.7573, -95.3555),
            "Angels": (33.8003, -117.8827),  # Angel Stadium
            "Los Angeles Angels": (33.8003, -117.8827),
            "Athletics": (37.7516, -122.2005),  # Oakland Coliseum
            "Oakland Athletics": (37.7516, -122.2005),
            "Mariners": (47.5914, -122.3325),  # T-Mobile Park
            "Seattle Mariners": (47.5914, -122.3325),
            "Rangers": (32.7512, -97.0832),  # Globe Life Field
            "Texas Rangers": (32.7512, -97.0832),
            
            # National League East
            "Braves": (33.8907, -84.4679),  # Truist Park
            "Atlanta Braves": (33.8907, -84.4679),
            "Marlins": (25.7781, -80.2196),  # loanDepot park
            "Miami Marlins": (25.7781, -80.2196),
            "Mets": (40.7571, -73.8458),  # Citi Field
            "New York Mets": (40.7571, -73.8458),
            "Phillies": (39.9061, -75.1665),  # Citizens Bank Park
            "Philadelphia Phillies": (39.9061, -75.1665),
            "Nationals": (38.8730, -77.0074),  # Nationals Park
            "Washington Nationals": (38.8730, -77.0074),
            
            # National League Central
            "Cubs": (41.9484, -87.6553),  # Wrigley Field
            "Chicago Cubs": (41.9484, -87.6553),
            "Reds": (39.0974, -84.5071),  # Great American Ball Park
            "Cincinnati Reds": (39.0974, -84.5071),
            "Brewers": (43.0280, -87.9712),  # American Family Field
            "Milwaukee Brewers": (43.0280, -87.9712),
            "Pirates": (40.4468, -80.0057),  # PNC Park
            "Pittsburgh Pirates": (40.4468, -80.0057),
            "Cardinals": (38.6226, -90.1928),  # Busch Stadium
            "St. Louis Cardinals": (38.6226, -90.1928),
            
            # National League West
            "Diamondbacks": (33.4455, -112.0667),  # Chase Field
            "Arizona Diamondbacks": (33.4455, -112.0667),
            "Rockies": (39.7560, -104.9942),  # Coors Field
            "Colorado Rockies": (39.7560, -104.9942),
            "Dodgers": (34.0739, -118.2400),  # Dodger Stadium
            "Los Angeles Dodgers": (34.0739, -118.2400),
            "Padres": (32.7076, -117.1569),  # Petco Park
            "San Diego Padres": (32.7076, -117.1569),
            "Giants": (37.7786, -122.3893),  # Oracle Park
            "San Francisco Giants": (37.7786, -122.3893)
        }
        
        # Cache for weather data
        self.weather_cache = {}
        # Support configurable cache duration (default 5 minutes)
        dedupe_minutes = int(os.environ.get("WEATHER_DEDUPE_MIN", "5"))
        self.cache_duration = timedelta(minutes=dedupe_minutes)
        
        # Previous weather data for tracking changes
        self.previous_weather = {}
    
    def is_available(self) -> bool:
        """Check if weather integration is available"""
        return self.enabled and self.api_key is not None
    
    def get_stadium_weather(self, home_team: str) -> Optional[Dict[str, Any]]:
        """Get current weather for a stadium location"""
        if not self.api_key:
            return None
        
        # Check cache first
        cache_key = home_team
        if cache_key in self.weather_cache:
            cached_data, timestamp = self.weather_cache[cache_key]
            if datetime.now() - timestamp < self.cache_duration:
                return cached_data
        
        # Get coordinates for the stadium
        coords = self.stadium_coordinates.get(home_team)
        if not coords:
            logging.warning(f"No coordinates found for team: {home_team}")
            return None
        
        try:
            lat, lon = coords
            url = f"https://api.openweathermap.org/data/2.5/weather"
            params = {
                "lat": lat,
                "lon": lon,
                "appid": self.api_key,
                "units": "imperial"  # Use Fahrenheit and mph
            }
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                
                # Extract relevant weather data
                weather_data = {
                    "temperature": data.get("main", {}).get("temp", 0),
                    "wind_speed": data.get("wind", {}).get("speed", 0),
                    "wind_direction": data.get("wind", {}).get("deg", 0),
                    "humidity": data.get("main", {}).get("humidity", 0),
                    "description": data.get("weather", [{}])[0].get("description", ""),
                    "city": data.get("name", home_team),
                    "timestamp": datetime.now().isoformat()
                }
                
                # Cache the data
                self.weather_cache[cache_key] = (weather_data, datetime.now())
                
                return weather_data
            else:
                logging.error(f"Weather API error: {response.status_code}")
                return None
                
        except Exception as e:
            logging.error(f"Error fetching weather for {home_team}: {e}")
            return None
    
    def calculate_wind_impact(self, wind_speed: float, wind_direction: float) -> Dict[str, Any]:
        """Calculate wind impact on home run probability"""
        # Wind directions (in degrees):
        # 0/360 = North, 90 = East, 180 = South, 270 = West
        # Most stadiums face roughly northeast, so southwest wind (225°) is optimal
        
        # Calculate outfield direction (opposite of home plate)
        # Assume average stadium orientation with outfield facing northeast (45°)
        outfield_direction = 45
        
        # Calculate how aligned the wind is with the outfield
        # Perfect alignment = wind blowing directly toward outfield
        angle_diff = abs(wind_direction - outfield_direction)
        if angle_diff > 180:
            angle_diff = 360 - angle_diff
        
        # Wind is "out" if it's within 90 degrees of outfield direction
        wind_out = angle_diff <= 90
        
        # Calculate wind effectiveness (0-1 scale)
        if wind_out:
            effectiveness = math.cos(math.radians(angle_diff))
        else:
            effectiveness = 0
        
        return {
            "wind_out": wind_out,
            "wind_speed_mph": wind_speed,
            "wind_direction_deg": wind_direction,
            "effectiveness": effectiveness,
            "boosted_hr_probability": wind_out and wind_speed >= 7.5
        }
    
    def check_wind_shift(self, game_id: int, current_wind_dir: float) -> bool:
        """Check if wind direction has shifted significantly"""
        if game_id in self.previous_weather:
            prev_dir = self.previous_weather[game_id].get("wind_direction", 0)
            
            # Calculate angle difference
            angle_diff = abs(current_wind_dir - prev_dir)
            if angle_diff > 180:
                angle_diff = 360 - angle_diff
            
            # Check if shift is >= 45 degrees
            return angle_diff >= 45
        
        return False
    
    def analyze_weather_conditions(self, game_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze weather conditions for alert triggers"""
        home_team = game_data.get("home_team", "")
        weather = self.get_stadium_weather(home_team)
        
        if not weather:
            return {"weather_available": False}
        
        game_id = game_data.get("id", 0)
        temp = weather.get("temperature", 0)
        wind_speed = weather.get("wind_speed", 0)
        wind_direction = weather.get("wind_direction", 0)
        
        # Calculate wind impact
        wind_impact = self.calculate_wind_impact(wind_speed, wind_direction)
        
        # Check for wind shift
        wind_shifted = self.check_wind_shift(game_id, wind_direction)
        
        # Update previous weather
        self.previous_weather[game_id] = weather
        
        # Determine alert conditions
        alerts = {
            "weather_available": True,
            "weather_data": weather,
            "wind_impact": wind_impact,
            "alerts": {
                "wind_speed": wind_impact["boosted_hr_probability"],
                "wind_shift": wind_shifted,
                "prime_hr_conditions": False,  # Will be set by MLB monitor with HRFI data
                "hot_windy": temp >= 85 and wind_impact["boosted_hr_probability"],
                "temp_wind": temp >= 85 and wind_impact["wind_out"]  # Temperature + any outward wind
            },
            "summary": self.generate_weather_summary(weather, wind_impact)
        }
        
        return alerts
    
    def generate_weather_summary(self, weather: Dict[str, Any], wind_impact: Dict[str, Any]) -> str:
        """Generate a human-readable weather summary"""
        temp = weather.get("temperature", 0)
        wind_speed = weather.get("wind_speed", 0)
        
        conditions = []
        
        if temp >= 85:
            conditions.append(f"Hot ({temp:.0f}°F)")
        elif temp <= 50:
            conditions.append(f"Cold ({temp:.0f}°F)")
        else:
            conditions.append(f"{temp:.0f}°F")
        
        if wind_impact["boosted_hr_probability"]:
            conditions.append(f"Wind {wind_speed:.1f} mph OUT")
        elif wind_speed >= 10:
            conditions.append(f"Wind {wind_speed:.1f} mph")
        
        if weather.get("description"):
            conditions.append(weather["description"].title())
        
        return " | ".join(conditions) if conditions else "Weather data unavailable"
    
    def get_weather_context(self, game_data: Dict[str, Any]) -> str:
        """Get weather context for AI analysis"""
        analysis = self.analyze_weather_conditions(game_data)
        
        if not analysis.get("weather_available"):
            return ""
        
        weather = analysis.get("weather_data", {})
        wind_impact = analysis.get("wind_impact", {})
        
        context = f"Weather at {weather.get('city', 'stadium')}: "
        context += f"{weather.get('temperature', 0):.0f}°F, "
        context += f"Wind {weather.get('wind_speed', 0):.1f} mph "
        
        if wind_impact.get("wind_out"):
            context += f"blowing OUT (HR boost active)"
        else:
            context += f"at {weather.get('wind_direction', 0):.0f}°"
        
        return context