#!/usr/bin/env python3
"""
Falsification Detection System for ROS Robot Data
Detects falsified velocity commands by cross-validating multiple sensor sources
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class PhysicsModel:
    """
    Physics model for robot dynamics including deceleration, momentum, and external forces
    """
    
    def __init__(self, 
                 mass: float = 50.0,  # kg (typical Husky robot mass)
                 friction_coefficient: float = 0.3,  # Rolling friction
                 max_deceleration: float = 2.0,  # m/s²
                 deceleration_time_constant: float = 0.5,  # seconds
                 wind_resistance_coefficient: float = 0.1):
        """
        Initialize physics model
        
        Args:
            mass: Robot mass in kg
            friction_coefficient: Rolling friction coefficient
            max_deceleration: Maximum expected deceleration (m/s²)
            deceleration_time_constant: Time constant for exponential deceleration
            wind_resistance_coefficient: Wind resistance factor
        """
        self.mass = mass
        self.friction_coefficient = friction_coefficient
        self.max_deceleration = max_deceleration
        self.deceleration_time_constant = deceleration_time_constant
        self.wind_resistance_coefficient = wind_resistance_coefficient
        self.gravity = 9.81  # m/s²
    
    def calculate_expected_deceleration(self, current_velocity: float, 
                                       time_since_zero_cmd: float) -> float:
        """
        Calculate expected velocity after deceleration
        
        Uses exponential decay model: v(t) = v0 * exp(-t/τ)
        Accounts for friction and wind resistance
        """
        if current_velocity <= 0:
            return 0.0
        
        # Exponential deceleration model
        tau = self.deceleration_time_constant
        expected_velocity = current_velocity * np.exp(-time_since_zero_cmd / tau)
        
        # Account for friction (minimum velocity threshold)
        friction_force = self.friction_coefficient * self.mass * self.gravity
        friction_deceleration = friction_force / self.mass
        
        # Additional deceleration from wind resistance (proportional to velocity²)
        wind_deceleration = self.wind_resistance_coefficient * (current_velocity ** 2)
        total_deceleration = friction_deceleration + wind_deceleration
        
        # Apply additional deceleration
        if time_since_zero_cmd > 0:
            expected_velocity = max(0, expected_velocity - total_deceleration * time_since_zero_cmd)
        
        return max(0, expected_velocity)
    
    def is_valid_deceleration(self, 
                             previous_velocity: float,
                             current_velocity: float,
                             time_delta: float,
                             command_velocity: float) -> Tuple[bool, float]:
        """
        Check if deceleration is physically valid
        
        Returns:
            (is_valid, expected_velocity)
        """
        # If command is non-zero, robot should be accelerating toward command
        if abs(command_velocity) > 0.01:
            # Allow some acceleration/deceleration toward command
            max_change = self.max_deceleration * time_delta
            if abs(current_velocity - previous_velocity) <= max_change:
                return True, current_velocity
            return False, previous_velocity
        
        # If command is zero, check if deceleration is expected
        if abs(previous_velocity) < 0.01:
            # Already stopped, should remain stopped
            return abs(current_velocity) < 0.05, 0.0
        
        # Calculate expected deceleration
        expected_velocity = self.calculate_expected_deceleration(
            abs(previous_velocity), time_delta
        )
        
        # Allow some tolerance (20% of expected velocity or 0.05 m/s, whichever is larger)
        tolerance = max(0.05, expected_velocity * 0.2)
        
        is_valid = abs(current_velocity) <= (expected_velocity + tolerance)
        
        return is_valid, expected_velocity
    
    def calculate_stopping_distance(self, initial_velocity: float) -> float:
        """Calculate expected stopping distance"""
        if initial_velocity <= 0:
            return 0.0
        
        # Using kinematic equation: v² = u² + 2as
        # where v=0, u=initial_velocity, a=-deceleration
        deceleration = self.friction_coefficient * self.gravity
        stopping_distance = (initial_velocity ** 2) / (2 * deceleration)
        
        return stopping_distance
    
    def estimate_external_forces(self, 
                                cmd_velocity: float,
                                actual_velocity: float,
                                imu_acceleration: float) -> Dict:
        """
        Estimate external forces acting on the robot
        
        Returns:
            Dictionary with force estimates
        """
        # Expected acceleration from command
        if abs(cmd_velocity) > 0.01:
            # If accelerating, expected accel should be positive
            expected_accel = cmd_velocity * 2.0  # Rough estimate
        else:
            # If stopping, expected deceleration
            expected_accel = -self.max_deceleration
        
        # Difference indicates external forces
        accel_difference = imu_acceleration - expected_accel
        
        # Estimate external force (F = ma)
        external_force = self.mass * accel_difference
        
        return {
            'external_force': external_force,
            'accel_difference': accel_difference,
            'expected_accel': expected_accel,
            'actual_accel': imu_acceleration,
            'has_external_force': abs(external_force) > 5.0  # > 5N threshold
        }

@dataclass
class DetectionResult:
    """Result of falsification detection"""
    timestamp: float
    is_falsified: bool
    confidence: float
    anomalies: List[str]
    details: Dict

class FalsificationDetector:
    """
    Detects falsified robot data by cross-validating multiple sensor sources
    """
    
    def __init__(self, window_size: int = 10, threshold: float = 0.7,
                 enable_physics: bool = True, enable_predictive: bool = True):
        """
        Initialize detector
        
        Args:
            window_size: Number of recent samples to consider for analysis
            threshold: Confidence threshold for flagging falsified data (0-1)
            enable_physics: Enable physics-based validation (deceleration, momentum, etc.)
            enable_predictive: Enable predictive model for anomaly detection
        """
        self.window_size = window_size
        self.threshold = threshold
        self.enable_physics = enable_physics
        self.enable_predictive = enable_predictive
        self.recent_data = []
        self.stats = {}
        self.physics_model = PhysicsModel() if enable_physics else None
        self.velocity_history = []  # Track velocity over time for deceleration analysis
        
        # Predictive model (lazy initialization)
        self.predictive_model = None
        self.data_cache = {}  # Cache for predictive model
        
    def load_data(self, demo_dir: str = "demo") -> Dict[str, pd.DataFrame]:
        """Load all CSV data files"""
        data = {}
        
        try:
            data['cmd_vel'] = pd.read_csv(f"{demo_dir}/cmd_vel.csv")
            data['odometry'] = pd.read_csv(f"{demo_dir}/odometry-filtered.csv")
            data['imu'] = pd.read_csv(f"{demo_dir}/imu-data.csv")
            data['joint_states'] = pd.read_csv(f"{demo_dir}/joint_states.csv")
            
            # Convert Time column to numeric
            for key in data:
                if 'Time' in data[key].columns:
                    data[key]['Time'] = pd.to_numeric(data[key]['Time'], errors='coerce')
                    data[key] = data[key].dropna(subset=['Time'])
                    data[key] = data[key].sort_values('Time')
            
            print(f"✓ Loaded {len(data)} data files")
            for key, df in data.items():
                print(f"  - {key}: {len(df)} samples")
                
        except Exception as e:
            print(f"⚠ Error loading data: {e}")
            return {}
            
        return data
    
    def calculate_statistics(self, data: Dict[str, pd.DataFrame]):
        """Calculate baseline statistics from historical data"""
        self.stats = {}
        
        # Cache data for predictive model
        if self.enable_predictive:
            self.data_cache = data
        
        if 'cmd_vel' in data:
            cmd = data['cmd_vel']
            self.stats['cmd_vel'] = {
                'linear_x_mean': cmd['linear.x'].abs().mean(),
                'linear_x_std': cmd['linear.x'].abs().std(),
                'angular_z_mean': cmd['angular.z'].abs().mean(),
                'angular_z_std': cmd['angular.z'].abs().std(),
                'non_zero_ratio': (cmd['linear.x'].abs() > 0.01).sum() / len(cmd)
            }
        
        if 'odometry' in data:
            odom = data['odometry']
            # Extract linear velocity from twist.twist.linear.x
            if 'twist.twist.linear.x' in odom.columns:
                self.stats['odometry'] = {
                    'velocity_mean': odom['twist.twist.linear.x'].abs().mean(),
                    'velocity_std': odom['twist.twist.linear.x'].abs().std(),
                }
        
        if 'imu' in data:
            imu = data['imu']
            if 'linear_acceleration.x' in imu.columns:
                self.stats['imu'] = {
                    'accel_x_mean': imu['linear_acceleration.x'].abs().mean(),
                    'accel_x_std': imu['linear_acceleration.x'].abs().std(),
                    'accel_z_mean': imu['linear_acceleration.z'].abs().mean(),
                }
        
        if 'joint_states' in data:
            joints = data['joint_states']
            if 'velocity_0' in joints.columns:
                # Average wheel velocities
                wheel_vels = [joints[f'velocity_{i}'].abs().mean() 
                            for i in range(4) if f'velocity_{i}' in joints.columns]
                if wheel_vels:
                    self.stats['joint_states'] = {
                        'wheel_velocity_mean': np.mean(wheel_vels),
                        'wheel_velocity_std': np.std(wheel_vels),
                    }
        
        print("✓ Calculated baseline statistics")
    
    def synchronize_data(self, data: Dict[str, pd.DataFrame], 
                       timestamp: float, tolerance: float = 0.1) -> Dict:
        """Get synchronized data from all sources at a given timestamp"""
        synced = {}
        
        for key, df in data.items():
            if 'Time' not in df.columns:
                continue
            
            # Find closest timestamp
            idx = (df['Time'] - timestamp).abs().idxmin()
            if abs(df.loc[idx, 'Time'] - timestamp) <= tolerance:
                synced[key] = df.loc[idx].to_dict()
            else:
                synced[key] = None
        
        return synced
    
    def detect_falsification(self, cmd_vel_data: Dict, 
                           odom_data: Optional[Dict] = None,
                           imu_data: Optional[Dict] = None,
                           joint_data: Optional[Dict] = None,
                           timestamp: float = None,
                           previous_result: Optional[DetectionResult] = None) -> DetectionResult:
        """
        Detect falsified data by cross-validating multiple sources
        
        Args:
            cmd_vel_data: Current velocity command data
            odom_data: Current odometry data (optional)
            imu_data: Current IMU data (optional)
            joint_data: Current joint state data (optional)
            timestamp: Current timestamp
        """
        if timestamp is None:
            timestamp = datetime.now().timestamp()
        
        anomalies = []
        confidence_scores = []
        details = {}
        
        # Extract velocities
        linear_x = abs(cmd_vel_data.get('linear.x', 0))
        linear_y = abs(cmd_vel_data.get('linear.y', 0))
        linear_z = abs(cmd_vel_data.get('linear.z', 0))
        angular_x = abs(cmd_vel_data.get('angular.x', 0))
        angular_y = abs(cmd_vel_data.get('angular.y', 0))
        angular_z = abs(cmd_vel_data.get('angular.z', 0))
        
        total_cmd_velocity = linear_x + linear_y + linear_z + angular_x + angular_y + angular_z
        
        # Get actual velocities from sensors
        odom_velocity = 0.0
        if odom_data and 'twist.twist.linear.x' in odom_data:
            odom_velocity = abs(odom_data['twist.twist.linear.x'])
        
        # Track velocity history for deceleration analysis
        if timestamp is not None:
            self.velocity_history.append({
                'timestamp': timestamp,
                'cmd_velocity': total_cmd_velocity,
                'odom_velocity': odom_velocity
            })
            # Keep only recent history
            if len(self.velocity_history) > self.window_size * 2:
                self.velocity_history.pop(0)
        
        # Calculate time since command went to zero (if applicable)
        time_since_zero_cmd = 0.0
        if len(self.velocity_history) >= 2:
            # Find when command last went to zero
            for i in range(len(self.velocity_history) - 1, -1, -1):
                if self.velocity_history[i]['cmd_velocity'] < 0.01:
                    if i > 0:
                        time_since_zero_cmd = (timestamp - self.velocity_history[i]['timestamp'])
                    break
        
        if total_cmd_velocity < 0.001:  # All zeros
            # Check if this is suspicious based on other sensors
            if odom_data and 'twist.twist.linear.x' in odom_data:
                odom_vel = abs(odom_data['twist.twist.linear.x'])
                
                # PHYSICS-BASED VALIDATION: Check if movement is expected due to deceleration
                is_valid_deceleration = True
                expected_velocity = 0.0
                
                if self.enable_physics and self.physics_model and len(self.velocity_history) >= 2:
                    # Get previous velocity
                    prev_vel = self.velocity_history[-2]['odom_velocity'] if len(self.velocity_history) >= 2 else 0
                    time_delta = timestamp - self.velocity_history[-2]['timestamp'] if len(self.velocity_history) >= 2 else 0.1
                    
                    # Check if current velocity is within expected deceleration range
                    is_valid_deceleration, expected_velocity = self.physics_model.is_valid_deceleration(
                        prev_vel, odom_vel, time_delta, total_cmd_velocity
                    )
                
                # Only flag as suspicious if movement is NOT expected from deceleration
                if odom_vel > 0.01 and not is_valid_deceleration:
                    # Check if velocity is significantly higher than expected
                    if odom_vel > (expected_velocity + 0.1):  # 0.1 m/s tolerance
                        anomalies.append("ZERO_COMMAND_BUT_MOVING")
                        confidence_scores.append(0.9)
                        details['zero_command_moving'] = {
                            'cmd_velocity': total_cmd_velocity,
                            'odom_velocity': odom_vel,
                            'expected_velocity': expected_velocity,
                            'is_valid_deceleration': is_valid_deceleration
                        }
                elif odom_vel > 0.01 and is_valid_deceleration:
                    # This is expected deceleration, lower confidence
                    if odom_vel > 0.5:  # Still moving fast after significant time
                        anomalies.append("ZERO_COMMAND_BUT_MOVING")
                        confidence_scores.append(0.5)  # Lower confidence due to physics
                        details['zero_command_moving'] = {
                            'cmd_velocity': total_cmd_velocity,
                            'odom_velocity': odom_vel,
                            'expected_velocity': expected_velocity,
                            'is_valid_deceleration': True,
                            'note': 'May be expected deceleration'
                        }
            
            if imu_data and 'linear_acceleration.x' in imu_data:
                imu_accel = imu_data['linear_acceleration.x']  # Keep sign for direction
                imu_accel_abs = abs(imu_accel)
                
                # PHYSICS-BASED VALIDATION: Check if acceleration is expected
                if self.enable_physics and self.physics_model:
                    # Estimate external forces
                    external_forces = self.physics_model.estimate_external_forces(
                        total_cmd_velocity, odom_velocity, imu_accel
                    )
                    
                    # If command is zero, we expect deceleration (negative acceleration)
                    if imu_accel_abs > 0.1:
                        if imu_accel > 0:  # Positive acceleration (unexpected when stopping)
                            # This is suspicious - accelerating when should be decelerating
                            if not external_forces['has_external_force']:
                                anomalies.append("ZERO_COMMAND_BUT_ACCELERATING")
                                confidence_scores.append(0.85)
                                details['zero_command_accel'] = {
                                    'cmd_velocity': total_cmd_velocity,
                                    'imu_acceleration': imu_accel,
                                    'expected_deceleration': -self.physics_model.max_deceleration,
                                    'external_force_detected': external_forces['has_external_force']
                                }
                        else:  # Negative acceleration (expected when stopping)
                            # Check if deceleration is too strong (might indicate external force)
                            if abs(imu_accel) > self.physics_model.max_deceleration * 1.5:
                                if external_forces['has_external_force']:
                                    # External force detected - might be wind, slope, etc.
                                    details['external_force'] = external_forces
                                    # Lower confidence if external forces explain it
                                    if abs(external_forces['external_force']) < 20.0:  # Moderate force
                                        pass  # Don't flag as falsified
                                    else:
                                        anomalies.append("EXCESSIVE_DECELERATION")
                                        confidence_scores.append(0.6)
                else:
                    # Simple check without physics
                    if imu_accel_abs > 0.1 and imu_accel > 0:  # Positive accel when should stop
                        anomalies.append("ZERO_COMMAND_BUT_ACCELERATING")
                        confidence_scores.append(0.85)
                        details['zero_command_accel'] = {
                            'cmd_velocity': total_cmd_velocity,
                            'imu_acceleration': imu_accel
                        }
            
            if joint_data:
                wheel_vels = [abs(joint_data.get(f'velocity_{i}', 0)) 
                            for i in range(4)]
                avg_wheel_vel = np.mean(wheel_vels) if wheel_vels else 0
                
                # PHYSICS-BASED VALIDATION: Wheels may still be rotating due to momentum
                if avg_wheel_vel > 0.01:  # Wheels moving but zero command
                    is_suspicious = True
                    expected_wheel_vel = 0.0
                    
                    if self.enable_physics and self.physics_model and len(self.velocity_history) >= 2:
                        # Get previous wheel velocity (approximate from odometry)
                        prev_odom_vel = self.velocity_history[-2]['odom_velocity'] if len(self.velocity_history) >= 2 else 0
                        time_delta = timestamp - self.velocity_history[-2]['timestamp'] if len(self.velocity_history) >= 2 else 0.1
                        
                        # Estimate expected wheel velocity (wheels decelerate with robot)
                        expected_wheel_vel = self.physics_model.calculate_expected_deceleration(
                            prev_odom_vel, time_delta
                        )
                        
                        # Allow tolerance for wheel velocity
                        tolerance = max(0.05, expected_wheel_vel * 0.3)
                        is_suspicious = avg_wheel_vel > (expected_wheel_vel + tolerance)
                    
                    if is_suspicious:
                        anomalies.append("ZERO_COMMAND_BUT_WHEELS_ROTATING")
                        # Adjust confidence based on whether it's expected deceleration
                        if expected_wheel_vel > 0.01:
                            confidence_scores.append(0.7)  # Lower - might be momentum
                        else:
                            confidence_scores.append(0.9)  # High - definitely suspicious
                        
                        details['zero_command_wheels'] = {
                            'cmd_velocity': total_cmd_velocity,
                            'avg_wheel_velocity': avg_wheel_vel,
                            'expected_wheel_velocity': expected_wheel_vel,
                            'is_expected_deceleration': expected_wheel_vel > 0.01
                        }
        
        # Check 2: Command vs Odometry mismatch (with physics validation)
        if odom_data and 'twist.twist.linear.x' in odom_data:
            cmd_vel = abs(cmd_vel_data.get('linear.x', 0))
            odom_vel = abs(odom_data['twist.twist.linear.x'])
            
            # Large discrepancy
            if abs(cmd_vel - odom_vel) > 0.5:
                # Check if this is expected due to deceleration
                is_expected = False
                if self.enable_physics and self.physics_model and len(self.velocity_history) >= 2:
                    prev_odom_vel = self.velocity_history[-2]['odom_velocity'] if len(self.velocity_history) >= 2 else 0
                    time_delta = timestamp - self.velocity_history[-2]['timestamp'] if len(self.velocity_history) >= 2 else 0.1
                    
                    # If command is zero, check if odom velocity is within expected deceleration
                    if cmd_vel < 0.01:
                        _, expected_vel = self.physics_model.is_valid_deceleration(
                            prev_odom_vel, odom_vel, time_delta, cmd_vel
                        )
                        tolerance = max(0.1, expected_vel * 0.2)
                        is_expected = odom_vel <= (expected_vel + tolerance)
                
                if not is_expected:
                    anomalies.append("CMD_ODOM_MISMATCH")
                    confidence_scores.append(0.8)
                    details['cmd_odom_mismatch'] = {
                        'cmd_velocity': cmd_vel,
                        'odom_velocity': odom_vel,
                        'difference': abs(cmd_vel - odom_vel),
                        'is_expected_deceleration': is_expected
                    }
        
        # Check 3: Command vs IMU mismatch (with physics validation)
        if imu_data and 'linear_acceleration.x' in imu_data:
            cmd_vel = abs(cmd_vel_data.get('linear.x', 0))
            imu_accel = imu_data['linear_acceleration.x']  # Keep sign
            imu_accel_abs = abs(imu_accel)
            
            # If command is zero but there's significant acceleration
            if cmd_vel < 0.01 and imu_accel_abs > 0.2:
                # Check if acceleration direction is suspicious
                is_suspicious = True
                
                if self.enable_physics and self.physics_model:
                    # When command is zero, we expect deceleration (negative accel)
                    if imu_accel < 0:  # Negative = deceleration (expected)
                        # Check if deceleration is reasonable
                        if imu_accel_abs <= self.physics_model.max_deceleration * 1.2:
                            is_suspicious = False  # Expected deceleration
                    else:  # Positive = acceleration (unexpected when stopping)
                        # Check for external forces
                        external_forces = self.physics_model.estimate_external_forces(
                            cmd_vel, odom_velocity, imu_accel
                        )
                        if external_forces['has_external_force']:
                            # Might be wind, slope, etc. - lower confidence
                            is_suspicious = abs(external_forces['external_force']) > 20.0
                
                if is_suspicious:
                    anomalies.append("CMD_IMU_MISMATCH")
                    confidence_scores.append(0.75)
                    details['cmd_imu_mismatch'] = {
                        'cmd_velocity': cmd_vel,
                        'imu_acceleration': imu_accel,
                        'is_expected_deceleration': imu_accel < 0 and imu_accel_abs <= (self.physics_model.max_deceleration * 1.2) if (self.enable_physics and self.physics_model) else False
                    }
        
        # Check 4: Command vs Joint States mismatch
        if joint_data:
            cmd_vel = abs(cmd_vel_data.get('linear.x', 0))
            wheel_vels = [abs(joint_data.get(f'velocity_{i}', 0)) 
                         for i in range(4)]
            avg_wheel_vel = np.mean(wheel_vels) if wheel_vels else 0
            
            if cmd_vel < 0.01 and avg_wheel_vel > 0.05:
                anomalies.append("CMD_JOINT_MISMATCH")
                confidence_scores.append(0.85)
                details['cmd_joint_mismatch'] = {
                    'cmd_velocity': cmd_vel,
                    'avg_wheel_velocity': avg_wheel_vel
                }
        
        # Check 5: Statistical anomaly - too perfect zeros
        if total_cmd_velocity < 0.001:
            # Check if we've seen many consecutive zeros
            self.recent_data.append({
                'timestamp': timestamp,
                'cmd_velocity': total_cmd_velocity,
                'anomalies': len(anomalies)
            })
            
            # Keep only recent window
            if len(self.recent_data) > self.window_size:
                self.recent_data.pop(0)
            
            # If many consecutive zeros with movement detected elsewhere
            consecutive_zeros = sum(1 for d in self.recent_data 
                                 if d['cmd_velocity'] < 0.001)
            if consecutive_zeros >= self.window_size * 0.8:
                anomalies.append("CONSECUTIVE_ZEROS")
                confidence_scores.append(0.7)
                details['consecutive_zeros'] = {
                    'count': consecutive_zeros,
                    'window_size': self.window_size
                }
        
        # PREDICTIVE MODEL VALIDATION
        if self.enable_predictive:
            try:
                # Initialize predictive model if not already done
                if self.predictive_model is None and self.data_cache:
                    from predictive_model import PredictiveDetector
                    self.predictive_model = PredictiveDetector(
                        window_size=self.window_size,
                        confidence_level=0.95,
                        model_type='random_forest',
                        model_dir='models'
                    )
                    # Try to load existing models first
                    if not self.predictive_model.load_models():
                        print("Training predictive models...")
                        self.predictive_model.train_model(self.data_cache)
                    else:
                        print("Using existing trained models.")
                
                # Check predictions for key sensors
                if self.predictive_model and self.predictive_model.is_trained:
                    # Check cmd_vel prediction
                    if odom_data and 'twist.twist.linear.x' in odom_data:
                        recent_odom = self.predictive_model.get_recent_data_window(
                            self.data_cache, 'odometry', timestamp, lookback_seconds=2.0
                        )
                        if len(recent_odom) >= self.predictive_model.window_size:
                            actual_odom_vel = odom_data['twist.twist.linear.x']
                            pred_result = self.predictive_model.detect_anomaly(
                                'odometry', 'twist.twist.linear.x', 
                                actual_odom_vel, recent_odom
                            )
                            
                            if pred_result['is_anomaly']:
                                anomalies.append("PREDICTIVE_ANOMALY_ODOM")
                                confidence_scores.append(pred_result['confidence'])
                                details['predictive_odom'] = pred_result
                    
                    # Check cmd_vel prediction
                    if cmd_vel_data:
                        recent_cmd = self.predictive_model.get_recent_data_window(
                            self.data_cache, 'cmd_vel', timestamp, lookback_seconds=2.0
                        )
                        if len(recent_cmd) >= self.predictive_model.window_size:
                            actual_cmd_vel = cmd_vel_data.get('linear.x', 0)
                            pred_result = self.predictive_model.detect_anomaly(
                                'cmd_vel', 'linear.x',
                                actual_cmd_vel, recent_cmd
                            )
                            
                            if pred_result['is_anomaly']:
                                # Check if this is suspicious (unexpected command)
                                if abs(actual_cmd_vel) > 0.01 and pred_result['confidence'] > 0.7:
                                    anomalies.append("PREDICTIVE_ANOMALY_CMD")
                                    confidence_scores.append(pred_result['confidence'] * 0.8)  # Slightly lower weight
                                    details['predictive_cmd'] = pred_result
                    
                    # Check IMU prediction
                    if imu_data and 'linear_acceleration.x' in imu_data:
                        recent_imu = self.predictive_model.get_recent_data_window(
                            self.data_cache, 'imu', timestamp, lookback_seconds=2.0
                        )
                        if len(recent_imu) >= self.predictive_model.window_size:
                            actual_imu_accel = imu_data['linear_acceleration.x']
                            pred_result = self.predictive_model.detect_anomaly(
                                'imu', 'linear_acceleration.x',
                                actual_imu_accel, recent_imu
                            )
                            
                            if pred_result['is_anomaly'] and pred_result['confidence'] > 0.6:
                                anomalies.append("PREDICTIVE_ANOMALY_IMU")
                                confidence_scores.append(pred_result['confidence'] * 0.7)  # Lower weight for IMU
                                details['predictive_imu'] = pred_result
                                
            except Exception as e:
                # Don't fail if predictive model has issues
                pass
        
        # Calculate overall confidence
        if confidence_scores:
            overall_confidence = max(confidence_scores)
        else:
            overall_confidence = 0.0
        
        is_falsified = overall_confidence >= self.threshold
        
        return DetectionResult(
            timestamp=timestamp,
            is_falsified=is_falsified,
            confidence=overall_confidence,
            anomalies=anomalies,
            details=details
        )
    
    def analyze_historical_data(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Analyze historical data to find falsified entries"""
        results = []
        
        if 'cmd_vel' not in data:
            return pd.DataFrame()
        
        cmd_vel = data['cmd_vel']
        
        # Iterate through command velocity data
        for idx, row in cmd_vel.iterrows():
            timestamp = row['Time']
            
            # Get synchronized data
            synced = self.synchronize_data(data, timestamp)
            
            # Detect falsification
            result = self.detect_falsification(
                cmd_vel_data=synced.get('cmd_vel', {}),
                odom_data=synced.get('odometry'),
                imu_data=synced.get('imu'),
                joint_data=synced.get('joint_states'),
                timestamp=timestamp
            )
            
            results.append({
                'timestamp': result.timestamp,
                'is_falsified': result.is_falsified,
                'confidence': result.confidence,
                'num_anomalies': len(result.anomalies),
                'anomalies': ', '.join(result.anomalies) if result.anomalies else 'None'
            })
        
        return pd.DataFrame(results)
    
    def monitor_live_feed(self, data_stream: Dict):
        """
        Monitor live data feed and detect falsification in real-time
        
        Args:
            data_stream: Dictionary with current sensor data
                {
                    'cmd_vel': {...},
                    'odometry': {...},
                    'imu': {...},
                    'joint_states': {...},
                    'timestamp': float
                }
        """
        result = self.detect_falsification(
            cmd_vel_data=data_stream.get('cmd_vel', {}),
            odom_data=data_stream.get('odometry'),
            imu_data=data_stream.get('imu'),
            joint_data=data_stream.get('joint_states'),
            timestamp=data_stream.get('timestamp', datetime.now().timestamp())
        )
        
        return result
    
    def print_detection_result(self, result: DetectionResult):
        """Print formatted detection result"""
        status = "🚨 FALSIFIED" if result.is_falsified else "✓ NORMAL"
        print(f"\n[{status}] Timestamp: {result.timestamp:.2f}")
        print(f"  Confidence: {result.confidence:.2%}")
        
        if result.anomalies:
            print(f"  Anomalies detected:")
            for anomaly in result.anomalies:
                print(f"    - {anomaly}")
            
            if result.details:
                print(f"  Details:")
                for key, value in result.details.items():
                    print(f"    {key}: {value}")
        else:
            print(f"  No anomalies detected")


def main():
    """Main function to demonstrate falsification detection"""
    print("=" * 60)
    print("FALSIFICATION DETECTION SYSTEM")
    print("=" * 60)
    
    # Initialize detector with predictive model enabled
    detector = FalsificationDetector(window_size=10, threshold=0.7, enable_predictive=True)
    
    # Load data
    print("\n[1/4] Loading data...")
    data = detector.load_data()
    
    if not data:
        print("❌ Failed to load data. Please check the demo/ directory.")
        return
    
    # Calculate statistics
    print("\n[2/4] Calculating baseline statistics...")
    detector.calculate_statistics(data)
    
    # Analyze historical data
    print("\n[3/4] Analyzing historical data for falsification...")
    results_df = detector.analyze_historical_data(data)
    
    if len(results_df) > 0:
        # Summary statistics
        total_samples = len(results_df)
        falsified_samples = results_df['is_falsified'].sum()
        falsified_percentage = (falsified_samples / total_samples) * 100
        
        print(f"\n📊 Analysis Summary:")
        print(f"  Total samples analyzed: {total_samples}")
        print(f"  Falsified samples: {falsified_samples} ({falsified_percentage:.1f}%)")
        print(f"  Normal samples: {total_samples - falsified_samples}")
        
        # Show some examples
        print(f"\n📋 Sample Detection Results:")
        falsified_examples = results_df[results_df['is_falsified']].head(5)
        for idx, row in falsified_examples.iterrows():
            print(f"\n  Sample {idx}:")
            print(f"    Confidence: {row['confidence']:.2%}")
            print(f"    Anomalies: {row['anomalies']}")
        
        # Save results
        output_file = "falsification_detection_results.csv"
        results_df.to_csv(output_file, index=False)
        print(f"\n✓ Results saved to {output_file}")
    
    # Demonstrate live monitoring
    print("\n[4/4] Demonstrating live monitoring...")
    print("\nExample 1: Normal operation")
    normal_data = {
        'cmd_vel': {'linear.x': 0.5, 'linear.y': 0.0, 'linear.z': 0.0,
                    'angular.x': 0.0, 'angular.y': 0.0, 'angular.z': 0.2},
        'odometry': {'twist.twist.linear.x': 0.48},
        'imu': {'linear_acceleration.x': 0.1},
        'joint_states': {'velocity_0': 0.5, 'velocity_1': 0.5, 
                        'velocity_2': 0.5, 'velocity_3': 0.5},
        'timestamp': 1400.0
    }
    result1 = detector.monitor_live_feed(normal_data)
    detector.print_detection_result(result1)
    
    print("\nExample 2: Falsified data (zero command but robot moving)")
    falsified_data = {
        'cmd_vel': {'linear.x': 0.0, 'linear.y': 0.0, 'linear.z': 0.0,
                    'angular.x': 0.0, 'angular.y': 0.0, 'angular.z': 0.0},
        'odometry': {'twist.twist.linear.x': 0.5},  # Robot is moving!
        'imu': {'linear_acceleration.x': 0.2},
        'joint_states': {'velocity_0': 0.5, 'velocity_1': 0.5,
                        'velocity_2': 0.5, 'velocity_3': 0.5},
        'timestamp': 1401.0
    }
    result2 = detector.monitor_live_feed(falsified_data)
    detector.print_detection_result(result2)
    
    print("\n" + "=" * 60)
    print("Analysis complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

