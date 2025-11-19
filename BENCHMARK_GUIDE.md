# Benchmark and Visualization Guide

## Overview

This guide explains the benchmarking system created for the falsification detection model. The system measures performance metrics including speed, accuracy, and detection capabilities.

## Files Created

### 1. Benchmark Script (`benchmark_model.py`)
Comprehensive benchmarking suite that measures:
- **Model Loading Speed**: Time to load trained models from disk
- **Prediction Speed**: Latency and throughput for each sensor model
- **Prediction Accuracy**: MAE, RMSE, R² score, and coverage
- **Anomaly Detection**: Precision, recall, F1 score
- **Batch Processing**: Performance with different batch sizes
- **Full Pipeline**: End-to-end detection performance

### 2. Visualization Script (`visualize_benchmarks.py`)
Generates visual charts and graphs from benchmark results:
- Prediction speed comparisons
- Accuracy metrics
- Anomaly detection performance
- Full pipeline statistics
- Summary dashboard

### 3. Generated Files

#### Benchmark Report (`benchmark_report.txt`)
Text-based report with all metrics and statistics.

#### Visualizations (`benchmark_plots/`)
- **prediction_speed.png**: Latency and throughput for each sensor
- **prediction_accuracy.png**: MAE, RMSE, R² scores, and coverage
- **anomaly_detection.png**: Precision, recall, F1 scores
- **full_pipeline.png**: End-to-end performance metrics
- **summary_dashboard.png**: Comprehensive overview of all metrics

#### Results JSON (`benchmark_results.json`)
Machine-readable format of all benchmark results for further analysis.

## How to Run

### Run Benchmarks Only
```bash
python benchmark_model.py
```

### Run Benchmarks and Generate Visualizations
```bash
python visualize_benchmarks.py
```

This will:
1. Run all benchmarks
2. Generate visualizations
3. Save results to JSON
4. Create benchmark report

## Key Metrics Explained

### Speed Metrics
- **Latency**: Time per prediction (milliseconds)
- **Throughput**: Predictions per second
- **Percentiles (95th, 99th)**: Performance under load

### Accuracy Metrics
- **MAE (Mean Absolute Error)**: Average prediction error
- **RMSE (Root Mean Squared Error)**: Penalizes larger errors more
- **R² Score**: Model fit quality (1.0 = perfect, 0 = baseline, negative = worse than baseline)
- **Coverage**: Percentage of actual values within prediction bounds

### Detection Metrics
- **Precision**: Of detected anomalies, how many are real? (fewer false positives)
- **Recall**: Of real anomalies, how many were detected? (fewer false negatives)
- **F1 Score**: Harmonic mean of precision and recall

## Current Benchmark Results Summary

Based on the latest run:

### Model Performance
- **Model Loading**: ~0.1 seconds for 4 models (3.12 MB total)
- **Average Prediction Latency**: ~27.6 ms
- **Best Throughput**: ~36.6 predictions/second

### Accuracy
- **cmd_vel.linear.x**: R² = 0.9254 (excellent), Coverage = 95.5%
- Other sensors show varying performance (some with negative R² indicating model issues)

### Detection
- **cmd_vel.linear.x**: F1 = 0.69 (moderate performance)
- Full pipeline: ~24,000 detections/second

### Full Pipeline
- **Throughput**: 24,394 detections/second
- **Falsified Detection Rate**: 33.5% of samples
- **Average Confidence**: 0.28

## Interpreting Results

### Good Performance Indicators
- ✅ R² Score > 0.7
- ✅ Coverage > 95%
- ✅ Latency < 50ms
- ✅ F1 Score > 0.7
- ✅ Throughput > 30 predictions/sec

### Areas for Improvement
- ⚠️ Some sensors show negative R² scores (model may need retraining)
- ⚠️ Low F1 scores for some sensors (may need threshold tuning)
- ⚠️ High false positive rates in anomaly detection

## Tips for Improvement

1. **Retrain Models**: If R² scores are negative, the model may not fit the data well
2. **Adjust Thresholds**: Tune confidence thresholds to balance precision/recall
3. **Feature Engineering**: Add more features or adjust window size
4. **Data Quality**: Ensure training data is representative and clean

## Next Steps

1. Review the visualizations in `benchmark_plots/`
2. Check `benchmark_report.txt` for detailed metrics
3. Use `benchmark_results.json` for programmatic analysis
4. Iterate on model improvements based on findings

## Troubleshooting

### Visualizations Not Generated
- Ensure matplotlib is installed: `pip install matplotlib`
- Check that benchmarks completed successfully
- Verify `benchmark_plots/` directory exists

### Extreme R² Values
- Negative R² values indicate the model performs worse than a simple baseline
- Consider retraining with different parameters
- Check data quality and feature engineering

### Missing Batch Processing Data
- Batch processing benchmark may not run if insufficient data
- This is normal and can be skipped

## Files Structure

```
DoD SAFE-tWObA2Vtnk8vL9AT/
├── benchmark_model.py          # Benchmark script
├── visualize_benchmarks.py     # Visualization script
├── benchmark_report.txt         # Text report
├── benchmark_results.json       # JSON results
└── benchmark_plots/            # Visualization images
    ├── prediction_speed.png
    ├── prediction_accuracy.png
    ├── anomaly_detection.png
    ├── full_pipeline.png
    └── summary_dashboard.png
```

