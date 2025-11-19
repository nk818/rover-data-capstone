#!/usr/bin/env python3
"""
Visualization Script for Benchmark Results
Creates charts and graphs for model performance metrics
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import json
import os
from typing import Dict
import warnings
warnings.filterwarnings('ignore')

# Import benchmark suite
from benchmark_model import BenchmarkSuite

class BenchmarkVisualizer:
    """Create visualizations from benchmark results"""
    
    def __init__(self, output_dir='benchmark_plots'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.results = {}
    
    def run_benchmarks(self):
        """Run benchmarks and collect results"""
        print("Running benchmarks...")
        suite = BenchmarkSuite(model_dir='models', demo_dir='demo')
        suite.run_all_benchmarks()
        self.results = suite.results
        return self.results
    
    def load_results_from_file(self, filepath='benchmark_results.json'):
        """Load results from JSON file"""
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                self.results = json.load(f)
            return True
        return False
    
    def save_results_to_file(self, filepath='benchmark_results.json'):
        """Save results to JSON file"""
        # Convert numpy types to native Python types for JSON
        def convert_to_json(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_to_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_json(item) for item in obj]
            return obj
        
        json_results = convert_to_json(self.results)
        with open(filepath, 'w') as f:
            json.dump(json_results, f, indent=2)
        print(f"✓ Results saved to {filepath}")
    
    def plot_prediction_speed(self):
        """Create visualization for prediction speed"""
        if 'prediction_speed' not in self.results:
            print("⚠ No prediction speed data available")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Prediction Speed Benchmarks', fontsize=16, fontweight='bold')
        
        sensors = list(self.results['prediction_speed'].keys())
        latencies = [self.results['prediction_speed'][s]['avg_latency_ms'] for s in sensors]
        throughputs = [self.results['prediction_speed'][s]['throughput_per_sec'] for s in sensors]
        p95_latencies = [self.results['prediction_speed'][s]['p95_latency_ms'] for s in sensors]
        p99_latencies = [self.results['prediction_speed'][s]['p99_latency_ms'] for s in sensors]
        
        # 1. Average Latency by Sensor
        ax1 = axes[0, 0]
        bars1 = ax1.bar(range(len(sensors)), latencies, color='steelblue', alpha=0.7)
        ax1.set_xlabel('Sensor', fontweight='bold')
        ax1.set_ylabel('Latency (ms)', fontweight='bold')
        ax1.set_title('Average Prediction Latency', fontweight='bold')
        ax1.set_xticks(range(len(sensors)))
        ax1.set_xticklabels([s.replace('.', '.\n') for s in sensors], rotation=0, ha='center')
        ax1.grid(axis='y', alpha=0.3)
        for i, (bar, val) in enumerate(zip(bars1, latencies)):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(latencies)*0.01,
                    f'{val:.2f}', ha='center', va='bottom', fontsize=9)
        
        # 2. Throughput by Sensor
        ax2 = axes[0, 1]
        bars2 = ax2.bar(range(len(sensors)), throughputs, color='forestgreen', alpha=0.7)
        ax2.set_xlabel('Sensor', fontweight='bold')
        ax2.set_ylabel('Throughput (predictions/sec)', fontweight='bold')
        ax2.set_title('Prediction Throughput', fontweight='bold')
        ax2.set_xticks(range(len(sensors)))
        ax2.set_xticklabels([s.replace('.', '.\n') for s in sensors], rotation=0, ha='center')
        ax2.grid(axis='y', alpha=0.3)
        for i, (bar, val) in enumerate(zip(bars2, throughputs)):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(throughputs)*0.01,
                    f'{val:.0f}', ha='center', va='bottom', fontsize=9)
        
        # 3. Latency Percentiles
        ax3 = axes[1, 0]
        x = np.arange(len(sensors))
        width = 0.25
        ax3.bar(x - width, latencies, width, label='Average', color='steelblue', alpha=0.7)
        ax3.bar(x, p95_latencies, width, label='95th Percentile', color='orange', alpha=0.7)
        ax3.bar(x + width, p99_latencies, width, label='99th Percentile', color='crimson', alpha=0.7)
        ax3.set_xlabel('Sensor', fontweight='bold')
        ax3.set_ylabel('Latency (ms)', fontweight='bold')
        ax3.set_title('Latency Distribution (Percentiles)', fontweight='bold')
        ax3.set_xticks(x)
        ax3.set_xticklabels([s.replace('.', '.\n') for s in sensors], rotation=0, ha='center')
        ax3.legend()
        ax3.grid(axis='y', alpha=0.3)
        
        # 4. Speed Comparison (latency vs throughput)
        ax4 = axes[1, 1]
        scatter = ax4.scatter(latencies, throughputs, s=200, alpha=0.6, c=range(len(sensors)), 
                             cmap='viridis', edgecolors='black', linewidth=1.5)
        for i, sensor in enumerate(sensors):
            ax4.annotate(sensor.split('.')[0], (latencies[i], throughputs[i]), 
                        fontsize=8, ha='center', va='bottom')
        ax4.set_xlabel('Average Latency (ms)', fontweight='bold')
        ax4.set_ylabel('Throughput (predictions/sec)', fontweight='bold')
        ax4.set_title('Speed vs Throughput Trade-off', fontweight='bold')
        ax4.grid(alpha=0.3)
        
        plt.tight_layout()
        output_path = os.path.join(self.output_dir, 'prediction_speed.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {output_path}")
        plt.close()
    
    def plot_prediction_accuracy(self):
        """Create visualization for prediction accuracy"""
        if 'prediction_accuracy' not in self.results:
            print("⚠ No prediction accuracy data available")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Prediction Accuracy Benchmarks', fontsize=16, fontweight='bold')
        
        sensors = list(self.results['prediction_accuracy'].keys())
        mae_values = [self.results['prediction_accuracy'][s]['mae'] for s in sensors]
        rmse_values = [self.results['prediction_accuracy'][s]['rmse'] for s in sensors]
        r2_values = [self.results['prediction_accuracy'][s]['r2_score'] for s in sensors]
        coverage_values = [self.results['prediction_accuracy'][s]['coverage_pct'] for s in sensors]
        
        # 1. MAE by Sensor
        ax1 = axes[0, 0]
        bars1 = ax1.bar(range(len(sensors)), mae_values, color='coral', alpha=0.7)
        ax1.set_xlabel('Sensor', fontweight='bold')
        ax1.set_ylabel('MAE (Mean Absolute Error)', fontweight='bold')
        ax1.set_title('Mean Absolute Error', fontweight='bold')
        ax1.set_xticks(range(len(sensors)))
        ax1.set_xticklabels([s.replace('.', '.\n') for s in sensors], rotation=0, ha='center')
        ax1.grid(axis='y', alpha=0.3)
        for i, (bar, val) in enumerate(zip(bars1, mae_values)):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(mae_values)*0.01,
                    f'{val:.4f}', ha='center', va='bottom', fontsize=9)
        
        # 2. RMSE by Sensor
        ax2 = axes[0, 1]
        bars2 = ax2.bar(range(len(sensors)), rmse_values, color='mediumpurple', alpha=0.7)
        ax2.set_xlabel('Sensor', fontweight='bold')
        ax2.set_ylabel('RMSE (Root Mean Squared Error)', fontweight='bold')
        ax2.set_title('Root Mean Squared Error', fontweight='bold')
        ax2.set_xticks(range(len(sensors)))
        ax2.set_xticklabels([s.replace('.', '.\n') for s in sensors], rotation=0, ha='center')
        ax2.grid(axis='y', alpha=0.3)
        for i, (bar, val) in enumerate(zip(bars2, rmse_values)):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(rmse_values)*0.01,
                    f'{val:.4f}', ha='center', va='bottom', fontsize=9)
        
        # 3. R² Score (clip extreme values for visualization)
        ax3 = axes[1, 0]
        # Clip R² values to reasonable range for visualization (-2 to 1.1)
        r2_clipped = [max(-2.0, min(1.1, r2)) for r2 in r2_values]
        bars3 = ax3.bar(range(len(sensors)), r2_clipped, color='teal', alpha=0.7)
        ax3.set_xlabel('Sensor', fontweight='bold')
        ax3.set_ylabel('R² Score (clipped)', fontweight='bold')
        ax3.set_title('R² Score (Higher is Better)', fontweight='bold')
        ax3.set_xticks(range(len(sensors)))
        ax3.set_xticklabels([s.replace('.', '.\n') for s in sensors], rotation=0, ha='center')
        ax3.axhline(y=0.9, color='green', linestyle='--', alpha=0.5, label='Excellent (0.9)')
        ax3.axhline(y=0.7, color='orange', linestyle='--', alpha=0.5, label='Good (0.7)')
        ax3.axhline(y=0.5, color='red', linestyle='--', alpha=0.5, label='Acceptable (0.5)')
        ax3.axhline(y=0.0, color='black', linestyle='-', alpha=0.3, linewidth=1)
        ax3.set_ylim([-2.1, 1.1])
        ax3.grid(axis='y', alpha=0.3)
        ax3.legend()
        for i, (bar, val, val_orig) in enumerate(zip(bars3, r2_clipped, r2_values)):
            # Show original value if it was clipped
            if val_orig < -2.0 or val_orig > 1.1:
                label = f'{val_orig:.1f}*'
            else:
                label = f'{val:.3f}'
            ax3.text(bar.get_x() + bar.get_width()/2, 
                    min(bar.get_height() + 0.05, 1.0) if bar.get_height() > 0 else max(bar.get_height() - 0.05, -2.0),
                    label, ha='center', va='bottom' if bar.get_height() > 0 else 'top', fontsize=8)
        
        # 4. Coverage Percentage
        ax4 = axes[1, 1]
        bars4 = ax4.bar(range(len(sensors)), coverage_values, color='gold', alpha=0.7)
        ax4.set_xlabel('Sensor', fontweight='bold')
        ax4.set_ylabel('Coverage (%)', fontweight='bold')
        ax4.set_title('Prediction Coverage (95% Confidence)', fontweight='bold')
        ax4.set_xticks(range(len(sensors)))
        ax4.set_xticklabels([s.replace('.', '.\n') for s in sensors], rotation=0, ha='center')
        ax4.axhline(y=95, color='green', linestyle='--', alpha=0.5, label='Target (95%)')
        ax4.set_ylim([0, 100])
        ax4.grid(axis='y', alpha=0.3)
        ax4.legend()
        for i, (bar, val) in enumerate(zip(bars4, coverage_values)):
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                    f'{val:.1f}%', ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        output_path = os.path.join(self.output_dir, 'prediction_accuracy.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {output_path}")
        plt.close()
    
    def plot_anomaly_detection(self):
        """Create visualization for anomaly detection performance"""
        if 'anomaly_detection' not in self.results:
            print("⚠ No anomaly detection data available")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Anomaly Detection Performance', fontsize=16, fontweight='bold')
        
        sensors = list(self.results['anomaly_detection'].keys())
        precision_values = [self.results['anomaly_detection'][s]['precision'] for s in sensors]
        recall_values = [self.results['anomaly_detection'][s]['recall'] for s in sensors]
        f1_values = [self.results['anomaly_detection'][s]['f1_score'] for s in sensors]
        detection_times = [self.results['anomaly_detection'][s]['avg_detection_time_ms'] for s in sensors]
        
        # 1. Precision, Recall, F1 Comparison
        ax1 = axes[0, 0]
        x = np.arange(len(sensors))
        width = 0.25
        ax1.bar(x - width, precision_values, width, label='Precision', color='steelblue', alpha=0.7)
        ax1.bar(x, recall_values, width, label='Recall', color='forestgreen', alpha=0.7)
        ax1.bar(x + width, f1_values, width, label='F1 Score', color='crimson', alpha=0.7)
        ax1.set_xlabel('Sensor', fontweight='bold')
        ax1.set_ylabel('Score', fontweight='bold')
        ax1.set_title('Precision, Recall, and F1 Score', fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels([s.replace('.', '.\n') for s in sensors], rotation=0, ha='center')
        ax1.set_ylim([0, 1.1])
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3)
        
        # 2. F1 Score by Sensor
        ax2 = axes[0, 1]
        bars2 = ax2.bar(range(len(sensors)), f1_values, color='crimson', alpha=0.7)
        ax2.set_xlabel('Sensor', fontweight='bold')
        ax2.set_ylabel('F1 Score', fontweight='bold')
        ax2.set_title('F1 Score (Overall Detection Quality)', fontweight='bold')
        ax2.set_xticks(range(len(sensors)))
        ax2.set_xticklabels([s.replace('.', '.\n') for s in sensors], rotation=0, ha='center')
        ax2.axhline(y=0.9, color='green', linestyle='--', alpha=0.5, label='Excellent (0.9)')
        ax2.axhline(y=0.7, color='orange', linestyle='--', alpha=0.5, label='Good (0.7)')
        ax2.set_ylim([0, 1.1])
        ax2.grid(axis='y', alpha=0.3)
        ax2.legend()
        for i, (bar, val) in enumerate(zip(bars2, f1_values)):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                    f'{val:.3f}', ha='center', va='bottom', fontsize=9)
        
        # 3. Detection Time
        ax3 = axes[1, 0]
        bars3 = ax3.bar(range(len(sensors)), detection_times, color='darkorange', alpha=0.7)
        ax3.set_xlabel('Sensor', fontweight='bold')
        ax3.set_ylabel('Detection Time (ms)', fontweight='bold')
        ax3.set_title('Anomaly Detection Latency', fontweight='bold')
        ax3.set_xticks(range(len(sensors)))
        ax3.set_xticklabels([s.replace('.', '.\n') for s in sensors], rotation=0, ha='center')
        ax3.grid(axis='y', alpha=0.3)
        for i, (bar, val) in enumerate(zip(bars3, detection_times)):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(detection_times)*0.01,
                    f'{val:.2f}', ha='center', va='bottom', fontsize=9)
        
        # 4. Precision-Recall Trade-off
        ax4 = axes[1, 1]
        scatter = ax4.scatter(precision_values, recall_values, s=200, alpha=0.6, 
                            c=f1_values, cmap='RdYlGn', edgecolors='black', linewidth=1.5,
                            vmin=0, vmax=1)
        for i, sensor in enumerate(sensors):
            ax4.annotate(sensor.split('.')[0], (precision_values[i], recall_values[i]), 
                        fontsize=8, ha='center', va='bottom')
        ax4.set_xlabel('Precision', fontweight='bold')
        ax4.set_ylabel('Recall', fontweight='bold')
        ax4.set_title('Precision-Recall Trade-off (Color = F1 Score)', fontweight='bold')
        ax4.set_xlim([0, 1.1])
        ax4.set_ylim([0, 1.1])
        ax4.grid(alpha=0.3)
        plt.colorbar(scatter, ax=ax4, label='F1 Score')
        
        plt.tight_layout()
        output_path = os.path.join(self.output_dir, 'anomaly_detection.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {output_path}")
        plt.close()
    
    def plot_batch_processing(self):
        """Create visualization for batch processing performance"""
        if 'batch_processing' not in self.results or not self.results['batch_processing']:
            print("⚠ No batch processing data available")
            return
        
        # Get data for first sensor (all should be similar)
        sensor_keys = list(self.results['batch_processing'].keys())
        if not sensor_keys:
            print("⚠ No batch processing data available")
            return
        
        sensor_key = sensor_keys[0]
        batch_data = self.results['batch_processing'][sensor_key]
        
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))
        fig.suptitle('Batch Processing Performance', fontsize=16, fontweight='bold')
        
        batch_sizes = sorted(batch_data.keys())
        throughputs = [batch_data[bs]['throughput_per_sec'] for bs in batch_sizes]
        times_per_sample = [batch_data[bs]['time_per_sample_ms'] for bs in batch_sizes]
        
        # 1. Throughput vs Batch Size
        ax1 = axes[0]
        ax1.plot(batch_sizes, throughputs, marker='o', linewidth=2, markersize=10, 
                color='steelblue', label='Throughput')
        ax1.set_xlabel('Batch Size', fontweight='bold')
        ax1.set_ylabel('Throughput (samples/sec)', fontweight='bold')
        ax1.set_title('Throughput vs Batch Size', fontweight='bold')
        ax1.grid(alpha=0.3)
        ax1.legend()
        for bs, tp in zip(batch_sizes, throughputs):
            ax1.annotate(f'{tp:.0f}', (bs, tp), textcoords="offset points", 
                        xytext=(0,10), ha='center', fontsize=9)
        
        # 2. Time per Sample vs Batch Size
        ax2 = axes[1]
        ax2.plot(batch_sizes, times_per_sample, marker='s', linewidth=2, markersize=10, 
                color='crimson', label='Time per Sample')
        ax2.set_xlabel('Batch Size', fontweight='bold')
        ax2.set_ylabel('Time per Sample (ms)', fontweight='bold')
        ax2.set_title('Latency vs Batch Size', fontweight='bold')
        ax2.grid(alpha=0.3)
        ax2.legend()
        for bs, tps in zip(batch_sizes, times_per_sample):
            ax2.annotate(f'{tps:.2f}', (bs, tps), textcoords="offset points", 
                        xytext=(0,10), ha='center', fontsize=9)
        
        plt.tight_layout()
        output_path = os.path.join(self.output_dir, 'batch_processing.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {output_path}")
        plt.close()
    
    def plot_full_pipeline(self):
        """Create visualization for full pipeline performance"""
        if 'full_pipeline' not in self.results:
            print("⚠ No full pipeline data available")
            return
        
        fp = self.results['full_pipeline']
        
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        fig.suptitle('Full Detection Pipeline Performance', fontsize=16, fontweight='bold')
        
        # 1. Detection Time Distribution
        ax1 = axes[0]
        metrics = ['Average', '95th %ile', '99th %ile']
        times = [fp['avg_detection_time_ms'], 
                fp['p95_detection_time_ms'], 
                fp['p99_detection_time_ms']]
        bars1 = ax1.bar(metrics, times, color=['steelblue', 'orange', 'crimson'], alpha=0.7)
        ax1.set_ylabel('Detection Time (ms)', fontweight='bold')
        ax1.set_title('Detection Latency Distribution', fontweight='bold')
        ax1.grid(axis='y', alpha=0.3)
        for bar, val in zip(bars1, times):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(times)*0.01,
                    f'{val:.2f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        # 2. Throughput
        ax2 = axes[1]
        throughput = fp['throughput_per_sec']
        bar2 = ax2.bar(['Throughput'], [throughput], color='forestgreen', alpha=0.7, width=0.5)
        ax2.set_ylabel('Detections per Second', fontweight='bold')
        ax2.set_title('Pipeline Throughput', fontweight='bold')
        ax2.grid(axis='y', alpha=0.3)
        ax2.text(bar2[0].get_x() + bar2[0].get_width()/2, bar2[0].get_height() + throughput*0.01,
                f'{throughput:.1f}', ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        # 3. Detection Statistics
        ax3 = axes[2]
        categories = ['Falsified\nDetections', 'Normal\nDetections']
        counts = [fp['falsified_count'], 
                 fp['samples_processed'] - fp['falsified_count']]
        colors = ['crimson', 'steelblue']
        bars3 = ax3.bar(categories, counts, color=colors, alpha=0.7)
        ax3.set_ylabel('Count', fontweight='bold')
        ax3.set_title('Detection Results Distribution', fontweight='bold')
        ax3.grid(axis='y', alpha=0.3)
        for bar, val in zip(bars3, counts):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(counts)*0.01,
                    f'{val}', ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        output_path = os.path.join(self.output_dir, 'full_pipeline.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {output_path}")
        plt.close()
    
    def plot_summary_dashboard(self):
        """Create a comprehensive summary dashboard"""
        fig = plt.figure(figsize=(20, 12))
        gs = fig.add_gridspec(3, 4, hspace=0.3, wspace=0.3)
        fig.suptitle('Model Performance Summary Dashboard', fontsize=18, fontweight='bold', y=0.98)
        
        # 1. Average Latency (Top Left)
        if 'prediction_speed' in self.results:
            ax1 = fig.add_subplot(gs[0, 0])
            sensors = list(self.results['prediction_speed'].keys())
            latencies = [self.results['prediction_speed'][s]['avg_latency_ms'] for s in sensors]
            ax1.barh(range(len(sensors)), latencies, color='steelblue', alpha=0.7)
            ax1.set_yticks(range(len(sensors)))
            ax1.set_yticklabels([s.split('.')[0] for s in sensors])
            ax1.set_xlabel('Latency (ms)', fontweight='bold')
            ax1.set_title('Avg Prediction Latency', fontweight='bold')
            ax1.grid(axis='x', alpha=0.3)
        
        # 2. R² Score (Top Middle Left) - clip extreme values
        if 'prediction_accuracy' in self.results:
            ax2 = fig.add_subplot(gs[0, 1])
            sensors = list(self.results['prediction_accuracy'].keys())
            r2_values = [self.results['prediction_accuracy'][s]['r2_score'] for s in sensors]
            r2_clipped = [max(-2.0, min(1.1, r2)) for r2 in r2_values]
            ax2.barh(range(len(sensors)), r2_clipped, color='teal', alpha=0.7)
            ax2.set_yticks(range(len(sensors)))
            ax2.set_yticklabels([s.split('.')[0] for s in sensors])
            ax2.set_xlabel('R² Score (clipped)', fontweight='bold')
            ax2.set_title('Prediction Accuracy (R²)', fontweight='bold')
            ax2.set_xlim([-2.1, 1.1])
            ax2.axvline(x=0.9, color='green', linestyle='--', alpha=0.5)
            ax2.axvline(x=0.0, color='black', linestyle='-', alpha=0.3, linewidth=1)
            ax2.grid(axis='x', alpha=0.3)
        
        # 3. F1 Score (Top Middle Right)
        if 'anomaly_detection' in self.results:
            ax3 = fig.add_subplot(gs[0, 2])
            sensors = list(self.results['anomaly_detection'].keys())
            f1_values = [self.results['anomaly_detection'][s]['f1_score'] for s in sensors]
            ax3.barh(range(len(sensors)), f1_values, color='crimson', alpha=0.7)
            ax3.set_yticks(range(len(sensors)))
            ax3.set_yticklabels([s.split('.')[0] for s in sensors])
            ax3.set_xlabel('F1 Score', fontweight='bold')
            ax3.set_title('Anomaly Detection (F1)', fontweight='bold')
            ax3.set_xlim([0, 1.1])
            ax3.axvline(x=0.7, color='orange', linestyle='--', alpha=0.5)
            ax3.grid(axis='x', alpha=0.3)
        
        # 4. Throughput (Top Right)
        if 'prediction_speed' in self.results:
            ax4 = fig.add_subplot(gs[0, 3])
            sensors = list(self.results['prediction_speed'].keys())
            throughputs = [self.results['prediction_speed'][s]['throughput_per_sec'] for s in sensors]
            ax4.barh(range(len(sensors)), throughputs, color='forestgreen', alpha=0.7)
            ax4.set_yticks(range(len(sensors)))
            ax4.set_yticklabels([s.split('.')[0] for s in sensors])
            ax4.set_xlabel('Throughput (pred/sec)', fontweight='bold')
            ax4.set_title('Prediction Throughput', fontweight='bold')
            ax4.grid(axis='x', alpha=0.3)
        
        # 5. Error Metrics (Middle Left - spans 2)
        if 'prediction_accuracy' in self.results:
            ax5 = fig.add_subplot(gs[1, 0:2])
            sensors = list(self.results['prediction_accuracy'].keys())
            x = np.arange(len(sensors))
            width = 0.35
            mae = [self.results['prediction_accuracy'][s]['mae'] for s in sensors]
            rmse = [self.results['prediction_accuracy'][s]['rmse'] for s in sensors]
            ax5.bar(x - width/2, mae, width, label='MAE', color='coral', alpha=0.7)
            ax5.bar(x + width/2, rmse, width, label='RMSE', color='mediumpurple', alpha=0.7)
            ax5.set_xticks(x)
            ax5.set_xticklabels([s.split('.')[0] for s in sensors], rotation=45, ha='right')
            ax5.set_ylabel('Error', fontweight='bold')
            ax5.set_title('Prediction Error Metrics', fontweight='bold')
            ax5.legend()
            ax5.grid(axis='y', alpha=0.3)
        
        # 6. Precision-Recall (Middle Right - spans 2)
        if 'anomaly_detection' in self.results:
            ax6 = fig.add_subplot(gs[1, 2:4])
            sensors = list(self.results['anomaly_detection'].keys())
            precision = [self.results['anomaly_detection'][s]['precision'] for s in sensors]
            recall = [self.results['anomaly_detection'][s]['recall'] for s in sensors]
            x = np.arange(len(sensors))
            width = 0.35
            ax6.bar(x - width/2, precision, width, label='Precision', color='steelblue', alpha=0.7)
            ax6.bar(x + width/2, recall, width, label='Recall', color='forestgreen', alpha=0.7)
            ax6.set_xticks(x)
            ax6.set_xticklabels([s.split('.')[0] for s in sensors], rotation=45, ha='right')
            ax6.set_ylabel('Score', fontweight='bold')
            ax6.set_title('Anomaly Detection: Precision vs Recall', fontweight='bold')
            ax6.set_ylim([0, 1.1])
            ax6.legend()
            ax6.grid(axis='y', alpha=0.3)
        
        # 7. Pipeline Performance (Bottom - spans 4)
        if 'full_pipeline' in self.results:
            ax7 = fig.add_subplot(gs[2, :])
            fp = self.results['full_pipeline']
            metrics = ['Avg Latency\n(ms)', 'Throughput\n(pred/sec)', 'Falsified\n(%)', 'Avg Confidence']
            values = [fp['avg_detection_time_ms'], 
                     fp['throughput_per_sec'],
                     fp['falsified_percentage'],
                     fp['avg_confidence'] * 100]
            colors = ['steelblue', 'forestgreen', 'crimson', 'gold']
            bars = ax7.bar(metrics, values, color=colors, alpha=0.7)
            ax7.set_ylabel('Value', fontweight='bold')
            ax7.set_title('Full Pipeline Performance Metrics', fontweight='bold')
            ax7.grid(axis='y', alpha=0.3)
            for bar, val in zip(bars, values):
                ax7.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.01,
                        f'{val:.2f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        output_path = os.path.join(self.output_dir, 'summary_dashboard.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {output_path}")
        plt.close()
    
    def generate_all_visualizations(self):
        """Generate all visualizations"""
        print("\n" + "=" * 80)
        print("GENERATING VISUALIZATIONS")
        print("=" * 80)
        
        if not self.results:
            print("⚠ No results available. Running benchmarks first...")
            self.run_benchmarks()
        
        print(f"\nOutput directory: {self.output_dir}/")
        
        self.plot_prediction_speed()
        self.plot_prediction_accuracy()
        self.plot_anomaly_detection()
        self.plot_batch_processing()
        self.plot_full_pipeline()
        self.plot_summary_dashboard()
        
        print("\n" + "=" * 80)
        print("ALL VISUALIZATIONS GENERATED!")
        print("=" * 80)
        print(f"\nVisualizations saved to: {self.output_dir}/")
        print("  - prediction_speed.png")
        print("  - prediction_accuracy.png")
        print("  - anomaly_detection.png")
        print("  - batch_processing.png")
        print("  - full_pipeline.png")
        print("  - summary_dashboard.png")


def main():
    """Main function"""
    visualizer = BenchmarkVisualizer(output_dir='benchmark_plots')
    visualizer.generate_all_visualizations()
    
    # Save results to JSON for later use
    visualizer.save_results_to_file('benchmark_results.json')


if __name__ == "__main__":
    main()

