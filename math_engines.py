# math_engines.py
# Drop-in math engines for MLB Live Game Monitor
# - No external deps beyond stdlib

from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import math
import time

# ==============================
# 0) Small utilities
# ==============================
def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

def safe(v, default):
    return default if v is None else v

def sigmoid(z: float) -> float:
    # numerically stable sigmoid
    if z >= 0:
        ez = math.exp(-z)
        return 1.0 / (1.0 + ez)
    ez = math.exp(z)
    return ez / (1.0 + ez)

# ==============================
# 1) Empirical-Bayes shrinkage
# ==============================
def eb_rate(observed_rate: Optional[float], n: Optional[int], prior_mean: float, prior_count: int) -> float:
    """Stabilize noisy rates: (n*r + n0*m)/(n+n0)"""
    if observed_rate is None or n is None or n <= 0:
        return prior_mean
    return (n * observed_rate + prior_count * prior_mean) / (n + prior_count)

# ==============================
# 2) Weather → wind toward CF + HRBoost
# ==============================
# NOTE: wind_deg is "direction wind is blowing TOWARD" in standard met format after correction.
def wind_component_out_to_cf(wind_deg: Optional[float], wind_mph: Optional[float], cf_azimuth_deg: Optional[float]) -> float:
    if wind_deg is None or wind_mph is None or cf_azimuth_deg is None:
        return 0.0
    theta = math.radians((wind_deg - cf_azimuth_deg) % 360.0)
    return wind_mph * math.cos(theta)  # positive = out to CF

def hr_boost_factor(w_out_cf: float, temp_f: Optional[float]) -> float:
    # Simple physics-inspired lift factor -> multiplicative on odds
    t_term = 0.0 if temp_f is None else 0.012 * ((temp_f - 70.0) / 10.0)
    w_term = 0.018 * w_out_cf
    return max(0.85, 1.0 + w_term + t_term)  # clamp floor to avoid madness on cold/wind in

# ==============================
# 3) Logistic PA-HR model (explainable & fast)
# ==============================
@dataclass
class PowerFeatures:
    iso_14: Optional[float] = None
    hr_per_pa_14: Optional[float] = None
    iso_season: Optional[float] = None
    platoon_iso_delta: Optional[float] = None
    park_hr_factor: Optional[float] = None  # ~1.00 neutral
    wind_deg_toward: Optional[float] = None
    wind_mph: Optional[float] = None
    cf_azimuth_deg: Optional[float] = None
    temp_f: Optional[float] = None
    pitcher_hr9_30d: Optional[float] = None
    tto: Optional[int] = None                   # 1/2/3+
    count_state: Optional[str] = None          # "neutral","2-0","3-1","3-0", etc.
    # Optional sample sizes for EB shrinkage
    n_iso_14: Optional[int] = None
    n_hr_per_pa_14: Optional[int] = None
    # League priors
    league_iso: float = 0.165
    league_hr_per_pa: float = 0.036
    league_pitcher_hr9_30d: float = 1.10

@dataclass
class PowerCoefficients:
    beta0: float = -6.4
    b_iso14: float = 3.0
    b_hrpa14: float = 4.0
    b_isoszn: float = 1.2
    b_platoon: float = 2.1
    b_park: float = 0.9
    b_wind: float = 0.08      # applied to wind component in mph
    b_temp: float = 0.35      # applied to ((T-70)/20)
    b_pHR9_30d: float = 0.5   # higher HR/9 → more HR risk
    b_tto: float = 0.25       # 3rd time through ↑
    # Count bumps
    b_count_20: float = 0.35
    b_count_31: float = 0.42
    b_count_30: float = 0.20  # auto-take/pressure

COUNT_BUMPS = {"2-0":"b_count_20", "3-1":"b_count_31", "3-0":"b_count_30"}

def pa_hr_probability(feat: PowerFeatures, coef: PowerCoefficients = PowerCoefficients()) -> Tuple[float, Dict[str, float]]:
    """Return (probability of HR this PA, components)"""
    # EB shrink: stabilize recent noisy samples
    iso14 = eb_rate(feat.iso_14, feat.n_iso_14, feat.league_iso, 40)
    hrpa14 = eb_rate(feat.hr_per_pa_14, feat.n_hr_per_pa_14, feat.league_hr_per_pa, 60)

    # Features with safe defaults
    iso_szn = safe(feat.iso_season, feat.league_iso)
    platoon = safe(feat.platoon_iso_delta, 0.0)
    park = safe(feat.park_hr_factor, 1.0)
    w_out = wind_component_out_to_cf(feat.wind_deg_toward, feat.wind_mph, feat.cf_azimuth_deg)
    temp_term = 0.0 if feat.temp_f is None else ((feat.temp_f - 70.0) / 20.0)
    p_hr9 = safe(feat.pitcher_hr9_30d, feat.league_pitcher_hr9_30d)
    tto3 = 1.0 if safe(feat.tto, 1) >= 3 else 0.0

    # Linear logit
    z = (coef.beta0
         + coef.b_iso14 * iso14
         + coef.b_hrpa14 * hrpa14
         + coef.b_isoszn * iso_szn
         + coef.b_platoon * platoon
         + coef.b_park * (park - 1.0)  # center at 1.00
         + coef.b_wind * w_out
         + coef.b_temp * temp_term
         + coef.b_pHR9_30d * (p_hr9 - 1.10)  # center around ~1.10
         + coef.b_tto * tto3)

    # Count bump
    if feat.count_state in COUNT_BUMPS:
        z += getattr(coef, COUNT_BUMPS[feat.count_state])

    # Weather boost as multiplicative on odds → additive on logit
    boost = hr_boost_factor(w_out, feat.temp_f)
    z += math.log(boost)

    p = sigmoid(z)

    parts = {
        "iso14": iso14, "hrpa14": hrpa14, "iso_szn": iso_szn, "platoon": platoon,
        "park": park, "w_out": w_out, "temp_term": temp_term, "p_hr9_30d": p_hr9,
        "tto3": tto3, "boost": boost, "logit": z, "p": p
    }
    return p, parts

# Optional 1-D Platt scaling (weekly; keep params in config)
@dataclass
class PlattParams:
    a: float = 1.0
    b: float = 0.0
def platt_scale(p_raw: float, params: PlattParams) -> float:
    # Maps raw p into calibrated space via logistic on logit(p)
    # guard p_raw in (0,1)
    eps = 1e-6
    p = min(max(p_raw, eps), 1 - eps)
    logit = math.log(p/(1-p))
    return clamp01(sigmoid(params.a * logit + params.b))

# ==============================
# 4) Run Expectancy & Leverage
# ==============================
# Provide RE table externally; we include helpers.
def delta_re(re_table: Dict[str, float], pre_key: str, post_key: str) -> float:
    return re_table.get(post_key, 0.0) - re_table.get(pre_key, 0.0)

def value_score(p_event: float, p_base: float = 0.036, leverage_index: float = 1.0) -> float:
    return 100.0 * max(0.0, p_event - p_base) * max(0.1, leverage_index)

# ==============================
# 5) EWMA & CUSUM for Softening
# ==============================
@dataclass
class EWMAState:
    value: Optional[float] = None
def ewma_update(state: EWMAState, x: float, alpha: float = 0.3) -> float:
    if state.value is None:
        state.value = x
    else:
        state.value = alpha * x + (1 - alpha) * state.value
    return state.value

@dataclass
class CUSUMState:
    c: float = 0.0
def cusum_update(state: CUSUMState, x: float, mu0: float, sigma: float, k: float = 0.5) -> Tuple[float, bool]:
    # one-sided (increase) detector
    state.c = max(0.0, state.c + (x - mu0 - k * sigma))
    return state.c, (state.c >= 3.0 * sigma)

@dataclass
class SofteningTracker:
    velo0: Optional[float] = None
    velo_ewma: Optional[EWMAState] = None
    ev_ewma: Optional[EWMAState] = None
    cusum_ev: Optional[CUSUMState] = None
    ev_mu0: Optional[float] = None
    ev_sigma0: Optional[float] = None
    
    def __post_init__(self):
        if self.velo_ewma is None:
            self.velo_ewma = EWMAState()
        if self.ev_ewma is None:
            self.ev_ewma = EWMAState()
        if self.cusum_ev is None:
            self.cusum_ev = CUSUMState()

    def update_velo(self, current_velo: float):
        if self.velo0 is None:
            self.velo0 = current_velo
        if self.velo_ewma is None:
            self.velo_ewma = EWMAState()
        return ewma_update(self.velo_ewma, current_velo, alpha=0.3)

    def update_ev(self, current_ev: float):
        # init baseline from first inning: caller should set ev_mu0/ev_sigma0 at inning 1 end
        if self.ev_ewma is None:
            self.ev_ewma = EWMAState()
        if self.cusum_ev is None:
            self.cusum_ev = CUSUMState()
        
        if self.ev_mu0 is None or self.ev_sigma0 is None:
            return ewma_update(self.ev_ewma, current_ev, alpha=0.3), False
        ev_mean = ewma_update(self.ev_ewma, current_ev, alpha=0.3)
        c, breach = cusum_update(self.cusum_ev, current_ev, self.ev_mu0, max(1.0, self.ev_sigma0), k=0.5)
        return ev_mean, breach

    def softening_signals(self, tto: int, pitch_count: int, velo_drop_thresh: float = 1.0, ev_rise_thresh: float = 1.5) -> Dict[str, bool]:
        velo_drop = False
        if self.velo0 is not None and self.velo_ewma is not None and self.velo_ewma.value is not None:
            velo_drop = (self.velo0 - self.velo_ewma.value) >= velo_drop_thresh
        
        contact_rise = False
        if self.ev_ewma is not None and self.ev_ewma.value is not None and self.ev_mu0 is not None:
            contact_rise = (self.ev_ewma.value - self.ev_mu0) >= ev_rise_thresh
        
        signals = {
            "TTO≥3": (tto >= 3),
            "Velo↓≥1.0": velo_drop,
            "Contact↑": contact_rise,
            "PitchCount≥90": (pitch_count >= 90)
        }
        return signals

# ==============================
# 6) SPRT for ball/strike control loss
# ==============================
@dataclass
class SPRTState:
    log_lr: float = 0.0
def sprt_ball_update(state: SPRTState, is_ball: bool, p0: float = 0.33, p1: float = 0.60, A: float = 20.0) -> Tuple[float, bool]:
    # returns (log_lr, crossed)
    inc = math.log((p1 if is_ball else (1 - p1)) / (p0 if is_ball else (1 - p0)))
    state.log_lr += inc
    return state.log_lr, (state.log_lr >= math.log(A))

# ==============================
# 7) Tiering helpers for your existing alerts
# ==============================
def power_tier_from_prob(p: float, league_pa_hr: float = 0.036) -> str:
    # Map to your Tier labels without changing alert names
    # Realistic thresholds based on actual MLB P(HR) rates
    if p >= 0.040:  # 4.0% or higher - Elite power (top 5%)
        return "A"
    if p >= 0.025:  # 2.5% or higher - Strong power (top 20%)
        return "B"
    if p >= 0.015:  # 1.5% or higher - Above average power
        return "C"
    return "None"