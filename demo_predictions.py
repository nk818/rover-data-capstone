#!/usr/bin/env python3
"""
Demonstration of Predictive Model with Sample Inputs
Shows predictions, bounds, and anomaly detection
"""

import pandas as pd
import numpy as np
from predictive_model import PredictiveDetector
from falsification_detector import FalsificationDetector
import warnings
warnings.filterwarnings('ignore')

def create_sample_data_window(base_value, trend=0, noise=0.01, window_size=10):
    """Create a sample data window for testing"""
    times = np.linspace(0, 2.0, window_size)
    values = base_value + trend * times + np.random.normal(0, noise, window_size)
    
    df = pd.DataFrame({
        'Time': times,
        'linear.x': values,
        'angular.z': np.zeros(window_size)
    })
    return df

def create_odom_window(base_value, trend=0, noise=0.005, window_size=10):
    """Create sample odometry data window"""
    times = np.linspace(0, 2.0, window_size)
    values = base_value + trend * times + np.random.normal(0, noise, window_size)
    
    df = pd.DataFrame({
        'Time': times,
        'twist.twist.linear.x': values,
        'twist.twist.linear.y': np.zeros(window_size),
        'twist.twist.linear.z': np.zeros(window_size)
    })
    return df

def create_imu_window(base_value, noise=0.1, window_size=10):
    """Create sample IMU data window"""
    times = np.linspace(0, 2.0, window_size)
    values = base_value + np.random.normal(0, noise, window_size)
    
    df = pd.DataFrame({
        'Time': times,
        'linear_acceleration.x': values,
        'linear_acceleration.y': np.random.normal(0, 0.05, window_size),
        'linear_acceleration.z': np.random.normal(9.8, 0.1, window_size)
    })
    return df

def print_prediction_result(sensor_name, col_name, actual_value, result):
    """Print formatted prediction result"""
    print(f"\n{'='*70}")
    print(f"Sensor: {sensor_name}.{col_name}")
    print(f"{'='*70}")
    print(f"Actual Value:     {actual_value:>10.4f}")
    print(f"Predicted Value:  {result['prediction']:>10.4f}")
    print(f"Lower Bound:      {result['lower_bound']:>10.4f}")
    print(f"Upper Bound:      {result['upper_bound']:>10.4f}")
    print(f"Bound Size:       {result['bound_size']:>10.4f}")
    print(f"Deviation:        {result['deviation']:>10.4f}")
    print(f"\n{'─'*70}")
    
    if result['is_anomaly']:
        print(f"🚨 ANOMALY DETECTED")
        print(f"   Confidence: {result['confidence']:.2%}")
        print(f"   Status: Value is OUTSIDE expected bounds")
        if actual_value < result['lower_bound']:
            print(f"   Reason: Value is {abs(actual_value - result['lower_bound']):.4f} below lower bound")
        else:
            print(f"   Reason: Value is {abs(actual_value - result['upper_bound']):.4f} above upper bound")
    else:
        print(f"✅ NORMAL")
        print(f"   Confidence: {result['confidence']:.2%}")
        print(f"   Status: Value is WITHIN expected bounds")
        print(f"   Distance to bounds: {min(abs(actual_value - result['lower_bound']), abs(actual_value - result['upper_bound'])):.4f}")

def main():
    print("="*70)
    print("PREDICTIVE MODEL DEMONSTRATION")
    print("="*70)
    
    # Load data and models
    print("\n[1/3] Loading data and models...")
    detector = FalsificationDetector(enable_predictive=True)
    data = detector.load_data()
    
    if not data:
        print("❌ Failed to load data")
        return
    
    # Initialize predictive model
    predictive = PredictiveDetector(
        window_size=10,
        confidence_level=0.95,
        model_type='random_forest',
        model_dir='models'
    )
    
    if not predictive.load_models():
        print("⚠ No trained models found. Please run falsification_detector.py first.")
        return
    
    print(f"✓ Loaded {len(predictive.models)} trained models")
    
    # Test scenarios
    print("\n[2/3] Testing sample scenarios...")
    print("\n" + "="*70)
    print("SCENARIO 1: Normal Operation - Expected Velocity Command")
    print("="*70)
    
    # Scenario 1: Normal velocity command (0.5 m/s, consistent)
    print("\nContext: Robot moving forward at 0.5 m/s consistently")
    recent_cmd = create_sample_data_window(0.5, trend=0, noise=0.01)
    actual_cmd = 0.48  # Slightly lower but normal
    result1 = predictive.detect_anomaly('cmd_vel', 'linear.x', actual_cmd, recent_cmd)
    print_prediction_result('cmd_vel', 'linear.x', actual_cmd, result1)
    
    print("\n" + "="*70)
    print("SCENARIO 2: Normal Operation - Expected Odometry")
    print("="*70)
    
    # Scenario 2: Normal odometry (matching command)
    print("\nContext: Odometry matches velocity command")
    recent_odom = create_odom_window(0.48, trend=0, noise=0.005)
    actual_odom = 0.47  # Close to command
    result2 = predictive.detect_anomaly('odometry', 'twist.twist.linear.x', actual_odom, recent_odom)
    print_prediction_result('odometry', 'twist.twist.linear.x', actual_odom, result2)
    
    print("\n" + "="*70)
    print("SCENARARIO 3: ANOMALY - Unexpected High Velocity Command")
    print("="*70)
    
    # Scenario 3: Anomaly - sudden high velocity when should be low
    print("\nContext: Robot was moving slowly (0.1 m/s), suddenly jumps to 1.0 m/s")
    recent_cmd_slow = create_sample_data_window(0.1, trend=0, noise=0.01)
    actual_cmd_high = 1.0  # Unexpected jump
    result3 = predictive.detect_anomaly('cmd_vel', 'linear.x', actual_cmd_high, recent_cmd_slow)
    print_prediction_result('cmd_vel', 'linear.x', actual_cmd_high, result3)
    
    print("\n" + "="*70)
    print("SCENARIO 4: ANOMALY - Zero Command But High Odometry")
    print("="*70)
    
    # Scenario 4: Anomaly - zero command but high odometry (falsified data)
    print("\nContext: Command is zero but odometry shows robot moving")
    recent_cmd_zero = create_sample_data_window(0.0, trend=0, noise=0.001)
    recent_odom_high = create_odom_window(0.5, trend=0, noise=0.005)
    actual_odom_high = 0.52  # High velocity when command is zero
    result4 = predictive.detect_anomaly('odometry', 'twist.twist.linear.x', actual_odom_high, recent_odom_high)
    print_prediction_result('odometry', 'twist.twist.linear.x', actual_odom_high, result4)
    
    print("\n" + "="*70)
    print("SCENARIO 5: ANOMALY - Unexpected IMU Acceleration")
    print("="*70)
    
    # Scenario 5: Anomaly - unexpected IMU reading
    print("\nContext: Robot should be stopped but IMU shows high acceleration")
    recent_imu_low = create_imu_window(0.0, noise=0.05)
    actual_imu_high = 2.5  # High acceleration when should be near zero
    result5 = predictive.detect_anomaly('imu', 'linear_acceleration.x', actual_imu_high, recent_imu_low)
    print_prediction_result('imu', 'linear_acceleration.x', actual_imu_high, result5)
    
    print("\n" + "="*70)
    print("SCENARIO 6: Normal Deceleration Pattern")
    print("="*70)
    
    # Scenario 6: Normal deceleration (gradual decrease)
    print("\nContext: Robot gradually slowing down (normal deceleration)")
    recent_cmd_decel = create_sample_data_window(0.5, trend=-0.1, noise=0.01)
    actual_cmd_decel = 0.3  # Continuing to slow down
    result6 = predictive.detect_anomaly('cmd_vel', 'linear.x', actual_cmd_decel, recent_cmd_decel)
    print_prediction_result('cmd_vel', 'linear.x', actual_cmd_decel, result6)
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    scenarios = [
        ("Normal velocity command", result1),
        ("Normal odometry", result2),
        ("Unexpected high velocity", result3),
        ("Zero command but moving", result4),
        ("Unexpected IMU acceleration", result5),
        ("Normal deceleration", result6)
    ]
    
    print(f"\n{'Scenario':<35} {'Status':<10} {'Confidence':<12} {'Deviation':<10}")
    print("-" * 70)
    
    for name, result in scenarios:
        status = "🚨 ANOMALY" if result['is_anomaly'] else "✅ NORMAL"
        conf = f"{result['confidence']:.1%}"
        dev = f"{result['deviation']:.4f}"
        print(f"{name:<35} {status:<10} {conf:<12} {dev:<10}")
    
    anomalies = sum(1 for _, r in scenarios if r['is_anomaly'])
    print(f"\nTotal anomalies detected: {anomalies} out of {len(scenarios)} scenarios")
    
    print("\n" + "="*70)
    print("Demonstration complete!")
    print("="*70)
    
    # Show model statistics
    print("\n[3/3] Model Statistics:")
    print("-" * 70)
    for key, bounds in predictive.bounds.items():
        print(f"\n{key}:")
        print(f"  Mean Error: {bounds['mean_error']:.6f}")
        print(f"  Std Error:  {bounds['std_error']:.6f}")
        print(f"  Bound (±):  {bounds['bound']:.6f}")
        print(f"  Test MAE:   {bounds['test_mae']:.6f}")
        print(f"  Test RMSE:  {bounds['test_rmse']:.6f}")

if __name__ == "__main__":
    main()

