# MLB Alert Tier System - Explained

## What "Tier: None" Means

"Tier: None" was appearing in some alerts when the advanced math engines calculated a home run probability that was too low to qualify for any meaningful tier.

## The Tier System

The advanced math engines calculate precise home run probabilities and classify them into tiers:

### **Tier A** - Elite Power (4.0%+ P(HR))
- Top 5% of all at-bats
- Extremely high probability situations
- Triggers high-confidence alerts

### **Tier B** - Strong Power (2.5%+ P(HR))  
- Top 20% of all at-bats
- Above-average probability situations
- Combined with scoring situations for ROI alerts

### **Tier C** - Above Average (1.5%+ P(HR))
- Above-average probability
- Informational tier

### **None** - Below Average (<1.5% P(HR))
- Low probability situations
- No tier designation needed

## Fix Applied

✅ **Problem**: Some alerts showed "Tier: None" which was confusing
✅ **Solution**: 
- Basic power hitter alerts now hide the tier when it's "None"
- Show clean "P(HR): 2.3%" instead of "P(HR): 2.3% | Tier: None"
- ROI alerts (Tier A/B only) always show tier since they require meaningful tiers

## Alert Behavior Now

### **Power Hitter Alerts**:
- **High probability**: "P(HR): 4.2% | Tier: A" 
- **Low probability**: "P(HR): 1.1%" (no tier shown)

### **ROI Alerts** (Power + Scoring, High-Confidence):
- Always show tier since they only trigger for Tier A or B
- "P(HR): 4.5% | Tier: A" - Elite power with scoring opportunity

The tier system provides sophisticated analysis while keeping alerts clean and informative.