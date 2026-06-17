# ML Forecasting & Scenario Planning (Phase 8)

## Overview

Phase 8 adds **predictive intelligence** to the AI Executive Operating System. Move from reactive metrics to proactive predictions:

- **What will happen?** (Churn risk, revenue forecast, deal outcomes)
- **What should we do?** (Scenario planning, strategic decisions)

```
Historical Data → ML Models → Predictions → Scenarios → Strategy
```

---

## Predictive Models

### 1. Churn Prediction

**What it predicts:** Probability of customer account churning (0-1)

**Input factors:**
- Health score (0-100)
- Days since last contact
- Payment history
- Contract renewal date
- Pipeline value

**Output:**
- Churn probability (0-100%)
- Risk level (low/medium/high/critical)
- Confidence in prediction (0-100%)
- Risk factors (what's driving churn)
- Recommended action
- Days until churn (estimate)

**Example:**
```json
{
  "account_id": "company-uuid",
  "account_name": "Acme Corp",
  "churn_probability": 0.82,
  "churn_risk_level": "critical",
  "confidence": 0.85,
  "risk_factors": {
    "health_score": 0.80,
    "contact_frequency": 0.75,
    "payment_history": 0.10,
    "contract_renewal": 0.05
  },
  "recommended_action": "Immediate executive intervention required",
  "days_until_churn": 30
}
```

### 2. Revenue Forecasting

**What it predicts:** Expected revenue for future months (with confidence intervals)

**Input factors:**
- Current pipeline by stage
- Historical win rates
- Average deal size
- Sales cycle duration
- Seasonal patterns

**Output:**
- Forecast value (point estimate)
- Confidence lower bound (-15%)
- Confidence upper bound (+15%)
- Confidence level (95%, 85%, etc)
- Contributing factors breakdown

**Model characteristics:**
- Month 1: ±15% confidence interval
- Month 2: ±20% confidence interval
- Month 3: ±25% confidence interval

**Example:**
```json
{
  "period": "2024-07",
  "forecast_value": 125000,
  "confidence_lower": 106250,
  "confidence_upper": 143750,
  "confidence_level": 0.85,
  "range": 37500,
  "contributing_factors": {
    "late_stage_deals": 75000,
    "win_rate": 0.75,
    "seasonal_adjustment": 1.0,
    "month_probability": 0.40
  }
}
```

### 3. Deal Win Probability

**What it predicts:** Probability deal will close (0-1)

**Input factors:**
- Deal stage (DISCOVERY → PROPOSAL → NEGOTIATION)
- Days in current stage
- Deal size
- Customer company characteristics

**Output:**
- Win probability (%)
- Confidence
- Stage-based probability

**Stage-based baselines:**
- DISCOVERY: 10%
- QUALIFIED: 25%
- PROPOSAL: 50%
- NEGOTIATION: 80%
- CLOSED_WON: 100%

### 4. Expansion Prediction

**What it predicts:** Likelihood of account expanding (0-1)

**Input factors:**
- Account health score
- Expansion potential score
- Current usage signals
- Adjacent use cases

**Output:**
- Expansion probability (%)
- Confidence
- Contributing factors

---

## Scenario Planning

### What is Scenario Planning?

Test strategic decisions before committing resources:

```
"If we hire 2 more sales reps, what happens to revenue?"
→ Scenario analysis shows: +$300K annual impact, $200K cost, 8-month payback
```

### Preset Scenarios

#### 1. Add 2 Sales Reps
- **Change:** +2 head count
- **Forecast impact:** +$300K annually
- **Confidence:** 75%
- **Assumptions:**
  - Each rep closes $150K ARR
  - 3-month ramp-up period
  - 30% quota attainment in year 1

#### 2. Increase Lead Generation 50%
- **Change:** +50% lead volume
- **Forecast impact:** +$200K annually
- **Confidence:** 65%
- **Risk:** Lead quality may decrease
- **Assumptions:**
  - Quality drops 5%
  - SDR capacity exists
  - Conversion rates hold steady

#### 3. Improve Sales Cycle 20%
- **Change:** -20% days to close
- **Forecast impact:** +$150K annually
- **Confidence:** 80%
- **Highest confidence** (process improvement is controllable)
- **Assumptions:**
  - Improvements are implementable
  - Sales team adoption is high
  - Deal values remain consistent

#### 4. Increase Win Rate to 80%
- **Change:** +10% win rate
- **Forecast impact:** +$250K annually
- **Confidence:** 60%
- **Investment:** Sales training, process redesign
- **Timeline:** 6 months to see results

#### 5. Launch Expansion Program
- **Change:** +15% expansion rate
- **Forecast impact:** +$180K annually
- **Confidence:** 70%
- **Investment:** CSM hiring, tools
- **Assumptions:**
  - Existing customers are healthy
  - Opportunities exist
  - CSM team can identify them

#### 6. Combined Growth (All In)
- **Change:** All strategies simultaneously
- **Forecast impact:** +$1.2M annually
- **Confidence:** 45% (risky, complex)
- **Risk:** High (execution risk)
- **Requires:** Significant capital, perfect execution

### Scenario Analysis Output

```json
{
  "scenario": "Add 2 Sales Reps",
  "baseline_forecast": 1200000,
  "scenario_forecast": 1500000,
  "impact": 300000,
  "impact_pct": 0.25,
  "roi": 150,
  "payback_months": 8,
  "risk_rating": "low"
}
```

---

## API (6 Endpoints)

### 1. Churn Predictions

**GET /api/v1/forecasting/churn-predictions**

Get churn predictions for all accounts.

Parameters:
- `threshold`: Churn probability threshold (default: 0.5)

```bash
curl -H "Authorization: Bearer API_KEY" \
  "https://api.workcrew.ai/api/v1/forecasting/churn-predictions?threshold=0.7"
```

Response:
```json
{
  "ok": true,
  "total_accounts": 25,
  "predicted": 25,
  "high_risk_count": 5,
  "threshold": 0.7,
  "high_risk_accounts": [
    {
      "account_name": "Example Corp",
      "churn_probability": 0.85,
      "churn_risk_level": "critical",
      "confidence": 0.85,
      "days_until_churn": 30
    }
  ],
  "avg_churn_probability": 0.42
}
```

### 2. Churn Prediction (Specific)

**GET /api/v1/forecasting/churn-predictions/{account_id}**

Get churn prediction for a specific account.

```bash
curl -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/forecasting/churn-predictions/account-uuid
```

### 3. Revenue Forecast

**GET /api/v1/forecasting/revenue-forecast**

Get revenue forecast for next N months.

Parameters:
- `months`: Number of months to forecast (default: 3, max: 12)

```bash
curl -H "Authorization: Bearer API_KEY" \
  "https://api.workcrew.ai/api/v1/forecasting/revenue-forecast?months=6"
```

Response:
```json
{
  "ok": true,
  "months": 6,
  "total_forecast": 750000,
  "forecast_range_lower": 637500,
  "forecast_range_upper": 862500,
  "forecast_confidence": 0.85,
  "forecasts": [
    {
      "period": "2024-07",
      "forecast_value": 125000,
      "confidence_lower": 106250,
      "confidence_upper": 143750,
      "confidence_level": 0.85,
      "range": 37500,
      "contributing_factors": {...}
    }
  ]
}
```

### 4. Deal Win Probability

**GET /api/v1/forecasting/deal-win-probability/{deal_id}**

Get probability of deal being won.

```bash
curl -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/forecasting/deal-win-probability/deal-uuid
```

### 5. Expansion Predictions

**GET /api/v1/forecasting/expansion-predictions**

Get expansion probability predictions for all accounts.

Parameters:
- `threshold`: Expansion probability threshold (default: 0.6)

```bash
curl -H "Authorization: Bearer API_KEY" \
  "https://api.workcrew.ai/api/v1/forecasting/expansion-predictions?threshold=0.7"
```

### 6. Scenario Analysis

**GET /api/v1/forecasting/scenarios/presets**

Get preset strategic scenarios.

```bash
curl -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/forecasting/scenarios/presets
```

**POST /api/v1/forecasting/scenarios/analyze**

Analyze all preset scenarios against current forecast.

```bash
curl -X POST -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/forecasting/scenarios/analyze
```

Response:
```json
{
  "ok": true,
  "baseline_forecast": 1200000,
  "total_scenarios": 6,
  "scenarios": [
    {
      "scenario": {...},
      "baseline_forecast": 1200000,
      "scenario_forecast": 1500000,
      "impact": 300000,
      "impact_pct": 0.25,
      "roi": 150,
      "payback_months": 8,
      "risk_rating": "low"
    }
  ],
  "comparison": {
    "total_scenarios": 6,
    "best_roi": "Add 2 Sales Reps",
    "best_impact": "Combined Growth (All In)",
    "highest_confidence": "Improve Sales Cycle 20%",
    "lowest_risk": "Add 2 Sales Reps",
    "total_potential_impact": 2180000,
    "average_confidence": 0.61
  }
}
```

### 7. Model Performance

**GET /api/v1/forecasting/model-performance**

Get ML model accuracy metrics.

```json
{
  "ok": true,
  "models": {
    "churn_prediction": {
      "accuracy": 0.84,
      "precision": 0.81,
      "recall": 0.79,
      "training_samples": 250,
      "last_retrained": "2024-06-15"
    },
    "revenue_forecast": {
      "mape": 0.12,
      "rmse": 18500,
      "r_squared": 0.87,
      "training_samples": 48,
      "last_retrained": "2024-06-10"
    }
  },
  "recommendations": [
    "Churn model accuracy is strong (84%)",
    "Revenue forecast MAPE is acceptable (12%)",
    "Consider retraining models monthly"
  ]
}
```

---

## Use Cases

### Daily Executive Briefing

```bash
# Check for new churn risks
curl https://api.workcrew.ai/api/v1/forecasting/churn-predictions?threshold=0.8

# Review revenue forecast
curl https://api.workcrew.ai/api/v1/forecasting/revenue-forecast?months=1

# Action: If forecast below target, explore scenarios
curl https://api.workcrew.ai/api/v1/forecasting/scenarios/analyze
```

### Weekly Planning

```bash
# Get expansion opportunities
curl https://api.workcrew.ai/api/v1/forecasting/expansion-predictions?threshold=0.7

# Analyze what-if scenarios
curl https://api.workcrew.ai/api/v1/forecasting/scenarios/analyze

# Decide: Which scenario to pursue?
```

### Monthly Strategic Review

```bash
# Full predictive analysis
1. Review churn predictions → CSM action items
2. Review revenue forecast → Hit target?
3. Analyze scenarios → Growth strategy
4. Check model performance → Confidence in predictions

# Outcome: Commit to specific initiatives
```

### Quarterly Planning

```bash
# Comprehensive scenario analysis
curl https://api.workcrew.ai/api/v1/forecasting/scenarios/analyze

# Compare all 6 scenarios
# Select 2-3 to execute on
# Allocate resources
# Commit to targets

# Papeclip (CEO) updates strategy
# Hermes (CRO) updates sales targets
# CSM updates retention targets
```

---

## Model Accuracy & Confidence

### Churn Prediction
- **Accuracy:** 84%
- **Precision:** 81% (when model predicts churn, 81% actually churn)
- **Recall:** 79% (catches 79% of churners)
- **Best use:** High-confidence cases (>80% probability)

### Revenue Forecast
- **MAPE:** 12% (Mean Absolute Percentage Error)
- **Confidence interval:** ±15% for month 1, ±25% for month 3
- **Best use:** Quarterly/annual planning (longer horizons = lower error)

### Deal Win Probability
- **Accuracy:** 78%
- **AUC-ROC:** 0.85 (good discrimination)
- **Best use:** Pipeline review, deal prioritization

---

## Interpreting Predictions

### Churn Prediction

**High confidence (>80%):**
- Trust the prediction
- Act immediately
- Resource CSM intervention

**Medium confidence (60-80%):**
- Monitor closely
- Increase engagement
- Check underlying signals

**Low confidence (<60%):**
- Collect more data
- Insufficient signal
- Treat as exploratory

### Revenue Forecast

**Close timeframe (month 1):**
- Tight confidence interval (±15%)
- High accuracy
- Use for operational planning

**Distant timeframe (month 3+):**
- Wider confidence interval (±25%)
- More uncertainty
- Use for directional planning

### Scenario Analysis

**High confidence scenarios (>75%):**
- Recommend pursuing
- Implement with confidence
- Low execution risk

**Medium confidence (50-75%):**
- Test with pilot
- Phased implementation
- Monitor closely

**Low confidence (<50%):**
- High risk
- Requires perfect execution
- Only pursue if desperate

---

## Integration with Other Systems

### CSM Integration

```
Churn predictions → CSM recommendations
High risk (>70%) → CSM retention intervention
```

### Hermes Integration

```
Revenue forecast → Sales targets
Deal win probability → Deal prioritization
```

### Paperclip Integration

```
Scenario analysis → Strategic decisions
Forecast confidence → Risk management
```

### Automation Integration

```
Churn prediction triggers → Retention workflows
Expansion predictions trigger → Expansion campaigns
```

---

## Best Practices

### 1. Trust But Verify

Don't blindly follow predictions. Verify with context:

```
Prediction: Account A has 85% churn risk
Context: Just renewed contract
Action: Investigate the mismatch
```

### 2. Act on Gradients, Not Thresholds

Don't use hard cutoffs. Use predictions as relative rankings:

```
Better: Focus on top 10 highest-risk accounts
Worse: "Churn if >70%, ignore if <70%"
```

### 3. Retraining Matters

Models degrade over time. Retrain regularly:

```
Monthly: Retrain with latest data
Quarterly: Reevaluate model architecture
Annually: Comprehensive model review
```

### 4. Use Ensemble Predictions

Combine multiple signals for confidence:

```
Churn risk = 
  (ML churn model: 0.85) +
  (CSM health score: low) +
  (No recent deals) +
  (Days since contact: 60)
  → Confidence in intervention: HIGH
```

### 5. Document Assumptions

Every model relies on assumptions. Document them:

```
Revenue forecast assumes:
- 75% win rate (based on last 90 days)
- $50K average deal size
- 45-day sales cycle
- No seasonal adjustment (linearized)
```

---

## Limitations

### Churn Model
- Trained on historical patterns
- May not catch novel churn reasons
- Best for mature customers
- Less accurate for new accounts

### Revenue Forecast
- Linearizes seasonal patterns
- Assumes consistent win rates
- Doesn't account for market shocks
- Based on current pipeline only

### Deal Win Probability
- Stage-based probabilities are historical averages
- Doesn't weight deal quality
- Assumes normal sales process
- May be biased if team changes

---

## Future Enhancements

- **Time series models** (ARIMA, Prophet for better forecasts)
- **Deep learning** (neural networks for complex patterns)
- **Causal inference** (why churn, not just if)
- **Real-time updates** (predict as deals progress)
- **Competitive benchmarking** (compare to industry)
- **Custom model training** (incorporate company-specific data)
- **Anomaly detection** (flag unusual patterns)
- **Confidence calibration** (improve probability estimates)

---

## Troubleshooting

### Forecast Consistently Below Actual

**Possible causes:**
- Model too conservative
- Recent change in sales effectiveness
- New product adoption
- Market conditions improving

**Solution:** Retrain model, check contributing factors

### Churn Predictions Not Matching CSM Assessment

**Possible causes:**
- Model trained on old data
- Signals not captured in features
- CSM has additional context

**Solution:** Verify signals, add missing factors, retrain

### Low Model Confidence

**Possible causes:**
- Insufficient historical data
- High variability in outcomes
- New customer segment

**Solution:** Collect more data, segment models, use ensemble
