# MLB Alert System - Complete Formulas & Calculations Reference

## Overview
This document provides all mathematical formulas, thresholds, and calculations used in our MLB alert system, organized by alert type and mathematical domain.

---

## 1. POWER HITTER PROBABILITY MODEL

### A. Core Logistic Regression Formula
```
P(HR) = sigmoid(z)
where z = β₀ + Σ(βᵢ × xᵢ)

sigmoid(z) = 1 / (1 + e^(-z))  for z ≥ 0
           = e^z / (1 + e^z)    for z < 0
```

### B. Linear Component (z) Calculation
```
z = β₀ + β₁×ISO₁₄ + β₂×HR/PA₁₄ + β₃×ISO_season + β₄×platoon + 
    β₅×(park-1) + β₆×wind_out + β₇×temp_term + β₈×(pHR9-1.1) + 
    β₉×TTO₃ + count_bumps
```

### C. Default Coefficients
```python
β₀ = -6.4        # Intercept
β₁ = 3.0         # 14-day ISO coefficient
β₂ = 4.0         # 14-day HR/PA coefficient  
β₃ = 1.2         # Season ISO coefficient
β₄ = 2.1         # Platoon advantage coefficient
β₅ = 0.9         # Park factor coefficient
β₆ = 0.08        # Wind component coefficient
β₇ = 0.35        # Temperature coefficient
β₈ = 0.5         # Pitcher HR/9 coefficient
β₉ = 0.25        # Third time through order coefficient
```

### D. Count State Bumps
```python
"2-0": +0.35     # Hitter's count
"3-1": +0.42     # Strong hitter's count
"3-0": +0.20     # Automatic take pressure
```

---

## 2. EMPIRICAL-BAYES SHRINKAGE

### Formula
```
Stabilized_Rate = (n × observed_rate + n₀ × prior_mean) / (n + n₀)

where:
- n = sample size of observed data
- n₀ = prior sample size (confidence in league average)
- observed_rate = player's recent performance
- prior_mean = league average
```

### Default Parameters
```python
ISO Shrinkage:     n₀ = 40, prior = 0.165
HR/PA Shrinkage:   n₀ = 60, prior = 0.036
```

---

## 3. WEATHER CALCULATIONS

### A. Wind Component Toward Center Field
```
w_out = wind_mph × cos(θ)

where θ = (wind_direction - cf_azimuth) mod 360°
```

### B. HR Boost Factor
```
boost = max(0.85, 1.0 + wind_term + temp_term)

wind_term = 0.018 × w_out_cf
temp_term = 0.012 × ((temp_f - 70) / 10)
```

### C. Park Center Field Azimuths
```python
"Yankee Stadium": 54°
"Fenway Park": 90°
"Wrigley Field": 0°
"Dodger Stadium": 45°
"Oracle Park": 90°
"Coors Field": 350°
"default": 45°
```

---

## 4. TIER CLASSIFICATION SYSTEM

### A. Power Tier Assignment
```python
if P(HR) ≥ 4.0% × league_avg:  Tier = "A"  # Elite (≥4.0%)
elif P(HR) ≥ 2.5% × league_avg: Tier = "B"  # Strong (≥2.5%)
elif P(HR) ≥ 1.5% × league_avg: Tier = "C"  # Above Average (≥1.5%)
else:                           Tier = None  # Below threshold
```

### B. Threshold Values (league_avg = 3.6%)
```
Tier A: ≥ 4.0% (144% of league average)
Tier B: ≥ 2.5% (69% of league average)  
Tier C: ≥ 1.5% (42% of league average)
```

---

## 5. ALERT TRIGGER THRESHOLDS

### A. Power Hitter Alerts
```python
# Trigger Conditions (OR logic)
season_hrs ≥ 25 OR (tier == "A" AND P(HR) ≥ 5.0%)
```

### B. Weather Alerts
```python
# Wind Speed Alert
wind_mph ≥ 15 AND wind_toward_cf > 0

# Hot & Windy Alert  
temp_f ≥ 85 AND wind_mph ≥ 12 AND wind_toward_cf > 0

# Temperature + Wind Out Alert
temp_f ≥ 85 AND wind_toward_cf > 5

# HR Boost Alert (calculated)
hr_boost_factor ≥ 1.15  # 15% or greater boost

# Gust Spike Alert
wind_mph_change ≥ 5 AND current_wind ≥ 10

# Wind Shift Alert  
wind_direction_change ≥ 45°
```

### C. Scoring Situation Alerts
```python
# Bases Loaded, No Outs
bases = ["1B", "2B", "3B"] AND outs = 0
Probability = 85%

# Bases Loaded, One Out
bases = ["1B", "2B", "3B"] AND outs = 1  
Probability = 70%

# Runners 2nd & 3rd, No Outs  
bases = ["2B", "3B"] AND outs = 0
Probability = 60%

# Runners 2nd & 3rd, One Out
bases = ["2B", "3B"] AND outs = 1
Probability = 45%

# Runner on 3rd, No Outs
bases = ["3B"] AND outs = 0  
Probability = 40%

# Runner on 3rd, One Out
bases = ["3B"] AND outs = 1
Probability = 25%

# Runners 1st & 3rd, No Outs
bases = ["1B", "3B"] AND outs = 0
Probability = 50%

# Runners 1st & 3rd, One Out  
bases = ["1B", "3B"] AND outs = 1
Probability = 35%

# Runners 1st & 2nd, No Outs
bases = ["1B", "2B"] AND outs = 0
Probability = 45%

# Runner on 2nd, No Outs
bases = ["2B"] AND outs = 0
Probability = 30%
```

---

## 6. PLATT CALIBRATION

### A. Calibration Formula
```
P_calibrated = sigmoid(A × logit(P_raw) + B)

where logit(p) = ln(p / (1-p))
```

### B. Weekly Calibration Parameters
```python
# Default values (updated weekly)
A = 1.0    # Scale parameter
B = 0.0    # Shift parameter
```

---

## 7. VALUE SCORING SYSTEM

### A. Alert Value Formula
```
Value = (P_event - P_base) × leverage_index × 100

where:
- P_event = predicted probability of event
- P_base = league baseline probability  
- leverage_index = situational importance (1.0 default)
```

### B. Leverage Adjustments
```python
Bases Loaded: leverage = 2.0
Late Innings (7+): leverage = 1.5
Tie Game: leverage = 1.3
Default: leverage = 1.0
```

---

## 8. PITCHER ANALYSIS FORMULAS

### A. EWMA (Exponentially Weighted Moving Average)
```
EWMA_t = α × value_t + (1-α) × EWMA_(t-1)

where α = 0.3 (smoothing parameter)
```

### B. CUSUM (Cumulative Sum) Drift Detection
```
S_t = max(0, S_(t-1) + (x_t - μ - k))

where:
- k = drift threshold (0.5 × std)
- μ = target mean
- Alert when S_t > h (threshold = 4.0)
```

### C. SPRT (Sequential Probability Ratio Test)
```
Λ_t = Σ ln(P(x_i | H₁) / P(x_i | H₀))

Alert when Λ_t ≥ ln(A) or Λ_t ≤ ln(B)
where A = 19, B = 1/19 (95% confidence)
```

---

## 9. AI POWER ENHANCED ALERTS

### A. AI Power High Trigger
```python
# Conditions (AND logic)
tier == "A" AND P(HR) ≥ 4.0% AND ai_prediction_favorable
```

### B. AI Power + Scoring Trigger  
```python
# Conditions (AND logic)
(tier == "A" OR tier == "B") AND 
runners_in_scoring_position AND
ai_prediction_score ≥ 7.0
```

---

## 10. DEDUPLICATION FORMULAS

### A. Time Window Check
```python
is_blocked = (current_time - last_alert_time) < window_seconds
```

### B. State Comparison
```python
is_duplicate = (current_state_value == previous_state_value)
```

### C. Re-alert Logic
```python
allow_realert = (current_time - last_sent_time) ≥ realert_after_seconds
```

---

## 11. LEAGUE BASELINE CONSTANTS

### A. Batting Constants
```python
LEAGUE_PA_HR = 0.036        # 3.6% HR rate per PA
LEAGUE_ISO = 0.165          # Isolated power average
LEAGUE_AVG = 0.265          # Batting average
LEAGUE_OBP = 0.335          # On-base percentage
LEAGUE_SLG = 0.430          # Slugging percentage
```

### B. Pitching Constants
```python
LEAGUE_PITCHER_HR9 = 1.10   # HR per 9 innings
LEAGUE_ERA = 4.00           # Earned run average
LEAGUE_WHIP = 1.30          # Walks + hits per inning
```

### C. Park Factors
```python
"Yankee Stadium": 1.15      # Favors HRs
"Coors Field": 1.25         # High altitude boost
"Oracle Park": 0.88         # Suppresses HRs
"Marlins Park": 0.85        # Pitcher friendly
"default": 1.00             # Neutral
```

---

## 12. MATHEMATICAL UTILITIES

### A. Clamping Function
```python
clamp01(x) = max(0.0, min(1.0, x))
```

### B. Safe Value Function
```python
safe(value, default) = default if value is None else value
```

### C. Bases Hash Generation
```python
bases_hash = "_".join(sorted(set(base_runners)))
# Examples: "1B_2B", "1B_2B_3B", "EMPTY"
```

---

## 13. ALERT PRIORITY SCORING

### A. Priority Calculation
```python
priority = base_score + situational_multipliers

Base Scores:
- Bases Loaded: 100
- Power Hitter: 80  
- Weather Alert: 60
- General Runner: 40

Multipliers:
- Late Inning (7+): ×1.5
- Close Game (≤2 runs): ×1.3
- Tier A Player: ×1.4
- Prime Conditions: ×1.2
```

### B. Alert Frequency Limits
```python
Power Hitter: max 1 per PA per player
Scoring Situation: max 1 per PA per situation
Weather: max 1 per 10 minutes
General: max 1 per 15 seconds
```

---

## 18. COMPLETE ALERT TRIGGER CONDITIONS

### A. Power & Performance Alerts
```python
# Power Hitter Alert
(season_hrs ≥ 25) OR (tier == "A" AND P(HR) ≥ 5.0%)

# Hot Hitter Alert  
game_hrs ≥ 2 OR (recent_hrs_3games ≥ 3)

# AI Power High Alert
tier == "A" AND P(HR) ≥ 4.0% AND ai_confidence ≥ 0.75

# AI Power + Scoring Alert
(tier == "A" OR tier == "B") AND runners_in_scoring_position AND ai_score ≥ 6.0
```

### B. Weather Condition Alerts
```python
# Wind Speed Alert
wind_mph ≥ 15 AND wind_component_toward_cf > 0

# Hot & Windy Alert
temp_f ≥ 85 AND wind_mph ≥ 12 AND wind_component_toward_cf > 0

# Temperature + Wind Alert  
temp_f ≥ 85 AND wind_component_toward_cf > 5

# HR Boost Alert
hr_boost_factor ≥ 1.15  # 15%+ boost

# Gust Spike Alert
wind_speed_increase ≥ 5 AND current_wind ≥ 10

# Wind Shift Alert
abs(wind_direction_change) ≥ 45°
```

### C. Scoring Probability Formulas
```python
# Historical MLB scoring probabilities by situation:

bases_loaded_0_outs = 0.85    # 85%
bases_loaded_1_out = 0.70     # 70%  
bases_loaded_2_outs = 0.30    # 30%

runners_23_0_outs = 0.60      # 60%
runners_23_1_out = 0.45       # 45%
runners_23_2_outs = 0.20      # 20%

runner_3rd_0_outs = 0.40      # 40%
runner_3rd_1_out = 0.25       # 25%
runner_3rd_2_outs = 0.12      # 12%

runners_13_0_outs = 0.50      # 50%
runners_13_1_out = 0.35       # 35%
runners_13_2_outs = 0.15      # 15%

runners_12_0_outs = 0.45      # 45%
runners_12_1_out = 0.30       # 30%
runners_12_2_outs = 0.12      # 12%

runner_2nd_0_outs = 0.30      # 30%
runner_2nd_1_out = 0.20       # 20%
runner_2nd_2_outs = 0.08      # 8%
```

---

## 19. SYSTEM PERFORMANCE METRICS

### A. Processing Targets
```python
Alert Check Frequency: Every 5 seconds
API Response Time: < 2 seconds
Deduplication Lookup: < 1 millisecond  
Memory Cleanup: Every monitoring cycle
Alert Delivery: < 5 seconds to Telegram
```

### B. Accuracy Metrics
```python
Power Tier Calibration: Weekly adjustment
False Positive Rate: Target < 5%
False Negative Rate: Target < 2%
Alert Relevance Score: Target > 8.0/10
```

### C. System Limits
```python
Max Concurrent Games: 50
Max Alerts per Game: 100
Max Memory per Game: 10MB
Alert Retention: 24 hours
Dedup Tracking: 1-10 minutes per type
```

This comprehensive formula reference ensures precise and consistent alert generation across all scenarios in the MLB monitoring system.