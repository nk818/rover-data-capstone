# DoD SAFE Data Analysis & Falsification Detection System

## Overview
This folder contains ROS (Robot Operating System) data from a Husky ground robot, including sensor data, control commands, and navigation information. The data has been manipulated using a bag editor script that falsified velocity commands.

---

## File Structure Explanation

### Python Scripts

#### 1. `bag_editor.py`
**Purpose**: Edits ROS bag files to modify message data
**What it does**:
- Reads a ROS bag file specified in `keyfile.txt`
- Copies all topics EXCEPT `/cmd_vel` (velocity commands) unchanged
- **FALSIFIES DATA**: Sets all velocity commands to zero:
  - `linear.x = 0.0`
  - `linear.y = 0.0`
  - `linear.z = 0.0`
  - `angular.x = 0.0`
  - `angular.y = 0.0`
  - `angular.z = 0.0`
- Writes the modified data back to the original bag file

**Security Issue**: This script demonstrates how ROS bag files can be tampered with, making it appear that the robot never received movement commands.

#### 2. `keylogger.py`
**Purpose**: Captures keyboard input
**What it does**:
- Logs all keystrokes to `keyfile.txt`
- Handles special keys (backspace, space, caps lock)
- Can be used to capture bag file names for processing

**Security Issue**: This is a keylogger that could be used maliciously to capture sensitive information.

---

### ROS Bag Files

#### 1. `Husky.bag`
- Original ROS bag file containing recorded robot data
- Contains all sensor topics, control commands, and navigation data

#### 2. `themaze.bag`
- Another ROS bag file (likely from a maze navigation scenario)
- Referenced in `keyfile.txt` as the target for editing

#### 3. `holder.bag`
- Temporary bag file used during the editing process
- Contains intermediate data before writing back to original file

#### 4. `subset.bag`, `vel.bag`
- Additional bag files (possibly subsets or filtered versions)

---

### Data Files

#### 1. `holder.txt`
**Content**: Shows all velocity commands were set to zero
**Evidence**: Contains 1305+ lines of identical zero velocity commands, proving the falsification occurred

#### 2. `keyfile.txt`
**Content**: Contains "themaze.bag lol"
**Purpose**: Specifies which bag file to edit

#### 3. `log.txt`
**Content**: Shows keylogger output with test data

---

### CSV Data Files (`demo/` folder)

All CSV files were extracted from ROS bag files and contain time-series sensor data:

#### 1. `cmd_vel.csv`
**Purpose**: Velocity commands sent to the robot
**Columns**: Time, linear.x, linear.y, linear.z, angular.x, angular.y, angular.z
**Key Insight**: Shows actual movement commands (non-zero values) before falsification

#### 2. `imu-data.csv`
**Purpose**: Inertial Measurement Unit (IMU) sensor data
**Columns**: 
- Time, header information
- Orientation (quaternion: x, y, z, w)
- Angular velocity (x, y, z)
- Linear acceleration (x, y, z)
- Covariance matrices for all measurements

**Key Insight**: IMU data shows actual robot motion and can be used to validate velocity commands

#### 3. `odometry-filtered.csv`
**Purpose**: Filtered odometry data (robot's estimated position and velocity)
**Columns**:
- Time, header information
- Pose (position: x, y, z; orientation: quaternion)
- Twist (linear and angular velocities)
- Covariance matrices

**Key Insight**: Shows where the robot actually moved, which should correlate with velocity commands

#### 4. `joint_states.csv`
**Purpose**: Joint positions, velocities, and efforts
**Columns**: Time, header, joint names, positions, velocities, efforts for 4 wheels
**Key Insight**: Shows actual wheel movement, which should match velocity commands

#### 5. Other CSV Files
- `diagnostics.csv`: System diagnostic information
- `gazebo-*.csv`: Gazebo simulator data (model states, link states, performance metrics)
- `move_base-*.csv`: Navigation stack data (goals, plans, costmaps)
- `navsat-fix.csv`: GPS/GNSS position data
- `tf.csv`, `tf_static.csv`: Transform data (coordinate frame relationships)

---

## Data Relationships & Validation

### Normal Operation Flow:
1. **Command** → `cmd_vel` topic receives velocity commands
2. **Execution** → Robot controller executes commands
3. **Sensing** → IMU, odometry, and joint sensors measure actual movement
4. **Validation** → All sensors should show consistent data

### Falsification Detection Points:

1. **Command vs. Odometry Mismatch**
   - If `cmd_vel` shows zeros but `odometry-filtered` shows movement → FALSIFIED
   - If `cmd_vel` shows movement but `odometry-filtered` shows no movement → SUSPICIOUS

2. **Command vs. IMU Mismatch**
   - If `cmd_vel` shows zeros but IMU shows acceleration/rotation → FALSIFIED
   - IMU linear acceleration should correlate with velocity changes

3. **Command vs. Joint States Mismatch**
   - If `cmd_vel` shows zeros but wheels are rotating → FALSIFIED
   - Wheel velocities should match commanded velocities

4. **Temporal Consistency**
   - Sudden changes from non-zero to all zeros → SUSPICIOUS
   - Long periods of zeros when robot should be moving → FALSIFIED

5. **Statistical Anomalies**
   - Unusually perfect zeros (no sensor noise) → FALSIFIED
   - Patterns that don't match expected robot behavior → SUSPICIOUS

---

## Security Implications

### Attack Vector:
1. Attacker uses `keylogger.py` to capture bag file names
2. Attacker uses `bag_editor.py` to falsify velocity commands
3. Falsified data makes it appear robot never moved
4. This could hide:
   - Unauthorized robot movement
   - Navigation to restricted areas
   - Evidence of tampering

### Detection Strategy:
- Cross-validate multiple sensor sources
- Check temporal consistency
- Look for statistical anomalies
- Validate physical constraints (e.g., can't move without wheel rotation)

---

## Next Steps

See `falsification_detector.py` for the automated detection system that:
1. Monitors live ROS data streams
2. Cross-validates multiple sensor sources
3. Detects anomalies and falsified data
4. Alerts when inconsistencies are found
5. **Accounts for physics**: Models deceleration, momentum, friction, and external forces

## Physics-Based Detection

The detection system now includes sophisticated physics modeling to reduce false positives:

- **Deceleration Modeling**: Accounts for natural deceleration when commands stop
- **Momentum/Inertia**: Considers robot mass and momentum
- **Friction & Wind**: Models rolling friction and wind resistance
- **External Forces**: Detects and accounts for wind, slopes, and other forces

See `PHYSICS_ENHANCEMENTS.md` for detailed information about the physics-based improvements.

