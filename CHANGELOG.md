# MLB Live Game Monitor - Changelog

All notable changes to the MLB Live Game Monitor application will be documented in this file.

## Project Summary — MLB Live Game Monitor

### Purpose
The MLB Live Game Monitor is a real-time MLB tracking and alert system designed to deliver actionable, high-accuracy game insights directly to our Telegram group. It uses multi-source data, AI analysis, and environmental factors to detect high-impact game events and notify users instantly.

### Core Scope (Do Not Change Without Approval)

**Real-time tracking** of MLB games with coverage for late-night West Coast games until 5 AM ET.

**Alert triggers for:**
- Bases loaded (0 and 1 out situations)
- Power hitters (17+ HR)
- Prime weather conditions for home runs
- AI-generated game insights

**Multi-source data integration** (MLB Official API, StatsAPI, API Sports, ESPN, Yahoo Sports).

**Telegram delivery** via @chirpbetabot to the "Chirp Chirp Chirp" group.

**Web dashboard** for game selection, preferences, and real-time visual alerts.

**Reliability features:** deduplication, persistent settings, failover data sources.

### Development Notes
- Avoid changes that disrupt real-time data flow or Telegram alert delivery.
- New features should align with the app's goal: fast, reliable, and actionable MLB game alerts.
- Any backend changes must maintain current multi-threaded Flask architecture and weather integration.

---

## [1.4.1] - 2025-08-10 (Critical Alert Bug Fixes)

### 🚨 Critical Bug Fixes
- **Hot Hitter Alert Fix**: Fixed critical bug where hot hitter alerts were using wrong alert type ("power_hitter" instead of "hot_hitter")
  - **Issue**: Players who already homered weren't triggering hot hitter alerts when batting again
  - **Impact**: Hot hitter alerts now properly trigger for each at-bat after a player has homered
  - **Technical**: Corrected `_add_alert()` call on line 1562 in `mlb_monitor.py`

### 🎯 System Stability
- **Auto-sync Service**: Disabled auto-sync to prevent infinite loop causing UI repetition
- **Alert Deduplication**: Enhanced context-aware scoping prevents blocking legitimate alerts
- **Production Ready**: Both critical fixes verified and ready for deployment

### 📊 Current Alert Thresholds
- **Power Hitters**: 20+ season home runs (elite players only)
- **Hot Hitters**: Players who already homered in current game
- **Clutch Situations**: Power hitters + RISP in 7th+ innings
- **Weather Alerts**: Wind ≥7.5 mph toward outfield

---

## [1.4.0] - 2025-08-10 (ROI Alerts Pack)

### 🤖 Advanced AI Alert System
- **AI Power Hitter + Scoring Opportunity**: High-leverage situations with elite power hitters
  - Combines Power Alert Score (0-100), park factors, weather, platoon splits
  - Triggers on RISP + late innings with Tier B+ power hitters (55+ score)
  - 90-second deduplication with immediate re-alert on tier upgrades
- **AI Power Hitter - High Confidence**: Tier A alerts (≥70 score) for immediate betting opportunities
- **Pitcher Softening Detection**: Fatigue/contact analysis using:
  - 3rd time through order (TTO≥3)
  - Hard-hit percentage increases
  - Velocity drops ≥1.0 mph
  - Pitch count thresholds (75/90 for starters)
- **Pitcher Control Loss**: 8+ consecutive balls with re-alerts at 10 and 12 balls

### 🎯 Enhanced Alert Intelligence
- **Context-Aware Scoring**: Alerts include score, tier, reasoning, and ROI hints
- **Real-time Adaptation**: Dedup keys prevent spam while surfacing upgrades immediately
- **Betting Integration**: ROI hints like "HR/XTBR", "Live total over", "Walk props"

---

## [1.3.4] - 2025-08-07 (Granular AI Controls)

### 🤖 Enhanced AI Configuration
- **Granular AI Controls**: Replaced single "AI Insights" toggle with 6 specific AI feature checkboxes:
  - ⚾ **Analyze Hits, Home Runs & Strikeouts**: AI analysis for offensive events
  - 🏃 **Insights for Runners on Base**: Detailed analysis of base runner situations  
  - 💪 **Analyze Power Hitter At-Bat**: Enhanced alerts for power hitters batting
  - 📊 **Predict Future Scoring Probability**: AI-powered scoring predictions
  - 📝 **Summarize Recent Game Events**: Contextual game summaries
  - ⚡ **Enhance Other Types of Alerts**: AI improvements for 7th inning, game start, tie games

### 🎯 Smart AI Integration
- AI analysis is now **conditionally applied** based on user preferences across all alert types:
  - Hit/home run/strikeout alerts use `ai_analyze_hits` preference
  - Runner alerts enhanced with `ai_analyze_runners` and `ai_predict_scoring`
  - Power hitter alerts controlled by `ai_analyze_power_hitter`
  - Game situation alerts use `ai_enhance_alerts` and `ai_summarize_events`
- **OpenAI GPT-4o Model**: All AI features powered by OpenAI's latest and most advanced model
- **Backwards Compatible**: Existing users maintain current AI functionality with new granular control

### 🔧 Technical Implementation
- Updated frontend with 6 new AI preference checkboxes in "AI Features" section
- Modified JavaScript to handle granular AI settings synchronization
- Enhanced monitoring logic to conditionally add AI analysis throughout alert pipeline
- Maintained system stability with all health checks passing (7/7)

### 📈 User Experience
- **Personalized AI**: Users can enable only the AI features they want
- **Reduced Noise**: Turn off unwanted AI analysis while keeping preferred features
- **Smart Defaults**: Most AI features enabled by default for optimal experience
- **Real-time Updates**: Changes apply immediately to active monitoring

---

## [1.3.3] - 2025-08-07 (Weather Filtering for Selected Live Games)

### 🎯 Changed
- Weather fetching and weather-based alerts now run **only** for games that are:
  1) **Selected** for monitoring, and
  2) **Live/In-Progress**.

### 🌦️ Added
- Eligibility rule for weather pipeline:
  - `eligible_for_weather = game.is_selected and game.status in {"LIVE","IN_PROGRESS"}`
- Weather context is **excluded** from AI payloads and alerts for ineligible games.
- Clear logs for skipped games: `Weather skipped: not selected or not live (game_id=...)`.

### 🔧 Technical Notes
- OpenWeatherMap calls occur **inside** the monitoring loop only for eligible games.
- Time-based deduplication for weather alerts remains (default **5 minutes**).
- Weather subsystem fails gracefully; **never blocks** core scoring alerts.

### ⚙️ Config / ENV
- `OWM_API_KEY` (required)
- `WEATHER_ENABLED=true`
- `WEATHER_POLL_SECS=60` (default)
- `WEATHER_DEDUPE_MIN=5` (default)

### 🧩 Reference Snippet (Python)
```python
def eligible_for_weather(game):
    return bool(getattr(game, "is_selected", False)) and game.status in {"LIVE", "IN_PROGRESS"}

for game in monitored_games:
    if not eligible_for_weather(game):
        logger.info(f"Weather skipped: not selected or not live (game_id={game.id})")
        continue

    weather = get_weather_for_coordinates(game.stadium_lat, game.stadium_lon)  # OWM call
    update_weather_context(game.id, weather)

    # Example triggers
    if weather.wind_out_mph >= 7.5:
        emit_alert("Boosted HR Probability", game, weather)

    if wind_shift_toward_outfield(prev=prev_weather(game.id), curr=weather, deg_threshold=45):
        emit_alert("Wind Shift Toward OF", game, weather)
```

---

## [1.3.2] - 2025-08-09 (High-Probability Scoring + Weather, Power Hitter, and OpenWeatherMap Integration)

### ⚾ Intelligent Scoring Alert System

- System now triggers smart alerts for high-probability scoring situations.

### 🌦️ Real-Time Weather Alerts
- Integrated **OpenWeatherMap API** for accurate live weather data at stadium locations.
- **Wind Speed Trigger**: Winds ≥ 7.5 mph blowing **out toward any outfield** triggers a "Boosted HR Probability" alert.
- **Wind Shift Trigger**: Wind direction changes ≥ 45° toward outfield from previous reading trigger alert.
- **Combined Conditions**:
  * High HRFI (8+) + wind out ≥ 7.5 mph → "Prime HR Conditions" alert
  * Temperature ≥ 85°F + wind out ≥ 7.5 mph → "Hot & Windy HR Boost" alert
- Weather data is updated every monitoring cycle and available for:
  * OpenAI-powered game analysis
  * Internal alert generation logic
- Alerts include wind speed, direction, and temperature context from OpenWeatherMap.

### 💥 Power Hitter / On-Deck Danger Alerts
- **Season Power Threat**: Batter with 20+ home runs this season is on deck or at bat → trigger "Power Hitter Alert".
- **In-Game Hot Bat**: Batter who has already hit a HR in the current game is on deck or at bat → trigger "Hot Hitter Alert".
- **Clutch Moment**: Power hitter batting with runners in scoring position in late innings (7th+) → trigger "Clutch HR Threat" alert.

### 🔧 Technical Notes
- OpenWeatherMap API key stored securely via environment variables.
- Weather and player data merged into single event object for AI and internal logic.
- Deduplication rules prevent repeat alerts within 5-minute window.

---

## [1.3.1] - 2025-08-08 (Rollback & Development Safeguards)

### ⚠️ ROLLBACK NOTICE
**Version 1.3.0 has been rolled back due to unexpected system instability**

All changes from v1.3.0 including OpenAI integration, system resilience features, and monitoring improvements have been reverted to restore stable operation. The system has been returned to the proven v1.2.0 codebase.

### 🔒 Development Safeguards Implemented

#### Core Mission Protection
The MLB Monitor's primary mission is **reliable, real-time alert delivery**. All development must prioritize:
1. **Alert Reliability**: Notifications must work 100% of the time
2. **System Stability**: No changes that risk monitoring interruption
3. **Production Safety**: All enhancements must be thoroughly tested
4. **User Trust**: Maintain consistent, dependable service

#### New Development Rules
1. **No Major Refactoring**: Incremental improvements only
2. **Test in Isolation**: New features tested separately before integration
3. **Preserve Core**: Alert system code remains untouched unless critical
4. **Rollback Ready**: All changes must be easily reversible
5. **User-Requested Only**: Features added only when explicitly requested

### 📋 Lessons Learned
- Complex threading improvements can introduce race conditions
- External API integrations (OpenAI) add failure points
- System "improvements" can reduce reliability
- Production stability > feature richness
- Working code should not be fixed if not broken

### ✅ Current Stable State
- **Monitoring**: Continuous operation confirmed
- **Alerts**: All notification types functioning
- **Performance**: Sub-second response times maintained
- **Reliability**: 24/7 uptime restored
- **Simplicity**: Reduced complexity for maintainability

### 🎯 Updated Objectives
1. **Stability First**: No changes that risk production
2. **Alert Focus**: All development serves notification delivery
3. **Minimal Changes**: Touch only what's necessary
4. **User-Driven**: Changes only per explicit requests
5. **Production-Ready**: Always maintain deployable state

### 🛡️ Guardrails for Future Development
- Always backup before changes
- Test components in isolation
- Monitor logs during changes
- Rollback immediately if issues arise
- Document all modifications clearly
- Prioritize reliability over features

**Status**: System fully operational on stable v1.2.0 foundation

---

## [1.3.0] - 2025-08-07 (System Reliability Update)

### 🛡️ Critical System Improvements
- **Thread Crash Recovery**: Automatic restart of monitoring thread if it crashes
- **Memory Leak Prevention**: Fixed AsyncIO event loop resource leaks
- **Connection Pooling**: Added HTTP connection pooling for better performance
- **Error Recovery**: Comprehensive crash protection with progressive backoff
- **Health Monitoring**: System health checks every 30 seconds with auto-recovery

### 🚀 Added
- **OpenAI Integration**: AI-powered game analysis and enhanced alerts
  - Game situation analysis with scoring probability
  - Enhanced alert messages with context
  - Scoring probability predictions
  - Event summaries for recent plays
- **System Resilience Features**:
  - Auto-restart manager for critical components
  - Circuit breaker pattern for external API calls
  - Rate limiting to prevent API violations
  - Resource manager for graceful shutdown
- **Health Check System**: Comprehensive test suite for system verification
- **Connection Pool Manager**: Efficient HTTP request handling with retry logic

### ✅ Fixed
- **Type Error in Aggregator**: Fixed dictionary access bug that could cause crashes
- **Thread Safety Issues**: Added proper locking mechanisms for thread operations
- **Import Path Errors**: Corrected urllib3 import paths
- **Event Loop Cleanup**: Proper closure of AsyncIO loops preventing memory leaks
- **Monitoring Thread Death**: Thread now auto-restarts if it dies unexpectedly

### 🔧 Optimized
- **Error Handling**: Added traceback logging for better debugging
- **Resource Management**: Automatic cleanup on shutdown
- **Connection Efficiency**: Connection pooling reduces API latency
- **Recovery Strategy**: Progressive backoff (5s to 30s) on consecutive errors
- **Health Logging**: Periodic health status logs every minute

### 📊 System Health Metrics
- **Auto-Recovery**: Thread restarts within 30 seconds of failure
- **Error Tolerance**: Handles up to 5 consecutive errors before stopping
- **Connection Pool**: 10 connections, max 20, with 3 retry attempts
- **Health Tests**: 7/7 system tests passing
- **Uptime**: Continuous operation with automatic recovery

## [1.2.0] - 2025-08-07

### 🎯 Major Improvements
- **Enhanced Real-time Performance**: Optimized API response times to 0.20-0.34 seconds
- **Multi-source Data Aggregation**: Integrated multiple MLB data sources for reliability
- **Persistent Monitoring**: Settings now survive application restarts automatically
- **PostgreSQL Integration**: Full database support for multi-user functionality

### ✅ Fixed
- **Duplicate Notifications**: Removed test notification system that was sending 4 identical alerts
- **Past Event Alerts**: System now only checks last 2 plays to prevent alerts for old events
- **Strikeout Detection**: Fixed to only alert on new strikeouts, not historical ones
- **Memory Leaks**: Optimized game state tracking to prevent excessive memory usage
- **Indentation Errors**: Fixed Python formatting issues that were preventing monitoring

### 🚀 Added
- **High-Probability Scoring Alerts**: New intelligent alert system for critical game moments
  - Runners on 2nd & 3rd with 0-1 outs
  - Bases loaded situations
  - Runner on 3rd with less than 2 outs
  - Multiple runner combinations with scoring potential
- **Telegram Integration**: Real-time alerts sent directly to Telegram
- **Auto-restore Monitoring**: Games automatically resume monitoring after restart
- **Debug Logging**: Cleaner, more informative logging for troubleshooting

### 🔧 Optimized
- **Reduced Logging Noise**: Only logs meaningful events (runners on base, actual plays)
- **API Call Efficiency**: Parallel processing of multiple data sources
- **Alert Deduplication**: Improved logic to prevent duplicate notifications
- **Response Times**: Consistent sub-second response times across all endpoints

### 📊 Performance Metrics
- **API Response Times**: 
  - MLB Official: 0.04-0.09 seconds
  - MLB StatsAPI: 0.20-1.38 seconds
- **Processing Speed**: 2-3 seconds per monitoring cycle
- **Alert Latency**: < 1 second from detection to Telegram notification
- **Active Monitoring**: Successfully tracking 5+ games simultaneously

## [1.1.0] - 2025-08-04

### Added
- **Base Runner Detection**: Real-time monitoring of runners on base
- **Custom Alert Messages**: Game-specific notifications with clear identification
- **Persistent Settings**: JSON-based configuration storage
- **Admin Authentication**: Secure access control system

### Fixed
- **API Timeout Issues**: Improved error handling for network failures
- **Game State Tracking**: Better management of in-progress game data

## [1.0.0] - 2025-08-01

### Initial Release
- **Core Monitoring Engine**: Basic MLB game tracking functionality
- **Web Interface**: Bootstrap-based responsive UI
- **Alert System**: Basic notification framework
- **Flask Backend**: RESTful API for game data
- **Real-time Updates**: Polling-based game state monitoring

---

## Upcoming Features (Roadmap)
- [ ] WebSocket support for instant updates
- [ ] Historical alert analytics
- [ ] Team-specific monitoring preferences
- [ ] Mobile app integration
- [ ] Advanced statistics tracking
- [ ] Custom alert sounds
- [ ] Email notification support
- [ ] Multi-language support

## Known Issues
- Preview page may show "Not Found" error (refresh usually fixes)
- Some completed games may still appear as "In Progress" briefly

## Technical Details
- **Framework**: Flask 3.0+ with SQLAlchemy
- **Database**: PostgreSQL with connection pooling
- **APIs**: MLB StatsAPI v1.1, MLB Official Feed
- **Notification**: Telegram Bot API
- **Frontend**: Bootstrap 5 with dark theme
- **Deployment**: Replit with Gunicorn WSGI server

---

*For questions or issues, please contact the development team.*