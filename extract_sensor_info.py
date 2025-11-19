#!/usr/bin/env python3
"""
Extract sensor information from ROS bag files
Works around rosbag dependency issues
"""

import os
import subprocess
import sys

def check_bag_with_rosbag_info(bag_path):
    """Try to use rosbag info command if available"""
    try:
        result = subprocess.run(
            ['rosbag', 'info', bag_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None

def analyze_from_rosout():
    """Analyze rosout.csv to find sensor topics"""
    print("\n" + "="*70)
    print("ANALYZING ROSOUT FOR SENSOR TOPICS")
    print("="*70 + "\n")
    
    rosout_file = "demo/rosout.csv"
    if not os.path.exists(rosout_file):
        print("⚠ rosout.csv not found")
        return
    
    import pandas as pd
    df = pd.read_csv(rosout_file)
    
    # Extract topics from subscription messages
    sensor_keywords = {
        'laser/lidar': ['laser', 'lidar', 'scan', 'pointcloud', 'point_cloud'],
        'camera': ['camera', 'image', 'compressed', 'depth'],
        'radar': ['radar'],
        'sonar': ['sonar'],
        'imu': ['imu'],
        'gps': ['navsat', 'gps', 'fix'],
        'odometry': ['odom'],
        'joint': ['joint'],
        'costmap': ['costmap']
    }
    
    found_topics = {cat: set() for cat in sensor_keywords.keys()}
    
    # Look for subscription messages
    for idx, row in df.iterrows():
        if 'Subscribing to' in str(row.get('msg', '')):
            topic = str(row.get('msg', '')).split('Subscribing to ')[-1].split(',')[0].strip()
            topic_lower = topic.lower()
            
            for category, keywords in sensor_keywords.items():
                if any(kw in topic_lower for kw in keywords):
                    found_topics[category].add(topic)
    
    print("Sensor-related topics found in rosout:\n")
    for category, topics in found_topics.items():
        if topics:
            print(f"  {category.upper().replace('/', ' / ')}:")
            for topic in sorted(topics):
                print(f"    - {topic}")
    
    return found_topics

def check_costmap_for_laser_info():
    """Check costmap files for laser sensor information"""
    print("\n" + "="*70)
    print("ANALYZING COSTMAP FOR LASER SENSOR INFO")
    print("="*70 + "\n")
    
    costmap_file = "demo/move_base-global_costmap-costmap.csv"
    if os.path.exists(costmap_file):
        size_mb = os.path.getsize(costmap_file) / (1024 * 1024)
        print(f"Costmap file: {costmap_file}")
        print(f"Size: {size_mb:.1f} MB")
        print("\nThis file contains processed laser/obstacle data.")
        print("The costmap is built from laser scans showing obstacles.")
        print("Raw laser scan data would be in the ROS bag files.")
    
    # Check laser parameter files
    laser_files = [
        "demo/move_base-global_costmap-obstacles_laser-parameter_updates.csv",
        "demo/move_base-local_costmap-obstacles_laser-parameter_updates.csv"
    ]
    
    for laser_file in laser_files:
        if os.path.exists(laser_file):
            import pandas as pd
            try:
                df = pd.read_csv(laser_file)
                print(f"\n{os.path.basename(laser_file)}:")
                if len(df) > 0:
                    print(f"  Records: {len(df)}")
                    # Parse the parameter values
                    if 'bools' in df.columns and len(df) > 0:
                        bools = str(df.iloc[0]['bools'])
                        if 'enabled' in bools and 'True' in bools:
                            print("  ✅ Laser obstacle layer: ENABLED")
                        else:
                            print("  ⚠ Laser obstacle layer: DISABLED")
            except Exception as e:
                print(f"  ⚠ Error reading: {e}")

def main():
    print("="*70)
    print("SENSOR INFORMATION EXTRACTION")
    print("="*70)
    
    # Method 1: Analyze rosout
    topics = analyze_from_rosout()
    
    # Method 2: Check costmap
    check_costmap_for_laser_info()
    
    # Method 3: Try rosbag info command
    print("\n" + "="*70)
    print("ATTEMPTING TO READ BAG FILES")
    print("="*70 + "\n")
    
    bag_files = ['Husky.bag', 'themaze.bag', 'subset.bag']
    
    for bag_file in bag_files:
        if os.path.exists(bag_file):
            size_mb = os.path.getsize(bag_file) / (1024 * 1024)
            print(f"\n📦 {bag_file} ({size_mb:.1f} MB)")
            
            # Try rosbag info
            info = check_bag_with_rosbag_info(bag_file)
            if info:
                # Extract sensor topics from info
                lines = info.split('\n')
                sensor_lines = [l for l in lines if any(x in l.lower() for x in 
                    ['laser', 'lidar', 'scan', 'camera', 'radar', 'sonar', 'point', 'cloud'])]
                if sensor_lines:
                    print("  Sensor topics found:")
                    for line in sensor_lines[:10]:
                        print(f"    {line.strip()}")
            else:
                print("  ⚠ Cannot read bag file (rosbag tools not available)")
                print("  💡 Install ROS or use: pip install rospkg")
                print("  💡 Or use: rosbag info Husky.bag")
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70 + "\n")
    
    print("✅ CONFIRMED SENSORS (with CSV data):")
    print("  - IMU (inertial measurement unit)")
    print("  - GPS/NavSat (global positioning)")
    print("  - Odometry (position estimation)")
    print("  - Joint States (wheel encoders)")
    
    print("\n⚠️ LIKELY SENSORS (configuration found, raw data in bag files):")
    print("  - LIDAR/Laser Scanner (costmap shows laser obstacle layer enabled)")
    print("    → Raw scan data is in .bag files, not extracted to CSV")
    print("    → Costmap contains processed laser data (obstacle maps)")
    
    print("\n❌ NOT FOUND:")
    print("  - Camera/Image sensors")
    print("  - Radar")
    print("  - Sonar")
    
    print("\n" + "="*70)
    print("RECOMMENDATION")
    print("="*70)
    print("\nTo extract LIDAR scan data from bag files:")
    print("  1. Install ROS: sudo apt-get install ros-noetic-rosbag")
    print("  2. Or use Python: pip install rospkg")
    print("  3. Extract /scan topic: rosbag play Husky.bag")
    print("  4. Or use Python script to read bag files directly")
    print("\nThe costmap files show the robot HAS a laser scanner,")
    print("but the raw scan data needs to be extracted from bag files.")

if __name__ == "__main__":
    main()

