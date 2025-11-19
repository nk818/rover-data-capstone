# Capstone Project - Falsification Detection System

This folder contains all model-related files, scripts, documentation, and benchmarks for the ROS Data Falsification Detection System.

## 📁 Folder Structure

```
capston/
├── models/                          # Trained machine learning models
│   ├── cmd_vel_linear_x_*.pkl      # Velocity command models
│   ├── odometry_*.pkl               # Odometry models
│   ├── imu_*.pkl                   # IMU models
│   ├── joint_states_*.pkl          # Joint state models
│   └── metadata.pkl                 # Model metadata
│
├── Core Model Scripts/
│   ├── predictive_model.py         # ML predictive detector
│   ├── falsification_detector.py   # Main detection system
│   ├── demo_predictions.py         # Prediction demonstrations
│   ├── check_sensors.py            # Sensor validation
│   ├── extract_sensor_info.py      # Sensor data extraction
│   └── live_monitor.py             # Real-time monitoring
│
├── Benchmarking/
│   ├── benchmark_model.py          # Benchmark suite
│   ├── visualize_benchmarks.py    # Visualization generator
│   ├── benchmark_report.txt        # Text benchmark report
│   ├── benchmark_results.json     # JSON benchmark data
│   ├── BENCHMARK_GUIDE.md          # Benchmark documentation
│   └── benchmark_plots/            # Visualization images
│       ├── prediction_speed.png
│       ├── prediction_accuracy.png
│       ├── anomaly_detection.png
│       ├── full_pipeline.png
│       └── summary_dashboard.png
│
└── Documentation/
    ├── README.md                    # Main project README
    ├── MODEL_LOCATION.md            # Model storage info
    ├── PREDICTIVE_MODEL.md          # Predictive model docs
    ├── EXPLANATION.md               # System explanation
    ├── PHYSICS_ENHANCEMENTS.md      # Physics model docs
    ├── SENSOR_ANALYSIS.md           # Sensor analysis
    └── SUMMARY.md                   # Project summary
```

## 🚀 Quick Start

### Running the Detection System
```bash
# Historical data analysis
python falsification_detector.py

# Live monitoring
python live_monitor.py

# Demo predictions
python demo_predictions.py
```

### Running Benchmarks
```bash
# Run benchmarks
python benchmark_model.py

# Generate visualizations
python visualize_benchmarks.py
```

## 📊 Model Information

### Trained Models
- **cmd_vel.linear.x**: Velocity command predictions
- **odometry.twist.twist.linear.x**: Odometry velocity predictions
- **imu.linear_acceleration.x**: IMU acceleration predictions
- **joint_states.velocity_0**: Joint state velocity predictions

### Model Performance
See `benchmark_report.txt` and `benchmark_plots/` for detailed performance metrics.

Key metrics:
- Average prediction latency: ~27.6 ms
- Best throughput: ~36.6 predictions/second
- cmd_vel model R² score: 0.9254 (excellent)
- Full pipeline: ~24,000 detections/second

## 📖 Documentation

- **README.md**: Main project overview and usage
- **MODEL_LOCATION.md**: Where models are stored and how to load them
- **PREDICTIVE_MODEL.md**: Details about the predictive ML models
- **EXPLANATION.md**: System architecture and detection methods
- **PHYSICS_ENHANCEMENTS.md**: Physics-based validation features
- **SENSOR_ANALYSIS.md**: Sensor data analysis
- **BENCHMARK_GUIDE.md**: How to run and interpret benchmarks
- **SUMMARY.md**: Project summary and findings

## 🔧 Requirements

All dependencies are listed in `requirements.txt` in the parent directory:
- pandas >= 1.3.0
- numpy >= 1.21.0
- scikit-learn >= 1.0.0
- scipy >= 1.7.0
- matplotlib (for visualizations)

## 📈 Benchmark Results

Comprehensive benchmark results are available in:
- **Text Report**: `benchmark_report.txt`
- **JSON Data**: `benchmark_results.json`
- **Visualizations**: `benchmark_plots/` directory
- **Guide**: `BENCHMARK_GUIDE.md`

## 🎯 Key Features

1. **Multi-Sensor Validation**: Cross-validates cmd_vel, odometry, IMU, and joint states
2. **Predictive Models**: ML-based anomaly detection using Random Forest
3. **Physics-Based Validation**: Accounts for deceleration, momentum, and external forces
4. **Real-Time Monitoring**: Live detection from ROS topics
5. **Comprehensive Benchmarks**: Speed, accuracy, and detection performance metrics

## 📝 Notes

- Models are automatically saved to `models/` directory after training
- Models can be loaded without retraining on subsequent runs
- Benchmark visualizations are generated as PNG files
- All scripts are designed to work with ROS bag files and live ROS topics

## 🔗 Related Files

Some related files remain in the parent directory:
- `requirements.txt`: Python dependencies
- `demo/`: Sample data files
- `falsification_detection_results.csv`: Detection results from historical analysis

