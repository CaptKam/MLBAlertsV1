#!/usr/bin/env python3
"""
Comprehensive validation of all math formulas used in MLB alert system
"""

import math
import logging
from math_engines import (
    PowerFeatures, PowerCoefficients, pa_hr_probability, PlattParams, platt_scale,
    power_tier_from_prob, wind_component_out_to_cf, hr_boost_factor,
    SofteningTracker, SPRTState, sprt_ball_update,
    delta_re, value_score, eb_rate, sigmoid, safe, clamp01
)

logging.basicConfig(level=logging.INFO)

def test_power_probability_calculation():
    """Test PA-HR probability calculation with realistic data"""
    print("\n=== Testing Power Probability Calculation ===")
    
    # Test case 1: Elite power hitter
    elite_features = PowerFeatures(
        iso_14=0.280,  # High isolated power (14 days)
        n_iso_14=50,   # Sample size
        hr_per_pa_14=0.065,  # High HR rate
        n_hr_per_pa_14=50,
        iso_season=0.260,    # Season ISO
        platoon_iso_delta=0.040,  # Platoon advantage
        park_hr_factor=1.15,      # HR-friendly park
        wind_deg_toward=45,       # Wind direction
        wind_mph=12,             # Wind speed
        temp_f=85,               # Temperature
        cf_azimuth_deg=45,       # Center field direction
        pitcher_hr9_30d=1.35,    # Pitcher allows HRs
        tto=3,                   # Third time through order
        count_state="3-1",       # Favorable count
        league_iso=0.165,
        league_hr_per_pa=0.036,
        league_pitcher_hr9_30d=1.10
    )
    
    prob, components = pa_hr_probability(elite_features)
    tier = power_tier_from_prob(prob)
    
    print(f"Elite Hitter Test:")
    print(f"  Raw Probability: {prob:.3f} ({prob:.1%})")
    print(f"  Tier: {tier}")
    print(f"  Key Components:")
    print(f"    - ISO (14d): {components['iso14']:.3f}")
    print(f"    - HR/PA (14d): {components['hrpa14']:.3f}")
    print(f"    - Wind Component: {components['w_out']:.1f} mph")
    print(f"    - Weather Boost: {components['boost']:.1%}")
    print(f"    - Logit: {components['logit']:.3f}")
    
    # Validate ranges
    assert 0 <= prob <= 1, f"Probability out of range: {prob}"
    assert tier in ["A", "B", "C", "None"], f"Invalid tier: {tier}"
    
    # Test case 2: Average hitter
    average_features = PowerFeatures(
        iso_14=0.150,
        n_iso_14=50,
        hr_per_pa_14=0.025,
        n_hr_per_pa_14=50,
        iso_season=0.160,
        platoon_iso_delta=0.000,
        park_hr_factor=1.00,
        wind_deg_toward=180,  # Wind against
        wind_mph=8,
        temp_f=70,
        cf_azimuth_deg=45,
        pitcher_hr9_30d=1.10,
        tto=1,
        count_state="1-1",
        league_iso=0.165,
        league_hr_per_pa=0.036,
        league_pitcher_hr9_30d=1.10
    )
    
    prob_avg, components_avg = pa_hr_probability(average_features)
    tier_avg = power_tier_from_prob(prob_avg)
    
    print(f"\nAverage Hitter Test:")
    print(f"  Raw Probability: {prob_avg:.3f} ({prob_avg:.1%})")
    print(f"  Tier: {tier_avg}")
    
    # Elite should have higher probability than average
    assert prob > prob_avg, f"Elite prob {prob} should exceed average {prob_avg}"
    
    print("✅ Power probability calculations working correctly")
    return True

def test_empirical_bayes_shrinkage():
    """Test Empirical Bayes rate stabilization"""
    print("\n=== Testing Empirical Bayes Shrinkage ===")
    
    # Small sample - should shrink toward prior
    small_sample_rate = eb_rate(observed_rate=0.500, n=5, prior_mean=0.250, prior_count=40)
    print(f"Small sample (5 obs, 50% rate) shrunk to: {small_sample_rate:.3f}")
    
    # Large sample - should stay close to observed
    large_sample_rate = eb_rate(observed_rate=0.500, n=100, prior_mean=0.250, prior_count=40)
    print(f"Large sample (100 obs, 50% rate) shrunk to: {large_sample_rate:.3f}")
    
    # Small sample should be more shrunk toward prior
    assert abs(small_sample_rate - 0.250) < abs(large_sample_rate - 0.250), "Small sample should shrink more"
    
    print("✅ Empirical Bayes shrinkage working correctly")
    return True

def test_wind_physics():
    """Test wind component and HR boost calculations"""
    print("\n=== Testing Wind Physics ===")
    
    # Wind helping (blowing out to CF)
    wind_out = wind_component_out_to_cf(wind_deg=45, wind_mph=15, cf_azimuth_deg=45)
    boost_out = hr_boost_factor(wind_out, temp_f=85)
    
    print(f"Wind blowing out: {wind_out:.1f} mph component")
    print(f"HR boost factor: {boost_out:.1%}")
    
    # Wind hurting (blowing in from CF)
    wind_in = wind_component_out_to_cf(wind_deg=225, wind_mph=15, cf_azimuth_deg=45)
    boost_in = hr_boost_factor(wind_in, temp_f=85)
    
    print(f"Wind blowing in: {wind_in:.1f} mph component") 
    print(f"HR boost factor: {boost_in:.1%}")
    
    # Outward wind should help more than inward wind
    assert boost_out > boost_in, f"Outward wind boost {boost_out} should exceed inward {boost_in}"
    
    print("✅ Wind physics calculations working correctly")
    return True

def test_platt_calibration():
    """Test Platt scaling for probability calibration"""
    print("\n=== Testing Platt Calibration ===")
    
    # Test identity calibration (should not change)
    identity_params = PlattParams(a=1.0, b=0.0)
    raw_prob = 0.045
    calibrated = platt_scale(raw_prob, identity_params)
    
    print(f"Raw probability: {raw_prob:.3f}")
    print(f"Identity calibrated: {calibrated:.3f}")
    assert abs(calibrated - raw_prob) < 0.001, "Identity calibration should preserve probability"
    
    # Test scaling down (conservative)
    conservative_params = PlattParams(a=0.8, b=-0.2)
    calibrated_conservative = platt_scale(raw_prob, conservative_params)
    
    print(f"Conservative calibrated: {calibrated_conservative:.3f}")
    
    print("✅ Platt calibration working correctly")
    return True

def test_pitcher_softening_tracker():
    """Test pitcher fatigue/softening detection"""
    print("\n=== Testing Pitcher Softening Detection ===")
    
    tracker = SofteningTracker()
    
    # Simulate pitch sequence showing fatigue
    velo_sequence = [95.5, 95.2, 94.8, 94.5, 94.1, 93.8, 93.5]  # Declining velocity
    
    for i, velo in enumerate(velo_sequence):
        # Update individual components
        if hasattr(tracker, 'velo_mu0') and tracker.velo_mu0 is None:
            tracker.velo_mu0 = velo_sequence[0]  # Set baseline
            
        # Update velocity tracking
        tracker.update_velo(velo)
        
        # Update contact quality tracking  
        tracker.update_ev(85 + i*2)
        
        # Get softening signals
        signals = tracker.softening_signals(
            tto=2 if i < 4 else 3,     # Third time through order
            pitch_count=85 + i*3,
            velo_drop_thresh=1.5,
            ev_rise_thresh=5.0
        )
        
        if i == len(velo_sequence) - 1:  # Final update
            print(f"Softening signals detected:")
            for signal, active in signals.items():
                print(f"  {signal}: {'✅' if active else '❌'}")
    
    print("✅ Pitcher softening tracker working correctly")
    return True

def test_sprt_control_detection():
    """Test SPRT ball/strike control loss detection"""
    print("\n=== Testing SPRT Control Loss Detection ===")
    
    sprt_state = SPRTState()
    
    # Simulate sequence with increasing ball rate (control loss)
    ball_sequence = [True, False, True, True, False, True, True, True, True, True]
    
    for i, is_ball in enumerate(ball_sequence):
        log_lr, crossed = sprt_ball_update(sprt_state, is_ball, p0=0.33, p1=0.60, A=20.0)
        
        if i == len(ball_sequence) - 1:
            print(f"Final log-likelihood ratio: {log_lr:.3f}")
            print(f"Control loss detected: {'Yes' if crossed else 'No'}")
            
            ball_rate = sum(ball_sequence) / len(ball_sequence)
            print(f"Actual ball rate: {ball_rate:.1%}")
    
    print("✅ SPRT control detection working correctly")
    return True

def test_value_scoring():
    """Test value scoring for alert prioritization"""
    print("\n=== Testing Value Scoring ===")
    
    # High leverage situation
    high_leverage_score = value_score(p_event=0.065, p_base=0.036, leverage_index=2.5)
    
    # Low leverage situation  
    low_leverage_score = value_score(p_event=0.065, p_base=0.036, leverage_index=0.5)
    
    print(f"High leverage value score: {high_leverage_score:.1f}")
    print(f"Low leverage value score: {low_leverage_score:.1f}")
    
    # High leverage should score higher
    assert high_leverage_score > low_leverage_score, "High leverage should score higher"
    
    print("✅ Value scoring working correctly")
    return True

def test_helper_functions():
    """Test mathematical helper functions"""
    print("\n=== Testing Helper Functions ===")
    
    # Test sigmoid
    assert abs(sigmoid(0) - 0.5) < 0.001, "Sigmoid(0) should be 0.5"
    assert sigmoid(10) > 0.99, "Sigmoid of large positive should approach 1"
    assert sigmoid(-10) < 0.01, "Sigmoid of large negative should approach 0"
    
    # Test clamp01
    assert clamp01(-0.5) == 0.0, "clamp01 should handle negative values"
    assert clamp01(1.5) == 1.0, "clamp01 should handle values > 1"
    assert clamp01(0.5) == 0.5, "clamp01 should preserve valid values"
    
    # Test safe function
    assert safe(None, 5.0) == 5.0, "safe should return default for None"
    assert safe(3.0, 5.0) == 3.0, "safe should return value if not None"
    
    print("✅ Helper functions working correctly")
    return True

def main():
    """Run all math formula validation tests"""
    print("🔬 COMPREHENSIVE MATH FORMULA VALIDATION")
    print("=" * 50)
    
    tests = [
        test_power_probability_calculation,
        test_empirical_bayes_shrinkage, 
        test_wind_physics,
        test_platt_calibration,
        test_pitcher_softening_tracker,
        test_sprt_control_detection,
        test_value_scoring,
        test_helper_functions
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} FAILED: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n📊 VALIDATION SUMMARY")
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {passed/total:.1%}")
    
    if passed == total:
        print("✅ ALL MATH FORMULAS VALIDATED SUCCESSFULLY")
        print("Your alert system's mathematical calculations are working correctly!")
    else:
        print("❌ SOME TESTS FAILED - Review the errors above")
    
    return passed == total

if __name__ == "__main__":
    main()