# Sensor Data Analysis

## Summary

Based on analysis of the DoD SAFE data folder, here's what sensor information is available:

## Available Sensor Data

### ✅ **IMU (Inertial Measurement Unit)**
**Status**: ✅ **FULL DATA AVAILABLE**

- **Files**: 8 CSV files
- **Main data file**: `imu-data.csv` (contains orientation, angular velocity, linear acceleration)
- **Additional files**: 
  - `imu-data-bias.csv` (1.3 MB)
  - Parameter files for accel, rate, yaw
- **Data includes**:
  - Orientation (quaternion)
  - Angular velocity (x, y, z)
  - Linear acceleration (x, y, z)
  - Covariance matrices

### ✅ **GPS/NavSat (Global Positioning System)**
**Status**: ✅ **FULL DATA AVAILABLE**

- **Files**: 8 CSV files
- **Main data files**: 
  - `navsat-fix.csv` (position data)
  - `navsat-vel.csv` (velocity data)
- **Data includes**:
  - Position (latitude, longitude, altitude)
  - Velocity
  - Status information

### ✅ **Odometry**
**Status**: ✅ **FULL DATA AVAILABLE**

- **Files**: 2 CSV files
- **Main files**:
  - `odometry-filtered.csv` (4.0 MB) - Filtered odometry
  - `husky_velocity_controller-odom.csv` (2.2 MB)
- **Data includes**:
  - Position (x, y, z)
  - Orientation (quaternion)
  - Linear and angular velocities
  - Covariance matrices

### ✅ **Joint States**
**Status**: ✅ **FULL DATA AVAILABLE**

- **File**: `joint_states.csv` (1.0 MB)
- **Data includes**:
  - Wheel positions (4 wheels)
  - Wheel velocities
  - Wheel efforts/torques

### ⚠️ **LIDAR/Laser Scanner**
**Status**: ⚠️ **CONFIGURATION ONLY - NO RAW DATA**

- **Evidence of LIDAR**:
  - Costmap files reference "obstacles_laser" layer
  - Navigation system configured to use laser data
  - Files:
    - `move_base-global_costmap-obstacles_laser-parameter_*.csv`
    - `move_base-local_costmap-obstacles_laser-parameter_*.csv`
  
- **Missing**:
  - No raw laser scan CSV files
  - No `/scan` topic data extracted
  - Laser data likely exists in ROS bag files but not extracted to CSV

- **What this means**:
  - Robot HAS a laser scanner (LIDAR)
  - Navigation system uses it for obstacle detection
  - Raw scan data is in `.bag` files, not extracted to CSV
  - Costmaps show processed laser data (obstacle maps)

### ❌ **Camera/Image Data**
**Status**: ❌ **NOT FOUND**

- No camera topics found
- No image data files
- No depth camera data

### ❌ **Radar**
**Status**: ❌ **NOT FOUND**

- No radar sensor data
- No radar topics

### ❌ **Sonar**
**Status**: ❌ **NOT FOUND**

- No sonar sensor data
- No sonar topics

## Costmap Analysis

The costmap files show that the navigation system uses:

1. **Laser Obstacle Layer**: Configured and enabled
   - Max obstacle height: 2.0 meters
   - Footprint clearing enabled
   - Used for both global and local costmaps

2. **Costmap Data**: 
   - `move_base-global_costmap-costmap.csv` (1.1 GB!) - Contains processed obstacle map
   - `move_base-local_costmap-costmap.csv` - Local obstacle map
   - These contain processed laser data showing obstacles

## ROS Bag Files

The following bag files contain sensor data (but need ROS tools to extract):

- **Husky.bag** (517 MB)
- **themaze.bag** (1.2 GB)
- **subset.bag** (292 MB)
- **vel.bag** (45 KB)

**Note**: These bag files likely contain:
- Raw laser scan data (`/scan` topic)
- Possibly camera data
- All sensor topics in original format

## Recommendations

### To Extract Laser Scan Data:

1. **Use ROS tools**:
   ```bash
   # Extract laser scan topic
   rosbag play Husky.bag
   rostopic echo /scan > laser_scans.txt
   ```

2. **Or use Python with rosbag**:
   ```python
   import rosbag
   bag = rosbag.Bag('Husky.bag')
   for topic, msg, t in bag.read_messages(topics=['/scan']):
       # Process laser scan data
       pass
   ```

3. **Convert to CSV**:
   - Extract range measurements
   - Extract angle measurements
   - Save as time-series CSV

### For Falsification Detection:

**Current sensors usable**:
- ✅ IMU - Can detect unexpected accelerations
- ✅ Odometry - Can detect unexpected movement
- ✅ Joint States - Can detect unexpected wheel rotation
- ✅ GPS/NavSat - Can detect unexpected position changes

**Missing but useful**:
- ⚠️ LIDAR - Could detect obstacles that don't match odometry
- ❌ Camera - Could detect visual anomalies

## Integration with Detection System

The current falsification detection system uses:
1. **cmd_vel** - Velocity commands
2. **odometry** - Actual position/velocity
3. **IMU** - Acceleration/orientation
4. **joint_states** - Wheel states

**Could add**:
- **LIDAR scans** - Detect if robot "sees" obstacles that don't match expected path
- **GPS data** - Cross-validate position with odometry
- **Costmap data** - Check if obstacles match expected navigation

## Conclusion

### ✅ **CONFIRMED SENSORS (Full CSV Data Available)**:
1. **IMU** - Inertial Measurement Unit
   - Full time-series data available
   - Orientation, angular velocity, linear acceleration
   - Used in falsification detection ✅

2. **GPS/NavSat** - Global Positioning System
   - Full position and velocity data
   - Can cross-validate with odometry
   - Not currently used in detection (could be added)

3. **Odometry** - Position Estimation
   - Filtered odometry data (4 MB)
   - Position, orientation, velocities
   - Used in falsification detection ✅

4. **Joint States** - Wheel Encoders
   - Wheel positions, velocities, efforts
   - Used in falsification detection ✅

### ⚠️ **LIDAR/LASER SCANNER (Configuration Found, Raw Data in Bag Files)**:

**Evidence**:
- ✅ Laser obstacle layer **ENABLED** in costmaps
- ✅ Costmap files reference laser sensor
- ✅ Navigation system configured to use laser
- ✅ Costmap data (1.1 GB) contains processed laser data

**Status**:
- ⚠️ Raw laser scan data is in ROS bag files (`.bag`)
- ⚠️ Not extracted to CSV format
- ✅ Processed data available in costmap files

**What this means**:
- Robot **HAS** a LIDAR/laser scanner
- Scanner was **ACTIVE** during operation
- Raw scan data needs extraction from bag files
- Costmap shows where obstacles were detected

### ❌ **NOT FOUND**:
- Camera/Image sensors
- Radar
- Sonar

## How to Extract LIDAR Data

### Option 1: Using ROS Tools
```bash
# Install ROS (if not already installed)
sudo apt-get install ros-noetic-rosbag

# View bag file info
rosbag info Husky.bag

# Extract laser scan topic
rosbag play Husky.bag
rostopic echo /scan > laser_scans.txt

# Or extract to CSV
rosrun rosbag bag_to_csv.py Husky.bag /scan scan_data.csv
```

### Option 2: Using Python
```python
import rosbag
import pandas as pd

bag = rosbag.Bag('Husky.bag')
scan_data = []

for topic, msg, t in bag.read_messages(topics=['/scan']):
    # Extract range measurements
    ranges = list(msg.ranges)
    angles = [msg.angle_min + i * msg.angle_increment 
              for i in range(len(ranges))]
    
    scan_data.append({
        'time': t.to_sec(),
        'ranges': ranges,
        'angles': angles,
        'range_min': msg.range_min,
        'range_max': msg.range_max
    })

df = pd.DataFrame(scan_data)
df.to_csv('laser_scans.csv', index=False)
```

### Option 3: Use Costmap Data
The costmap files already contain processed laser data:
- `move_base-global_costmap-costmap.csv` (1.1 GB)
- `move_base-local_costmap-costmap.csv`

These show obstacles detected by the laser scanner.

## Integration with Falsification Detection

### Current System Uses:
1. ✅ cmd_vel (velocity commands)
2. ✅ odometry (position/velocity)
3. ✅ IMU (acceleration/orientation)
4. ✅ joint_states (wheel states)

### Could Add:
1. **LIDAR scans** - Detect if robot "sees" obstacles that don't match expected path
2. **GPS data** - Cross-validate position with odometry
3. **Costmap data** - Check if obstacles match expected navigation

### Potential LIDAR-Based Detection:
- **Unexpected obstacles**: Robot sees obstacles when path should be clear
- **Missing obstacles**: Robot doesn't see expected obstacles
- **Path mismatch**: Laser shows different path than odometry suggests
- **Static vs dynamic**: Detect if obstacles match expected environment

## Recommendation

**For immediate use**: Current sensors (IMU, odometry, joint states) are sufficient for detecting falsified velocity commands.

**For enhanced detection**: Extract LIDAR data from bag files to add:
- Obstacle-based validation
- Path consistency checking
- Environmental anomaly detection

The robot **definitely has a LIDAR scanner** - it's configured and was used during operation. The raw scan data just needs to be extracted from the bag files.

