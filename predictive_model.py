#!/usr/bin/env python3
"""
Predictive Model for Falsification Detection
Uses machine learning to predict expected sensor values and detect anomalies
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import os
import warnings
warnings.filterwarnings('ignore')

class PredictiveDetector:
    """
    Predictive model that learns normal behavior patterns and detects anomalies
    """
    
    def __init__(self, 
                 window_size: int = 10,
                 confidence_level: float = 0.95,
                 model_type: str = 'random_forest',
                 model_dir: str = 'models'):
        """
        Initialize predictive detector
        
        Args:
            window_size: Number of previous samples to use for prediction
            confidence_level: Confidence level for bounds (0.95 = 95%)
            model_type: 'random_forest' or 'gradient_boosting'
            model_dir: Directory to save/load trained models
        """
        self.window_size = window_size
        self.confidence_level = confidence_level
        self.model_type = model_type
        self.model_dir = model_dir
        
        # Create model directory if it doesn't exist
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)
        
        # Models for different sensor types
        self.models = {}
        self.scalers = {}
        self.bounds = {}  # Store prediction bounds
        self.is_trained = False
        
        # History for predictions
        self.prediction_history = []
        
    def create_features(self, data_window: pd.DataFrame, 
                       target_col: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create features from time window for prediction
        
        Args:
            data_window: DataFrame with time series data
            target_col: Column name to predict
            
        Returns:
            (features, targets)
        """
        features = []
        targets = []
        
        for i in range(self.window_size, len(data_window)):
            # Get window of previous values
            window = data_window.iloc[i-self.window_size:i]
            
            # Features: previous values, statistics, time features
            feature_vec = []
            
            # Previous values
            if target_col in window.columns:
                prev_values = window[target_col].values
                feature_vec.extend(prev_values)
                
                # Statistics
                feature_vec.append(np.mean(prev_values))
                feature_vec.append(np.std(prev_values))
                feature_vec.append(np.min(prev_values))
                feature_vec.append(np.max(prev_values))
                feature_vec.append(prev_values[-1] - prev_values[0])  # Trend
                
                # Time features
                if 'Time' in window.columns:
                    time_delta = window['Time'].iloc[-1] - window['Time'].iloc[0]
                    feature_vec.append(time_delta)
            
            # Ensure consistent feature length
            # Always include: window_size values + 5 statistics + 1 time = window_size + 6
            expected_len = self.window_size + 6
            
            # Pad or truncate to expected length
            if len(feature_vec) < expected_len:
                feature_vec.extend([0.0] * (expected_len - len(feature_vec)))
            elif len(feature_vec) > expected_len:
                feature_vec = feature_vec[:expected_len]
            
            features.append(feature_vec)
            targets.append(data_window[target_col].iloc[i])
        
        return np.array(features), np.array(targets)
    
    def train_model(self, data: Dict[str, pd.DataFrame], 
                   target_sensors: List[str] = None):
        """
        Train predictive models on historical data
        
        Args:
            data: Dictionary of DataFrames (cmd_vel, odometry, imu, etc.)
            target_sensors: List of sensor columns to predict
        """
        if target_sensors is None:
            target_sensors = [
                ('cmd_vel', 'linear.x'),
                ('odometry', 'twist.twist.linear.x'),
                ('imu', 'linear_acceleration.x'),
                ('joint_states', 'velocity_0')
            ]
        
        print(f"Training predictive models for {len(target_sensors)} sensors...")
        
        for sensor_name, col_name in target_sensors:
            if sensor_name not in data:
                continue
            
            df = data[sensor_name].copy()
            
            if col_name not in df.columns:
                continue
            
            # Remove NaN values
            df = df.dropna(subset=[col_name, 'Time'])
            df = df.sort_values('Time')
            
            if len(df) < self.window_size * 2:
                print(f"  ⚠ Skipping {sensor_name}.{col_name}: insufficient data")
                continue
            
            # Create features and targets
            try:
                X, y = self.create_features(df, col_name)
                
                if len(X) < 50:
                    print(f"  ⚠ Skipping {sensor_name}.{col_name}: insufficient samples after feature creation")
                    continue
                
                # Split data
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42
                )
                
                # Scale features
                scaler = StandardScaler()
                X_train_scaled = scaler.fit_transform(X_train)
                X_test_scaled = scaler.transform(X_test)
                
                # Train model
                if self.model_type == 'random_forest':
                    model = RandomForestRegressor(
                        n_estimators=100,
                        max_depth=10,
                        random_state=42,
                        n_jobs=-1
                    )
                else:  # gradient_boosting
                    model = GradientBoostingRegressor(
                        n_estimators=100,
                        max_depth=5,
                        random_state=42
                    )
                
                model.fit(X_train_scaled, y_train)
                
                # Calculate prediction bounds on test set
                y_pred = model.predict(X_test_scaled)
                residuals = y_test - y_pred
                std_residual = np.std(residuals)
                mean_residual = np.mean(residuals)
                
                # Calculate bounds (using z-score for confidence level)
                from scipy import stats
                z_score = stats.norm.ppf((1 + self.confidence_level) / 2)
                bound = z_score * std_residual
                
                # Store model and scaler
                key = f"{sensor_name}.{col_name}"
                self.models[key] = model
                self.scalers[key] = scaler
                self.bounds[key] = {
                    'mean_error': mean_residual,
                    'std_error': std_residual,
                    'bound': bound,
                    'test_mae': np.mean(np.abs(residuals)),
                    'test_rmse': np.sqrt(np.mean(residuals**2))
                }
                
                print(f"  ✓ Trained {key}: MAE={self.bounds[key]['test_mae']:.4f}, "
                      f"RMSE={self.bounds[key]['test_rmse']:.4f}, "
                      f"Bound=±{bound:.4f}")
                
            except Exception as e:
                print(f"  ⚠ Error training {sensor_name}.{col_name}: {e}")
                continue
        
        self.is_trained = len(self.models) > 0
        print(f"\n✓ Training complete: {len(self.models)} models trained")
        
        # Save models to disk
        if self.is_trained:
            self.save_models()
    
    def predict(self, sensor_name: str, col_name: str, 
                recent_data: pd.DataFrame) -> Tuple[float, float, float]:
        """
        Predict next value and return prediction with bounds
        
        Args:
            sensor_name: Name of sensor (e.g., 'cmd_vel')
            col_name: Column name to predict
            recent_data: Recent data window (last window_size samples)
            
        Returns:
            (prediction, lower_bound, upper_bound)
        """
        key = f"{sensor_name}.{col_name}"
        
        if key not in self.models:
            return None, None, None
        
        if len(recent_data) < self.window_size:
            return None, None, None
        
        try:
            # Get last window
            window = recent_data.iloc[-self.window_size:].copy()
            
            # Create feature vector
            feature_vec = []
            
            if col_name in window.columns:
                prev_values = window[col_name].values
                feature_vec.extend(prev_values)
                
                # Statistics
                feature_vec.append(np.mean(prev_values))
                feature_vec.append(np.std(prev_values))
                feature_vec.append(np.min(prev_values))
                feature_vec.append(np.max(prev_values))
                feature_vec.append(prev_values[-1] - prev_values[0])
                
                # Time features
                if 'Time' in window.columns:
                    time_delta = window['Time'].iloc[-1] - window['Time'].iloc[0]
                    feature_vec.append(time_delta)
            
            # Ensure correct length (window_size + 5 stats + 1 time = window_size + 6)
            expected_len = self.window_size + 6
            if len(feature_vec) < expected_len:
                feature_vec.extend([0.0] * (expected_len - len(feature_vec)))
            elif len(feature_vec) > expected_len:
                feature_vec = feature_vec[:expected_len]
            
            # Scale and predict
            X = np.array(feature_vec).reshape(1, -1)
            X_scaled = self.scalers[key].transform(X)
            prediction = self.models[key].predict(X_scaled)[0]
            
            # Calculate bounds
            bound = self.bounds[key]['bound']
            lower_bound = prediction - bound
            upper_bound = prediction + bound
            
            return prediction, lower_bound, upper_bound
            
        except Exception as e:
            print(f"Error in prediction for {key}: {e}")
            return None, None, None
    
    def detect_anomaly(self, sensor_name: str, col_name: str,
                      actual_value: float, recent_data: pd.DataFrame) -> Dict:
        """
        Detect if actual value is anomalous compared to prediction
        
        Args:
            sensor_name: Name of sensor
            col_name: Column name
            actual_value: Actual observed value
            recent_data: Recent data window
            
        Returns:
            Dictionary with detection results
        """
        prediction, lower_bound, upper_bound = self.predict(
            sensor_name, col_name, recent_data
        )
        
        if prediction is None:
            return {
                'is_anomaly': False,
                'confidence': 0.0,
                'reason': 'Model not available'
            }
        
        # Check if actual value is within bounds
        is_within_bounds = lower_bound <= actual_value <= upper_bound
        
        # Calculate anomaly score (how far outside bounds)
        if is_within_bounds:
            anomaly_score = 0.0
        else:
            if actual_value < lower_bound:
                deviation = lower_bound - actual_value
            else:
                deviation = actual_value - upper_bound
            
            # Normalize by bound size
            bound_size = upper_bound - lower_bound
            if bound_size > 0:
                anomaly_score = deviation / bound_size
            else:
                anomaly_score = abs(deviation)
        
        # Calculate confidence (higher deviation = higher confidence)
        confidence = min(1.0, anomaly_score * 2.0) if not is_within_bounds else 0.0
        
        return {
            'is_anomaly': not is_within_bounds,
            'confidence': confidence,
            'prediction': prediction,
            'actual': actual_value,
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
            'deviation': abs(actual_value - prediction) if not is_within_bounds else 0.0,
            'bound_size': upper_bound - lower_bound
        }
    
    def save_models(self):
        """Save trained models, scalers, and bounds to disk"""
        if not self.is_trained:
            return
        
        print(f"\nSaving models to {self.model_dir}/...")
        
        for key in self.models:
            # Save model
            model_path = os.path.join(self.model_dir, f"{key.replace('.', '_')}_model.pkl")
            joblib.dump(self.models[key], model_path)
            
            # Save scaler
            scaler_path = os.path.join(self.model_dir, f"{key.replace('.', '_')}_scaler.pkl")
            joblib.dump(self.scalers[key], scaler_path)
            
            # Save bounds (as JSON-compatible dict)
            bounds_path = os.path.join(self.model_dir, f"{key.replace('.', '_')}_bounds.pkl")
            joblib.dump(self.bounds[key], bounds_path)
        
        # Save metadata
        metadata = {
            'window_size': self.window_size,
            'confidence_level': self.confidence_level,
            'model_type': self.model_type,
            'trained_models': list(self.models.keys())
        }
        metadata_path = os.path.join(self.model_dir, 'metadata.pkl')
        joblib.dump(metadata, metadata_path)
        
        print(f"✓ Saved {len(self.models)} models to {self.model_dir}/")
    
    def load_models(self) -> bool:
        """
        Load trained models, scalers, and bounds from disk
        
        Returns:
            True if models were loaded successfully, False otherwise
        """
        metadata_path = os.path.join(self.model_dir, 'metadata.pkl')
        
        if not os.path.exists(metadata_path):
            return False
        
        try:
            # Load metadata
            metadata = joblib.load(metadata_path)
            self.window_size = metadata['window_size']
            self.confidence_level = metadata['confidence_level']
            self.model_type = metadata['model_type']
            
            # Load each model
            for key in metadata['trained_models']:
                safe_key = key.replace('.', '_')
                
                # Load model
                model_path = os.path.join(self.model_dir, f"{safe_key}_model.pkl")
                if os.path.exists(model_path):
                    self.models[key] = joblib.load(model_path)
                
                # Load scaler
                scaler_path = os.path.join(self.model_dir, f"{safe_key}_scaler.pkl")
                if os.path.exists(scaler_path):
                    self.scalers[key] = joblib.load(scaler_path)
                
                # Load bounds
                bounds_path = os.path.join(self.model_dir, f"{safe_key}_bounds.pkl")
                if os.path.exists(bounds_path):
                    self.bounds[key] = joblib.load(bounds_path)
            
            self.is_trained = len(self.models) > 0
            
            if self.is_trained:
                print(f"✓ Loaded {len(self.models)} models from {self.model_dir}/")
                print(f"  Models: {', '.join(self.models.keys())}")
            
            return self.is_trained
            
        except Exception as e:
            print(f"⚠ Error loading models: {e}")
            return False
    
    def get_recent_data_window(self, data: Dict[str, pd.DataFrame],
                              sensor_name: str, current_time: float,
                              lookback_seconds: float = 5.0) -> pd.DataFrame:
        """
        Get recent data window for a sensor
        
        Args:
            data: Dictionary of all sensor data
            sensor_name: Name of sensor
            current_time: Current timestamp
            lookback_seconds: How far back to look
            
        Returns:
            DataFrame with recent data
        """
        if sensor_name not in data:
            return pd.DataFrame()
        
        df = data[sensor_name].copy()
        
        if 'Time' not in df.columns:
            return pd.DataFrame()
        
        # Get data within time window
        time_window = df[
            (df['Time'] >= current_time - lookback_seconds) &
            (df['Time'] <= current_time)
        ].copy()
        
        # Sort by time
        time_window = time_window.sort_values('Time')
        
        return time_window


def main():
    """Test the predictive model"""
    from falsification_detector import FalsificationDetector
    
    print("=" * 60)
    print("PREDICTIVE MODEL FOR FALSIFICATION DETECTION")
    print("=" * 60)
    
    # Load data
    detector = FalsificationDetector()
    print("\n[1/3] Loading data...")
    data = detector.load_data()
    
    if not data:
        print("❌ Failed to load data")
        return
    
    # Train or load predictive model
    print("\n[2/3] Loading/Training predictive models...")
    predictive = PredictiveDetector(
        window_size=10,
        confidence_level=0.95,
        model_type='random_forest',
        model_dir='models'
    )
    
    # Try to load existing models first
    if not predictive.load_models():
        # If loading failed, train new models
        print("No existing models found. Training new models...")
        predictive.train_model(data)
    else:
        print("Using existing trained models.")
    
    if not predictive.is_trained:
        print("❌ Model training failed")
        return
    
    # Test predictions
    print("\n[3/3] Testing predictions...")
    
    # Test on cmd_vel
    if 'cmd_vel' in data:
        cmd_data = data['cmd_vel'].copy()
        test_time = cmd_data['Time'].iloc[100]  # Use a sample from middle
        
        recent_data = predictive.get_recent_data_window(
            data, 'cmd_vel', test_time, lookback_seconds=2.0
        )
        
        if len(recent_data) > 0:
            # Get actual next value
            next_idx = cmd_data[cmd_data['Time'] > test_time].index
            if len(next_idx) > 0:
                actual_value = cmd_data.loc[next_idx[0], 'linear.x']
                
                # Predict
                result = predictive.detect_anomaly(
                    'cmd_vel', 'linear.x', actual_value, recent_data
                )
                
                print(f"\nTest Prediction for cmd_vel.linear.x:")
                print(f"  Actual value: {actual_value:.4f}")
                print(f"  Predicted: {result['prediction']:.4f}")
                print(f"  Bounds: [{result['lower_bound']:.4f}, {result['upper_bound']:.4f}]")
                print(f"  Is anomaly: {result['is_anomaly']}")
                print(f"  Confidence: {result['confidence']:.2%}")
                if result['is_anomaly']:
                    print(f"  Deviation: {result['deviation']:.4f}")
    
    print("\n" + "=" * 60)
    print("Predictive model test complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

