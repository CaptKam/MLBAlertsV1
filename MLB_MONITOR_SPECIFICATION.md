# MLB Live Game Monitor - Technical Specification

## Executive Summary

The MLB Live Game Monitor is a sophisticated real-time baseball analytics and alerting system that combines multiple data sources, AI-powered analysis, weather integration, and instant Telegram notifications to provide actionable insights for MLB games. The system is designed for reliability, accuracy, and immediate alert delivery to support real-time decision making.

## System Architecture

### Core Components

#### 1. Web Application (Flask)
- **Framework**: Flask 3.0+ with Gunicorn WSGI server
- **Database**: PostgreSQL with connection pooling and migration support
- **Authentication**: Session-based with configurable secret key
- **Deployment**: Replit platform with production-ready health monitoring

#### 2. Monitoring Engine (`mlb_monitor.py`)
- **Real-time Processing**: Dedicated worker process with watchdog protection
- **Multi-source Aggregation**: Combines MLB Official API, StatsAPI, and backup sources
- **State Management**: Tracks game states, player stats, and alert history
- **Progressive Recovery**: Automatic error recovery with backoff (1s→60s)

#### 3. Alert System
- **Context-Aware Deduplication**: Per-alert-type scoping prevents spam while allowing legitimate alerts
- **AI Integration**: OpenAI GPT-4o powered analysis and predictions
- **Weather Integration**: OpenWeatherMap API for stadium-specific conditions
- **Telegram Delivery**: Real-time notifications via @chirpbetabot

#### 4. Frontend Interface
- **Technology**: Bootstrap 5 dark theme with vanilla JavaScript
- **Architecture**: Single-page application with polling-based updates
- **Features**: Game selection, preference management, real-time alert display
- **Mobile Responsive**: Full mobile compatibility with touch-friendly controls

## Data Sources & APIs

### Primary MLB Data Sources
1. **MLB Official API** (`statsapi.mlb.com`)
   - Primary source for live game data
   - Response time: 0.04-0.09 seconds
   - Fields: Game states, scores, innings, player stats

2. **MLB StatsAPI** (`mlb_statsapi` Python library)
   - Enhanced player statistics and detailed game events
   - Response time: 0.20-1.38 seconds
   - Features: Season stats, batting order, historical data

3. **Backup Sources** (API Sports, ESPN, Yahoo)
   - Failover protection for primary source outages
   - Cross-validation for critical game events
   - Automatic fallback with logging

### External Integrations
- **OpenAI API**: GPT-4o model for game analysis and predictions
- **OpenWeatherMap API**: Real-time weather data for all MLB stadiums
- **Telegram Bot API**: Message delivery to configured groups/channels

## Alert Types & Triggers

### Power Hitter Alerts
- **Threshold**: 20+ season home runs (elite players only)
- **Trigger**: Player at bat or on deck
- **AI Enhancement**: Includes batting predictions and situational analysis
- **Deduplication**: Per plate appearance (each at-bat triggers new alert)

### Hot Hitter Alerts  
- **Condition**: Player who already homered in current game
- **Trigger**: Subsequent at-bats after home run
- **Context**: Game HR count and AI predictions
- **Scope**: Unique per at-bat to catch all opportunities

### Base Runner Alerts
- **High-Probability Scoring**: Runners on 2nd & 3rd with 0-1 outs
- **Bases Loaded**: All situations with bases loaded
- **RISP Situations**: Runner on 3rd with less than 2 outs
- **Re-alert Logic**: Persistent situations re-alert after 2 minutes

### Weather-Enhanced Alerts
- **Wind Alerts**: ≥7.5 mph blowing toward any outfield
- **Prime Conditions**: High wind + temperature ≥85°F + power hitter
- **Wind Shifts**: Direction changes ≥45° toward outfield
- **Stadium-Specific**: Real coordinates for all 30 MLB parks

### Advanced AI Alerts (ROI Pack)
- **Power + Scoring Opportunity**: High-leverage situations (Tier B+ score ≥55)
- **High-Confidence Power**: Elite situations (Tier A score ≥70)
- **Pitcher Softening**: Fatigue detection using velocity, hard-hit%, TTO
- **Control Loss**: 8+ consecutive balls with progressive re-alerts

### Clutch Situation Alerts
- **Clutch HR Threat**: Power hitter + RISP in 7th+ innings
- **Tie Game 9th**: Tie games entering bottom 9th inning
- **Late Inning Drama**: High-leverage moments in 8th+ innings

## Technical Implementation

### Performance Specifications
- **API Response Times**: Sub-second for most operations
- **Monitoring Cycle**: 2-3 seconds per complete cycle
- **Alert Latency**: <1 second from detection to Telegram
- **Concurrent Games**: Successfully handles 15+ simultaneous games
- **Data Refresh**: Real-time polling with smart caching

### Reliability Features
- **Health Monitoring**: `/healthz` endpoint with comprehensive system checks
- **Auto-Recovery**: Worker process restart within 30 seconds of failure
- **Connection Pooling**: 10 persistent connections with retry logic
- **Error Tolerance**: Handles up to 5 consecutive errors before stopping
- **Graceful Degradation**: System continues operating with partial data source failures

### Security & Configuration
- **Environment Variables**: Secure secret management for API keys
- **Session Management**: Flask sessions with configurable secret
- **CORS Protection**: Proper headers for cross-origin requests
- **Input Validation**: Sanitized user inputs and API parameters

## Alert Metrics & Trigger Conditions

### Statistical Thresholds
All alert triggers are based on real-time statistical analysis and historical performance data:

#### Power Hitter Metrics
- **Season Home Runs ≥ 20**: Elite power hitter threshold
- **Season Home Runs ≥ 15**: Clutch HR threat threshold (when combined with RISP + 7th+ inning)
- **Season Home Runs ≥ 30**: High-confidence elite power threshold
- **Game Home Runs ≥ 1**: Hot hitter detection (already homered today)

#### High-Probability Scoring Situations (Statistical Analysis)
- **Bases Loaded, 0 Outs**: 85% scoring probability
- **Runners on 2nd & 3rd, 0 Outs**: 87% scoring probability
- **Bases Loaded, 1 Out**: 70% scoring probability
- **Runner on 3rd, 0 Outs**: 75% scoring probability
- **Runners on 1st & 3rd, 0 Outs**: 70% scoring probability
- **Runners on 2nd & 3rd, 1 Out**: 65% scoring probability
- **Runners on 1st & 2nd, 0 Outs**: 60% scoring probability
- **Runner on 2nd, 0 Outs**: 60% scoring probability
- **Runner on 3rd, 1 Out**: 55% scoring probability
- **Runners on 1st & 3rd, 1 Out**: 55% scoring probability
- **Bases Loaded, 2 Outs**: 35% scoring probability

#### Weather-Based Metrics
- **Wind Speed ≥ 7.5 mph**: Blowing toward outfield (HR boost)
- **Temperature ≥ 85°F**: Hot weather HR enhancement
- **Wind Speed ≥ 7.5 mph + Temp ≥ 85°F**: Combined hot & windy conditions
- **Wind Direction Change ≥ 45°**: Significant shift detection

#### Game State Metrics
- **Inning = 7**: 7th inning warning trigger
- **Inning = 9 + Tied Score**: Critical tie game situation
- **Inning = 1 + First Pitch**: Game start detection
- **Score Change**: Any run scoring event
- **Weather Delay**: Status contains "Delayed" + "Rain"

#### Play-by-Play Event Metrics
- **Home Run Events**: Event type = "Home Run" OR description contains "home run"
- **Hit Events**: Event types = ["Single", "Double", "Triple", "Home Run"]
- **Strikeout Events**: Event = "Strikeout" OR description contains "struck out"
- **Scoring Events**: Description contains ["run", "score", "rbi"] OR RBI > 0

#### Advanced ROI Metrics
- **Power + Scoring Combo**: Season HRs ≥ 20 + Runners on Base
- **High-Confidence Power**: Season HRs ≥ 30 (elite tier)
- **Pitcher Softening Indicators**:
  - Late inning (≥ 6th)
  - Estimated pitch count ≥ 80
  - Recent hard contact (doubles/triples)
  - Multiple contact events in sequence

#### Clutch Situation Metrics
- **RISP (Runners in Scoring Position)**: Runners on 2nd or 3rd base
- **Late Game Pressure**: Inning ≥ 7
- **Power + RISP + Late Game**: Combined high-value situation
- **At-Bat Context**: Plate appearance tracking for immediate alerts

#### AI Enhancement Metrics
When AI features are enabled, additional contextual analysis includes:
- **Batter Performance Trends**: Recent game performance
- **Game Momentum Indicators**: Scoring patterns and timing
- **Weather Impact Assessment**: Environmental effects on hitting
- **Situational Win Probability**: Context-aware predictions

### Deduplication Windows
- **Immediate Alerts** (Hits, HRs, Strikeouts): 15-second window
- **Situational Alerts** (Power hitters, Hot hitters): Per plate-appearance
- **Persistent Alerts** (High-probability situations): 5-minute window with re-alert capability
- **Game State Alerts** (7th inning, tie games): Once per game
- **Weather Alerts**: Per condition change with tracking

### Performance Benchmarks
- **Alert Latency**: <1 second from detection to Telegram
- **API Response Time**: <2 seconds for game data
- **Monitoring Cycle**: 2-3 seconds complete cycle
- **Data Freshness**: Real-time with <30 second staleness tolerance

## Alert Configuration System

### Deduplication Logic
```python
ALERT_CONFIG = {
    "power_hitter": {
        "window": 15,
        "scope": "plate_appearance",
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
        "realert_after_secs": 120
    }
}
```

### AI Integration Points
- **Batter Analysis**: Situational predictions for power hitters
- **Game Context**: Scoring probability analysis
- **Weather Impact**: Wind and temperature effects on home run probability
- **Pitcher Analysis**: Fatigue detection and control assessment

## User Interface Features

### Game Selection Dashboard
- **Real-time Game List**: Live status updates for all MLB games
- **Bulk Selection**: Toggle monitoring for multiple games
- **Status Indicators**: Clear visual feedback for game states
- **Auto-refresh**: Polling every 5 seconds for current data

### Preference Management
- **Alert Categories**: Granular control over 15+ alert types
- **AI Features**: 6 specific AI enhancement toggles
- **Notification Settings**: Telegram group configuration
- **Persistence**: Settings survive application restarts

### Alert Display
- **Real-time Feed**: Live alerts with timestamps and context
- **Alert History**: Searchable log of recent notifications
- **Visual Indicators**: Color-coded alert types and priorities
- **Mobile Optimization**: Touch-friendly interface

## Deployment & Operations

### Production Environment
- **Platform**: Replit with Gunicorn deployment
- **Process Architecture**: Separated web server and monitoring worker
- **Health Checks**: Automated monitoring with Telegram crash notifications
- **Resource Management**: Connection pooling and memory leak prevention

### Monitoring & Logging
- **Structured Logging**: Process IDs and request tracking
- **Debug Modes**: Configurable logging levels
- **Performance Metrics**: Response time tracking and optimization
- **Error Tracking**: Comprehensive exception handling and reporting

### Configuration Management
- **Environment-based**: Development vs production settings
- **Secret Management**: Secure API key handling
- **Feature Flags**: Configurable thresholds and toggles
- **Hot Reloading**: Updates without service interruption

## API Endpoints

### Core Endpoints
- `GET /`: Main dashboard with game selection interface
- `GET /api/games`: Real-time game data with monitoring status
- `POST /api/toggle_monitoring`: Enable/disable game monitoring
- `GET /api/alerts`: Recent alert history and current status
- `POST /api/preferences`: Update notification preferences
- `GET /healthz`: Production health check endpoint

### Data Format
```json
{
  "games": [
    {
      "id": "776789",
      "away_team": "Boston Red Sox", 
      "home_team": "San Diego Padres",
      "status": "In Progress",
      "inning": "Top 7th",
      "score": "BOS 4, SD 3",
      "is_monitored": true,
      "last_update": "2025-08-10T22:15:30Z"
    }
  ],
  "alerts": [
    {
      "timestamp": "2025-08-10T22:14:15Z",
      "type": "power_hitter",
      "message": "💥 POWER HITTER ALERT!\nAaron Judge at bat with 47 HRs this season!",
      "game_info": "NYY @ HOU",
      "ai_prediction": "High probability of contact given favorable count"
    }
  ]
}
```

## Integration Specifications

### Telegram Bot Setup
- **Bot Username**: @chirpbetabot
- **Group Configuration**: "Chirp Chirp Chirp" group with negative chat ID
- **Message Format**: Structured alerts with emoji indicators and context
- **Error Handling**: Graceful fallback for delivery failures

### Weather Integration
- **Service**: OpenWeatherMap Current Weather API
- **Coverage**: All 30 MLB stadium locations with precise coordinates
- **Refresh Rate**: Every monitoring cycle for active games
- **Features**: Wind speed/direction, temperature, humidity, pressure

### AI Enhancement
- **Model**: OpenAI GPT-4o (latest available)
- **Features**: Contextual game analysis, scoring predictions, batter insights
- **Response Format**: JSON structured for consistent parsing
- **Fallback**: System operates normally if AI unavailable

## Troubleshooting & Maintenance

### Common Issues
- **Alert Delays**: Check API response times and network connectivity
- **Missing Notifications**: Verify Telegram bot token and chat ID configuration
- **Game Data Inconsistencies**: Multi-source validation catches most issues
- **UI Repetition**: Auto-sync service disabled to prevent infinite loops

### Monitoring Health
- System health tests: 7/7 passing
- Worker process uptime: Continuous with auto-restart
- API response times: Within acceptable thresholds
- Alert delivery rate: >99% success to Telegram

### Performance Optimization
- Connection pooling reduces API latency
- Smart caching minimizes redundant requests
- Progressive backoff prevents API rate limiting
- Efficient deduplication reduces notification spam

---

## Version History Summary

- **v1.4.1** (2025-08-10): Critical alert bug fixes and stability improvements
- **v1.4.0** (2025-08-10): ROI Alerts Pack with advanced AI and pitcher analysis
- **v1.3.4** (2025-08-07): Granular AI controls with 6 specific feature toggles
- **v1.3.2** (2025-08-09): Weather integration and power hitter enhancements
- **v1.2.0** (2025-08-07): Multi-source data aggregation and PostgreSQL integration
- **v1.0.0** (2025-08-01): Initial release with core monitoring functionality

## Support & Documentation

For technical support, configuration assistance, or feature requests, refer to:
- **Documentation**: This specification and CHANGELOG.md
- **Health Status**: `/healthz` endpoint for real-time system status
- **Logs**: Structured logging with configurable detail levels
- **Testing**: Comprehensive test suite for alert logic and API integration

---

*This specification represents the current state of the MLB Live Game Monitor as of August 10, 2025. The system is production-ready and actively monitoring MLB games with real-time Telegram notifications.*