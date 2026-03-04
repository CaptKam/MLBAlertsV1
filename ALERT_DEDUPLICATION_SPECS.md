# MLB Alert System - Deduplication Technical Specifications

## Overview
The MLB monitoring system uses a sophisticated multi-layered deduplication system to prevent spam alerts while ensuring all meaningful events are captured. This document provides complete technical specifications.

## Architecture Components

### 1. Alert Configuration System
```python
ALERT_CONFIG = {
    "alert_type": {
        "window": int,              # Time window in seconds to block duplicates
        "scope": str,               # Deduplication scope level
        "content_fields": [str],    # Fields used for uniqueness detection
        "realert_after_secs": int   # Re-alert interval for persistent conditions
    }
}
```

### 2. Deduplication Scopes

#### A. Plate Appearance Scope (`"plate_appearance"`)
- **Used for**: Power hitter alerts, scoring situation alerts
- **Behavior**: Each batter's plate appearance is tracked separately
- **Key Format**: `{game_id}_{alert_type}_{half_inning}_{pa_id}`
- **Purpose**: Allows same situation type for different batters

#### B. Half Inning Scope (`"half_inning"`)  
- **Used for**: General runner alerts, persistent game state
- **Behavior**: Tracks per half-inning regardless of batter
- **Key Format**: `{game_id}_{alert_type}_{half_inning}`
- **Purpose**: Prevents spam within same half inning

#### C. Play Scope (`"play"`)
- **Used for**: Hits, home runs, strikeouts, scoring plays
- **Behavior**: Each individual play/event tracked
- **Key Format**: `{game_id}_{alert_type}_{play_id}`
- **Purpose**: Ensures each discrete event generates exactly one alert

#### D. Game Scope (`"game"`)
- **Used for**: Game-wide events (start, delay, weather)
- **Behavior**: Once per game regardless of when triggered
- **Key Format**: `{game_id}_{alert_type}_{data_hash}`
- **Purpose**: Game-level announcements

### 3. Current Alert Type Configurations

```python
# Power & Performance Alerts
"power_hitter": {
    "window": 15,                    # 15-second rapid duplicate prevention
    "scope": "plate_appearance",     # Per-batter, per-PA
    "content_fields": ["batter_id", "season_hr", "pa_id"],
    "realert_after_secs": None       # No re-alerts (situational)
}

# Scoring Situation Alerts (Fixed 8/15/2025)
"bases_loaded_no_outs": {
    "window": 60,                    # 1-minute window (reduced from 300)
    "scope": "plate_appearance",     # Changed from "half_inning" 
    "content_fields": ["bases_hash", "outs", "batter_id"],  # Added batter_id
    "realert_after_secs": 180        # Re-alert after 3 minutes
}

"runners_23_no_outs": {
    "window": 60,                    # 1-minute window  
    "scope": "plate_appearance",     # Per-batter tracking
    "content_fields": ["bases_hash", "outs", "batter_id"],
    "realert_after_secs": 180
}

# Play-by-Play Alerts
"hit": {
    "window": 15,                    # Rapid duplicate prevention
    "scope": "play",                 # Per individual play
    "content_fields": ["play_id", "description"],
    "realert_after_secs": None       # No re-alerts (discrete events)
}

"home_run": {
    "window": 15,
    "scope": "play", 
    "content_fields": ["play_id", "description"],
    "realert_after_secs": None
}
```

### 4. Key Generation Algorithm

#### A. Simple Key Generation
```python
def _make_simple_key(game_id, alert_type, scope, data):
    if scope == "play":
        return f"{game_id}_{alert_type}_{data.get('play_id', data)}"
    elif scope == "plate_appearance":
        return f"{game_id}_{alert_type}_{half_inning}_{pa_id}"
    elif scope == "half_inning":
        return f"{game_id}_{alert_type}_{half_inning}"
    elif scope == "game":
        return f"{game_id}_{alert_type}"
```

#### B. Deduplication Key Generation
```python
def _make_dedup_key(game_id, alert_type, content_fields, data):
    content_pieces = []
    for field in content_fields:
        if field == "batter_id":
            content_pieces.append(str(data.get("batter_id", "")))
        elif field == "bases_hash":
            content_pieces.append(self._bases_hash(data.get("runners", [])))
        elif field == "pa_id":
            content_pieces.append(str(data.get("pa_id", "")))
        # ... other field mappings
    
    content = "|".join(content_pieces)
    return f"{game_id}_{alert_type}_{content}"
```

### 5. Deduplication Logic Flow

```python
def _is_new_alert(game_id, alert_type, data):
    simple_key, dedup_key, cfg = self._make_keys(game_id, alert_type, data)
    
    # 1. Time-based throttle check
    last_timestamp = self.recent_alerts.get(dedup_key)
    if last_timestamp:
        time_since = now - last_timestamp
        if time_since < cfg["window"]:
            return False  # Blocked by time window
    
    # 2. State-based check
    state_value = data.get("state_value", data)
    prev_state = self.game_states.get(simple_key)
    
    if prev_state == state_value:
        # 3. Re-alert policy check
        realert_after = cfg.get("realert_after_secs")
        if realert_after:
            last_sent = self.last_sent_by_simple.get(simple_key, 0)
            if (now - last_sent) >= realert_after:
                return True  # Re-alert allowed
        return False  # Blocked by state duplication
    
    # 4. Update tracking
    self.recent_alerts[dedup_key] = now
    self.game_states[simple_key] = state_value
    self.last_sent_by_simple[simple_key] = now
    
    return True  # New alert allowed
```

### 6. Memory Management

#### A. Automatic Cleanup
```python
def _cleanup_old_alerts():
    current_time = time.time()
    
    # Clean expired deduplication entries
    for key, timestamp in self.recent_alerts.items():
        alert_type = key.split('_')[1]
        cfg = ALERT_CONFIG.get(alert_type, ALERT_CONFIG["default"])
        ttl = cfg.get("window", self.alert_dedup_window)
        
        if current_time - timestamp > (ttl + 10):  # Buffer
            self.recent_alerts.pop(key, None)
    
    # Clean old simple keys (1-hour retention)
    for key, timestamp in self.last_sent_by_simple.items():
        if current_time - timestamp > 3600:
            self.last_sent_by_simple.pop(key, None)
```

#### B. Memory Structures
- `recent_alerts`: Dict[str, float] - Dedup key -> timestamp
- `game_states`: Dict[str, Any] - Simple key -> last state value  
- `last_sent_by_simple`: Dict[str, float] - Simple key -> last sent timestamp

### 7. Special Cases & Edge Handling

#### A. Bases Hash Generation
```python
def _bases_hash(runners):
    """Generate consistent hash for base runner configuration"""
    if not runners:
        return "EMPTY"
    
    # Sort to ensure consistent ordering
    sorted_bases = sorted(set(runners))
    return "_".join(sorted_bases)  # e.g., "1B_2B_3B"
```

#### B. Plate Appearance ID Generation
```python
def _plate_appearance_id(data):
    """Generate unique PA identifier"""
    inning = data.get('inning', 0)
    batter_id = data.get('batter_id', 'unknown')
    ab_index = data.get('at_bat_index', 0)
    
    return f"inning_{inning}_batter_{batter_id}_ab_{ab_index}"
```

#### C. Half Inning Key Generation
```python
def _half_inning_key(game_data):
    """Generate half-inning identifier"""
    inning = game_data.get('inning', 0)
    is_top = game_data.get('inning_top', True)
    half = "top" if is_top else "bottom"
    
    return f"inning_{inning}_{half}"
```

### 8. Performance Characteristics

- **Memory Usage**: O(N) where N = active alerts * average key length
- **Lookup Time**: O(1) for deduplication checks (hash table)
- **Cleanup Frequency**: Every monitoring iteration (~5 seconds)
- **Retention Period**: Variable by alert type (15s - 300s + 10s buffer)

### 9. Recent Fixes (August 15, 2025)

#### Problem: Batch Duplicate Alerts
- **Issue**: Different batters in same scoring situation blocked as duplicates
- **Root Cause**: Scope was "half_inning" with only bases+outs tracking
- **Fix**: Changed to "plate_appearance" scope with batter_id included

#### Before Fix:
```python
"bases_loaded_no_outs": {
    "scope": "half_inning",              # ❌ Too broad
    "content_fields": ["bases_hash", "outs"],  # ❌ Missing batter
    "window": 300                        # ❌ Too long
}
```

#### After Fix:
```python
"bases_loaded_no_outs": {
    "scope": "plate_appearance",         # ✅ Per-batter
    "content_fields": ["bases_hash", "outs", "batter_id"],  # ✅ Includes batter
    "window": 60                         # ✅ Reasonable window
}
```

### 10. Testing & Validation

The system includes comprehensive test suites:
- `test_deduplication_fix.py` - Core deduplication logic
- `debug_power_hitter_alerts.py` - Power hitter specific scenarios  
- `test_alert_triggering.py` - Fixed scoring situation alerts
- `check_recent_alerts.py` - Live alert analysis

### 11. Configuration Guidelines

#### When to Use Each Scope:
- **play**: Discrete events that should never repeat (hits, HRs)
- **plate_appearance**: Situational alerts that can occur per batter (power, scoring)  
- **half_inning**: Persistent conditions (general runner alerts)
- **game**: Once-per-game events (weather, delays)

#### Window Size Guidelines:
- **15s**: Rapid duplicate prevention (hits, power)
- **60s**: Moderate situational alerts (scoring opportunities)
- **300s**: Persistent conditions (weather, delays)

#### Re-alert Policy:
- **None**: Discrete events (hits, strikeouts)
- **120-300s**: Persistent opportunities (scoring situations, weather)

This deduplication system ensures comprehensive coverage while preventing alert spam through intelligent scoping and timing controls.