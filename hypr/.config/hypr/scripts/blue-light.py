#!/usr/bin/env python3
import os
import sys
import json
import time
import signal
import configparser
import requests
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Tuple, Optional, Dict


# Configuration
CONFIG_DIR = Path.home() / ".config/hypr-py-light"
CACHE_DIR = CONFIG_DIR / "cache"
CONFIG_FILE = CONFIG_DIR / "config.ini"
STATE_FILE = CONFIG_DIR / "state.json"
LOG_FILE = CONFIG_DIR / "hyprlight.log"


# Temperature presets (Kelvin)
TEMPERATURE_PROFILE = {
    'DAY_CLEAR': 6500,
    'DAY_CLOUDY': 5800,
    'DAY_RAINY': 5200,
    'NIGHT_DEFAULT': 4600,
    'NIGHT_COLD': 4200,
    'MANUAL_ON': 5000,  # For manual blue light ON (toggled)
    'MANUAL_OFF': 6500,  # For manual blue light OFF (neutral)
}


# API endpoints
IPGEO_API_URL = "https://api.ipgeolocation.io/ipgeo"
OWM_API_URL = "https://api.openweathermap.org/data/2.5/weather"


class ScreenLightManager:
    def __init__(self):
        self.setup_directories()
        self.load_config()
        self.load_state()
        self.hyprsunset_pid = None


    def setup_directories(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_DIR.mkdir(exist_ok=True)


    def load_config(self):
        self.config = configparser.ConfigParser()
        if CONFIG_FILE.exists():
            self.config.read(CONFIG_FILE)
        else:
            self.config['API'] = {
                'openweather': '',
                'ipgeolocation': ''
            }


    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            self.config.write(f)


    def load_state(self):
        try:
            with open(STATE_FILE) as f:
                self.state = json.load(f)
            self.log(f"State loaded: {self.state}")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.state = {
                'manual': False,
                'bluelight': False,
                'last_temp': 4500
            }
            self.log(f"State file not found or invalid, using defaults: {self.state}")
        except Exception as e:
            self.log(f"Error loading state: {str(e)}")
            self.state = {
                'manual': False,
                'bluelight': False,
                'last_temp': 4500
            }


    def save_state(self):
        try:
            with open(STATE_FILE, 'w') as f:
                json.dump(self.state, f, indent=2)
            self.log(f"State saved: {self.state}")
        except Exception as e:
            self.log(f"Error saving state: {str(e)}")


    def notify(self, message: str):
        try:
            subprocess.run(['notify-send', '-a', 'Screen Lighting', '-t', '3000', '🌡️ ' + message])
            self.log(message)
        except FileNotFoundError:
            pass


    def log(self, message: str):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(LOG_FILE, 'a') as f:
            f.write(f"[{timestamp}] {message}\n")


    def get_coordinates(self) -> Tuple[float, float]:
        # Try IP geolocation API first (don't use cache if we want fresh location)
        api_key = self.config['API'].get('ipgeolocation')
        if api_key:
            try:
                self.log("Attempting to fetch location from IP geolocation API...")
                response = requests.get(
                    IPGEO_API_URL,
                    params={'apiKey': api_key, 'fields': 'latitude,longitude,city,country_name'},
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()
                
                lat = float(data['latitude'])
                lon = float(data['longitude'])
                
                self.log(f"Successfully fetched location: {data.get('city', 'Unknown')}, {data.get('country_name', 'Unknown')} ({lat}, {lon})")
                
                # Cache coordinates
                cache_file = CACHE_DIR / "coordinates"
                with open(cache_file, 'w') as f:
                    f.write(f"{lat} {lon}")
                
                # Cache location info
                location_cache = CACHE_DIR / "location.json"
                location_data = {
                    'city': data.get('city', 'Unknown'),
                    'country': data.get('country_name', 'Unknown'),
                    'lat': lat,
                    'lon': lon
                }
                with open(location_cache, 'w') as f:
                    json.dump(location_data, f)
                    
                return lat, lon
            except Exception as e:
                self.log(f"Geolocation API error: {str(e)}")
        else:
            self.log("No IP geolocation API key configured")


        # Try cached coordinates as fallback
        cache_file = CACHE_DIR / "coordinates"
        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    lat, lon = map(float, f.read().split())
                self.log(f"Using cached coordinates: {lat}, {lon}")
                return lat, lon
            except Exception as e:
                self.log(f"Error reading cached coordinates: {str(e)}")


        # Fallback to London coordinates
        self.log("Using fallback coordinates (London)")
        return 51.5074, -0.1278


    def get_location_info(self) -> Dict:
        """Get cached location information"""
        location_cache = CACHE_DIR / "location.json"
        try:
            if location_cache.exists():
                with open(location_cache) as f:
                    return json.load(f)
        except Exception as e:
            self.log(f"Error reading location cache: {str(e)}")
        
        # Fallback location info
        return {
            'city': 'London',
            'country': 'United Kingdom',
            'lat': 51.5074,
            'lon': -0.1278
        }
    def get_weather(self) -> Optional[Dict]:
        cache_file = CACHE_DIR / "weather.json"
        try:
            lat, lon = self.get_coordinates()
            api_key = self.config['API'].get('openweather')
            if not api_key:
                self.log("OpenWeather API key not configured")
                if cache_file.exists():
                    with open(cache_file) as f:
                        return json.load(f)
                return None
                
            response = requests.get(
                OWM_API_URL,
                params={
                    'lat': lat,
                    'lon': lon,
                    'appid': api_key,
                    'units': 'metric'
                },
                timeout=15
            )
            data = response.json()
            with open(cache_file, 'w') as f:
                json.dump(data, f)
            return data
        except Exception as e:
            self.log(f"Weather API error: {str(e)}")
            if cache_file.exists():
                with open(cache_file) as f:
                    return json.load(f)
            return None


    def calculate_temperature(self) -> int:
        current_hour = datetime.now(timezone.utc).hour
        is_night = current_hour < 6 or current_hour >= 20


        if self.state['bluelight']:
            # In auto mode, blue light flag ignored
            # Just return normal auto temps here
            pass


        weather = self.get_weather()
        if not weather:
            return TEMPERATURE_PROFILE['NIGHT_DEFAULT'] if is_night else TEMPERATURE_PROFILE['DAY_CLEAR']


        if is_night:
            temp = weather['main']['temp']
            if weather['weather'][0]['main'] in ['Rain', 'Drizzle', 'Thunderstorm']:
                return TEMPERATURE_PROFILE['NIGHT_COLD']
            return TEMPERATURE_PROFILE['NIGHT_COLD'] if temp < 5 else TEMPERATURE_PROFILE['NIGHT_DEFAULT']
        else:
            weather_main = weather['weather'][0]['main']
            if weather_main == 'Clear':
                return TEMPERATURE_PROFILE['DAY_CLEAR']
            if weather_main in ['Rain', 'Drizzle', 'Thunderstorm']:
                return TEMPERATURE_PROFILE['DAY_RAINY']
            return TEMPERATURE_PROFILE['DAY_CLOUDY']


    def apply_temperature(self, temp: int):
        # Kill all existing hyprsunset processes
        try:
            subprocess.run(['pkill', 'hyprsunset'], check=False)
            time.sleep(0.5)  # Give processes time to terminate
        except Exception as e:
            self.log(f"Error killing hyprsunset processes: {str(e)}")


        # Start new process
        try:
            process = subprocess.Popen(['hyprsunset', '-t', str(temp)], 
                                     stdout=subprocess.DEVNULL, 
                                     stderr=subprocess.DEVNULL)
            self.hyprsunset_pid = process.pid
            self.state['last_temp'] = temp
            self.save_state()
            self.notify(f"Screen temperature set to {temp}K")
            self.log(f"Started hyprsunset with PID {process.pid}, temp {temp}K")
        except FileNotFoundError:
            self.log("Error: hyprsunset command not found")
            self.notify("Error: hyprsunset not installed or not in PATH")
        except Exception as e:
            self.log(f"Error starting hyprsunset: {str(e)}")
            self.notify(f"Error setting temperature: {str(e)}")


    def toggle_bluelight(self):
        if not self.state['manual']:
            self.notify("Cannot toggle blue light filter in automatic mode. Switch to manual mode first.")
            return
        self.state['bluelight'] = not self.state['bluelight']
        temp = TEMPERATURE_PROFILE['MANUAL_ON'] if self.state['bluelight'] else TEMPERATURE_PROFILE['MANUAL_OFF']
        self.apply_temperature(temp)
        self.save_state()
        status = "ON (5000K)" if self.state['bluelight'] else "OFF (6500K)"
        self.notify(f"Blue light filter toggled {status}")


    def toggle_manual_mode(self):
        """Toggle between manual and automatic modes"""
        # Reload state to ensure we have the latest state
        self.load_state()
        
        current_mode = "Manual" if self.state['manual'] else "Automatic"
        self.log(f"Current mode before toggle: {current_mode}")
        
        if self.state['manual']:
            # Switch to automatic mode
            self.state['manual'] = False
            self.state['bluelight'] = False
            self.save_state()
            self.log("Toggled to automatic mode")
            self.notify("Switched to automatic mode")
            self.update_temperature()  # Apply automatic temperature immediately
        else:
            # Switch to manual mode
            self.state['manual'] = True
            self.state['bluelight'] = False  # turn off bluelight filter on manual mode
            self.save_state()
            self.log("Toggled to manual mode")
            self.apply_temperature(TEMPERATURE_PROFILE['MANUAL_OFF'])  # neutral 6500K
            self.notify("Switched to manual mode - screen set to neutral (6500K)")
        
        # Log final state
        final_mode = "Manual" if self.state['manual'] else "Automatic"
        self.log(f"Final mode after toggle: {final_mode}")


    def toggle_auto_mode(self):
        """Force switch to automatic mode"""
        if self.state['manual']:
            self.state['manual'] = False
            self.state['bluelight'] = False
            self.save_state()
            self.notify("Switched to automatic mode")
            self.update_temperature()
        else:
            self.notify("Already in automatic mode")


    def force_manual_mode(self):
        """Force switch to manual mode"""  
        if not self.state['manual']:
            self.state['manual'] = True
            self.state['bluelight'] = False  # turn off bluelight filter on manual mode
            self.apply_temperature(TEMPERATURE_PROFILE['MANUAL_OFF'])  # neutral 6500K
            self.save_state()
            self.notify("Switched to manual mode - screen set to neutral (6500K)")
        else:
            self.notify("Already in manual mode")


    def update_temperature(self):
        if not self.state['manual']:
            new_temp = self.calculate_temperature()
            self.log(f"Calculated temperature: {new_temp}K, current: {self.state['last_temp']}K")
            if new_temp != self.state['last_temp']:
                self.apply_temperature(new_temp)
            else:
                self.log(f"Temperature unchanged at {new_temp}K")


    def status(self):
        # Reload state to ensure we show current state
        self.load_state()
        
        # Get location info
        location_info = self.get_location_info()
        location_str = f"{location_info['city']}, {location_info['country']}"
        
        # Get weather info
        weather = self.get_weather()
        weather_str = "Unknown"
        temp_str = "Unknown"
        
        if weather:
            try:
                weather_main = weather['weather'][0]['main']
                weather_desc = weather['weather'][0]['description'].title()
                temp_celsius = weather['main']['temp']
                temp_str = f"{temp_celsius:.1f}°C"
                weather_str = f"{weather_main} ({weather_desc})"
            except (KeyError, IndexError):
                weather_str = "Weather data unavailable"
        
        # Get current time info
        current_hour = datetime.now(timezone.utc).hour
        is_night = current_hour < 6 or current_hour >= 20
        time_period = "Night" if is_night else "Day"
        
        # Get current state
        temp = self.state.get('last_temp', 'Unknown')
        manual = self.state.get('manual', False)
        bluelight = self.state.get('bluelight', False)
        mode = "Manual" if manual else "Automatic"
        bluelight_status = "ON" if bluelight else "OFF"
        
        # Display status
        print("=" * 50)
        print("📍 LOCATION & WEATHER")
        print(f"   Location: {location_str}")
        print(f"   Weather: {weather_str}")
        print(f"   Temperature: {temp_str}")
        print(f"   Time Period: {time_period}")
        print()
        print("🖥️  SCREEN SETTINGS")
        print(f"   Screen Temperature: {temp}K")
        print(f"   Mode: {mode}")
        print(f"   Blue Light Filter: {bluelight_status}")
        print()
        print("📂 FILES")
        print(f"   Config: {CONFIG_FILE}")
        print(f"   State: {STATE_FILE}")
        print(f"   Logs: {LOG_FILE}")
        print("=" * 50)
        
        # Also log this info
        self.log(f"Status check - Location: {location_str}, Weather: {weather_str}, Mode: {mode}, Temp: {temp}K, BlueLight: {bluelight_status}")


    def run_daemon(self):
        self.notify(f"Starting screen temperature service, initial temp: {self.state.get('last_temp', 'Unknown')}K")
        # Apply initial temperature
        if not self.state['manual']:
            self.update_temperature()
        
        while True:
            try:
                self.update_temperature()
                time.sleep(300)  # 5 minutes
            except Exception as e:
                self.log(f"Error in daemon loop: {str(e)}")
                time.sleep(60)  # Wait 1 minute on error before retrying


def initial_setup():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


    config = configparser.ConfigParser()
    config['API'] = {}


    print("Screen Temperature Setup")
    config['API']['openweather'] = input("Enter OpenWeather API key: ").strip()
    config['API']['ipgeolocation'] = input("Enter IPGeolocation API key: ").strip()


    with open(CONFIG_FILE, 'w') as f:
        config.write(f)


    print("Configuration saved. Starting service...")


if __name__ == "__main__":
    if not CONFIG_FILE.exists():
        initial_setup()


    manager = ScreenLightManager()


    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == 'toggle':
            manager.toggle_bluelight()
        elif cmd == 'manual':
            manager.toggle_manual_mode()  # Now properly toggles
        elif cmd == 'auto':
            manager.toggle_auto_mode()
        elif cmd == 'force-manual':
            manager.force_manual_mode()  # New: force manual mode
        elif cmd == 'refresh-location':
            # Force refresh location data
            cache_file = CACHE_DIR / "coordinates"
            location_cache = CACHE_DIR / "location.json"
            if cache_file.exists():
                cache_file.unlink()
            if location_cache.exists():
                location_cache.unlink()
            manager.get_coordinates()  # This will fetch fresh data
            print("Location data refreshed")
        elif cmd == 'test':
            # Test command to manually apply temperature
            if len(sys.argv) > 2:
                try:
                    temp = int(sys.argv[2])
                    manager.apply_temperature(temp)
                except ValueError:
                    print("Invalid temperature value")
            else:
                print("Usage: ./blue-light.py test <temperature>")
        elif cmd == 'status':
            manager.status()
        else:
            print("Usage: ./blue-light.py [toggle|manual|auto|force-manual|refresh-location|test <temp>|status]")
    else:
        try:
            manager.run_daemon()
        except KeyboardInterrupt:
            manager.notify("Service stopped")
            sys.exit(0)





