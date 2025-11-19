#!/usr/bin/env python3
"""
Comprehensive Benchmarking Script for Falsification Detection Model
Measures speed, accuracy, and detection performance
"""

import pandas as pd
import numpy as np
import time
import sys
import os
from typing import Dict, List, Tuple
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# Import model classes
from predictive_model import PredictiveDetector
from falsification_detector import FalsificationDetector

class BenchmarkSuite:
    """Comprehensive benchmarking suite for the falsification detection system"""
    
    def __init__(self, model_dir='models', demo_dir='demo'):
        self.model_dir = model_dir
        self.demo_dir = demo_dir
        self.results = defaultdict(dict)
        
    def load_models_and_data(self):
        """Load models and sample data"""
        print("=" * 80)
        print("LOADING MODELS AND DATA")
        print("=" * 80)
        
        # Load data
        detector = FalsificationDetector(enable_predictive=True)
        print(f"\n[1/2] Loading data from {self.demo_dir}/...")
        data = detector.load_data(self.demo_dir)
        
        if not data:
            print("❌ Failed to load data")
            return None, None, None
        
        # Load predictive model
        print(f"\n[2/2] Loading models from {self.model_dir}/...")
        predictive = PredictiveDetector(
            window_size=10,
            confidence_level=0.95,
            model_type='random_forest',
            model_dir=self.model_dir
        )
        
        if not predictive.load_models():
            print("❌ Failed to load models")
            return None, None, None
        
        print(f"✓ Loaded {len(predictive.models)} models")
        
        return detector, predictive, data
    
    def benchmark_model_loading(self, predictive: PredictiveDetector):
        """Benchmark model loading time"""
        print("\n" + "=" * 80)
        print("BENCHMARK: Model Loading Speed")
        print("=" * 80)
        
        # Clear models
        predictive.models = {}
        predictive.scalers = {}
        predictive.bounds = {}
        predictive.is_trained = False
        
        # Time loading
        start_time = time.time()
        success = predictive.load_models()
        load_time = time.time() - start_time
        
        if success:
            print(f"\n✓ Model loading successful")
            print(f"  Load time: {load_time:.4f} seconds")
            print(f"  Models loaded: {len(predictive.models)}")
            
            # Calculate model sizes
            total_size = 0
            model_sizes = {}
            for key in predictive.models:
                # Estimate model size (rough approximation)
                model = predictive.models[key]
                scaler = predictive.scalers[key]
                bounds = predictive.bounds[key]
                
                # Count parameters (rough estimate)
                if hasattr(model, 'n_estimators'):
                    n_trees = model.n_estimators
                    n_features = model.n_features_in_
                    # Rough estimate: each tree has ~2^max_depth nodes
                    estimated_size = n_trees * (2 ** 10) * 8  # bytes (assuming 8 bytes per node)
                else:
                    estimated_size = 100000  # Default estimate
                
                model_sizes[key] = estimated_size / (1024 * 1024)  # MB
                total_size += estimated_size
            
            total_size_mb = total_size / (1024 * 1024)
            
            print(f"\n  Model sizes:")
            for key, size in model_sizes.items():
                print(f"    {key}: {size:.2f} MB")
            print(f"  Total size: {total_size_mb:.2f} MB")
            
            self.results['model_loading'] = {
                'load_time_seconds': load_time,
                'num_models': len(predictive.models),
                'total_size_mb': total_size_mb,
                'models_per_second': len(predictive.models) / load_time if load_time > 0 else 0
            }
        else:
            print("❌ Model loading failed")
            self.results['model_loading'] = {'load_time_seconds': None, 'success': False}
        
        return success
    
    def benchmark_prediction_speed(self, predictive: PredictiveDetector, data: Dict):
        """Benchmark prediction speed for different sensors"""
        print("\n" + "=" * 80)
        print("BENCHMARK: Prediction Speed")
        print("=" * 80)
        
        prediction_results = {}
        
        # Test each sensor model
        for key in predictive.models:
            sensor_name, col_name = key.split('.', 1)
            
            if sensor_name not in data:
                continue
            
            df = data[sensor_name].copy()
            if col_name not in df.columns:
                continue
            
            # Get test data (skip first window_size samples)
            df = df.dropna(subset=[col_name, 'Time'])
            df = df.sort_values('Time')
            
            if len(df) < predictive.window_size + 100:
                continue
            
            # Test on 200 samples (reduced for faster benchmarking)
            test_indices = range(predictive.window_size, min(predictive.window_size + 200, len(df)))
            test_samples = list(test_indices)
            
            # Warm-up (first 10 predictions)
            for i in test_samples[:10]:
                recent_data = df.iloc[i-predictive.window_size:i]
                try:
                    predictive.predict(sensor_name, col_name, recent_data)
                except:
                    pass
            
            # Actual timing
            times = []
            successful_predictions = 0
            
            for i in test_samples:
                recent_data = df.iloc[i-predictive.window_size:i]
                start = time.time()
                try:
                    pred, lower, upper = predictive.predict(sensor_name, col_name, recent_data)
                    if pred is not None:
                        successful_predictions += 1
                        times.append(time.time() - start)
                except Exception as e:
                    pass
            
            if times:
                avg_time = np.mean(times)
                std_time = np.std(times)
                min_time = np.min(times)
                max_time = np.max(times)
                p95_time = np.percentile(times, 95)
                p99_time = np.percentile(times, 99)
                
                predictions_per_second = 1.0 / avg_time if avg_time > 0 else 0
                
                print(f"\n{key}:")
                print(f"  Samples tested: {len(test_samples)}")
                print(f"  Successful predictions: {successful_predictions}")
                print(f"  Average latency: {avg_time*1000:.3f} ms")
                print(f"  Std deviation: {std_time*1000:.3f} ms")
                print(f"  Min latency: {min_time*1000:.3f} ms")
                print(f"  Max latency: {max_time*1000:.3f} ms")
                print(f"  95th percentile: {p95_time*1000:.3f} ms")
                print(f"  99th percentile: {p99_time*1000:.3f} ms")
                print(f"  Throughput: {predictions_per_second:.1f} predictions/second")
                
                prediction_results[key] = {
                    'avg_latency_ms': avg_time * 1000,
                    'std_latency_ms': std_time * 1000,
                    'min_latency_ms': min_time * 1000,
                    'max_latency_ms': max_time * 1000,
                    'p95_latency_ms': p95_time * 1000,
                    'p99_latency_ms': p99_time * 1000,
                    'throughput_per_sec': predictions_per_second,
                    'successful_predictions': successful_predictions,
                    'total_samples': len(test_samples)
                }
        
        self.results['prediction_speed'] = prediction_results
        return prediction_results
    
    def benchmark_prediction_accuracy(self, predictive: PredictiveDetector, data: Dict):
        """Benchmark prediction accuracy (MAE, RMSE, R²)"""
        print("\n" + "=" * 80)
        print("BENCHMARK: Prediction Accuracy")
        print("=" * 80)
        
        accuracy_results = {}
        
        for key in predictive.models:
            sensor_name, col_name = key.split('.', 1)
            
            if sensor_name not in data:
                continue
            
            df = data[sensor_name].copy()
            if col_name not in df.columns:
                continue
            
            df = df.dropna(subset=[col_name, 'Time'])
            df = df.sort_values('Time')
            
            if len(df) < predictive.window_size + 100:
                continue
            
            # Test on samples (reduced for faster benchmarking)
            test_indices = range(predictive.window_size, min(predictive.window_size + 200, len(df)))
            
            predictions = []
            actuals = []
            errors = []
            
            for i in test_indices:
                recent_data = df.iloc[i-predictive.window_size:i]
                actual_value = df.iloc[i][col_name]
                
                try:
                    pred, lower, upper = predictive.predict(sensor_name, col_name, recent_data)
                    if pred is not None:
                        predictions.append(pred)
                        actuals.append(actual_value)
                        errors.append(actual_value - pred)
                except:
                    pass
            
            if len(predictions) > 0:
                predictions = np.array(predictions)
                actuals = np.array(actuals)
                errors = np.array(errors)
                
                # Calculate metrics
                mae = np.mean(np.abs(errors))
                rmse = np.sqrt(np.mean(errors ** 2))
                mape = np.mean(np.abs(errors / (actuals + 1e-10))) * 100  # Mean Absolute Percentage Error
                
                # R² score
                ss_res = np.sum((actuals - predictions) ** 2)
                ss_tot = np.sum((actuals - np.mean(actuals)) ** 2)
                r2 = 1 - (ss_res / (ss_tot + 1e-10))
                
                # Coverage (percentage of actuals within bounds)
                coverage = 0
                for i, actual in enumerate(actuals):
                    _, lower, upper = predictive.predict(sensor_name, col_name, 
                                                         df.iloc[test_indices[i]-predictive.window_size:test_indices[i]])
                    if lower is not None and upper is not None:
                        if lower <= actual <= upper:
                            coverage += 1
                coverage_pct = (coverage / len(actuals)) * 100 if len(actuals) > 0 else 0
                
                print(f"\n{key}:")
                print(f"  Test samples: {len(predictions)}")
                print(f"  MAE (Mean Absolute Error): {mae:.6f}")
                print(f"  RMSE (Root Mean Squared Error): {rmse:.6f}")
                print(f"  MAPE (Mean Absolute % Error): {mape:.2f}%")
                print(f"  R² Score: {r2:.4f}")
                print(f"  Prediction Coverage: {coverage_pct:.1f}%")
                
                accuracy_results[key] = {
                    'mae': mae,
                    'rmse': rmse,
                    'mape': mape,
                    'r2_score': r2,
                    'coverage_pct': coverage_pct,
                    'num_samples': len(predictions)
                }
        
        self.results['prediction_accuracy'] = accuracy_results
        return accuracy_results
    
    def benchmark_anomaly_detection(self, predictive: PredictiveDetector, data: Dict):
        """Benchmark anomaly detection performance"""
        print("\n" + "=" * 80)
        print("BENCHMARK: Anomaly Detection Performance")
        print("=" * 80)
        
        detection_results = {}
        
        for key in predictive.models:
            sensor_name, col_name = key.split('.', 1)
            
            if sensor_name not in data:
                continue
            
            df = data[sensor_name].copy()
            if col_name not in df.columns:
                continue
            
            df = df.dropna(subset=[col_name, 'Time'])
            df = df.sort_values('Time')
            
            if len(df) < predictive.window_size + 100:
                continue
            
            # Test on samples (reduced for faster benchmarking)
            test_indices = range(predictive.window_size, min(predictive.window_size + 200, len(df)))
            
            true_anomalies = 0
            detected_anomalies = 0
            false_positives = 0
            false_negatives = 0
            
            detection_times = []
            
            for i in test_indices:
                recent_data = df.iloc[i-predictive.window_size:i]
                actual_value = df.iloc[i][col_name]
                
                # Determine if this is a true anomaly (using statistical method)
                # Anomaly = value is more than 3 standard deviations from mean
                mean_val = recent_data[col_name].mean()
                std_val = recent_data[col_name].std()
                is_true_anomaly = abs(actual_value - mean_val) > 3 * std_val if std_val > 0 else False
                
                if is_true_anomaly:
                    true_anomalies += 1
                
                # Detect anomaly
                start = time.time()
                result = predictive.detect_anomaly(sensor_name, col_name, actual_value, recent_data)
                detection_times.append(time.time() - start)
                
                if result['is_anomaly']:
                    detected_anomalies += 1
                    if not is_true_anomaly:
                        false_positives += 1
                else:
                    if is_true_anomaly:
                        false_negatives += 1
            
            # Calculate metrics
            precision = detected_anomalies / (detected_anomalies + false_positives) if (detected_anomalies + false_positives) > 0 else 0
            recall = detected_anomalies / (detected_anomalies + false_negatives) if (detected_anomalies + false_negatives) > 0 else 0
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            avg_detection_time = np.mean(detection_times) if detection_times else 0
            
            print(f"\n{key}:")
            print(f"  Test samples: {len(test_indices)}")
            print(f"  True anomalies: {true_anomalies}")
            print(f"  Detected anomalies: {detected_anomalies}")
            print(f"  False positives: {false_positives}")
            print(f"  False negatives: {false_negatives}")
            print(f"  Precision: {precision:.4f}")
            print(f"  Recall: {recall:.4f}")
            print(f"  F1 Score: {f1_score:.4f}")
            print(f"  Avg detection time: {avg_detection_time*1000:.3f} ms")
            
            detection_results[key] = {
                'precision': precision,
                'recall': recall,
                'f1_score': f1_score,
                'true_anomalies': true_anomalies,
                'detected_anomalies': detected_anomalies,
                'false_positives': false_positives,
                'false_negatives': false_negatives,
                'avg_detection_time_ms': avg_detection_time * 1000
            }
        
        self.results['anomaly_detection'] = detection_results
        return detection_results
    
    def benchmark_batch_processing(self, predictive: PredictiveDetector, data: Dict):
        """Benchmark batch processing performance"""
        print("\n" + "=" * 80)
        print("BENCHMARK: Batch Processing Performance")
        print("=" * 80)
        
        batch_results = {}
        
        # Test different batch sizes
        batch_sizes = [1, 10, 50, 100, 500]
        
        for key in list(predictive.models.keys())[:1]:  # Test on first model only
            sensor_name, col_name = key.split('.', 1)
            
            if sensor_name not in data:
                continue
            
            df = data[sensor_name].copy()
            if col_name not in df.columns:
                continue
            
            df = df.dropna(subset=[col_name, 'Time'])
            df = df.sort_values('Time')
            
            if len(df) < predictive.window_size + 500:
                continue
            
            batch_times = {}
            
            for batch_size in batch_sizes:
                test_indices = range(predictive.window_size, 
                                   min(predictive.window_size + batch_size, len(df)))
                
                # Time batch processing
                start = time.time()
                processed = 0
                
                for i in test_indices:
                    recent_data = df.iloc[i-predictive.window_size:i]
                    try:
                        pred, lower, upper = predictive.predict(sensor_name, col_name, recent_data)
                        if pred is not None:
                            processed += 1
                    except:
                        pass
                
                elapsed = time.time() - start
                throughput = processed / elapsed if elapsed > 0 else 0
                
                batch_times[batch_size] = {
                    'total_time_seconds': elapsed,
                    'samples_processed': processed,
                    'throughput_per_sec': throughput,
                    'time_per_sample_ms': (elapsed / processed * 1000) if processed > 0 else 0
                }
                
                print(f"\nBatch size {batch_size}:")
                print(f"  Total time: {elapsed:.4f} seconds")
                print(f"  Samples processed: {processed}")
                print(f"  Throughput: {throughput:.1f} samples/second")
                print(f"  Time per sample: {elapsed/processed*1000:.3f} ms" if processed > 0 else "  Time per sample: N/A")
            
            batch_results[key] = batch_times
        
        self.results['batch_processing'] = batch_results
        return batch_results
    
    def benchmark_full_detection_pipeline(self, detector: FalsificationDetector, 
                                         predictive: PredictiveDetector, data: Dict):
        """Benchmark the full falsification detection pipeline"""
        print("\n" + "=" * 80)
        print("BENCHMARK: Full Detection Pipeline")
        print("=" * 80)
        
        if 'cmd_vel' not in data:
            print("❌ cmd_vel data not available")
            return {}
        
        cmd_vel = data['cmd_vel']
        
        # Test on subset of data (reduced for faster benchmarking)
        test_size = min(200, len(cmd_vel))
        test_indices = range(0, test_size)
        
        detection_times = []
        detections = []
        
        print(f"\nTesting on {test_size} samples...")
        
        for idx in test_indices:
            row = cmd_vel.iloc[idx]
            timestamp = row['Time']
            
            # Get synchronized data
            synced = detector.synchronize_data(data, timestamp)
            
            # Time detection
            start = time.time()
            result = detector.detect_falsification(
                cmd_vel_data=synced.get('cmd_vel', {}),
                odom_data=synced.get('odometry'),
                imu_data=synced.get('imu'),
                joint_data=synced.get('joint_states'),
                timestamp=timestamp
            )
            detection_times.append(time.time() - start)
            detections.append(result)
        
        # Calculate statistics
        avg_time = np.mean(detection_times)
        std_time = np.std(detection_times)
        p95_time = np.percentile(detection_times, 95)
        p99_time = np.percentile(detection_times, 99)
        
        falsified_count = sum(1 for d in detections if d.is_falsified)
        avg_confidence = np.mean([d.confidence for d in detections])
        
        print(f"\nPipeline Performance:")
        print(f"  Samples processed: {test_size}")
        print(f"  Average detection time: {avg_time*1000:.3f} ms")
        print(f"  Std deviation: {std_time*1000:.3f} ms")
        print(f"  95th percentile: {p95_time*1000:.3f} ms")
        print(f"  99th percentile: {p99_time*1000:.3f} ms")
        print(f"  Throughput: {1.0/avg_time:.1f} detections/second")
        print(f"  Falsified detections: {falsified_count} ({falsified_count/test_size*100:.1f}%)")
        print(f"  Average confidence: {avg_confidence:.4f}")
        
        pipeline_results = {
            'avg_detection_time_ms': avg_time * 1000,
            'std_detection_time_ms': std_time * 1000,
            'p95_detection_time_ms': p95_time * 1000,
            'p99_detection_time_ms': p99_time * 1000,
            'throughput_per_sec': 1.0 / avg_time,
            'falsified_count': falsified_count,
            'falsified_percentage': falsified_count / test_size * 100,
            'avg_confidence': avg_confidence,
            'samples_processed': test_size
        }
        
        self.results['full_pipeline'] = pipeline_results
        return pipeline_results
    
    def generate_report(self, output_file='benchmark_report.txt'):
        """Generate comprehensive benchmark report"""
        print("\n" + "=" * 80)
        print("GENERATING BENCHMARK REPORT")
        print("=" * 80)
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("FALSIFICATION DETECTION MODEL - BENCHMARK REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # Model Loading
        if 'model_loading' in self.results:
            report_lines.append("=" * 80)
            report_lines.append("1. MODEL LOADING PERFORMANCE")
            report_lines.append("=" * 80)
            ml = self.results['model_loading']
            if ml.get('success', True):
                report_lines.append(f"Load Time: {ml.get('load_time_seconds', 0):.4f} seconds")
                report_lines.append(f"Models Loaded: {ml.get('num_models', 0)}")
                report_lines.append(f"Total Model Size: {ml.get('total_size_mb', 0):.2f} MB")
                report_lines.append(f"Loading Rate: {ml.get('models_per_second', 0):.2f} models/second")
            report_lines.append("")
        
        # Prediction Speed
        if 'prediction_speed' in self.results:
            report_lines.append("=" * 80)
            report_lines.append("2. PREDICTION SPEED")
            report_lines.append("=" * 80)
            for key, metrics in self.results['prediction_speed'].items():
                report_lines.append(f"\n{key}:")
                report_lines.append(f"  Average Latency: {metrics['avg_latency_ms']:.3f} ms")
                report_lines.append(f"  Throughput: {metrics['throughput_per_sec']:.1f} predictions/second")
                report_lines.append(f"  95th Percentile: {metrics['p95_latency_ms']:.3f} ms")
                report_lines.append(f"  99th Percentile: {metrics['p99_latency_ms']:.3f} ms")
            report_lines.append("")
        
        # Prediction Accuracy
        if 'prediction_accuracy' in self.results:
            report_lines.append("=" * 80)
            report_lines.append("3. PREDICTION ACCURACY")
            report_lines.append("=" * 80)
            for key, metrics in self.results['prediction_accuracy'].items():
                report_lines.append(f"\n{key}:")
                report_lines.append(f"  MAE: {metrics['mae']:.6f}")
                report_lines.append(f"  RMSE: {metrics['rmse']:.6f}")
                report_lines.append(f"  R² Score: {metrics['r2_score']:.4f}")
                report_lines.append(f"  Coverage: {metrics['coverage_pct']:.1f}%")
            report_lines.append("")
        
        # Anomaly Detection
        if 'anomaly_detection' in self.results:
            report_lines.append("=" * 80)
            report_lines.append("4. ANOMALY DETECTION PERFORMANCE")
            report_lines.append("=" * 80)
            for key, metrics in self.results['anomaly_detection'].items():
                report_lines.append(f"\n{key}:")
                report_lines.append(f"  Precision: {metrics['precision']:.4f}")
                report_lines.append(f"  Recall: {metrics['recall']:.4f}")
                report_lines.append(f"  F1 Score: {metrics['f1_score']:.4f}")
                report_lines.append(f"  Detection Time: {metrics['avg_detection_time_ms']:.3f} ms")
            report_lines.append("")
        
        # Batch Processing
        if 'batch_processing' in self.results:
            report_lines.append("=" * 80)
            report_lines.append("5. BATCH PROCESSING PERFORMANCE")
            report_lines.append("=" * 80)
            for key, batch_data in self.results['batch_processing'].items():
                report_lines.append(f"\n{key}:")
                for batch_size, metrics in batch_data.items():
                    report_lines.append(f"  Batch Size {batch_size}: {metrics['throughput_per_sec']:.1f} samples/sec")
            report_lines.append("")
        
        # Full Pipeline
        if 'full_pipeline' in self.results:
            report_lines.append("=" * 80)
            report_lines.append("6. FULL DETECTION PIPELINE")
            report_lines.append("=" * 80)
            fp = self.results['full_pipeline']
            report_lines.append(f"Average Detection Time: {fp['avg_detection_time_ms']:.3f} ms")
            report_lines.append(f"Throughput: {fp['throughput_per_sec']:.1f} detections/second")
            report_lines.append(f"Falsified Detections: {fp['falsified_count']} ({fp['falsified_percentage']:.1f}%)")
            report_lines.append(f"Average Confidence: {fp['avg_confidence']:.4f}")
            report_lines.append("")
        
        # Summary
        report_lines.append("=" * 80)
        report_lines.append("SUMMARY")
        report_lines.append("=" * 80)
        
        if 'prediction_speed' in self.results:
            all_latencies = [m['avg_latency_ms'] for m in self.results['prediction_speed'].values()]
            if all_latencies:
                report_lines.append(f"Average Prediction Latency: {np.mean(all_latencies):.3f} ms")
                report_lines.append(f"Best Throughput: {max([m['throughput_per_sec'] for m in self.results['prediction_speed'].values()]):.1f} predictions/sec")
        
        if 'prediction_accuracy' in self.results:
            all_r2 = [m['r2_score'] for m in self.results['prediction_accuracy'].values()]
            if all_r2:
                report_lines.append(f"Average R² Score: {np.mean(all_r2):.4f}")
        
        if 'anomaly_detection' in self.results:
            all_f1 = [m['f1_score'] for m in self.results['anomaly_detection'].values()]
            if all_f1:
                report_lines.append(f"Average F1 Score: {np.mean(all_f1):.4f}")
        
        report_lines.append("")
        report_lines.append("=" * 80)
        
        # Write report
        report_text = "\n".join(report_lines)
        with open(output_file, 'w') as f:
            f.write(report_text)
        
        print(f"\n✓ Report saved to {output_file}")
        print("\n" + report_text)
        
        return report_text
    
    def run_all_benchmarks(self):
        """Run all benchmark tests"""
        print("\n" + "=" * 80)
        print("COMPREHENSIVE BENCHMARK SUITE")
        print("=" * 80)
        
        # Load models and data
        detector, predictive, data = self.load_models_and_data()
        if not all([detector, predictive, data]):
            print("❌ Failed to load models or data. Cannot run benchmarks.")
            return
        
        # Run benchmarks
        self.benchmark_model_loading(predictive)
        self.benchmark_prediction_speed(predictive, data)
        self.benchmark_prediction_accuracy(predictive, data)
        self.benchmark_anomaly_detection(predictive, data)
        self.benchmark_batch_processing(predictive, data)
        self.benchmark_full_detection_pipeline(detector, predictive, data)
        
        # Generate report
        self.generate_report()
        
        print("\n" + "=" * 80)
        print("ALL BENCHMARKS COMPLETE!")
        print("=" * 80)


def main():
    """Main function"""
    benchmark = BenchmarkSuite(model_dir='models', demo_dir='demo')
    benchmark.run_all_benchmarks()


if __name__ == "__main__":
    main()

