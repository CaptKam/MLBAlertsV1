import requests
import asyncio
import aiohttp
import time
import logging
import os
import statsapi as mlb
from datetime import datetime
import pytz
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed


class MultiSourceBaseballAggregator:
    """
    Aggregates live baseball data from multiple sources for fastest possible alerts
    Cross-validates data across sources and uses the fastest/most reliable source
    """
    
    def __init__(self):
        self.sources = {
            'mlb_statsapi': {
                'name': 'MLB-StatsAPI (Enhanced)',
                'base_url': 'https://statsapi.mlb.com/api/v1',
                'headers': {},
                'priority': 1,
                'speed_score': 10,  # Start with high score
                'reliability_score': 0.98,  # Highest reliability
                'last_response_time': 0,
                'features': ['live_runners', 'play_by_play', 'enhanced_tracking']
            },
            'mlb_official': {
                'name': 'MLB Official API',
                'base_url': 'https://statsapi.mlb.com/api/v1',
                'headers': {},
                'priority': 2,
                'speed_score': 0,
                'reliability_score': 0.95,
                'last_response_time': 0
            },
            'api_sports': {
                'name': 'API-Sports',
                'base_url': 'https://v1.baseball.api-sports.io',
                'headers': {
                    'X-RapidAPI-Key': os.environ.get('API_SPORTS_KEY', ''),
                    'X-RapidAPI-Host': 'v1.baseball.api-sports.io'
                },
                'priority': 3,
                'speed_score': 0,
                'reliability_score': 0.90,
                'last_response_time': 0
            },
            'espn': {
                'name': 'ESPN API',
                'base_url': 'https://site.api.espn.com/apis/site/v2/sports/baseball/mlb',
                'headers': {},
                'priority': 4,
                'speed_score': 0,
                'reliability_score': 0.85,
                'last_response_time': 0
            },
            'yahoo': {
                'name': 'Yahoo Sports API',
                'base_url': 'https://api.sports.yahoo.com/v1/editorial/s/baseball/mlb',
                'headers': {},
                'priority': 5,
                'speed_score': 0,
                'reliability_score': 0.80,
                'last_response_time': 0
            },
            'thesportsdb': {
                'name': 'TheSportsDB',
                'base_url': 'https://www.thesportsdb.com/api/v1/json/3',
                'headers': {},
                'priority': 6,
                'speed_score': 0,
                'reliability_score': 0.75,
                'last_response_time': 0
            }
        }
        
        self.game_data_cache = {}
        self.alert_threshold = 2  # Need data from at least 2 sources to confirm alert
        
    def get_fastest_sources(self, limit: int = 3) -> List[str]:
        """Get the fastest responding sources based on recent performance"""
        sorted_sources = sorted(
            self.sources.items(),
            key=lambda x: (x[1]['speed_score'], x[1]['reliability_score']),
            reverse=True
        )
        return [source[0] for source in sorted_sources[:limit]]
    
    async def fetch_games_from_source(self, source_name: str) -> Optional[Dict[str, Any]]:
        """Fetch games from a specific source with timing"""
        source = self.sources[source_name]
        start_time = time.time()
        
        try:
            timeout = aiohttp.ClientTimeout(total=2)  # Reduced timeout for speed
            async with aiohttp.ClientSession(timeout=timeout) as session:
                
                if source_name == 'mlb_statsapi':
                    # Use enhanced MLB-StatsAPI for better live data
                    return await self._fetch_mlb_statsapi_data(source, start_time)
                    
                elif source_name == 'mlb_official':
                    # Use Eastern Time for MLB games with 5-hour delay
                    from datetime import timedelta
                    eastern = pytz.timezone('US/Eastern')
                    et_time = datetime.now(eastern) - timedelta(hours=5)
                    today = et_time.strftime('%Y-%m-%d')
                    url = f"{source['base_url']}/schedule?sportId=1&date={today}&hydrate=team,linescore"
                    
                elif source_name == 'api_sports':
                    # Use Eastern Time for MLB games with 5-hour delay
                    from datetime import timedelta
                    eastern = pytz.timezone('US/Eastern')
                    et_time = datetime.now(eastern) - timedelta(hours=5)
                    today = et_time.strftime('%Y-%m-%d')
                    url = f"{source['base_url']}/games?league=1&season=2024&date={today}"
                    
                elif source_name == 'espn':
                    url = f"{source['base_url']}/scoreboard"
                    
                elif source_name == 'yahoo':
                    url = f"{source['base_url']}/games"
                    
                elif source_name == 'thesportsdb':
                    # Use Eastern Time for MLB games with 5-hour delay
                    from datetime import timedelta
                    eastern = pytz.timezone('US/Eastern')
                    et_time = datetime.now(eastern) - timedelta(hours=5)
                    today = et_time.strftime('%Y-%m-%d')
                    url = f"{source['base_url']}/eventsday.php?d={today}&s=Baseball"
                else:
                    return None
                
                async with session.get(url, headers=source['headers']) as response:
                    if response.status == 200:
                        data = await response.json()
                        response_time = time.time() - start_time
                        
                        # Update speed score (lower is better, so invert)
                        source['speed_score'] = max(0, 10 - response_time)
                        source['last_response_time'] = response_time
                        
                        logging.info(f"{source['name']}: {response_time:.2f}s response time")
                        return {'source': source_name, 'data': data, 'response_time': response_time}
                    else:
                        logging.warning(f"{source['name']}: HTTP {response.status}")
                        return None
                        
        except Exception as e:
            logging.error(f"{source['name']} failed: {e}")
            # Penalize failed sources
            source['speed_score'] = max(0, source['speed_score'] - 2)
            return None
    
    async def _fetch_mlb_statsapi_data(self, source: Dict[str, Any], start_time: float) -> Optional[Dict[str, Any]]:
        """Enhanced fetch using MLB-StatsAPI for better live data including base runners"""
        try:
            # Get today's games using the enhanced API
            # Use Eastern Time for MLB games with 5-hour delay
            # Games are considered "today's games" until 5 AM ET the next day
            from datetime import timedelta
            eastern = pytz.timezone('US/Eastern')
            et_time = datetime.now(eastern) - timedelta(hours=5)
            today = et_time.strftime('%Y-%m-%d')
            
            # Use statsapi in a thread to avoid blocking
            loop = asyncio.get_event_loop()
            
            def get_statsapi_data():
                try:
                    # Get schedule with enhanced hydration for live data
                    schedule = mlb.schedule(date=today)
                    
                    games_data = []
                    for game in schedule:
                        game_id = game.get('game_id')
                        if game_id:
                            # Get enhanced live data for each game
                            try:
                                # Get live game data with play-by-play
                                try:
                                    # Get boxscore data which includes more details
                                    live_data = mlb.boxscore_data(game_id)
                                    if live_data:
                                        game['live_data'] = live_data
                                        # Log if we have play data
                                        if 'info' in live_data or 'players' in live_data:
                                            logging.debug(f"Got enhanced data for game {game_id}")
                                except Exception as e:
                                    logging.debug(f"Could not get boxscore data for {game_id}: {e}")
                                games_data.append(game)
                            except Exception as e:
                                logging.warning(f"Could not get live data for game {game_id}: {e}")
                                games_data.append(game)  # Add without live data
                    
                    return {
                        'dates': [{
                            'games': games_data
                        }]
                    }
                except Exception as e:
                    logging.error(f"MLB-StatsAPI error: {e}")
                    return None
            
            # Run in thread pool to avoid blocking the async loop
            data = await loop.run_in_executor(None, get_statsapi_data)
            
            if data:
                response_time = time.time() - start_time
                
                # Give high score for successful enhanced API calls
                source['speed_score'] = max(0, 15 - response_time)  # Higher base score
                source['last_response_time'] = response_time
                
                logging.info(f"{source['name']}: {response_time:.2f}s response time (enhanced)")
                return {'source': 'mlb_statsapi', 'data': data, 'response_time': response_time}
            
            return None
            
        except Exception as e:
            logging.error(f"MLB-StatsAPI enhanced fetch failed: {e}")
            return None
    
    def normalize_game_data(self, source_name: str, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalize game data from different sources into a standard format"""
        games = []
        
        try:
            if source_name == 'mlb_statsapi':
                # Enhanced MLB-StatsAPI format with live data
                for date_info in raw_data.get('dates', []):
                    for game in date_info.get('games', []):
                        # Extract enhanced live data if available
                        live_data = game.get('live_data', {})
                        linescore = live_data.get('linescore', {})
                        
                        # Get base runner information from live data
                        offense = linescore.get('offense', {})
                        base_runners = []
                        if offense.get('first'):
                            base_runners.append('1st')
                        if offense.get('second'):
                            base_runners.append('2nd')
                        if offense.get('third'):
                            base_runners.append('3rd')
                        
                        normalized_game = {
                            'id': game.get('game_id', game.get('gamePk', 0)),
                            'home_team': game.get('home_name', 'Home'),
                            'away_team': game.get('away_name', 'Away'),
                            'status': game.get('status', 'Unknown'),
                            'inning': linescore.get('currentInning', 0),
                            'inning_state': linescore.get('inningState', ''),
                            'home_score': game.get('home_score', 0),
                            'away_score': game.get('away_score', 0),
                            'outs': linescore.get('outs', 0),
                            'base_runners': base_runners,  # Enhanced feature
                            'runner_details': {
                                'first': offense.get('first', {}),
                                'second': offense.get('second', {}),
                                'third': offense.get('third', {})
                            },
                            'source': source_name,
                            'timestamp': time.time(),
                            'enhanced': True  # Flag for enhanced data
                        }
                        games.append(normalized_game)
                        
            elif source_name == 'mlb_official':
                for date_info in raw_data.get('dates', []):
                    for game in date_info.get('games', []):
                        normalized_game = {
                            'id': game['gamePk'],
                            'home_team': game['teams']['home']['team']['name'],
                            'away_team': game['teams']['away']['team']['name'],
                            'status': game['status']['detailedState'],
                            'inning': game.get('linescore', {}).get('currentInning', 0),
                            'inning_state': game.get('linescore', {}).get('inningState', ''),
                            'home_score': game.get('linescore', {}).get('teams', {}).get('home', {}).get('runs', 0),
                            'away_score': game.get('linescore', {}).get('teams', {}).get('away', {}).get('runs', 0),
                            'source': source_name,
                            'timestamp': time.time()
                        }
                        games.append(normalized_game)
            
            elif source_name == 'api_sports':
                for game in raw_data.get('response', []):
                    teams = game.get('teams', {})
                    scores = game.get('scores', {})
                    status = game.get('status', {})
                    
                    normalized_game = {
                        'id': game.get('id', 0),
                        'home_team': teams.get('home', {}).get('name', 'Home'),
                        'away_team': teams.get('away', {}).get('name', 'Away'),
                        'status': status.get('long', 'Unknown'),
                        'inning': status.get('inning', 0),
                        'inning_state': 'Top' if status.get('inning_top', True) else 'Bottom',
                        'home_score': scores.get('home', {}).get('total', 0),
                        'away_score': scores.get('away', {}).get('total', 0),
                        'source': source_name,
                        'timestamp': time.time()
                    }
                    games.append(normalized_game)
            
            elif source_name == 'espn':
                for event in raw_data.get('events', []):
                    competitions = event.get('competitions', [{}])
                    if competitions:
                        comp = competitions[0]
                        competitors = comp.get('competitors', [])
                        
                        home_team = None
                        away_team = None
                        home_score = 0
                        away_score = 0
                        
                        for competitor in competitors:
                            if competitor.get('homeAway') == 'home':
                                home_team = competitor.get('team', {}).get('displayName', 'Home')
                                home_score = int(competitor.get('score', 0))
                            else:
                                away_team = competitor.get('team', {}).get('displayName', 'Away')
                                away_score = int(competitor.get('score', 0))
                        
                        status = comp.get('status', {})
                        normalized_game = {
                            'id': event.get('id', 0),
                            'home_team': home_team,
                            'away_team': away_team,
                            'status': status.get('type', {}).get('description', 'Unknown'),
                            'inning': status.get('period', 0),
                            'inning_state': '',
                            'home_score': home_score,
                            'away_score': away_score,
                            'source': source_name,
                            'timestamp': time.time()
                        }
                        games.append(normalized_game)
                        
        except Exception as e:
            logging.error(f"Error normalizing {source_name} data: {e}")
            
        return games
    
    async def get_all_games(self) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch games from all sources simultaneously"""
        fastest_sources = self.get_fastest_sources(2)  # Use top 2 fastest sources for speed
        
        tasks = []
        for source_name in fastest_sources:
            task = self.fetch_games_from_source(source_name)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_games_data = {}
        for result in results:
            if result and not isinstance(result, Exception) and isinstance(result, dict):
                source_name = result.get('source')
                if source_name:
                    games = self.normalize_game_data(source_name, result.get('data', {}))
                    all_games_data[source_name] = {
                        'games': games,
                        'response_time': result.get('response_time', 0),
                        'timestamp': time.time()
                    }
        
        logging.info(f"Fetched data from {len(all_games_data)} sources")
        return all_games_data
    
    def cross_validate_games(self, all_games_data: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Cross-validate game data across sources and return the most reliable data"""
        game_map = {}
        
        # Group games by team matchup and game ID for double headers
        for source_name, source_data in all_games_data.items():
            if isinstance(source_data, dict) and 'games' in source_data:
                games_list = source_data.get('games', [])
                for game in games_list:
                    # Use game ID in matchup key to handle double headers correctly
                    # This ensures each game gets its own entry even with same teams
                    matchup_key = f"{game['away_team']}@{game['home_team']}#{game['id']}"
                    
                    if matchup_key not in game_map:
                        game_map[matchup_key] = []
                    
                    game_map[matchup_key].append({
                        **game,
                        'source_reliability': self.sources[source_name]['reliability_score'],
                        'source_speed': self.sources[source_name]['speed_score']
                    })
        
        # Select best data for each game
        validated_games = []
        for matchup, game_versions in game_map.items():
            if len(game_versions) >= 1:  # At least one source
                # Sort by reliability and speed, prefer faster sources with recent data
                best_game = max(game_versions, key=lambda x: (
                    x['source_reliability'] * 0.7 + 
                    x['source_speed'] * 0.3 + 
                    (1.0 if time.time() - x['timestamp'] < 30 else 0.5)  # Prefer recent data
                ))
                
                # Add validation info
                best_game['sources_count'] = len(game_versions)
                best_game['validated'] = len(game_versions) >= 2
                validated_games.append(best_game)
        
        return validated_games
    
    async def get_fastest_game_details(self, game_id: int) -> Optional[Dict[str, Any]]:
        """Get game details from the fastest responding source"""
        fastest_sources = self.get_fastest_sources(3)
        
        # Try sources in order of speed
        for source_name in fastest_sources:
            try:
                if source_name == 'mlb_official':
                    url = f"https://statsapi.mlb.com/api/v1.1/game/{game_id}/feed/live"
                    headers = {}
                elif source_name == 'api_sports':
                    url = f"https://v1.baseball.api-sports.io/games?id={game_id}"
                    headers = self.sources[source_name]['headers']
                else:
                    continue  # Skip sources that don't support game details yet
                
                start_time = time.time()
                response = requests.get(url, headers=headers, timeout=2)  # Faster timeout
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    logging.info(f"Game details from {source_name}: {response_time:.2f}s")
                    return response.json()
                    
            except Exception as e:
                logging.warning(f"{source_name} game details failed: {e}")
                continue
        
        return None