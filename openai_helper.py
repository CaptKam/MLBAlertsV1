import json
import os
import logging
from typing import Dict, Any, Optional, List
from openai import OpenAI

class OpenAIHelper:
    def __init__(self):
        """Initialize OpenAI helper with API key from environment"""
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logging.warning("OpenAI API key not found - AI features disabled")
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)
            logging.info("OpenAI integration initialized successfully")
    
    def is_available(self) -> bool:
        """Check if OpenAI is available"""
        return self.client is not None
    
    def analyze_game_situation(self, game_data: Dict[str, Any]) -> Optional[str]:
        """Generate AI analysis of current game situation"""
        if not self.client:
            return None
        
        try:
            # Extract key game information
            game_info = {
                "teams": f"{game_data.get('away_team', 'Away')} @ {game_data.get('home_team', 'Home')}",
                "score": f"{game_data.get('away_score', 0)}-{game_data.get('home_score', 0)}",
                "inning": game_data.get('inning', 0),
                "inning_state": game_data.get('inning_state', ''),
                "outs": game_data.get('outs', 0),
                "runners": game_data.get('base_runners', [])
            }
            
            prompt = f"""Analyze this MLB game situation in 10 words or less:
            
            Game: {game_info['teams']}
            Score: {game_info['score']}
            Inning: {game_info['inning']} {game_info['inning_state']}
            Outs: {game_info['outs']}
            Runners on: {', '.join(game_info['runners']) if game_info['runners'] else 'None'}
            
            ONE key insight only. Be ultra-concise."""
            
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            # do not change this unless explicitly requested by the user
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an MLB analyst. Maximum 10 words. ONE key insight only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=25,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            return content.strip() if content else None
            
        except Exception as e:
            logging.error(f"OpenAI analysis error: {e}")
            return None
    
    def enhance_alert_message(self, alert_type: str, game_info: str, details: str) -> Optional[str]:
        """Enhance alert messages with AI-generated context"""
        if not self.client:
            return None
        
        try:
            prompt = f"""Enhance this MLB alert in 10 words max:
            
            Alert Type: {alert_type}
            Game: {game_info}
            Details: {details}
            
            ONE key point only. Be ultra-concise."""
            
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            # do not change this unless explicitly requested by the user
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an MLB announcer. Max 10 words. ONE key point only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=25,
                temperature=0.8
            )
            
            content = response.choices[0].message.content
            return content.strip() if content else None
            
        except Exception as e:
            logging.error(f"OpenAI enhancement error: {e}")
            return None
    
    def predict_scoring_probability(self, game_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get AI prediction for scoring probability"""
        if not self.client:
            return None
        
        try:
            game_context = {
                "inning": game_data.get('inning', 0),
                "outs": game_data.get('outs', 0),
                "runners": game_data.get('base_runners', []),
                "score_diff": abs(game_data.get('away_score', 0) - game_data.get('home_score', 0))
            }
            
            prompt = f"""Based on this MLB situation, provide a scoring probability assessment:
            
            Inning: {game_context['inning']}
            Outs: {game_context['outs']}
            Runners on: {', '.join(game_context['runners']) if game_context['runners'] else 'None'}
            Score differential: {game_context['score_diff']} runs
            
            Respond in JSON format with:
            {{"probability_percentage": number, "key_factor": "10 words max - focus on ONE key factor"}}"""
            
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            # do not change this unless explicitly requested by the user
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an MLB statistician. Be extremely concise - max 10 words for explanations. Focus on ONE key factor only."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=50,
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            if not content:
                return None
            result = json.loads(content)
            return {
                "probability": result.get("probability_percentage", 0),
                "factor": result.get("key_factor", "")
            }
            
        except Exception as e:
            logging.error(f"OpenAI prediction error: {e}")
            return None
    
    def summarize_game_events(self, events: List[str], game_info: str) -> Optional[str]:
        """Create an AI summary of recent game events"""
        if not self.client or not events:
            return None
        
        try:
            events_text = "\n".join(events[-5:])  # Last 5 events
            
            prompt = f"""Summarize these recent MLB game events in ONE short sentence (15 words max):
            
            Game: {game_info}
            Recent events:
            {events_text}
            
            Focus on the SINGLE most important play."""
            
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            # do not change this unless explicitly requested by the user
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an MLB broadcaster. ONE sentence only, 15 words maximum. Be ultra-concise."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=30,
                temperature=0.6
            )
            
            content = response.choices[0].message.content
            return content.strip() if content else None
            
        except Exception as e:
            logging.error(f"OpenAI summary error: {e}")
            return None
    
    def predict_at_bat_outcome(self, batter_data: Dict[str, Any], game_situation: Dict[str, Any]) -> Optional[str]:
        """Predict what might happen in the current at-bat based on batter and game situation"""
        if not self.client:
            return None
        
        try:
            batter_name = batter_data.get('name', 'Unknown')
            season_hrs = batter_data.get('season_home_runs', 0)
            game_hrs = batter_data.get('game_home_runs', 0)
            
            situation = {
                "teams": f"{game_situation.get('away_team', 'Away')} @ {game_situation.get('home_team', 'Home')}",
                "inning": game_situation.get('inning', 0),
                "outs": game_situation.get('outs', 0),
                "runners": game_situation.get('base_runners', []),
                "score_diff": abs(game_situation.get('away_score', 0) - game_situation.get('home_score', 0))
            }
            
            prompt = f"""MLB at-bat prediction in 8 words max:
            
            {batter_name} ({season_hrs} HRs)
            Inning: {situation['inning']}, Outs: {situation['outs']}
            Runners: {', '.join(situation['runners']) if situation['runners'] else 'None'}
            
            ONE outcome only. 8 words max."""
            
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            # do not change this unless explicitly requested by the user
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "MLB predictor. 8 words max. ONE outcome."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=15,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            return content.strip() if content else None
            
        except Exception as e:
            logging.error(f"OpenAI at-bat prediction error: {e}")
            return None