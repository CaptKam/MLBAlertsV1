# MLB Alert System Comprehensive Audit
**Generated:** August 15, 2025

## Executive Summary
**Found 41 alert locations** across the system with **7 major issues requiring immediate fixes**:

## 🚨 CRITICAL ISSUES IDENTIFIED

### 1. **Missing AI Alert Preferences** (HIGH PRIORITY)
**ISSUE:** Several AI-powered alerts are missing from notification_preferences
- `ai_power_plus_scoring` ❌ (the one you asked about)
- `ai_power_high` ❌
- `pitcher_softening` ❌

**FIX NEEDED:** Add these to default preferences in persistent_settings.py

### 2. **Inconsistent AI Enhancement Settings** (MEDIUM)
**ISSUE:** AI enhancement preferences are disabled by default but referenced throughout
- `ai_enhance_alerts` = False (but used in 8+ locations)
- `ai_summarize_events` = False (but used in multiple locations)
- `ai_analyze_hits` = True (inconsistent with others)

### 3. **Duplicate Alert Logic** (FIXED)
**STATUS:** ✅ Previously cleaned up - removed 5 duplicate alert sections

### 4. **Power Hitter Alert Timing Issues** (PARTIALLY FIXED)
**STATUS:** 🔄 Enhanced debugging added but Pete Crow-Armstrong issue shows timing problems
- Power alerts should fire BEFORE batter reaches plate ("COMING UP!")
- Current: Fires when batter is already batting (too late)

### 5. **Missing Fallback Tier Assignment** (MEDIUM)
**ISSUE:** Some batters might not get tier assignments if math engines fail
- Need to ensure ALL power hitters (10+ HRs) get basic tiers

### 6. **Scoring Alert Data Dependency** (MEDIUM)  
**ISSUE:** Base runner detection relies on specific data formats
- `bases_occupied = game_data.get('base_runners', [])`
- May miss runners if data format varies between sources

### 7. **Clutch HR Alert Scoping** (LOW)
**ISSUE:** Uses `at_bat_index` which may not be reliable
- Should use more stable identifiers

## 📊 ALERT CATEGORIES ANALYSIS

### Power Hitter Alerts (5 types)
1. ✅ **Basic Power Hitter** - Working (25+ HRs)
2. ❌ **AI: Power Hitter + Scoring** - Missing preference
3. ❌ **AI: Power High-Confidence** - Missing preference  
4. ✅ **Clutch HR Threat** - Working (15+ HRs, late innings, RISP)
5. ❌ **Pitcher Softening** - Missing preference

### Scoring Situation Alerts (12 types)
- ✅ **Bases Loaded** scenarios - Working
- ✅ **Runner on 3rd** scenarios - Working
- ✅ **Multiple runner** scenarios - Working
- ⚠️  **Data dependency risk** - All rely on `base_runners` field

### Game State Alerts (8 types)
- ✅ **Game Start** - Fixed timing (waits for actual first pitch)
- ✅ **Inning Change** - Working
- ✅ **7th Inning Warning** - Working
- ✅ **Tie 9th Inning** - Working

### Weather Alerts (5 types)
- ✅ **Wind Speed** - Working
- ✅ **Temperature + Wind** - Working  
- ✅ **Hot + Windy** - Working
- ✅ **Wind Shift** - Working

### Hit/Run Alerts (8 types)
- ✅ **Hits** - Working
- ✅ **Runs** - Working
- ✅ **Strikeouts** - Working
- ✅ **Home Runs** - Working

## 🔧 IMMEDIATE ACTION PLAN

### Phase 1: Fix Missing Preferences (NOW)
1. Add missing AI alert preferences to persistent_settings.py
2. Enable them by default for ROI alerts
3. Test Pete Crow-Armstrong scenario

### Phase 2: Improve Alert Timing (NEXT)
1. Enhance power hitter detection to trigger earlier
2. Add better plate appearance prediction
3. Test with live games

### Phase 3: Data Robustness (LATER)
1. Add fallback base runner detection methods
2. Improve tier assignment fallbacks
3. Enhanced error handling

## 🎯 SUCCESS METRICS
- "AI: Power Hitter + Scoring Opportunity" alerts start firing
- Power alerts arrive 15-60 seconds before batter reaches plate
- 95%+ alert firing rate for qualifying situations
- Zero duplicate alerts
- Enhanced user ROI alert experience