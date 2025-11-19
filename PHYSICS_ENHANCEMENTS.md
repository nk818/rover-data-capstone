# Physics-Based Falsification Detection Enhancements

## Overview

The detection system has been enhanced to account for real-world physics including deceleration, momentum, friction, wind resistance, and external forces. This significantly reduces false positives while maintaining high detection accuracy.

## Key Improvements

### 1. **Deceleration Modeling**

**Problem**: When a velocity command goes to zero, the robot doesn't instantly stop. It decelerates due to:
- Friction (rolling resistance)
- Momentum/inertia
- Wind resistance
- Mechanical braking

**Solution**: The system now uses an exponential deceleration model:
```
v(t) = v₀ × exp(-t/τ)
```
Where:
- `v₀` = initial velocity
- `t` = time since command went to zero
- `τ` = deceleration time constant (typically 0.5 seconds)

**Impact**: The system now distinguishes between:
- ✅ **Expected deceleration**: Robot slowing down naturally after command stops
- 🚨 **Falsified data**: Robot moving when it should have stopped long ago

### 2. **Momentum and Inertia**

**Problem**: Heavy robots (like Husky, ~50kg) have significant momentum. Even after commands stop, they continue moving.

**Solution**: The system tracks velocity history and calculates expected velocity based on:
- Previous velocity
- Time elapsed
- Robot mass
- Friction coefficient

**Example**:
- Command goes to zero at velocity 1.0 m/s
- After 0.5 seconds, expected velocity: ~0.6 m/s (normal deceleration)
- If actual velocity is 1.0 m/s after 0.5 seconds → **SUSPICIOUS**

### 3. **External Forces Detection**

**Problem**: External forces (wind, slopes, pushing) can cause movement without commands.

**Solution**: The system estimates external forces using:
```
F_external = m × (a_actual - a_expected)
```

**Handling**:
- **Moderate forces** (< 20N): Likely wind/slope → Lower confidence flag
- **Large forces** (> 20N): Unlikely natural → Higher confidence flag
- **No external forces**: Movement is suspicious → High confidence flag

### 4. **Friction and Wind Resistance**

**Modeled Forces**:
1. **Friction**: `F_friction = μ × m × g`
   - μ = friction coefficient (0.3 for typical terrain)
   - Accounts for rolling resistance

2. **Wind Resistance**: `F_wind = k × v²`
   - k = wind resistance coefficient
   - Proportional to velocity squared

**Impact**: More accurate velocity predictions, especially at higher speeds.

### 5. **Acceleration Direction Validation**

**Problem**: When command is zero, we expect **deceleration** (negative acceleration), not acceleration.

**Solution**: The system checks:
- ✅ **Negative acceleration** (deceleration): Expected when stopping
- 🚨 **Positive acceleration**: Suspicious when command is zero
- ⚠️ **Excessive deceleration**: Might indicate external force (wind, slope)

## Configuration Parameters

### Physics Model Parameters

```python
PhysicsModel(
    mass=50.0,                      # Robot mass (kg)
    friction_coefficient=0.3,        # Rolling friction
    max_deceleration=2.0,            # Maximum expected deceleration (m/s²)
    deceleration_time_constant=0.5,  # Time constant for exponential decay (s)
    wind_resistance_coefficient=0.1  # Wind resistance factor
)
```

### Tuning for Your Robot

**Lightweight robots** (< 20kg):
- Lower `mass`
- Lower `friction_coefficient` (0.2)
- Faster `deceleration_time_constant` (0.3)

**Heavy robots** (> 100kg):
- Higher `mass`
- Higher `friction_coefficient` (0.4)
- Slower `deceleration_time_constant` (0.7)

**High-speed robots**:
- Higher `wind_resistance_coefficient` (0.15)
- Adjust `max_deceleration` based on braking capability

## Detection Logic Flow

### When Command is Zero:

1. **Check if movement is expected**:
   - Calculate expected velocity from deceleration model
   - Compare with actual velocity
   - If within tolerance → Normal deceleration
   - If significantly higher → Suspicious

2. **Check acceleration direction**:
   - Negative (deceleration) → Expected
   - Positive (acceleration) → Suspicious
   - Check for external forces

3. **Check wheel rotation**:
   - Wheels may still rotate due to momentum
   - Compare with expected deceleration
   - Flag only if significantly higher than expected

### When Command is Non-Zero:

1. **Check acceleration toward command**:
   - Robot should accelerate/decelerate toward commanded velocity
   - Allow reasonable time for response

2. **Check for external forces**:
   - Large discrepancies might indicate external forces
   - Distinguish from falsification

## Example Scenarios

### Scenario 1: Normal Stopping
```
Time: 0.0s  Command: 1.0 m/s  Actual: 1.0 m/s  → Normal
Time: 0.1s  Command: 0.0 m/s  Actual: 0.9 m/s  → Expected deceleration
Time: 0.2s  Command: 0.0 m/s  Actual: 0.7 m/s  → Expected deceleration
Time: 0.5s  Command: 0.0 m/s  Actual: 0.4 m/s  → Expected deceleration
```
**Result**: ✅ No falsification detected

### Scenario 2: Falsified Data
```
Time: 0.0s  Command: 1.0 m/s  Actual: 1.0 m/s  → Normal
Time: 0.1s  Command: 0.0 m/s  Actual: 1.0 m/s  → Suspicious (should be decelerating)
Time: 0.2s  Command: 0.0 m/s  Actual: 1.0 m/s  → Suspicious
Time: 0.5s  Command: 0.0 m/s  Actual: 1.0 m/s  → FALSIFIED
```
**Result**: 🚨 Falsification detected (90% confidence)

### Scenario 3: External Force (Wind)
```
Time: 0.0s  Command: 0.0 m/s  Actual: 0.0 m/s  → Normal
Time: 0.1s  Command: 0.0 m/s  Actual: 0.1 m/s  → External force detected
Time: 0.2s  Command: 0.0 m/s  Actual: 0.1 m/s  → Moderate force (< 20N)
```
**Result**: ⚠️ Low confidence flag (60%) - likely external force

## Benefits

1. **Reduced False Positives**: 
   - Distinguishes natural deceleration from falsification
   - Accounts for momentum and external forces

2. **Higher Accuracy**:
   - Physics-based validation improves detection confidence
   - Better understanding of expected vs. actual behavior

3. **More Realistic**:
   - Models real-world robot dynamics
   - Accounts for environmental factors

4. **Configurable**:
   - Adjustable parameters for different robot types
   - Can be tuned for specific environments

## Disabling Physics Validation

If you want to use the simpler detection (without physics):

```python
detector = FalsificationDetector(enable_physics=False)
```

This reverts to the original simple checks without deceleration modeling.

## Future Enhancements

Potential improvements:
- Machine learning models trained on physics data
- Terrain-specific friction coefficients
- Dynamic mass estimation
- Integration with IMU for better force estimation
- Slope detection from IMU orientation
- Wind speed estimation from multiple sensors

