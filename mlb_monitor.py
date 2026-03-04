import requests
import threading
import time
import logging
import os
import base64
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from multi_source_aggregator import MultiSourceBaseballAggregator
from telegram_notifier import TelegramNotifier
from persistent_settings import PersistentSettings
from openai_helper import OpenAIHelper
from weather_integration import WeatherIntegration
import traceback

# Import math engines for advanced analytics
from math_engines import (
    PowerFeatures, PowerCoefficients, pa_hr_probability, PlattParams, platt_scale,
    power_tier_from_prob, wind_component_out_to_cf, hr_boost_factor,
    SofteningTracker, SPRTState, sprt_ball_update,
    delta_re, value_score
)

# Import enhanced deduplication system
from dedup import AlertDeduper

# Math Engine Configuration
MATH_ENGINE_CONFIG = {
    # League averages and priors
    "LEAGUE_PA_HR": 0.036,
    "LEAGUE_ISO": 0.165,
    "LEAGUE_PITCHER_HR9_30D": 1.10,
    
    # Platt calibration (weekly tuning)
    "PLATT_A": 1.0,  # Identity by default
    "PLATT_B": 0.0,
    
    # SPRT parameters for ball control detection
    "SPRT_P0": 0.33,  # Normal ball rate
    "SPRT_P1": 0.60,  # Control loss ball rate
    "SPRT_A": 20.0,   # Type I error threshold
    
    # EWMA/CUSUM parameters
    "EWMA_ALPHA": 0.3,
    "CUSUM_K_SIGMA": 0.5,
    "CUSUM_THRESH": 3.0,
    
    # Park CF azimuth degrees (for popular parks)
    "PARK_CF_AZIMUTH": {
        "Yankee Stadium": 54,
        "Fenway Park": 90,
        "Wrigley Field": 0,
        "Dodger Stadium": 45,
        "Oracle Park": 90,
        "Coors Field": 350,
        "default": 45  # Northeast typical
    },
    
    # Park HR factors
    "PARK_HR_FACTOR": {
        "Yankee Stadium": 1.15,
        "Coors Field": 1.25,
        "Great American Ball Park": 1.12,
        "Citizens Bank Park": 1.10,
        "Fenway Park": 1.08,
        "Oracle Park": 0.88,
        "Marlins Park": 0.85,
        "default": 1.00
    }
}

# Alert configuration for deduplication and re-alert policies
ALERT_CONFIG = {
    "power_hitter": {
        "window": 15,
        "scope": "plate_appearance",   # Alert once per at-bat
        "content_fields": ["batter_id", "season_hr", "pa_id"],
        "realert_after_secs": None
    },
    "hot_hitter": {
        "window": 15,
        "scope": "plate_appearance",
        "content_fields": ["batter_id", "game_hr", "pa_id"],
        "realert_after_secs": None
    },
    "runners": {
        "window": 15,
        "scope": "half_inning",
        "content_fields": ["bases_hash", "outs", "batter_id", "pa_id"],
        "realert_after_secs": 120      # Allow reminder if runners persist
    },
    "hit": {
        "window": 15,
        "scope": "play",
        "content_fields": ["play_id", "description"],
        "realert_after_secs": None
    },
    "home_run": {
        "window": 15,
        "scope": "play",
        "content_fields": ["play_id", "description"],
        "realert_after_secs": None
    },
    "scoring": {
        "window": 15,
        "scope": "play",
        "content_fields": ["play_id", "score_key"],
        "realert_after_secs": None
    },
    "strikeout": {
        "window": 15,
        "scope": "play",
        "content_fields": ["play_id", "description"],
        "realert_after_secs": None
    },
    "bases_loaded_no_outs": {
        "window": 60,   # Reduced to 1-minute window - allow alerts for different batters
        "scope": "plate_appearance",  # Changed to PA scope to allow per-batter alerts
        "content_fields": ["bases_hash", "outs", "batter_id"],  # Include batter_id
        "realert_after_secs": 180  # Re-alert after 3 minutes if situation persists with same batter
    },
    "bases_loaded_one_out": {
        "window": 60,   # Reduced to 1-minute window  
        "scope": "plate_appearance",  # Changed to PA scope
        "content_fields": ["bases_hash", "outs", "batter_id"],  # Include batter_id
        "realert_after_secs": 180  # Re-alert after 3 minutes if situation persists with same batter
    },
    "runner_3rd_no_outs": {
        "window": 60,   # Reduced to 1-minute window
        "scope": "plate_appearance",  # Changed to PA scope  
        "content_fields": ["bases_hash", "outs", "batter_id"],  # Include batter_id
        "realert_after_secs": 180  # Re-alert after 3 minutes if situation persists with same batter
    },
    "runners_23_no_outs": {
        "window": 60,   # Reduced to 1-minute window
        "scope": "plate_appearance",  # Changed to PA scope
        "content_fields": ["bases_hash", "outs", "batter_id"],  # Include batter_id
        "realert_after_secs": 180  # Re-alert after 3 minutes if situation persists with same batter
    },
    "runners_13_no_outs": {
        "window": 60,   
        "scope": "plate_appearance",  
        "content_fields": ["bases_hash", "outs", "batter_id"], 
        "realert_after_secs": 180  
    },
    "runners_12_no_outs": {
        "window": 60,   
        "scope": "plate_appearance",  
        "content_fields": ["bases_hash", "outs", "batter_id"], 
        "realert_after_secs": 180  
    },
    "runner_2nd_no_outs": {
        "window": 60,   
        "scope": "plate_appearance",  
        "content_fields": ["bases_hash", "outs", "batter_id"], 
        "realert_after_secs": 180  
    },
    "runner_3rd_one_out": {
        "window": 60,   
        "scope": "plate_appearance",  
        "content_fields": ["bases_hash", "outs", "batter_id"], 
        "realert_after_secs": 180  
    },
    "runners_13_one_out": {
        "window": 60,   
        "scope": "plate_appearance",  
        "content_fields": ["bases_hash", "outs", "batter_id"], 
        "realert_after_secs": 180  
    },
    "runners_23_one_out": {
        "window": 60,   
        "scope": "plate_appearance",  
        "content_fields": ["bases_hash", "outs", "batter_id"], 
        "realert_after_secs": 180  
    },
    "high_probability": {
        "window": 30,   # Shorter window for high probability situations 
        "scope": "plate_appearance",  
        "content_fields": ["bases_hash", "outs", "batter_id"], 
        "realert_after_secs": 120  
    },
    # Add other alert types as needed
    "default": {
        "window": 15,
        "scope": "game",
        "content_fields": ["data"],
        "realert_after_secs": None
    }
}

class MLBMonitor:
    def __init__(self):
        self.base_url = "https://v1.baseball.api-sports.io"
        self.api_key = os.environ.get('API_SPORTS_KEY')
        
        # Initialize persistent settings first
        self.persistent_settings = PersistentSettings()
        
        # Load monitored games from persistent storage
        saved_games = self.persistent_settings.get_monitored_games()
        self.monitored_games = set(saved_games)
        
        self.alerts = []
        self.max_alerts = 100
        self.running = False
        self.monitor_thread = None
        self.game_states = {}  # Track previous game states for change detection
        
        # Enhanced deduplication system (NEW - replaces old tracking)
        self.deduper = AlertDeduper(
            alert_config=ALERT_CONFIG,
            enable_buckets=True,
            bucket_capacity=8,
            bucket_refill_seconds=15
        )
        
        # Legacy tracking (keep for backward compatibility during transition)
        self.recent_alerts = {}  # Track recent alerts with timestamps
        self.alert_dedup_window = 2  # Immediate alerts - only prevent rapid duplicates (2 second window)
        self.last_sent_by_simple = {}  # Track last sent time for re-alert policy
        
        # Math engine tracking structures
        self.softening_trackers = {}  # {(game_id, pitcher_id): SofteningTracker}
        self.ball_sprt_states = {}    # {(game_id, pitcher_id): SPRTState}
        self.last_power_probs = {}    # {(game_id, batter_id): probability}
        
        # Load notification preferences from persistent storage
        self.notification_preferences = self.persistent_settings.get_notification_preferences()
        
        # Initialize multi-source aggregator for faster alerts
        self.multi_source = MultiSourceBaseballAggregator()
        self.last_multi_source_check = 0
        
        # Initialize Telegram notifier
        self.telegram_notifier = TelegramNotifier()
        
        # Initialize OpenAI helper for AI-enhanced features
        self.openai_helper = OpenAIHelper()
        
        # Initialize weather integration
        self.weather_integration = WeatherIntegration()
        
        # Set up authentication headers for API-Sports fallback
        if self.api_key:
            self.headers = {
                'X-RapidAPI-Key': self.api_key,
                'X-RapidAPI-Host': 'v1.baseball.api-sports.io'
            }
        else:
            logging.warning("API-Sports API key not found, will use fallback")
            self.headers = {}
        
        # Auto-restore monitoring if enabled and games were previously monitored
        self._auto_restore_monitoring()
    
    def _auto_restore_monitoring(self):
        """Automatically restore monitoring settings from previous session"""
        try:
            if self.persistent_settings.is_auto_monitoring_enabled():
                saved_games = self.persistent_settings.get_monitored_games()
                if saved_games:
                    logging.info(f"🔄 Auto-restoring monitoring for {len(saved_games)} games: {saved_games}")
                    # Restore without triggering another save
                    self.monitored_games = set(saved_games)
                    
                    # Add system alert about restoration
                    settings_summary = self.persistent_settings.get_settings_summary()
                    self._add_alert(
                        0,
                        "System Status", 
                        f"🔄 Monitoring automatically restored from previous session\n{settings_summary}",
                        "system"
                    )
                else:
                    logging.info("📭 No previous monitoring settings to restore")
            else:
                logging.info("⚠️ Auto-monitoring restoration is disabled")
        except Exception as e:
            logging.error(f"Error during auto-restore: {e}")
        
    def get_todays_games(self) -> List[Dict[str, Any]]:
        """Get list of today's MLB games using multi-source aggregation"""
        try:
            # Use multi-source aggregator for fastest data
            logging.info("🚀 Fetching games from multiple sources for maximum speed...")
            
            loop = None
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                all_games_data = loop.run_until_complete(self.multi_source.get_all_games())
                validated_games = self.multi_source.cross_validate_games(all_games_data)
                
                if validated_games:
                    logging.info(f"✅ Multi-source returned {len(validated_games)} validated games")
                    # Log source performance if all_games_data is a dict
                    if isinstance(all_games_data, dict):
                        for source, data in all_games_data.items():
                            if isinstance(data, dict):
                                response_time = data.get('response_time', 0)
                                game_count = len(data.get('games', []))
                                logging.info(f"   📊 {source}: {response_time:.2f}s, {game_count} games")
                    
                    return validated_games
                else:
                    logging.warning("Multi-source returned no games, using fallback")
                    
            finally:
                if loop:
                    try:
                        loop.close()
                    except:
                        pass
                    asyncio.set_event_loop(None)
                
        except Exception as e:
            logging.error(f"Error with multi-source aggregation: {e}")
        
        # Fallback to original method if multi-source fails
        logging.info("⚠️ Using fallback single-source API")
        return self._get_fallback_games()
    
    def _get_fallback_games(self) -> List[Dict[str, Any]]:
        """Fallback to original MLB API if MySportsFeeds fails"""
        try:
            # Use 5-hour delay to account for late-running games
            # Games are considered "today's games" until 5 AM the next day
            from datetime import timedelta
            adjusted_time = datetime.now() - timedelta(hours=5)
            today = adjusted_time.strftime('%Y-%m-%d')
            url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}&hydrate=team,linescore"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            games = []
            
            for date_info in data.get('dates', []):
                for game in date_info.get('games', []):
                    game_info = {
                        'id': game['gamePk'],
                        'home_team': game['teams']['home']['team']['name'],
                        'away_team': game['teams']['away']['team']['name'],
                        'status': game['status']['detailedState'],
                        'start_time': game.get('gameDate', ''),
                        'inning': game.get('linescore', {}).get('currentInning', 0),
                        'inning_state': game.get('linescore', {}).get('inningState', ''),
                        'home_score': game.get('linescore', {}).get('teams', {}).get('home', {}).get('runs', 0),
                        'away_score': game.get('linescore', {}).get('teams', {}).get('away', {}).get('runs', 0)
                    }
                    games.append(game_info)
            
            return games
            
        except Exception as e:
            logging.error(f"Error fetching games from fallback API: {e}")
            raise
    
    def get_game_details(self, game_id: int) -> Dict[str, Any]:
        """Get detailed game information using fastest available source"""
        try:
            # Try multi-source fastest method first
            loop = None
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                game_details = loop.run_until_complete(self.multi_source.get_fastest_game_details(game_id))
                if game_details:
                    logging.info(f"Got live game details from multi-source for game {game_id}")
                    return game_details
            finally:
                if loop:
                    try:
                        loop.close()
                    except:
                        pass
                    asyncio.set_event_loop(None)
            
        except Exception as e:
            logging.error(f"Error with multi-source game details: {e}")
        
        # Instead of fallback API, use current game data from today's games
        try:
            current_games = self.get_todays_games()
            for game in current_games:
                if game.get('id') == game_id:
                    logging.info(f"Using current game data for {game_id}: {game.get('away_team')} @ {game.get('home_team')}")
                    # Return in a format compatible with alert checking
                    return {
                        'gameData': {
                            'teams': {
                                'home': {'name': game.get('home_team')},
                                'away': {'name': game.get('away_team')}
                            }
                        },
                        'liveData': {
                            'linescore': {
                                'currentInning': game.get('inning', 0),
                                'inningState': game.get('inning_state', ''),
                                'offense': {}  # Will be populated by live data when available
                            },
                            'plays': {
                                'currentPlay': {}
                            }
                        }
                    }
        except Exception as e:
            logging.error(f"Error getting current game data for {game_id}: {e}")
        
        return {}
    
    def _get_fallback_game_details(self, game_id: int) -> Dict[str, Any]:
        """Fallback to original MLB API for game details"""
        try:
            # Use the working feed/live endpoint
            url = f"https://statsapi.mlb.com/api/v1.1/game/{game_id}/feed/live"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                logging.info(f"Successfully got live feed for game {game_id}")
                # Log if we have plays
                plays = data.get('liveData', {}).get('plays', {}).get('allPlays', [])
                if plays:
                    logging.info(f"Game {game_id} has {len(plays)} plays available")
                return data
            else:
                logging.warning(f"Feed endpoint returned {response.status_code} for game {game_id}")
            
        except Exception as e:
            logging.error(f"Error fetching game {game_id} details from fallback: {e}")
        
        # Return minimal structure to avoid errors
        return {
            'gameData': {'status': {'detailedState': 'Unknown'}},
            'liveData': {'linescore': {}, 'plays': {'allPlays': []}}
        }
    
    def check_for_alerts(self, game_id: int, game_data: Dict[str, Any]):
        """Check game data for alert conditions based on user preferences"""
        try:
            # Check if this is API-Sports format or fallback format
            if 'teams' in game_data and 'scores' in game_data:
                self._check_api_sports_alerts(game_id, game_data)
            else:
                self._check_fallback_alerts(game_id, game_data)
                        
        except Exception as e:
            logging.error(f"Error checking alerts for game {game_id}: {e}")
    
    def _check_api_sports_alerts(self, game_id: int, game_data: Dict[str, Any]):
        """Check alerts using API-Sports data format"""
        try:
            teams = game_data.get('teams', {})
            scores = game_data.get('scores', {})
            status = game_data.get('status', {})
            
            home_team = teams.get('home', {}).get('name', 'Home')
            away_team = teams.get('away', {}).get('name', 'Away')
            
            # Inning change alerts handled in MLB-StatsAPI section for better data accuracy
            
            # 7th inning alerts handled in MLB-StatsAPI section for better data accuracy
            
            # Tie 9th inning alerts handled in MLB-StatsAPI section for better data accuracy
            
            # Game start alert handling moved to mlb-statsapi section for better accuracy
            
            # Scoring alerts handled in MLB-StatsAPI section with detailed play data
            
            # Add a connection test alert every few minutes
            current_time = datetime.now().timestamp()
            if self._is_new_alert(game_id, 'connection_test', int(current_time / 180)):  # Every 3 minutes
                home_score = scores.get('home', {}).get('total', 0)
                away_score = scores.get('away', {}).get('total', 0)
                self._add_alert(
                    game_id,
                    f"{away_team} @ {home_team}",
                    f"📡 Live data connected - {status.get('long', 'Unknown')} - Score: {away_score}-{home_score}",
                    "test_connection"
                )
                        
        except Exception as e:
            logging.error(f"Error checking API-Sports alerts for game {game_id}: {e}")
    
    def _check_fallback_alerts(self, game_id: int, game_data: Dict[str, Any]):
        """Check alerts using fallback MLB API data format"""
        try:
            # Get basic game info
            game_info = game_data.get('gameData', {})
            live_data = game_data.get('liveData', {})
            
            home_team = game_info.get('teams', {}).get('home', {}).get('name', 'Home')
            away_team = game_info.get('teams', {}).get('away', {}).get('name', 'Away')
            
            # Only log game check if debug level is enabled
            
            # Check current play situation
            linescore = live_data.get('linescore', {})
            current_play = live_data.get('plays', {}).get('currentPlay', {})
            
            # Initialize variables
            current_batter = None
            game_data_for_alerts = None
            
            # Extract current batter information for power hitter alerts
            matchup = current_play.get('matchup', {})
            if matchup:
                batter = matchup.get('batter', {})
                if batter:
                    logging.info(f"Found batter in matchup: {batter.get('fullName', 'Unknown')}")
                    # Get batter stats - ensure they're dictionaries
                    batter_stats = matchup.get('batterHotColdZones', {})
                    if not isinstance(batter_stats, dict):
                        batter_stats = {}
                    
                    splits = matchup.get('splits', {})
                    if not isinstance(splits, dict):
                        splits = {}
                    
                    # Extract home run data - try multiple possible locations
                    season_hrs = 0
                    game_hrs = 0  # Will attempt to detect from game box score data
                    
                    # Try to get season home runs from various possible fields
                    if 'stats' in batter:
                        for stat in batter.get('stats', []):
                            if stat.get('type', {}).get('displayName') == 'season':
                                season_hrs = stat.get('stats', {}).get('homeRuns', 0)
                                break
                    
                    # Also check if home runs are in the matchup data directly
                    if not season_hrs:
                        # Try various possible locations for home run data
                        if isinstance(splits.get('batter'), dict):
                            season_hrs = splits.get('batter', {}).get('homeRuns', 0)
                        
                        if not season_hrs and isinstance(matchup.get('batterStats'), dict):
                            season_hrs = matchup.get('batterStats', {}).get('homeRuns', 0)
                        
                        if not season_hrs and isinstance(batter.get('seasonStats'), dict):
                            batting = batter.get('seasonStats', {}).get('batting', {})
                            if isinstance(batting, dict):
                                season_hrs = batting.get('homeRuns', 0)
                        
                        if not season_hrs and isinstance(batter.get('stats'), dict):
                            batting = batter.get('stats', {}).get('batting', {})
                            if isinstance(batting, dict):
                                season_hrs = batting.get('homeRuns', 0)
                    
                    # If still no home runs found, fetch from API
                    batter_id = batter.get('id', 0)
                    if not season_hrs and batter_id:
                        logging.info(f"Fetching season stats for batter ID {batter_id}")
                        player_stats = self._get_player_season_stats(batter_id)
                        season_hrs = player_stats.get('homeRuns', 0)
                    
                    # Get batter name - handle both string and dict formats
                    if isinstance(batter.get('fullName'), str):
                        batter_name = batter.get('fullName', '')
                    else:
                        batter_name = f"{batter.get('firstName', '')} {batter.get('lastName', '')}".strip()
                    
                    # Now attempt to detect same-game home runs from boxscore data
                    game_hrs = self._detect_same_game_hrs(game_id, batter_id, batter_name)
                    if game_hrs > 0:
                        logging.info(f"🚀 SAME-GAME HR DETECTED: {batter_name} has {game_hrs} HR(s) in current game!")
                    
                    if not batter_name:
                        batter_name = batter.get('boxscoreName', '') or 'Unknown Batter'
                    
                    # Create batter data dictionary
                    current_batter = {
                        'name': batter_name,
                        'season_home_runs': season_hrs,
                        'game_home_runs': game_hrs,
                        'id': batter.get('id', 0)
                    }
                    
                    # Log current batter for debugging
                    if batter_name and batter_name != 'Unknown Batter':
                        logging.info(f"🏏 Current batter: {batter_name} (Season HRs: {season_hrs}, Game HRs: {game_hrs})")
                        # Log what data fields we found
                        logging.debug(f"Batter data fields: {list(batter.keys())}")
                        if matchup:
                            logging.debug(f"Matchup data fields: {list(matchup.keys())}")
                    
                    # Check for power hitter alerts
                    game_data_for_alerts = {
                        'home_team': home_team,
                        'away_team': away_team,
                        'inning': linescore.get('currentInning', 0),
                        'base_runners': []  # Will be updated after we calculate bases_occupied
                    }
                    
                    # Note: we'll call power hitter check after we calculate bases_occupied below
            
            # Also check for baserunners in the linescore offense data
            offense = linescore.get('offense', {})
            
            # Always check for runners (needed for high-probability situations)
            # Only log runner detection if runners are found
            current_runners = current_play.get('runners', [])
            
            bases_occupied = []
            
            # Check runners from current play
            runners = current_play.get('runners', [])
            for runner in runners:
                if runner.get('movement', {}).get('end'):
                    base = runner['movement']['end']
                    if base in ['1B', '2B', '3B']:
                        bases_occupied.append(base)
            
            # Also check linescore for base runners
            if offense.get('first'):
                if '1B' not in bases_occupied:
                    bases_occupied.append('1B')
            if offense.get('second'):
                if '2B' not in bases_occupied:
                    bases_occupied.append('2B')
            if offense.get('third'):
                if '3B' not in bases_occupied:
                    bases_occupied.append('3B')
            
            # Only log if there are actually runners on base
            if bases_occupied:
                logging.info(f"🏃 Runners detected in {away_team} @ {home_team}: {bases_occupied}")
            
            # Get current outs
            outs = linescore.get('outs', current_play.get('count', {}).get('outs', 0))
            
            # ALWAYS check for high-probability scoring situations (regardless of other settings)
            if bases_occupied:  # Only if there are runners on base
                self._check_high_probability_situations(game_id, f"{away_team} @ {home_team}", bases_occupied, outs)
            
            # Check for power hitter alerts if we have batter info
            if current_batter and game_data_for_alerts:
                game_data_for_alerts['base_runners'] = bases_occupied
                logging.info(f"Checking power hitter alerts for {current_batter['name']} with {current_batter['season_home_runs']} HRs")
                self._check_power_hitter_alerts(game_id, game_data_for_alerts, current_batter)
                
                # Check weather delays and resumptions
                self._check_weather_delay_alerts(game_id, game_data)
                
                # Check weather condition alerts (wind, temperature, HR boost conditions)
                self._check_weather_alerts(game_id, game_data)
            elif matchup and not current_batter:
                logging.debug("Matchup found but no current batter extracted")
            
            # Regular runners alert (if enabled and not covered by high-probability alerts)
            if bases_occupied and self.notification_preferences.get('runners', False):
                # Create proper context data for runner alerts
                runner_alert_data = {
                    'bases_hash': self._bases_hash(bases_occupied),
                    'outs': outs,
                    'batter_id': current_batter.get('id', '') if current_batter else '',
                    'pa_id': current_batter.get('at_bat_index', '') if current_batter else '',
                    'runners': bases_occupied,
                    'context_game': game_data,
                    'half_inning': self._half_inning_key(game_data),
                    'state_value': f"{self._bases_hash(bases_occupied)}_{outs}"  # Unique per base/out state
                }
                
                if self._is_new_alert(game_id, 'runners', runner_alert_data):
                    alert_msg = f"Runners on base: {', '.join(sorted(bases_occupied))}\nScoring opportunity developing!"
                    
                    # Add AI analysis if enabled for runners
                    logging.info(f"🔍 AI Runners Check: ai_analyze_runners={self.notification_preferences.get('ai_analyze_runners', False)}, ai_predict_scoring={self.notification_preferences.get('ai_predict_scoring', False)}")
                    if self.openai_helper.is_available() and self.notification_preferences.get('ai_analyze_runners', False):
                        # Create enhanced game data with more context
                        enhanced_game_data = {
                            'inning': linescore.get('currentInning', 0),
                            'outs': outs,
                            'base_runners': bases_occupied,
                            'away_score': linescore.get('teams', {}).get('away', {}).get('runs', 0),
                            'home_score': linescore.get('teams', {}).get('home', {}).get('runs', 0),
                            'inning_state': linescore.get('inningState', ''),
                            'runners_count': len(bases_occupied)
                        }
                        
                        # Add scoring probability prediction if enabled
                        if self.notification_preferences.get('ai_predict_scoring', False):
                            logging.info(f"🎯 FIRING AI Scoring Probability prediction!")
                            scoring_prediction = self.openai_helper.predict_scoring_probability(enhanced_game_data)
                            if scoring_prediction:
                                alert_msg += f"\n\n📊 Predict Scoring Probability: {scoring_prediction['probability']}%"
                                alert_msg += f"\n🎯 Key Factor: {scoring_prediction['factor']}"
                            else:
                                logging.warning("AI scoring prediction failed - no response from OpenAI")
                        else:
                            # Fallback: General runner analysis (when ai_predict_scoring is disabled)
                            scoring_prediction = self.openai_helper.predict_scoring_probability(enhanced_game_data)
                            if scoring_prediction:
                                alert_msg += f"\n\n🔮 AI Analysis: {scoring_prediction['probability']}% chance to score"
                                alert_msg += f"\n📈 Factor: {scoring_prediction['factor']}"
                    else:
                        # Enhanced fallback when AI completely disabled
                        risp_runners = [base for base in bases_occupied if base in ['2B', '3B']]
                        if len(risp_runners) > 0:
                            alert_msg += f"\n🎯 {len(risp_runners)} runner(s) in scoring position!"
                        if outs <= 1:
                            alert_msg += f"\n⚡ Good scoring opportunity with {outs} out(s)!"
                    
                    self._add_alert(
                        game_id,
                        f"{away_team} @ {home_team}",
                        alert_msg,
                        "runners"
                    )
            
            # Check for inning changes (only if enabled)
            if self.notification_preferences.get('inning_change', False):
                current_inning = linescore.get('currentInning', 0)
                inning_state = linescore.get('inningState', '')
                inning_key = f"{current_inning}_{inning_state}"
                
                if current_inning > 0 and self._is_new_alert(game_id, 'inning', inning_key):
                    self._add_alert(
                        game_id,
                        f"{away_team} @ {home_team}",
                        f"Inning Change: {inning_state} of the {current_inning}",
                        "inning"
                    )
            
            # Check for 7th inning warning (only if enabled)
            if self.notification_preferences.get('seventh_inning', False):
                current_inning = linescore.get('currentInning', 0)
                # Use game_id in the data to make it unique per game
                if current_inning == 7 and self._is_new_alert(game_id, 'seventh_inning_warning', f'7th_game_{game_id}'):
                    alert_msg = f"⚠️ 7th Inning Warning!\nGame entering final innings - critical moments ahead!"
                    
                    # Add AI analysis if enabled for enhanced alerts
                    if self.openai_helper.is_available() and self.notification_preferences.get('ai_enhance_alerts', False):
                        # Add game event summary if enabled
                        if self.notification_preferences.get('ai_summarize_events', False):
                            # Get recent alerts for this game for context
                            recent_events = [alert['message'] for alert in self.alerts[:5] if alert.get('game_id') == game_id]
                            if recent_events:
                                summary = self.openai_helper.summarize_game_events(
                                    recent_events,
                                    f"{away_team} @ {home_team}"
                                )
                                if summary:
                                    alert_msg += f"\n\n📝 Game Summary: {summary}"
                        else:
                            ai_analysis = self.openai_helper.enhance_alert_message(
                                "seventh_inning",
                                f"{away_team} @ {home_team}",
                                "Entering 7th inning"
                            )
                            if ai_analysis:
                                alert_msg += f"\n\n🤖 AI Insight: {ai_analysis}"
                    
                    self._add_alert(
                        game_id,
                        f"{away_team} @ {home_team}",
                        alert_msg,
                        "seventh_inning"
                    )
            
            # Check for tie game going into 9th inning (only if enabled)
            if self.notification_preferences.get('tie_ninth', True):
                current_inning = linescore.get('currentInning', 0)
                home_score = linescore.get('teams', {}).get('home', {}).get('runs', 0)
                away_score = linescore.get('teams', {}).get('away', {}).get('runs', 0)
                
                # Check if it's the 9th inning and scores are tied
                if (current_inning == 9 and home_score == away_score and 
                    self._is_new_alert(game_id, 'tie_ninth', f'tie9th_game_{game_id}')):
                    alert_msg = f"🔥 TIED GOING INTO THE 9TH!\nScore: {away_score}-{home_score}\nEvery pitch counts now - sudden death territory!"
                    
                    # Add AI analysis if enabled for enhanced alerts
                    if self.openai_helper.is_available() and self.notification_preferences.get('ai_enhance_alerts', False):
                        game_data = {
                            'away_team': away_team,
                            'home_team': home_team,
                            'away_score': away_score,
                            'home_score': home_score,
                            'inning': 9,
                            'inning_state': 'Top',
                            'base_runners': [],
                            'outs': 0
                        }
                        ai_analysis = self.openai_helper.analyze_game_situation(game_data)
                        if ai_analysis:
                            alert_msg += f"\n\n🤖 AI Insight: {ai_analysis}"
                    
                    self._add_alert(
                        game_id,
                        f"{away_team} @ {home_team}",
                        alert_msg,
                        "tie_ninth"
                    )
            
            # Check for game start (only if enabled) - ULTRA STRICT timing
            if self.notification_preferences.get('game_start', False):
                current_inning = linescore.get('currentInning', 0)
                inning_state = linescore.get('inningState', '')
                game_status = game_data.get('status', {}).get('detailedState', '')
                
                # Get plays to confirm the game has actually started with real play data
                all_plays = live_data.get('plays', {}).get('allPlays', [])
                
                # EXTRA STRICT: Verify there are actual at-bats, not just status changes
                actual_at_bats = []
                for play in all_plays:
                    if play.get('about', {}).get('atBatIndex') is not None:
                        # This is a real at-bat with pitch data
                        actual_at_bats.append(play)
                
                logging.debug(f"Game {game_id} start check: Inning={current_inning}, State={inning_state}, Status={game_status}, TotalPlays={len(all_plays)}, AtBats={len(actual_at_bats)}")
                
                # Game has TRULY started when:
                # 1. We're in inning 1 or later AND
                # 2. Game status is "In Progress" (not Preview/Warmup) AND  
                # 3. There's actual at-bat data (not just lineup changes) AND
                # 4. Inning state shows active play (Top/Bottom)
                if (current_inning >= 1 and 
                    game_status == 'In Progress' and
                    len(actual_at_bats) > 0 and
                    inning_state in ['Top', 'Bottom'] and 
                    self._is_new_alert(game_id, 'game_started_verified', f'started_game_{game_id}_verified')):
                    
                    first_at_bat = actual_at_bats[0]
                    batter_name = first_at_bat.get('matchup', {}).get('batter', {}).get('fullName', 'Unknown')
                    
                    alert_msg = f"🎮 FIRST PITCH THROWN!\n{batter_name} steps into the box\nGame is officially underway!"
                    
                    # Add AI analysis if enabled for enhanced alerts
                    if self.openai_helper.is_available() and self.notification_preferences.get('ai_enhance_alerts', False):
                        ai_analysis = self.openai_helper.enhance_alert_message(
                            "game_start",
                            f"{away_team} @ {home_team}",
                            f"First pitch to {batter_name} - game underway"
                        )
                        if ai_analysis:
                            alert_msg += f"\n\n🤖 AI Insight: {ai_analysis}"
                    
                    self._add_alert(
                        game_id,
                        f"{away_team} @ {home_team}",
                        alert_msg,
                        "game_start"
                    )
                    
                    logging.info(f"🎮 Game start alert sent for {game_id} after confirming {len(actual_at_bats)} at-bats")
            
            # Check recent plays for hits, home runs, strikeouts, and scoring
            all_plays = live_data.get('plays', {}).get('allPlays', [])
            
            # Debug: Log play structure to understand format
            if all_plays and len(all_plays) > 0:
                latest_play = all_plays[-1]
                # Check multiple fields for play outcome
                result = latest_play.get('result', {})
                about = latest_play.get('about', {})
                play_desc = latest_play.get('description', '')
                
                # Only log if there's an actual event happening
                if about.get('isComplete', False):
                    event = result.get('event', '')
                    if event and event not in ['Game Advisory', 'Batter Timeout', 'Mound Visit']:
                        logging.info(f"Recent play detected: {event} - {play_desc}")
            
            if all_plays:
                # Only check the most recent at-bat or the one just completed
                current_at_bat_index = current_play.get('about', {}).get('atBatIndex', 0)
                
                # Check only the last 2 plays (current and previous at-bat)
                for i in range(min(2, len(all_plays))):
                    play = all_plays[-(i+1)]
                    play_result = play.get('result', {})
                    about = play.get('about', {})
                    play_at_bat_index = about.get('atBatIndex', 0)
                    
                    # Skip if this play is too old (more than 1 at-bat ago)
                    if play_at_bat_index < current_at_bat_index - 1:
                        continue
                    
                    # Skip incomplete plays
                    if not about.get('isComplete', False):
                        continue
                    
                    # Get play details
                    event = play_result.get('event', '')
                    event_type = play_result.get('eventType', '')
                    description = play_result.get('description', '')
                    play_index = play.get('atBatIndex', 0)
                    
                    # Additional description from play object
                    if not description:
                        description = play.get('description', '')
                
                    # Check for home runs only (if enabled and takes priority over regular hits)
                    if self.notification_preferences.get('home_runs', False):
                        if event == 'Home Run' or event_type == 'home_run' or 'home run' in description.lower():
                            # Use description for deduplication to avoid duplicate alerts
                            if self._is_new_alert(game_id, 'home_run', {'play_index': play_index, 'description': description}):
                                alert_msg = f"🚀 HOME RUN!\n{description}"
                                
                                # Add AI analysis if enabled for hits/home runs
                                if self.openai_helper.is_available() and self.notification_preferences.get('ai_analyze_hits', True):
                                    ai_analysis = self.openai_helper.enhance_alert_message(
                                        "home_run",
                                        f"{away_team} @ {home_team}",
                                        description
                                    )
                                    if ai_analysis:
                                        alert_msg += f"\n\n🤖 AI Insight: {ai_analysis}"
                                
                                self._add_alert(
                                    game_id,
                                    f"{away_team} @ {home_team}",
                                    alert_msg,
                                    "home_run"
                                )
                                break
                    # Check for all hits (only if home runs only is not enabled)
                    elif self.notification_preferences.get('hits', False):
                        if event in ['Single', 'Double', 'Triple', 'Home Run'] or event_type in ['single', 'double', 'triple', 'home_run'] or 'hit' in description.lower():
                            # Use description for deduplication to avoid duplicate alerts
                            if self._is_new_alert(game_id, 'hit', {'play_index': play_index, 'description': description}):
                                alert_msg = f"🏏 Hit!\n{description}"
                                
                                # Add AI analysis if enabled for hits
                                if self.openai_helper.is_available() and self.notification_preferences.get('ai_analyze_hits', True):
                                    ai_analysis = self.openai_helper.enhance_alert_message(
                                        "hit",
                                        f"{away_team} @ {home_team}",
                                        description
                                    )
                                    if ai_analysis:
                                        alert_msg += f"\n\n🤖 AI Insight: {ai_analysis}"
                                
                                self._add_alert(
                                    game_id,
                                    f"{away_team} @ {home_team}",
                                    alert_msg,
                                    "hit"
                                )
                                break
                    
                    # Check for strikeouts (only if enabled)
                    if self.notification_preferences.get('strikeouts', False):
                        if event == 'Strikeout' or event_type == 'strikeout' or 'strikeout' in description.lower() or 'struck out' in description.lower():
                            # Use description for deduplication
                            if self._is_new_alert(game_id, 'strikeout', {'play_index': play_index, 'description': description}):
                                alert_msg = f"⚾ STRIKEOUT!\n{description if description else event}"
                                
                                # Add AI analysis if enabled for strikeouts
                                if self.openai_helper.is_available() and self.notification_preferences.get('ai_analyze_hits', True):
                                    ai_analysis = self.openai_helper.enhance_alert_message(
                                        "strikeout",
                                        f"{away_team} @ {home_team}",
                                        description if description else event
                                    )
                                    if ai_analysis:
                                        alert_msg += f"\n\n🤖 AI Insight: {ai_analysis}"
                                
                                self._add_alert(
                                    game_id,
                                    f"{away_team} @ {home_team}",
                                    alert_msg,
                                    "strikeout"
                                )
                                break
                    
                    # Check for scoring plays (only if enabled) - PRIMARY scoring detection
                    if self.notification_preferences.get('scoring', False):
                        if 'run' in description.lower() or 'score' in description.lower() or 'rbi' in description.lower() or play_result.get('rbi', 0) > 0:
                            # Create unique key for this scoring event
                            # Use current score and inning to avoid duplicates
                            home_score = linescore.get('teams', {}).get('home', {}).get('runs', 0)
                            away_score = linescore.get('teams', {}).get('away', {}).get('runs', 0)
                            current_inning = linescore.get('currentInning', 0)
                            score_key = f"play_score_{away_score}_{home_score}_inning_{current_inning}_{play_index}"
                            
                            if self._is_new_alert(game_id, 'scoring_detailed', score_key):
                                alert_msg = f"💯 SCORE!\n{description}"
                                
                                # Add AI analysis if available and enabled
                                if self.openai_helper.is_available() and self.notification_preferences.get('ai_insights', True):
                                    game_data_for_ai = {
                                        'away_team': away_team,
                                        'home_team': home_team,
                                        'away_score': away_score,
                                        'home_score': home_score,
                                        'inning': current_inning,
                                        'inning_state': linescore.get('inningState', ''),
                                        'base_runners': bases_occupied,
                                        'outs': outs
                                    }
                                    ai_analysis = self.openai_helper.analyze_game_situation(game_data_for_ai)
                                    if ai_analysis:
                                        alert_msg += f"\n\n🤖 AI Insight: {ai_analysis}"
                                
                                self._add_alert(
                                    game_id,
                                    f"{away_team} @ {home_team}",
                                    alert_msg,
                                    "scoring"
                                )
                                break
            

            
            # Debug logging for API issues
            if not all_plays and home_team != 'Home':
                logging.warning(f"No play-by-play data available for {game_id}: {away_team} @ {home_team}")
                        
        except Exception as e:
            logging.error(f"Error checking fallback alerts for game {game_id}: {e}", exc_info=True)
    
    def _half_inning_key(self, game_data):
        """Generate half-inning key from game context"""
        if isinstance(game_data, dict):
            # Check for MLB API format
            linescore = game_data.get('liveData', {}).get('linescore', {})
            if linescore:
                inning = linescore.get('currentInning', 0)
                is_top = linescore.get('inningState', '').lower() == 'top'
                return f"{'T' if is_top else 'B'}{inning}"
            
            # Check for simplified format
            inning = game_data.get('inning', 0)
            inning_state = game_data.get('inning_state', '')
            if inning and inning_state:
                is_top = 'top' in inning_state.lower()
                return f"{'T' if is_top else 'B'}{inning}"
        
        return "unknown"
    
    def _plate_appearance_id(self, play_data):
        """Extract plate appearance ID from play data"""
        if isinstance(play_data, dict):
            # Try to get official atBatIndex
            about = play_data.get('about', {})
            if about:
                return about.get('atBatIndex', '')
            
            # Fallback to play index
            return play_data.get('play_index', '')
        
        return str(play_data)[:20]  # Fallback to truncated string representation
    
    def _bases_hash(self, runners):
        """Create stable hash for base runner positions"""
        if isinstance(runners, list):
            return '_'.join(sorted(str(r) for r in runners)) if runners else "EMPTY"
        return "EMPTY"
    
    def _make_keys(self, game_id: int, alert_type: str, data):
        """Generate deduplication keys based on alert type configuration"""
        # Get configuration for this alert type
        cfg = ALERT_CONFIG.get(alert_type, ALERT_CONFIG["default"])
        
        # Extract context data
        if isinstance(data, dict):
            half_inning = data.get("half_inning") or self._half_inning_key(data.get("context_game", data))
            pa_id = data.get("pa_id") or self._plate_appearance_id(data.get("context_play", data))
            
            # Build content key from configured fields
            content_pieces = []
            for field in cfg["content_fields"]:
                if field == "bases_hash":
                    content_pieces.append(self._bases_hash(data.get("runners", [])))
                elif field == "pa_id":
                    content_pieces.append(str(pa_id))
                elif field == "half_inning":
                    content_pieces.append(half_inning)
                elif field == "batter_id":
                    content_pieces.append(str(data.get("batter_id", data.get("batter_name", ""))))
                elif field == "season_hr":
                    content_pieces.append(str(data.get("season_hr", "")))
                elif field == "game_hr":
                    content_pieces.append(str(data.get("game_hr", "")))
                elif field == "outs":
                    content_pieces.append(str(data.get("outs", "")))
                elif field == "play_id":
                    content_pieces.append(str(data.get("play_id", data.get("play_index", ""))))
                elif field == "description":
                    desc = data.get("description", "")[:50]  # Truncate long descriptions
                    content_pieces.append(desc)
                elif field == "score_key":
                    content_pieces.append(str(data.get("score_key", "")))
                else:
                    content_pieces.append(str(data.get(field, "")))
            
            content = "|".join(content_pieces)
        else:
            # Simple data types
            half_inning = "unknown"
            pa_id = ""
            content = str(data)[:100]
        
        # Build scope-based simple key
        if cfg["scope"] == "play":
            simple_key = f"{game_id}_{alert_type}_{data.get('play_id', data) if isinstance(data, dict) else data}"
        elif cfg["scope"] == "plate_appearance":
            simple_key = f"{game_id}_{alert_type}_{half_inning}_{pa_id}"
        elif cfg["scope"] == "half_inning":
            simple_key = f"{game_id}_{alert_type}_{half_inning}"
        else:  # game scope
            simple_key = f"{game_id}_{alert_type}"
        
        dedup_key = f"{game_id}_{alert_type}_{content}"
        
        return simple_key, dedup_key, cfg
    
    def _is_new_alert(self, game_id: int, alert_type: str, data) -> bool:
        """Enhanced deduplication check using new robust system"""
        # Convert data format for new deduper
        if isinstance(data, dict):
            alert_data = data.copy()
        else:
            # Handle legacy string/simple data format
            alert_data = {"legacy_data": str(data)}
        
        # Ensure game_id is in data for the deduper
        alert_data["game_id"] = str(game_id)
        
        # Use the enhanced deduplication system
        result = self.deduper.is_new_alert(str(game_id), alert_type, alert_data)
        
        if result:
            logging.debug(f"✅ Alert allowed: {alert_type} for game {game_id}")
        else:
            logging.debug(f"⛔ Alert blocked: {alert_type} for game {game_id} (deduplication)")
        
        return result
    
    def _cleanup_old_alerts(self, current_time: float):
        """Remove old entries from recent_alerts to prevent memory growth"""
        # Use per-key expiry based on each alert type's window
        to_delete = []
        
        for key, timestamp in self.recent_alerts.items():
            try:
                # Extract alert type from key format: {game_id}_{alert_type}_{content}
                parts = key.split("_", 2)
                if len(parts) >= 2:
                    alert_type = parts[1]
                    cfg = ALERT_CONFIG.get(alert_type, ALERT_CONFIG["default"])
                    ttl = cfg.get("window", self.alert_dedup_window)
                else:
                    ttl = self.alert_dedup_window
            except Exception:
                ttl = self.alert_dedup_window
            
            # Add buffer to prevent premature cleanup (window + 10 seconds)
            if current_time - timestamp > (ttl + 10):
                to_delete.append(key)
        
        # Remove expired entries
        for key in to_delete:
            self.recent_alerts.pop(key, None)
        
        # Also clean up old simple keys (older than 1 hour)
        to_delete = []
        for key, timestamp in self.last_sent_by_simple.items():
            if current_time - timestamp > 3600:  # 1 hour
                to_delete.append(key)
        
        for key in to_delete:
            self.last_sent_by_simple.pop(key, None)
            # Also remove corresponding game state
            self.game_states.pop(key, None)
    
    def _add_alert(self, game_id: int, game_info: str, message: str, alert_type: str):
        """Add a new alert"""
        alert = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'game_id': game_id,
            'game_info': game_info,
            'message': message,
            'type': alert_type
        }
        
        self.alerts.insert(0, alert)  # Add to beginning for newest first
        
        # Keep only the most recent alerts
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[:self.max_alerts]
        
        logging.info(f"Alert added: {game_info} - {message}")
        
        # Track alert outcome for success rate statistics (skip system alerts)
        if alert_type != "system":
            self._track_alert_outcome(game_id, game_info, message, alert_type)
        
        # Send Telegram notification if enabled (but skip system status messages)
        if self.telegram_notifier.enabled and alert_type != "system":
            self.telegram_notifier.send_alert(game_info, message, alert_type)
    
    def set_monitored_games(self, game_ids: List[int], notification_preferences: Optional[Dict[str, bool]] = None):
        """Set which games to monitor and notification preferences"""
        self.monitored_games = set(game_ids)
        if notification_preferences:
            self.notification_preferences.update(notification_preferences)
            # Save notification preferences to persistent storage
            self.persistent_settings.update_notification_preferences(notification_preferences)
        
        # Save monitored games to persistent storage
        self.persistent_settings.update_monitored_games(game_ids)
        
        enabled_alerts = [k for k, v in self.notification_preferences.items() if v]
        logging.info(f"💾 Now monitoring {len(game_ids)} games: {game_ids} (saved to persistent storage)")
        logging.info(f"🔔 Alert types enabled: {enabled_alerts}")
        
        # Add confirmation alert
        if game_ids:
            settings_summary = self.persistent_settings.get_settings_summary()
            self._add_alert(
                0, 
                "System Status",
                f"✅ Settings saved and will persist across restarts\n{settings_summary}",
                "system"
            )
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get current alerts"""
        return self.alerts.copy()
    
    def clear_alerts(self) -> int:
        """Clear all current alerts and return count of cleared alerts"""
        cleared_count = len(self.alerts)
        self.alerts.clear()
        # Also clear recent alerts tracking to prevent any re-population
        self.recent_alerts.clear()
        # Clear deduplication state safely
        try:
            self.deduper.cleanup_old_alerts()  # Use existing cleanup method
        except Exception as e:
            logging.debug(f"Could not clear deduper state: {e}")
        logging.info(f"Cleared {cleared_count} alerts from monitoring system")
        return cleared_count
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent alerts with a limit"""
        return self.alerts[:limit].copy() if self.alerts else []
    
    def get_status(self) -> Dict[str, Any]:
        """Get monitoring status"""
        enabled_alerts = [k for k, v in self.notification_preferences.items() if v]
        return {
            'running': self.running,
            'monitored_games_count': len(self.monitored_games),
            'monitored_games': list(self.monitored_games),
            'total_alerts': len(self.alerts),
            'notification_preferences': self.notification_preferences.copy(),
            'enabled_alert_types': enabled_alerts,
            'last_update': datetime.now(timezone.utc).isoformat()
        }
    
    def start_monitoring(self):
        """Start the background monitoring thread with crash protection"""
        if not self.running:
            self.running = True
            self.monitor_thread = threading.Thread(target=self._safe_monitor_loop, daemon=True)
            self.monitor_thread.start()
            logging.info("MLB monitoring started")
        elif self.monitor_thread and not self.monitor_thread.is_alive():
            # Thread crashed, restart it
            logging.warning("⚠️ Monitoring thread was dead, restarting...")
            self.monitor_thread = threading.Thread(target=self._safe_monitor_loop, daemon=True)
            self.monitor_thread.start()
            logging.info("🔄 Monitoring thread restarted")
    
    def stop_monitoring(self):
        """Stop the background monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logging.info("MLB monitoring stopped")
    
    def _check_live_game_events(self, game):
        """Check for live game events based on score/status changes"""
        game_id = game.get('id')
        away_team = game.get('away_team')
        home_team = game.get('home_team')
        away_score = game.get('away_score', 0)
        home_score = game.get('home_score', 0)
        inning = game.get('inning', 0)
        inning_state = game.get('inning_state', '')
        
        # Track previous state
        prev_state = self.game_states.get(game_id, {})
        prev_away_score = prev_state.get('away_score', 0)
        prev_home_score = prev_state.get('home_score', 0)
        prev_inning = prev_state.get('inning', 0)
        prev_inning_state = prev_state.get('inning_state', '')
        
        # Update current state
        self.game_states[game_id] = {
            'away_score': away_score,
            'home_score': home_score,
            'inning': inning,
            'inning_state': inning_state
        }
        
        # Score change alerts (FALLBACK - only if detailed play-by-play misses it)
        # NOTE: This is secondary to the detailed play-by-play analysis above
        if self.notification_preferences.get('scoring', False):
            if away_score > prev_away_score:
                # Use fallback key to avoid conflicts with detailed alerts
                score_key = f"fallback_{away_team}_scores_{away_score}_{home_score}_inning_{inning}"
                if self._is_new_alert(game_id, 'scoring_fallback', score_key):
                    alert_msg = f"🏃 {away_team} SCORES! Now {away_score}-{home_score}"
                    
                    self._add_alert(
                        game_id,
                        f"{away_team} @ {home_team}",
                        alert_msg,
                        "scoring"
                    )
            if home_score > prev_home_score:
                # Use fallback key to avoid conflicts with detailed alerts
                score_key = f"fallback_{home_team}_scores_{away_score}_{home_score}_inning_{inning}"
                if self._is_new_alert(game_id, 'scoring_fallback', score_key):
                    alert_msg = f"🏃 {home_team} SCORES! Now {away_score}-{home_score}"
                    
                    self._add_alert(
                        game_id,
                        f"{away_team} @ {home_team}",
                        alert_msg,
                        "scoring"
                    )
        
        # Inning changes handled in MLB-StatsAPI detailed section to avoid duplication
        
        # Note: Removed simplified runner and hit detection from here
        # These are now handled by detailed play-by-play analysis in _check_fallback_alerts
        # This prevents duplicate alerts for the same events
    
    def _safe_monitor_loop(self):
        """Safe wrapper for monitoring loop with crash recovery"""
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while self.running:
            try:
                self._monitor_loop()
                consecutive_errors = 0  # Reset on success
            except Exception as e:
                consecutive_errors += 1
                logging.error(f"❌ Critical error in monitoring (error {consecutive_errors}/{max_consecutive_errors}): {e}")
                logging.error(f"Traceback: {traceback.format_exc()}")
                
                if consecutive_errors >= max_consecutive_errors:
                    logging.error("🛑 Too many consecutive errors, stopping monitoring")
                    self.running = False
                    self._add_alert(
                        0,
                        "System Error",
                        f"⚠️ Monitoring stopped due to repeated errors. Please check logs.",
                        "system"
                    )
                    break
                
                # Progressive backoff
                time.sleep(min(consecutive_errors * 5, 30))
        
        logging.info("Monitoring loop exited")
    
    def _monitor_loop(self):
        """Main monitoring loop with enhanced live data detection"""
        iteration_count = 0
        while self.running:
            iteration_count += 1
            try:
                if self.monitored_games:
                    # Get fresh game data
                    current_games = self.get_todays_games()
                    
                    for game_id in self.monitored_games.copy():
                        try:
                            # Find the game in current data
                            current_game = None
                            for game in current_games:
                                if game.get('id') == game_id:
                                    current_game = game
                                    break
                            
                            if current_game:
                                status = current_game.get('status', '')
                                away_team = current_game.get('away_team', 'Away')
                                home_team = current_game.get('home_team', 'Home')
                                
                                if 'In Progress' in status or 'Live' in status:
                                    logging.info(f"🔴 LIVE GAME: {away_team} @ {home_team} - {status} - CHECKING FOR ALERTS")
                                    self._check_live_game_events(current_game)
                                else:
                                    logging.info(f"⏳ WAITING: {away_team} @ {home_team} - {status} - No alerts until game starts")
                                
                                # Also try to get detailed data
                                game_data = self.get_game_details(game_id)
                                if game_data:
                                    self.check_for_alerts(game_id, game_data)
                                    # Check weather-based alerts  
                                    self._check_weather_alerts(game_id, current_game)
                            
                        except Exception as e:
                            logging.error(f"Error monitoring game {game_id}: {e}")
                
                # Check every 3 seconds for maximum speed
                for _ in range(3):
                    if not self.running:
                        break
                    time.sleep(1)
                
                # Periodic health log and cleanup
                if iteration_count % 20 == 0:  # Every minute
                    logging.debug(f"✅ Monitoring healthy - iteration {iteration_count}")
                    # Clean up old deduplication entries
                    self.deduper.cleanup_old_alerts()
                    
            except Exception as e:
                logging.error(f"Error in monitoring iteration: {e}")
                raise  # Re-raise to be handled by _safe_monitor_loop

    def _get_player_season_stats(self, player_id: int) -> Dict[str, Any]:
        """Fetch player's season statistics from MLB API"""
        try:
            # Get current year
            current_year = datetime.now().year
            
            # MLB Stats API endpoint for player stats
            url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats"
            params = {
                'stats': 'season',
                'season': current_year,
                'gameType': 'R'  # Regular season
            }
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                stats = data.get('stats', [])
                
                if stats and len(stats) > 0:
                    season_stats = stats[0].get('splits', [])
                    if season_stats and len(season_stats) > 0:
                        batting_stats = season_stats[0].get('stat', {})
                        home_runs = batting_stats.get('homeRuns', 0)
                        logging.info(f"Fetched season stats for player {player_id}: {home_runs} HRs")
                        return {
                            'homeRuns': home_runs,
                            'rbi': batting_stats.get('rbi', 0),
                            'avg': batting_stats.get('avg', '.000')
                        }
            
            logging.debug(f"Could not fetch season stats for player {player_id}")
            return {'homeRuns': 0}
            
        except Exception as e:
            logging.error(f"Error fetching player stats: {e}")
            return {'homeRuns': 0}
    
    def _calc_power_prob(self, batter_data: Dict[str, Any], pitcher_data: Dict[str, Any], game_context: Dict[str, Any]) -> tuple:
        """Calculate power probability using advanced math engines"""
        try:
            # Extract batter statistics
            batter_id = batter_data.get('id', '')
            season_hrs = batter_data.get('season_home_runs', 0)
            
            # Build PowerFeatures
            feat = PowerFeatures(
                # Use actual values if available, otherwise use defaults
                iso_14=batter_data.get('iso_14'),
                hr_per_pa_14=batter_data.get('hr_per_pa_14'),
                iso_season=batter_data.get('iso_season'),
                platoon_iso_delta=batter_data.get('platoon_iso_delta'),
                park_hr_factor=MATH_ENGINE_CONFIG["PARK_HR_FACTOR"].get(
                    game_context.get('park_name', 'default'),
                    MATH_ENGINE_CONFIG["PARK_HR_FACTOR"]["default"]
                ),
                wind_deg_toward=game_context.get('wind_deg_toward'),
                wind_mph=game_context.get('wind_mph'),
                cf_azimuth_deg=MATH_ENGINE_CONFIG["PARK_CF_AZIMUTH"].get(
                    game_context.get('park_name', 'default'),
                    MATH_ENGINE_CONFIG["PARK_CF_AZIMUTH"]["default"]
                ),
                temp_f=game_context.get('temp_f'),
                pitcher_hr9_30d=pitcher_data.get('hr9_30d') if pitcher_data else None,
                tto=pitcher_data.get('tto') if pitcher_data else None,
                count_state=game_context.get('count'),
                n_iso_14=batter_data.get('n_iso_14'),
                n_hr_per_pa_14=batter_data.get('n_hr_per_pa_14'),
                league_iso=MATH_ENGINE_CONFIG["LEAGUE_ISO"],
                league_hr_per_pa=MATH_ENGINE_CONFIG["LEAGUE_PA_HR"],
                league_pitcher_hr9_30d=MATH_ENGINE_CONFIG["LEAGUE_PITCHER_HR9_30D"]
            )
            
            # Calculate raw probability
            p_raw, parts = pa_hr_probability(feat)
            
            # Apply Platt calibration
            platt_params = PlattParams(
                a=MATH_ENGINE_CONFIG["PLATT_A"],
                b=MATH_ENGINE_CONFIG["PLATT_B"]
            )
            p_calibrated = platt_scale(p_raw, platt_params)
            
            # Determine tier
            tier = power_tier_from_prob(p_calibrated, MATH_ENGINE_CONFIG["LEAGUE_PA_HR"])
            
            # Store for value scoring
            self.last_power_probs[(game_context.get('game_id'), batter_id)] = p_calibrated
            
            return p_calibrated, tier, parts
            
        except Exception as e:
            logging.debug(f"Error calculating power probability: {e}")
            # Fallback to simple threshold-based calculation
            season_hrs = batter_data.get('season_home_runs', 0)
            if season_hrs >= 30:
                return 0.08, "A", {}
            elif season_hrs >= 20:
                return 0.05, "B", {}
            else:
                return 0.036, "C", {}
    
    def _check_power_hitter_alerts(self, game_id: int, game_data: Dict[str, Any], current_batter: Optional[Dict[str, Any]] = None):
        """Check for power hitter situations and generate alerts"""
        if not current_batter:
            return
        
        try:
            # Validate inputs are dictionaries
            if not isinstance(game_data, dict):
                logging.error(f"game_data is not a dict: {type(game_data)}")
                return
            if not isinstance(current_batter, dict):
                logging.error(f"current_batter is not a dict: {type(current_batter)}")
                return
            
            game_info = f"{game_data.get('away_team', 'Away')} @ {game_data.get('home_team', 'Home')}"
            batter_name = current_batter.get('name', 'Unknown')
            batter_id = current_batter.get('id', batter_name)  # Use ID if available, else name
            season_hrs = current_batter.get('season_home_runs', 0)
            game_hrs = current_batter.get('game_home_runs', 0)
            inning = game_data.get('inning', 0)
            bases_occupied = game_data.get('base_runners', [])
            
            # Get plate appearance context
            pa_id = current_batter.get('at_bat_index', f"{inning}_{batter_id}")
            
            # Calculate power probability using math engines
            game_context = {
                'game_id': game_id,
                'park_name': game_data.get('park_name', 'default'),
                'wind_deg_toward': game_data.get('wind_deg_toward'),
                'wind_mph': game_data.get('wind_mph'),
                'temp_f': game_data.get('temp_f'),
                'count': game_data.get('count', 'neutral'),
                'inning': inning
            }
            
            pitcher_data = game_data.get('current_pitcher', {})
            p_hr, tier, components = self._calc_power_prob(current_batter, pitcher_data, game_context)
            
            logging.info(f"Power check: {batter_name} has {season_hrs} HRs, P(HR)={p_hr:.3f}, Tier={tier}, Bases={bases_occupied}")
            
            # Check for power hitter (20+ HRs or very high probability - Tier A)
            logging.info(f"🔍 Power Hitter Check: {batter_name} - season_hrs={season_hrs}, tier={tier}, p_hr={p_hr:.3f}")
            if (self.notification_preferences.get('power_hitter', True) and 
                (season_hrs >= 20 or (tier == "A" and p_hr >= 0.040))):
                # Create proper context data for new deduplication system
                alert_data = {
                    'batter_id': batter_id,
                    'batter_name': batter_name,
                    'season_hr': season_hrs,
                    'pa_id': pa_id,
                    'context_game': game_data,
                    'half_inning': self._half_inning_key(game_data),
                    'state_value': f"{batter_id}_{season_hrs}_{pa_id}"  # Unique per at-bat
                }
                
                if self._is_new_alert(game_id, 'power_hitter', alert_data):
                    logging.info(f"🎯 FIRING Power Hitter alert for {batter_name}!")
                    # Determine qualification reason for transparency
                    qual_reason = f"{season_hrs} HRs" if season_hrs >= 20 else f"Elite Tier A ({p_hr:.1%})"
                    alert_msg = f"💥 Batter with 20+ HRs This Season!\n{batter_name} COMING UP - {qual_reason}!"
                    # Only show tier if it has a meaningful value
                    if tier and tier != "None":
                        alert_msg += f"\n📊 P(HR): {p_hr:.1%} | Tier: {tier}"
                    else:
                        alert_msg += f"\n📊 P(HR): {p_hr:.1%}"
                    if 'w_out' in components and components['w_out'] > 0:
                        alert_msg += f"\n💨 Wind helping: +{components['boost']:.0%} boost"
                    
                    # Add AI prediction if enabled for power hitters
                    if self.openai_helper.is_available() and self.notification_preferences.get('ai_analyze_power_hitter', True):
                        # Create enhanced game situation with real data
                        game_situation = {
                            'away_team': game_data.get('away_team'),
                            'home_team': game_data.get('home_team'),
                            'inning': game_data.get('inning', 0),
                            'outs': game_data.get('outs', 0),  # Use real outs data
                            'base_runners': bases_occupied,
                            'away_score': game_data.get('away_score', 0),  # Use real scores
                            'home_score': game_data.get('home_score', 0),
                            'power_hitter_context': True,
                            'season_hrs': season_hrs,
                            'tier': tier
                        }
                        
                        ai_prediction = self.openai_helper.predict_at_bat_outcome(
                            current_batter,
                            game_situation
                        )
                        if ai_prediction:
                            alert_msg += f"\n\n🔮 AI Prediction: {ai_prediction}"
                    else:
                        # Fallback analysis when AI unavailable
                        if len(bases_occupied) > 0:
                            alert_msg += f"\n🎯 Power threat with runners on base!"
                        if inning >= 7:
                            alert_msg += f"\n⏰ Late-game power situation!"
                    
                    self._add_alert(
                        game_id, game_info,
                        alert_msg,
                        "power_hitter"
                    )
            
            # Check for hot hitter (already homered in this game)
            logging.info(f"🔍 Hot Hitter Check: {batter_name} - game_hrs={game_hrs}, season_hrs={season_hrs}")
            if (self.notification_preferences.get('hot_hitter', True) and
                game_hrs > 0):
                # Create proper context data for hot hitter alerts
                hot_alert_data = {
                    'batter_id': batter_id,
                    'batter_name': batter_name,
                    'game_hr': game_hrs,
                    'pa_id': pa_id,
                    'context_game': game_data,
                    'half_inning': self._half_inning_key(game_data),
                    'state_value': f"{batter_id}_{game_hrs}_{pa_id}"  # Unique per at-bat
                }
                
                if self._is_new_alert(game_id, 'hot_hitter', hot_alert_data):
                    logging.info(f"🎯 FIRING Hot Hitter alert for {batter_name}!")
                    # Enhanced messaging for multi-HR games
                    if game_hrs >= 2:
                        alert_msg = f"🚀 Batter with HR in Current Game!\n{batter_name} COMING UP - MULTI-HR GAME ({game_hrs} HRs today)!"
                    else:
                        alert_msg = f"🔥 Batter with HR in Current Game!\n{batter_name} COMING UP - already homered today!"
                    
                    # Add AI prediction if enabled for power hitters
                    if self.openai_helper.is_available() and self.notification_preferences.get('ai_analyze_power_hitter', True):
                        # Create enhanced game situation with hot hitter context
                        game_situation = {
                            'away_team': game_data.get('away_team'),
                            'home_team': game_data.get('home_team'),
                            'inning': game_data.get('inning', 0),
                            'outs': game_data.get('outs', 0),  # Use real outs data
                            'base_runners': bases_occupied,
                            'away_score': game_data.get('away_score', 0),  # Use real scores
                            'home_score': game_data.get('home_score', 0),
                            'hot_hitter_context': True,
                            'same_game_hrs': game_hrs,
                            'confidence_boost': True,
                            'multi_hr_game': game_hrs >= 2,
                            'momentum_factor': 'high'
                        }
                        
                        ai_prediction = self.openai_helper.predict_at_bat_outcome(
                            current_batter,
                            game_situation
                        )
                        if ai_prediction:
                            alert_msg += f"\n\n🔮 Hot Streak Analysis: {ai_prediction}"
                    else:
                        # Enhanced fallback analysis for hot hitters
                        if game_hrs >= 2:
                            alert_msg += f"\n🚀 RARE: Multi-HR game - elite confidence level!"
                        if len(bases_occupied) > 0:
                            alert_msg += f"\n🎯 Hot hitter + runners on base = prime RBI opportunity!"
                        if inning >= 7:
                            alert_msg += f"\n⏰ Late-game momentum situation!"
                    
                    self._add_alert(
                        game_id, game_info,
                        alert_msg,
                        "hot_hitter"
                    )
            
            # Check for clutch HR threat (power hitter + RISP in late innings)
            # True RISP = runners in scoring position (2B or 3B)
            risp_runners = [base for base in bases_occupied if base in ['2B', '3B']]
            true_risp = len(risp_runners) > 0
            logging.info(f"🔍 Clutch HR Check: {batter_name} - season_hrs={season_hrs}, inning={inning}, true_risp={true_risp}, risp_runners={risp_runners}")
            if (self.notification_preferences.get('clutch_hr', True) and
                season_hrs >= 20 and inning >= 7 and true_risp):
                # Use plate appearance scoping to trigger immediately when batter approaches
                # Get current at-bat index from game data
                at_bat_index = game_data.get('at_bat_index', f"{inning}_{current_batter.get('id', batter_name)}")
                clutch_alert_data = {
                    "player_id": current_batter.get("id"),
                    "inning": inning,
                    "at_bat_index": at_bat_index
                }
                if self._is_new_alert(game_id, 'clutch_hr', clutch_alert_data):
                    logging.info(f"🎯 FIRING Clutch HR alert for {batter_name}!")
                    # Enhanced messaging for clutch situations
                    urgency = "CRITICAL" if inning >= 9 else ("HIGH" if inning == 8 else "MODERATE")
                    risp_count = len(risp_runners)
                    risp_detail = f"{risp_count} RISP" if risp_count > 1 else "RISP"
                    alert_msg = f"⚡ Power Hitter + RISP in 7th+ Inning!\n{batter_name} ({season_hrs} HRs) COMING UP with {risp_detail} in inning {inning}!"
                    alert_msg += f"\n🚨 {urgency} clutch situation!"
                    
                    # Add AI prediction if enabled for power hitters
                    if self.openai_helper.is_available() and self.notification_preferences.get('ai_analyze_power_hitter', True):
                        # Create enhanced clutch situation context
                        clutch_situation = {
                            'away_team': game_data.get('away_team'),
                            'home_team': game_data.get('home_team'),
                            'inning': inning,
                            'outs': game_data.get('outs', 0),  # Use real outs data
                            'base_runners': bases_occupied,
                            'away_score': game_data.get('away_score', 0),  # Use real scores
                            'home_score': game_data.get('home_score', 0),
                            'clutch_situation': True,
                            'risp_count': len(risp_runners),
                            'late_inning_pressure': True,
                            'power_hitter_clutch': True,
                            'game_hrs': game_hrs,  # Use real same-game HRs
                            'urgency_level': urgency.lower(),
                            'season_hrs': season_hrs
                        }
                        
                        ai_prediction = self.openai_helper.predict_at_bat_outcome(
                            current_batter,
                            clutch_situation
                        )
                        if ai_prediction:
                            alert_msg += f"\n\n🔮 Clutch Analysis: {ai_prediction}"
                    else:
                        # Enhanced fallback analysis for clutch situations
                        if inning >= 9:
                            alert_msg += f"\n🚨 CRITICAL: 9th+ inning clutch moment!"
                        elif inning == 8:
                            alert_msg += f"\n⚡ HIGH PRESSURE: Late-game setup situation!"
                        if risp_count > 1:
                            alert_msg += f"\n🎯 MULTIPLE RISP: {risp_count} runners in scoring position!"
                        if game_hrs > 0:
                            alert_msg += f"\n🔥 HOT STREAK: Already {game_hrs} HR(s) today!"
                    
                    self._add_alert(
                        game_id, game_info,
                        alert_msg,
                        "clutch_hr"
                    )
            
            # Advanced ROI Alert: AI Power Hitter + Scoring Opportunity
            logging.info(f"🔍 AI Power+Scoring Check: {batter_name} - tier={tier}, bases={bases_occupied}, season_hrs={season_hrs}")
            if (self.notification_preferences.get('ai_power_plus_scoring', True) and
                tier in ("A", "B") and len(bases_occupied) > 0):
                
                alert_data = {
                    'batter_id': batter_id,
                    'season_hr': season_hrs,
                    'pa_id': pa_id,
                    'bases_hash': self._bases_hash(bases_occupied),
                    'state_value': f"power_scoring_{batter_id}_{pa_id}_{self._bases_hash(bases_occupied)}"
                }
                
                if self._is_new_alert(game_id, 'ai_power_plus_scoring', alert_data):
                    logging.info(f"🎯 FIRING AI Power+Scoring alert for {batter_name}!")
                    alert_msg = f"💰 AI: Power Hitter + Scoring Opportunity!\n{batter_name} ({season_hrs} HRs) COMING UP with runners on base!"
                    # Always show tier for ROI alerts (only triggers for Tier A/B)
                    alert_msg += f"\n📊 P(HR): {p_hr:.1%} | Tier: {tier}"
                    
                    # Enhanced AI analysis for ROI situation
                    if self.openai_helper.is_available():
                        # Calculate ROI potential based on bases and power
                        risp_runners = [base for base in bases_occupied if base in ['2B', '3B']]
                        roi_context = {
                            'power_hitter': True,
                            'season_hrs': season_hrs,
                            'runners_in_scoring_position': len(risp_runners),
                            'total_runners': len(bases_occupied),
                            'inning': inning,
                            'late_game': inning >= 7
                        }
                        
                        ai_analysis = self.openai_helper.predict_at_bat_outcome(current_batter, roi_context)
                        if ai_analysis:
                            alert_msg += f"\n\n🎯 ROI Analysis: {ai_analysis}"
                    
                    self._add_alert(game_id, game_info, alert_msg, "ai_power_plus_scoring")
            
            # Advanced ROI Alert: AI Power Hitter High-Confidence
            logging.info(f"🔍 AI High-Confidence Check: {batter_name} - tier={tier}, season_hrs={season_hrs}, p_hr={p_hr:.3f}")
            # Use hybrid criteria: Tier A (4.0%+ P(HR)) OR 30+ HRs for elite sluggers
            high_confidence_eligible = (tier == "A") or (season_hrs >= 30)
            if (self.notification_preferences.get('ai_power_high', True) and high_confidence_eligible):
                
                alert_data = {
                    'batter_id': batter_id,
                    'season_hr': season_hrs,
                    'pa_id': pa_id,
                    'state_value': f"power_high_{batter_id}_{pa_id}"
                }
                
                if self._is_new_alert(game_id, 'ai_power_high', alert_data):
                    logging.info(f"🎯 FIRING AI High-Confidence alert for {batter_name}!")
                    # Determine qualification reason
                    qual_reason = "Elite Tier A" if tier == "A" else f"Elite Slugger ({season_hrs} HRs)"
                    alert_msg = f"🚀 AI: Power Hitter — High-Confidence!\n{batter_name} ({season_hrs} HRs) COMING UP - {qual_reason}!"
                    # Always show tier and probability for high-confidence alerts
                    alert_msg += f"\n📊 P(HR): {p_hr:.1%} | Tier: {tier}"
                    if 'w_out' in components and components['w_out'] > 0:
                        alert_msg += f"\n💨 Wind helping: +{components['boost']:.0%} boost"
                    
                    # High-confidence AI prediction for elite hitters
                    if self.openai_helper.is_available():
                        elite_context = {
                            'elite_power': True,
                            'season_hrs': season_hrs,
                            'confidence_level': 'high',
                            'bases': bases_occupied,
                            'inning': inning,
                            'qualification_reason': qual_reason
                        }
                        
                        ai_prediction = self.openai_helper.predict_at_bat_outcome(current_batter, elite_context)
                        if ai_prediction:
                            alert_msg += f"\n\n⭐ Elite Prediction: {ai_prediction}"
                    else:
                        # Fallback analysis when OpenAI unavailable
                        if len(bases_occupied) > 0:
                            alert_msg += f"\n🎯 Elite power + runners on base = high RBI potential!"
                        if inning >= 7:
                            alert_msg += f"\n⏰ Late-game situation - clutch moment!"
                    
                    self._add_alert(game_id, game_info, alert_msg, "ai_power_high")
            
            # Advanced ROI Alert: Pitcher Softening (Fatigue/Contact) 
            if self.notification_preferences.get('pitcher_softening', True):
                self._check_pitcher_softening_alert(game_id, game_data, current_batter)
        
        except Exception as e:
            logging.error(f"Error checking power hitter alerts for game {game_id}: {e}")
    
    def _check_pitcher_softening_alert(self, game_id: int, game_data: Dict[str, Any], current_batter: Optional[Dict[str, Any]] = None):
        """Check for pitcher fatigue/contact patterns indicating softening (ROI opportunity)"""
        try:
            if not current_batter:
                logging.debug("No current batter for pitcher softening check")
                return
            
            game_info = f"{game_data.get('away_team', 'Away')} @ {game_data.get('home_team', 'Home')}"
            inning = game_data.get('inning', 0)
            
            # Track pitcher performance indicators
            if not hasattr(self, 'pitcher_tracking'):
                self.pitcher_tracking = {}
            
            # Get actual pitcher ID from game data (FIXED: was using inning-based key)
            current_pitcher = game_data.get('current_pitcher', {})
            pitcher_id = current_pitcher.get('id', f'unknown_{game_id}')
            pitcher_name = current_pitcher.get('name', 'Unknown Pitcher')
            pitcher_key = f"game_{game_id}_pitcher_{pitcher_id}"
            
            logging.info(f"🔍 Pitcher Softening Check: {pitcher_name} (ID: {pitcher_id}) in inning {inning}")
            
            if pitcher_key not in self.pitcher_tracking:
                self.pitcher_tracking[pitcher_key] = {
                    'contact_events': 0,
                    'hard_contact': 0,
                    'pitch_count_est': 0,
                    'first_inning': inning,
                    'last_inning': inning,
                    'pitcher_name': pitcher_name
                }
            
            pitcher_data = self.pitcher_tracking[pitcher_key]
            pitcher_data['last_inning'] = inning  # Update last seen inning
            
            # Get real pitch count from game data (IMPROVED: use actual data)
            real_pitch_count = current_pitcher.get('pitch_count', 0)
            if real_pitch_count > 0:
                pitcher_data['pitch_count_est'] = real_pitch_count
                logging.info(f"Using real pitch count: {real_pitch_count}")
            else:
                # Fallback estimation (improved calculation)
                pitcher_data['pitch_count_est'] += 4  # More realistic per-batter estimate
                logging.debug(f"Estimated pitch count: {pitcher_data['pitch_count_est']}")
            
            # Advanced ROI conditions for pitcher softening
            softening_indicators = []
            
            # Late inning fatigue (6th inning or later)
            if inning >= 6:
                softening_indicators.append("late_inning")
                logging.debug(f"Late inning indicator: inning {inning}")
            
            # High pitch count threshold
            if pitcher_data['pitch_count_est'] >= 80:
                softening_indicators.append("high_pitch_count")
                logging.debug(f"High pitch count indicator: {pitcher_data['pitch_count_est']}")
            
            # Enhanced contact pattern tracking (IMPROVED: broader detection)
            last_result = current_batter.get('last_result', '').lower()
            if last_result and any(contact in last_result for contact in ['hit', 'single', 'double', 'triple', 'home']):
                pitcher_data['contact_events'] += 1
                # Detect hard contact (expanded criteria)
                if any(hard in last_result for hard in ['double', 'triple', 'home run', 'homer', 'hr']):
                    pitcher_data['hard_contact'] += 1
                    softening_indicators.append("hard_contact")
                    logging.debug(f"Hard contact detected: {last_result}")
                logging.debug(f"Contact event tracked: {last_result}")
            
            # Additional softening indicators (ENHANCED)
            # Multiple hits in recent innings
            if pitcher_data['contact_events'] >= 3:
                softening_indicators.append("frequent_contact")
                logging.debug(f"Frequent contact indicator: {pitcher_data['contact_events']} events")
            
            logging.info(f"Softening indicators for {pitcher_name}: {softening_indicators}")
            
            # Generate ROI alert if multiple softening indicators present
            if len(softening_indicators) >= 2:
                alert_data = {
                    'pitcher_key': pitcher_key,
                    'inning': inning,
                    'indicators': softening_indicators,
                    'state_value': f"pitcher_soft_{pitcher_key}_{len(softening_indicators)}"
                }
                
                if self._is_new_alert(game_id, 'pitcher_softening', alert_data):
                    logging.info(f"🎯 FIRING Pitcher Softening alert for {pitcher_name}!")
                    alert_msg = f"⚾ Pitcher Softening (Fatigue/Contact)!\n{pitcher_name} showing multiple warning signs in inning {inning}"
                    
                    # Add specific indicators (ENHANCED)
                    if 'late_inning' in softening_indicators:
                        alert_msg += "\n• Late inning fatigue factor"
                    if 'high_pitch_count' in softening_indicators:
                        pitch_count_text = f"real: {real_pitch_count}" if real_pitch_count > 0 else f"est: ~{pitcher_data['pitch_count_est']}"
                        alert_msg += f"\n• High pitch count ({pitch_count_text})"
                    if 'hard_contact' in softening_indicators:
                        alert_msg += f"\n• Recent hard contact allowed ({pitcher_data['hard_contact']} events)"
                    if 'frequent_contact' in softening_indicators:
                        alert_msg += f"\n• Frequent contact pattern ({pitcher_data['contact_events']} hits)"
                    
                    # Enhanced AI analysis for ROI
                    if self.openai_helper.is_available():
                        softening_context = {
                            'pitcher_softening': True,
                            'pitcher_name': pitcher_name,
                            'inning': inning,
                            'indicators': softening_indicators,
                            'pitch_count': pitcher_data['pitch_count_est'],
                            'contact_events': pitcher_data['contact_events'],
                            'hard_contact': pitcher_data['hard_contact'],
                            'current_batter': current_batter,
                            'roi_opportunity': True
                        }
                        
                        ai_analysis = self.openai_helper.predict_at_bat_outcome(current_batter, softening_context)
                        if ai_analysis:
                            alert_msg += f"\n\n💡 ROI Insight: {ai_analysis}"
                    else:
                        # Fallback analysis when OpenAI unavailable
                        alert_msg += f"\n🎯 ROI Opportunity: Pitcher vulnerability detected!"
                        if current_batter.get('season_home_runs', 0) >= 15:
                            alert_msg += f"\n⚡ Power hitter vs struggling pitcher = prime situation!"
                    
                    self._add_alert(game_id, game_info, alert_msg, "pitcher_softening")
        
        except Exception as e:
            logging.error(f"Error checking pitcher softening alert for game {game_id}: {e}")
    
    def _check_weather_delay_alerts(self, game_id: int, game_data: Dict[str, Any]):
        """Check for weather delays and game resumption"""
        try:
            status = game_data.get('status', '')
            game_info = f"{game_data.get('away_team', 'Away')} @ {game_data.get('home_team', 'Home')}"
            
            # Check for weather delays
            if self.notification_preferences.get('weather_delay', False):
                if 'Delayed:' in status and 'Rain' in status:
                    alert_key = f"delay_{game_id}"
                    if self._is_new_alert(game_id, 'weather_delay', alert_key):
                        self._add_alert(
                            game_id,
                            game_info,
                            f"⛈️ WEATHER DELAY!\nGame delayed due to rain\nMonitoring for resumption...",
                            "weather_delay"
                        )
            
            # Check for game resumption after delay
            if self.notification_preferences.get('game_resumption', False):
                # Track previously delayed games
                if not hasattr(self, 'previously_delayed_games'):
                    self.previously_delayed_games = set()
                
                # If game was delayed but now in progress, it resumed
                if 'In Progress' in status and game_id in self.previously_delayed_games:
                    alert_key = f"resume_{game_id}"
                    if self._is_new_alert(game_id, 'game_resumption', alert_key):
                        self._add_alert(
                            game_id,
                            game_info,
                            f"🌤️ GAME RESUMED!\nPlay has resumed after weather delay\nBetting lines may have shifted",
                            "game_resumption"
                        )
                    # Remove from delayed set since it resumed
                    self.previously_delayed_games.discard(game_id)
                elif 'Delayed:' in status:
                    # Track this game as delayed
                    self.previously_delayed_games.add(game_id)
            
        except Exception as e:
            logging.debug(f"Error checking weather delay alerts: {e}")
    
    def _check_weather_alerts(self, game_id: int, game_data: Dict[str, Any]):
        """Check weather conditions and generate appropriate alerts"""
        if not self.weather_integration.is_available():
            return
        
        # Only fetch weather for selected, live games to optimize API usage
        status = game_data.get('status', '')
        is_live = 'In Progress' in status or 'Live' in status
        is_selected = game_id in self.monitored_games
        
        if not (is_selected and is_live):
            logging.info(f"Weather skipped: not selected or not live (game_id={game_id}, status={status}, monitored_games={list(self.monitored_games)})")
            return
        
        try:
            # Analyze weather conditions for the game
            weather_analysis = self.weather_integration.analyze_weather_conditions(game_data)
            
            if not weather_analysis.get('weather_available'):
                return
            
            weather_data = weather_analysis.get('weather_data', {})
            wind_impact = weather_analysis.get('wind_impact', {})
            alerts = weather_analysis.get('alerts', {})
            
            game_info = f"{game_data.get('away_team', 'Away')} @ {game_data.get('home_team', 'Home')}"
            
            # Check wind speed alert
            if (self.notification_preferences.get('wind_speed', True) and 
                alerts.get('wind_speed', False)):
                wind_speed = weather_data.get('wind_speed', 0)
                if self._is_new_alert(game_id, 'wind_speed', f"wind_{wind_speed:.1f}"):
                    self._add_alert(
                        game_id, game_info,
                        f"💨 BOOSTED HR PROBABILITY!\nWind {wind_speed:.1f} mph blowing OUT toward outfield!\nHome runs more likely!",
                        "weather"
                    )
            
            # Check wind shift alert
            if (self.notification_preferences.get('wind_shift', True) and
                alerts.get('wind_shift', False)):
                wind_dir = weather_data.get('wind_direction', 0)
                if self._is_new_alert(game_id, 'wind_shift', f"shift_{wind_dir:.0f}"):
                    self._add_alert(
                        game_id, game_info,
                        f"🔄 WIND SHIFT ALERT!\nWind direction changed significantly!\nNew conditions may affect play",
                        "weather"
                    )
            
            # Check hot & windy conditions with math engine calculations
            if (self.notification_preferences.get('hot_windy', True) and
                alerts.get('hot_windy', False)):
                temp = weather_data.get('temperature', 0)
                wind_speed = weather_data.get('wind_speed', 0)
                wind_dir = weather_data.get('wind_direction', 0)
                
                # Calculate wind component toward CF and HR boost
                park_name = game_data.get('park_name', 'default')
                cf_azimuth = MATH_ENGINE_CONFIG["PARK_CF_AZIMUTH"].get(park_name, MATH_ENGINE_CONFIG["PARK_CF_AZIMUTH"]["default"])
                w_out = wind_component_out_to_cf(wind_dir, wind_speed, cf_azimuth)
                boost = hr_boost_factor(w_out, temp)
                
                if self._is_new_alert(game_id, 'hot_windy', f"hot_{temp:.0f}_{wind_speed:.1f}"):
                    alert_msg = f"🔥💨 HOT & WINDY HR BOOST!\n{temp:.0f}°F + Wind {wind_speed:.1f} mph"
                    if w_out > 0:
                        alert_msg += f" OUT toward CF!"
                        alert_msg += f"\n📈 HR odds boosted by {(boost-1)*100:.0f}%!"
                    else:
                        alert_msg += f" (partially helping)"
                    alert_msg += f"\nPerfect conditions for home runs!"
                    
                    self._add_alert(
                        game_id, game_info,
                        alert_msg,
                        "weather"
                    )
            
            # Check temp + wind out conditions (85°F+ with wind blowing out)
            if (self.notification_preferences.get('temp_wind', True) and
                alerts.get('temp_wind', False)):
                temp = weather_data.get('temperature', 0)
                wind_speed = weather_data.get('wind_speed', 0)
                if self._is_new_alert(game_id, 'temp_wind', f"temp_{temp:.0f}_{wind_speed:.1f}"):
                    self._add_alert(
                        game_id, game_info,
                        f"🌡️💨 TEMPERATURE ALERT!\n{temp:.0f}°F + Wind {wind_speed:.1f} mph OUT!\nHot weather + favorable wind = HR boost!",
                        "weather"
                    )
            
            # Check prime HR conditions (needs HRFI data - placeholder for now)
            # This would be set by combining weather data with player/team statistics
            
        except Exception as e:
            logging.error(f"Error checking weather alerts for game {game_id}: {e}")
    
    def _check_high_probability_situations(self, game_id: int, game_info: str, bases_occupied: List[str], outs: int):
        """Check for high-probability scoring situations based on runners and outs"""
        bases_set = set(bases_occupied)
        
        # Log if bases are loaded regardless of outs for debugging
        if len(bases_set) == 3 and '1B' in bases_set and '2B' in bases_set and '3B' in bases_set:
            logging.info(f"⚾ BASES LOADED DETECTED: {game_info} - {outs} outs")
        
        # Check most specific situations first (bases loaded) before less specific ones
        # Bases loaded, 0 outs (85% scoring probability)
        if (self.notification_preferences.get('bases_loaded_no_outs', True) and
            outs == 0 and len(bases_set) == 3 and '1B' in bases_set and '2B' in bases_set and '3B' in bases_set):
            # Create proper context data with unique half-inning key to prevent re-alerts
            half_inning_key = f"game_{game_id}_bases_loaded_0_outs_{int(time.time() // 300)}"  # 5-minute window
            alert_data = {
                'bases_hash': self._bases_hash(bases_occupied),
                'outs': outs,
                'half_inning': half_inning_key,
                'state_value': f"bases_loaded_{outs}_{int(time.time() // 300)}"  # Include time window
            }
            if self._is_new_alert(game_id, 'bases_loaded_no_outs', alert_data):
                logging.info(f"🔥 BASES LOADED ALERT TRIGGERED: {game_info} - Bases loaded, 0 outs!")
                alert_msg = f"🔥 HIGH ALERT!\nBASES LOADED, NO OUTS!\n85% chance of scoring"
                
                # Add AI prediction if enabled for enhanced alerts
                if self.openai_helper.is_available() and self.notification_preferences.get('ai_enhance_alerts', False):
                    # Create game situation for prediction
                    game_data = {
                        'away_team': game_info.split(' @ ')[0] if ' @ ' in game_info else 'Away',
                        'home_team': game_info.split(' @ ')[1] if ' @ ' in game_info else 'Home',
                        'inning': 0,  # Will be filled with actual inning if available
                        'outs': outs,
                        'base_runners': bases_occupied,
                        'away_score': 0,
                        'home_score': 0
                    }
                    ai_prediction = self.openai_helper.analyze_game_situation(game_data)
                    if ai_prediction:
                        alert_msg += f"\n\n🔮 AI Prediction: {ai_prediction}"
                
                self._add_alert(
                    game_id, game_info,
                    alert_msg,
                    "high_probability"
                )
        
        # Bases loaded, 1 out (70% scoring probability)
        elif (self.notification_preferences.get('bases_loaded_one_out', True) and
              outs == 1 and len(bases_set) == 3 and '1B' in bases_set and '2B' in bases_set and '3B' in bases_set):
            # Create proper context data with unique half-inning key to prevent re-alerts
            half_inning_key = f"game_{game_id}_bases_loaded_1_out_{int(time.time() // 300)}"  # 5-minute window
            alert_data = {
                'bases_hash': self._bases_hash(bases_occupied),
                'outs': outs,
                'half_inning': half_inning_key,
                'state_value': f"bases_loaded_{outs}_{int(time.time() // 300)}"  # Include time window
            }
            if self._is_new_alert(game_id, 'bases_loaded_one_out', alert_data):
                logging.info(f"🔥 BASES LOADED ALERT TRIGGERED: {game_info} - Bases loaded, 1 out!")
                alert_msg = f"🔥 HIGH ALERT!\nBASES LOADED, 1 OUT!\n70% chance of scoring"
                
                # Add AI prediction if enabled for enhanced alerts
                if self.openai_helper.is_available() and self.notification_preferences.get('ai_enhance_alerts', False):
                    # Create game situation for prediction
                    game_data = {
                        'away_team': game_info.split(' @ ')[0] if ' @ ' in game_info else 'Away',
                        'home_team': game_info.split(' @ ')[1] if ' @ ' in game_info else 'Home',
                        'inning': 0,  # Will be filled with actual inning if available
                        'outs': outs,
                        'base_runners': bases_occupied,
                        'away_score': 0,
                        'home_score': 0
                    }
                    ai_prediction = self.openai_helper.analyze_game_situation(game_data)
                    if ai_prediction:
                        alert_msg += f"\n\n🔮 AI Prediction: {ai_prediction}"
                
                self._add_alert(
                    game_id, game_info,
                    alert_msg,
                    "high_probability"
                )
        
        # Runners on 2nd & 3rd, 0 outs (87% scoring probability)
        elif (self.notification_preferences.get('runners_23_no_outs', True) and 
              outs == 0 and '2B' in bases_set and '3B' in bases_set and len(bases_set) == 2):
            # Create unique half-inning key to prevent re-alerts
            half_inning_key = f"game_{game_id}_runners_23_0_outs_{int(time.time() // 300)}"  # 5-minute window
            alert_data = {
                'bases_hash': self._bases_hash(bases_occupied),
                'outs': outs,
                'half_inning': half_inning_key,
                'state_value': f"runners_23_{outs}_{int(time.time() // 300)}"  # Include time window
            }
            if self._is_new_alert(game_id, 'runners_23_no_outs', alert_data):
                logging.info(f"🔥 HIGH PROBABILITY ALERT TRIGGERED: {game_info} - Runners on 2nd & 3rd, 0 outs!")
                alert_msg = f"🔥 HIGH ALERT!\nRunners on 2nd & 3rd, NO OUTS!\n87% chance of scoring"
                
                # Add AI prediction if enabled for enhanced alerts
                if self.openai_helper.is_available() and self.notification_preferences.get('ai_enhance_alerts', False):
                    # Create game situation for prediction
                    game_data = {
                        'away_team': game_info.split(' @ ')[0] if ' @ ' in game_info else 'Away',
                        'home_team': game_info.split(' @ ')[1] if ' @ ' in game_info else 'Home',
                        'inning': 0,  # Will be filled with actual inning if available
                        'outs': outs,
                        'base_runners': bases_occupied,
                        'away_score': 0,
                        'home_score': 0
                    }
                    ai_prediction = self.openai_helper.analyze_game_situation(game_data)
                    if ai_prediction:
                        alert_msg += f"\n\n🔮 AI Prediction: {ai_prediction}"
                
                self._add_alert(
                    game_id, game_info,
                    alert_msg,
                    "high_probability"
                )
        
        # Runner on 3rd, 0 outs (75% scoring probability)
        elif (self.notification_preferences.get('runner_3rd_no_outs', True) and
              outs == 0 and '3B' in bases_set and len(bases_set) == 1):
            # Create unique half-inning key to prevent re-alerts
            half_inning_key = f"game_{game_id}_runner_3rd_0_outs_{int(time.time() // 300)}"  # 5-minute window
            alert_data = {
                'bases_hash': self._bases_hash(bases_occupied),
                'outs': outs,
                'half_inning': half_inning_key,
                'state_value': f"runner_3rd_{outs}_{int(time.time() // 300)}"  # Include time window
            }
            if self._is_new_alert(game_id, 'runner_3rd_no_outs', alert_data):
                self._add_alert(
                    game_id, game_info,
                    f"⚡ SCORING THREAT!\nRunner on 3rd, NO OUTS!\n75% chance of scoring",
                    "high_probability"
                )
        
        # Runners on 1st & 3rd, 0 outs (70% scoring probability)
        elif (self.notification_preferences.get('runners_13_no_outs', True) and
              outs == 0 and '1B' in bases_set and '3B' in bases_set and len(bases_set) == 2):
            alert_data = {
                'bases_hash': self._bases_hash(bases_occupied),
                'outs': outs,
                'half_inning': f"game_{game_id}_runners_13_0_outs_{int(time.time() // 300)}",
                'state_value': f"runners_13_{outs}_{int(time.time() // 300)}"
            }
            if self._is_new_alert(game_id, 'runners_13_no_outs', alert_data):
                self._add_alert(
                    game_id, game_info,
                    f"⚡ SCORING THREAT!\nRunners on 1st & 3rd, NO OUTS!\n70% chance of scoring",
                    "high_probability"
                )
        
        # Runners on 2nd & 3rd, 1 out (65% scoring probability)
        elif (self.notification_preferences.get('runners_23_one_out', True) and
              outs == 1 and '2B' in bases_set and '3B' in bases_set and len(bases_set) == 2):
            alert_data = {
                'bases_hash': self._bases_hash(bases_occupied),
                'outs': outs,
                'half_inning': f"game_{game_id}_runners_23_1_out_{int(time.time() // 300)}",
                'state_value': f"runners_23_{outs}_{int(time.time() // 300)}"
            }
            if self._is_new_alert(game_id, 'runners_23_one_out', alert_data):
                self._add_alert(
                    game_id, game_info,
                    f"⚠️ SCORING POSITION!\nRunners on 2nd & 3rd, 1 OUT\n65% chance of scoring",
                    "high_probability"
                )
        
        # Runners on 1st & 2nd, 0 outs (60% scoring probability)
        elif (self.notification_preferences.get('runners_12_no_outs', True) and
              outs == 0 and '1B' in bases_set and '2B' in bases_set and len(bases_set) == 2):
            alert_data = {
                'bases_hash': self._bases_hash(bases_occupied),
                'outs': outs,
                'half_inning': f"game_{game_id}_runners_12_0_outs_{int(time.time() // 300)}",
                'state_value': f"runners_12_{outs}_{int(time.time() // 300)}"
            }
            if self._is_new_alert(game_id, 'runners_12_no_outs', alert_data):
                self._add_alert(
                    game_id, game_info,
                    f"⚡ SCORING OPPORTUNITY!\nRunners on 1st & 2nd, NO OUTS!\n60% chance of scoring",
                    "high_probability"
                )
        
        # Runner on 2nd, 0 outs (60% scoring probability)
        elif (self.notification_preferences.get('runner_2nd_no_outs', True) and
              outs == 0 and '2B' in bases_set and len(bases_set) == 1):
            alert_data = {
                'bases_hash': self._bases_hash(bases_occupied),
                'outs': outs,
                'half_inning': f"game_{game_id}_runner_2nd_0_outs_{int(time.time() // 300)}",
                'state_value': f"runner_2nd_{outs}_{int(time.time() // 300)}"
            }
            if self._is_new_alert(game_id, 'runner_2nd_no_outs', alert_data):
                self._add_alert(
                    game_id, game_info,
                    f"⚡ SCORING POSITION!\nRunner on 2nd, NO OUTS!\n60% chance of scoring",
                    "high_probability"
                )
        
        # Runner on 3rd, 1 out (55% scoring probability)
        elif (self.notification_preferences.get('runner_3rd_one_out', True) and
              outs == 1 and '3B' in bases_set and len(bases_set) == 1):
            alert_data = {
                'bases_hash': self._bases_hash(bases_occupied),
                'outs': outs,
                'half_inning': f"game_{game_id}_runner_3rd_1_out_{int(time.time() // 300)}",
                'state_value': f"runner_3rd_{outs}_{int(time.time() // 300)}"
            }
            if self._is_new_alert(game_id, 'runner_3rd_one_out', alert_data):
                self._add_alert(
                    game_id, game_info,
                    f"🏃 RUNNER ON 3RD, 1 OUT!\n55% scoring probability - sac fly or contact play!",
                    "high_probability"
                )
        
        # Runners on 1st & 3rd, 1 out (55% scoring probability)
        elif (self.notification_preferences.get('runners_13_one_out', True) and
              outs == 1 and '1B' in bases_set and '3B' in bases_set and len(bases_set) == 2):
            alert_data = {
                'bases_hash': self._bases_hash(bases_occupied),
                'outs': outs,
                'half_inning': f"game_{game_id}_runners_13_1_out_{int(time.time() // 300)}",
                'state_value': f"runners_13_{outs}_{int(time.time() // 300)}"
            }
            if self._is_new_alert(game_id, 'runners_13_one_out', alert_data):
                self._add_alert(
                    game_id, game_info,
                    f"🎲 RUNNERS ON 1ST & 3RD, 1 OUT!\n55% scoring probability - squeeze play opportunity!",
                    "high_probability"
                )
        
        # Bases loaded, 2 outs (35% scoring probability)
        elif (self.notification_preferences.get('bases_loaded_two_outs', True) and
              outs == 2 and len(bases_set) == 3 and '1B' in bases_set and '2B' in bases_set and '3B' in bases_set):
            alert_data = {
                'bases_hash': self._bases_hash(bases_occupied),
                'outs': outs,
                'half_inning': f"inning_{game_id}",
                'state_value': f"bases_loaded_{outs}"
            }
            if self._is_new_alert(game_id, 'bases_loaded_two_outs', alert_data):
                logging.info(f"⚡ BASES LOADED ALERT TRIGGERED: {game_info} - Bases loaded, 2 outs!")
                alert_msg = f"⚡ PRESSURE COOKER!\nBASES LOADED, 2 OUTS!\nLast chance - 35% scoring odds"
                
                # Add AI prediction if enabled for enhanced alerts
                if self.openai_helper.is_available() and self.notification_preferences.get('ai_enhance_alerts', False):
                    # Create game situation for prediction
                    game_data = {
                        'away_team': game_info.split(' @ ')[0] if ' @ ' in game_info else 'Away',
                        'home_team': game_info.split(' @ ')[1] if ' @ ' in game_info else 'Home',
                        'inning': 0,  # Will be filled with actual inning if available
                        'outs': outs,
                        'base_runners': bases_occupied,
                        'away_score': 0,
                        'home_score': 0
                    }
                    ai_prediction = self.openai_helper.analyze_game_situation(game_data)
                    if ai_prediction:
                        alert_msg += f"\n\n🔮 AI Prediction: {ai_prediction}"
                
                self._add_alert(
                    game_id, game_info,
                    alert_msg,
                    "high_probability"
                )
        
        # Runner on 3rd, 1 out (55% scoring probability)
        elif (self.notification_preferences.get('runner_3rd_one_out', True) and
              outs == 1 and '3B' in bases_set and len(bases_set) == 1):
            alert_data = {
                'bases_hash': self._bases_hash(bases_occupied),
                'outs': outs,
                'half_inning': f"inning_{game_id}",
                'state_value': f"runner_3rd_{outs}"
            }
            if self._is_new_alert(game_id, 'runner_3rd_one_out', alert_data):
                self._add_alert(
                    game_id, game_info,
                    f"📍 SCORING CHANCE!\nRunner on 3rd, 1 OUT\n55% chance of scoring",
                    "high_probability"
                )
        
        # Runners on 1st & 3rd, 1 out (55% scoring probability)
        elif (self.notification_preferences.get('runners_13_one_out', True) and
              outs == 1 and '1B' in bases_set and '3B' in bases_set and len(bases_set) == 2):
            if self._is_new_alert(game_id, 'runners_13_one_out', f"{outs}_{sorted(bases_occupied)}"):
                self._add_alert(
                    game_id, game_info,
                    f"📍 SCORING CHANCE!\nRunners on 1st & 3rd, 1 OUT\n55% chance of scoring",
                    "high_probability"
                )
    
    def send_telegram_test(self) -> bool:
        """Send a test Telegram message to verify connection"""
        return self.telegram_notifier.send_test_message()
    
    def get_telegram_status(self) -> Dict[str, Any]:
        """Get Telegram notifier status"""
        return self.telegram_notifier.get_status()
    
    def stop_monitoring_with_clear(self) -> bool:
        """Stop monitoring and clear persistent settings"""
        try:
            self.running = False
            self.monitored_games.clear()
            self.persistent_settings.clear_monitored_games()
            
            self._add_alert(
                0,
                "System Status",
                "🛑 Monitoring stopped and settings cleared",
                "system"
            )
            
            logging.info("🛑 Monitoring stopped and persistent settings cleared")
            return True
        except Exception as e:
            logging.error(f"Error stopping monitoring: {e}")
            return False
    
    def get_persistent_settings_status(self) -> Dict[str, Any]:
        """Get current persistent settings status"""
        return {
            "auto_monitoring_enabled": self.persistent_settings.is_auto_monitoring_enabled(),
            "monitoring_active": self.persistent_settings.is_monitoring_active(),
            "monitored_games_count": len(self.persistent_settings.get_monitored_games()),
            "monitored_games": self.persistent_settings.get_monitored_games(),
            "notification_preferences": self.persistent_settings.get_notification_preferences(),
            "settings_summary": self.persistent_settings.get_settings_summary()
        }
    
    def _track_alert_outcome(self, game_id: int, game_info: str, message: str, alert_type: str):
        """Track alert outcome for success rate statistics"""
        try:
            from app import db
            from models import AlertOutcome
            from flask_login import current_user
            
            # Parse game info to extract team names
            teams = game_info.split(' @ ')
            away_team = teams[0] if len(teams) > 0 else 'Away'
            home_team = teams[1] if len(teams) > 1 else 'Home'
            
            # Create AlertOutcome record
            outcome = AlertOutcome()
            outcome.game_id = str(game_id)  # Ensure string type for consistency
            outcome.alert_type = alert_type
            outcome.alert_message = message  # Correct column name
            outcome.was_successful = None  # Will be updated later by user or auto-verification
            
            # Try to get current user context, but don't fail if not available
            try:
                from flask import has_request_context
                if has_request_context() and current_user and hasattr(current_user, 'id'):
                    outcome.user_id = current_user.id
                else:
                    # For background monitoring, use admin user ID (1) or create default tracking
                    from models import User
                    admin_user = User.query.filter_by(is_admin=True).first()
                    if admin_user:
                        outcome.user_id = admin_user.id
                    else:
                        # Skip tracking if no user context available
                        logging.debug("No user context available for alert outcome tracking")
                        return
            except Exception as e:
                logging.debug(f"Could not determine user context for alert tracking: {e}")
                return
            
            db.session.add(outcome)
            db.session.commit()
            
            logging.debug(f"✅ Alert outcome tracked: {alert_type} for game {game_id}")
            
        except Exception as e:
            logging.error(f"Error tracking alert outcome: {e}")
            # Don't fail the alert creation if tracking fails
    
    def _detect_same_game_hrs(self, game_id: int, batter_id: int, batter_name: str) -> int:
        """
        Detect how many home runs a batter has hit in the current game.
        Uses MLB StatsAPI boxscore data to get accurate same-game HR counts.
        """
        try:
            # First check if we have a valid batter_id
            if not batter_id or batter_id == 0:
                logging.info(f"⚠️ Cannot detect same-game HRs for {batter_name}: No valid batter ID")
                return 0
            
            # Import statsapi to access boxscore data
            import statsapi
            
            # Get detailed boxscore data for the game
            boxscore_data = statsapi.get('game', {'gamePk': game_id})
            
            if not boxscore_data:
                logging.debug(f"No boxscore data available for game {game_id}")
                return 0
            
            # Navigate to boxscore player data
            live_data = boxscore_data.get('liveData', {})
            boxscore = live_data.get('boxscore', {})
            teams = boxscore.get('teams', {})
            
            # Check both home and away teams for the batter
            for team_type in ['away', 'home']:
                team_data = teams.get(team_type, {})
                players = team_data.get('players', {})
                
                # Look for our batter in this team's players
                player_key = f"ID{batter_id}"
                if player_key in players:
                    player_data = players[player_key]
                    
                    # Get batting stats for this game
                    batting_stats = player_data.get('stats', {}).get('batting', {})
                    if batting_stats:
                        game_hrs = batting_stats.get('homeRuns', 0)
                        if game_hrs > 0:
                            logging.info(f"✅ GAME HR DETECTION: {batter_name} has {game_hrs} HR(s) in game {game_id}")
                            return game_hrs
            
            # If not found in boxscore, try alternative approach via play data
            plays = live_data.get('plays', {}).get('allPlays', [])
            hr_count = 0
            
            for play in plays:
                result = play.get('result', {})
                if result.get('event') == 'Home Run':
                    # Check if this HR was by our batter
                    matchup = play.get('matchup', {})
                    play_batter = matchup.get('batter', {})
                    if play_batter.get('id') == batter_id:
                        hr_count += 1
            
            if hr_count > 0:
                logging.info(f"✅ PLAY-BY-PLAY HR DETECTION: {batter_name} has {hr_count} HR(s) in game {game_id}")
            
            return hr_count
            
        except Exception as e:
            logging.debug(f"Error detecting same-game HRs for {batter_name} in game {game_id}: {e}")
            return 0
