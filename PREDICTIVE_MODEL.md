# Predictive Model for Falsification Detection

## Overview

The predictive model uses machine learning to learn normal behavior patterns from historical data and predicts expected sensor values. It then compares actual values with predictions and flags anomalies when values fall outside confidence bounds.

## How It Works

### 1. **Training Phase**

The model trains on historical data to learn patterns:

1. **Feature Extraction**: For each sensor, creates features from a sliding window:
   - Previous `window_size` values (default: 10)
   - Statistical features: mean, std, min, max, trend
   - Time delta between samples

2. **Model Training**: Uses Random Forest or Gradient Boosting:
   - Trains separate models for each sensor type
   - Predicts next expected value
   - Calculates confidence bounds based on prediction errors

3. **Bound Calculation**: 
   - Uses 95% confidence intervals (z-score)
   - Bounds = prediction ± (z-score × std_residual)

### 2. **Prediction Phase**

For each new sensor reading:

1. **Get Recent Window**: Collects last `window_size` samples
2. **Create Features**: Extracts same features as training
3. **Predict**: Model predicts expected value
4. **Compare**: Checks if actual value is within bounds
5. **Flag Anomaly**: If outside bounds, flags as suspicious

### 3. **Anomaly Detection**

```python
if actual_value < lower_bound or actual_value > upper_bound:
    anomaly_score = deviation / bound_size
    confidence = min(1.0, anomaly_score * 2.0)
```

## Model Performance

Based on training results:

| Sensor | MAE | RMSE | Bound (±) |
|--------|-----|------|-----------|
| cmd_vel.linear.x | 0.0404 | 0.0873 | ±0.1710 |
| odometry.twist.twist.linear.x | 0.0051 | 0.0135 | ±0.0265 |
| imu.linear_acceleration.x | 0.6262 | 1.1596 | ±2.2706 |
| joint_states.velocity_0 | 0.0546 | 0.1371 | ±0.2687 |

**MAE** = Mean Absolute Error (average prediction error)  
**RMSE** = Root Mean Squared Error (penalizes large errors)  
**Bound** = 95% confidence interval

## Advantages

### 1. **Learns Normal Patterns**
- Adapts to specific robot behavior
- Learns from historical data
- No manual threshold tuning needed

### 2. **Context-Aware**
- Considers recent history
- Accounts for trends and patterns
- More accurate than static thresholds

### 3. **Confidence Bounds**
- Statistical confidence intervals
- Adjusts based on prediction uncertainty
- More reliable than fixed thresholds

### 4. **Multi-Sensor**
- Separate models for each sensor
- Cross-validates predictions
- Detects inconsistencies

## Integration with Existing System

The predictive model works alongside:

1. **Physics Model**: Validates deceleration patterns
2. **Cross-Sensor Validation**: Checks sensor consistency
3. **Statistical Analysis**: Identifies outliers

**Combined Approach**:
- Physics model: "Should robot be moving based on physics?"
- Predictive model: "Is this value expected based on history?"
- Cross-validation: "Do sensors agree with each other?"

## Example Detection

### Normal Operation:
```
Time: 1400.0s
Predicted odom velocity: 0.50 m/s
Actual odom velocity: 0.48 m/s
Bounds: [0.47, 0.53]
Result: ✅ Within bounds (normal)
```

### Falsified Data:
```
Time: 1401.0s
Predicted odom velocity: 0.02 m/s (based on recent history)
Actual odom velocity: 0.50 m/s
Bounds: [-0.01, 0.05]
Result: 🚨 Outside bounds (anomaly detected, 100% confidence)
```

## Configuration

### Model Parameters

```python
PredictiveDetector(
    window_size=10,           # Number of previous samples
    confidence_level=0.95,    # 95% confidence bounds
    model_type='random_forest' # or 'gradient_boosting'
)
```

### Tuning Guidelines

**Window Size**:
- **Small (5-10)**: More sensitive to recent changes, faster adaptation
- **Large (20-30)**: More stable, better for long-term patterns

**Confidence Level**:
- **0.90 (90%)**: More sensitive, more false positives
- **0.95 (95%)**: Balanced (recommended)
- **0.99 (99%)**: Less sensitive, fewer false positives

**Model Type**:
- **Random Forest**: Faster training, good for non-linear patterns
- **Gradient Boosting**: More accurate, slower training

## Usage

### Enable Predictive Model

```python
detector = FalsificationDetector(
    enable_predictive=True,  # Enable predictive model
    window_size=10,
    threshold=0.7
)
```

### Disable Predictive Model

```python
detector = FalsificationDetector(
    enable_predictive=False  # Use only physics and cross-validation
)
```

## Limitations & Considerations

### 1. **Training Data Quality**
- Requires sufficient historical data
- Needs representative normal behavior
- May need retraining for different scenarios

### 2. **Adaptation Time**
- Needs `window_size` samples before first prediction
- May have higher false positives initially
- Improves as more data is collected

### 3. **Computational Cost**
- Training takes time (one-time cost)
- Prediction is fast (< 1ms per sensor)
- Memory usage: ~10-50MB per model

### 4. **False Positives**
- Legitimate but unusual behavior may be flagged
- Can be reduced by adjusting confidence level
- Should be combined with other detection methods

## Best Practices

1. **Train on Normal Data**: Use data from normal operations only
2. **Regular Retraining**: Retrain when robot behavior changes
3. **Combine Methods**: Use with physics model and cross-validation
4. **Monitor Performance**: Track false positive/negative rates
5. **Adjust Bounds**: Fine-tune confidence level based on results

## Future Enhancements

Potential improvements:
- **Online Learning**: Update model continuously
- **LSTM/RNN**: Better for time series patterns
- **Ensemble Methods**: Combine multiple models
- **Adaptive Bounds**: Adjust bounds based on uncertainty
- **Anomaly Types**: Classify different types of anomalies

## Comparison with Other Methods

| Method | Pros | Cons |
|--------|------|------|
| **Predictive Model** | Learns patterns, adaptive, context-aware | Needs training data, computational cost |
| **Physics Model** | No training needed, physically accurate | May miss learned behaviors |
| **Static Thresholds** | Simple, fast | Not adaptive, many false positives |
| **Cross-Validation** | Detects inconsistencies | May miss coordinated falsification |

**Recommendation**: Use all methods together for best results!

