# ROS Data Falsification Detection System

A comprehensive system for detecting falsified robot data by cross-validating multiple sensor sources.

## Overview

This system detects when ROS bag files or live data streams have been tampered with, specifically when velocity commands have been falsified (e.g., set to zero when the robot is actually moving).

## Features

- **Multi-Sensor Validation**: Cross-validates cmd_vel, odometry, IMU, and joint state data
- **Historical Analysis**: Analyzes existing CSV data to find falsified entries
- **Live Monitoring**: Real-time detection from ROS topics
- **Anomaly Detection**: Identifies multiple types of inconsistencies
- **Confidence Scoring**: Provides confidence levels for detections

## Installation

### Prerequisites

- Python 3.7+
- ROS (for live monitoring)
- Required Python packages

### Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# For ROS (if using live monitoring)
# Ensure ROS is installed and sourced
source /opt/ros/<distro>/setup.bash
```

## Usage

### 1. Historical Data Analysis

Analyze existing CSV data files:

```bash
python falsification_detector.py
```

This will:
- Load all CSV files from the `demo/` directory
- Calculate baseline statistics
- Analyze historical data for falsification
- Generate `falsification_detection_results.csv` with results

### 2. Live Feed Monitoring

Monitor ROS topics in real-time:

```bash
# Start ROS master (if not already running)
roscore

# In another terminal, start the monitor
python live_monitor.py
```

The monitor will:
- Subscribe to `/cmd_vel`, `/odometry/filtered`, `/imu/data`, `/joint_states`
- Detect falsification in real-time
- Print alerts when falsified data is detected
- Save alerts to `alerts_YYYYMMDD.jsonl`

## Detection Methods

The system uses multiple validation techniques:

### 1. Command vs. Odometry Mismatch
- Detects when velocity commands are zero but odometry shows movement
- Confidence: High (0.8-0.9)

### 2. Command vs. IMU Mismatch
- Detects when commands are zero but IMU shows acceleration
- Confidence: Medium-High (0.75-0.85)

### 3. Command vs. Joint States Mismatch
- Detects when commands are zero but wheels are rotating
- Confidence: High (0.85-0.9)

### 4. Consecutive Zeros Pattern
- Detects suspicious patterns of consecutive zero commands
- Confidence: Medium (0.7)

### 5. Statistical Anomalies
- Identifies data that doesn't match expected patterns
- Uses baseline statistics from historical data

## Configuration

### Threshold Adjustment

Modify the confidence threshold in the detector:

```python
detector = FalsificationDetector(threshold=0.7)  # 0.0 to 1.0
```

- Lower threshold (0.5-0.6): More sensitive, more false positives
- Higher threshold (0.8-0.9): Less sensitive, fewer false positives

### Window Size

Adjust the window size for temporal analysis:

```python
detector = FalsificationDetector(window_size=10)  # Number of recent samples
```

## Output Files

### `falsification_detection_results.csv`
Contains detection results for all historical data:
- `timestamp`: Time of detection
- `is_falsified`: Boolean flag
- `confidence`: Confidence score (0-1)
- `num_anomalies`: Number of anomalies detected
- `anomalies`: List of anomaly types

### `alerts_YYYYMMDD.jsonl`
JSON Lines file containing real-time alerts:
- Timestamp and datetime
- Detection results
- Anomaly details
- Current sensor data snapshot

## Example Output

```
[🚨 FALSIFIED] Timestamp: 1400.50
  Confidence: 90.00%
  Anomalies detected:
    - ZERO_COMMAND_BUT_MOVING
    - CMD_ODOM_MISMATCH
  Details:
    zero_command_moving: {
      'cmd_velocity': 0.0,
      'odom_velocity': 0.5
    }
```

## Understanding the Data

See `EXPLANATION.md` for detailed information about:
- File structure
- Data relationships
- Security implications
- Detection strategies

## Troubleshooting

### No data loaded
- Ensure CSV files are in the `demo/` directory
- Check file names match expected format

### ROS topics not found
- Verify ROS is running: `rostopic list`
- Check topic names match your robot configuration
- Ensure topics are being published

### Low detection rate
- Adjust threshold lower
- Check that sensor data is synchronized
- Verify data quality in source files

## Security Considerations

This system helps detect:
- Tampered ROS bag files
- Falsified velocity commands
- Data manipulation attacks
- Unauthorized robot movement

## License

This project is for educational and security research purposes.

## Contributing

To improve detection:
1. Add new validation methods
2. Improve sensor synchronization
3. Enhance statistical analysis
4. Add machine learning models

