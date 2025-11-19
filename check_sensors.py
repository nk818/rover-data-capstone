#!/usr/bin/env python3
"""
Check for sensor data in ROS bag files
Looks for lidar, laser scan, radar, camera, and other sensor topics
"""

import os
import sys

def check_bag_file(bag_path):
    """Check topics in a ROS bag file"""
    try:
        import rosbag
        print(f"\n{'='*70}")
        print(f"Checking: {os.path.basename(bag_path)}")
        print(f"{'='*70}")
        
        bag = rosbag.Bag(bag_path, 'r')
        topics = bag.get_type_and_topic_info()[1]
        
        # Categorize topics
        sensor_topics = {
            'lidar/laser': [],
            'camera/image': [],
            'radar': [],
            'sonar': [],
            'imu': [],
            'gps/navsat': [],
            'odometry': [],
            'joint_states': [],
            'other_sensors': []
        }
        
        all_topics = []
        for topic, info in sorted(topics.items()):
            all_topics.append((topic, info.msg_type, info.message_count))
            
            topic_lower = topic.lower()
            msg_lower = info.msg_type.lower()
            
            # Categorize
            if any(x in topic_lower or x in msg_lower for x in ['laser', 'lidar', 'scan', 'pointcloud', 'point_cloud']):
                sensor_topics['lidar/laser'].append((topic, info.msg_type, info.message_count))
            elif any(x in topic_lower or x in msg_lower for x in ['camera', 'image', 'compressed', 'depth']):
                sensor_topics['camera/image'].append((topic, info.msg_type, info.message_count))
            elif 'radar' in topic_lower or 'radar' in msg_lower:
                sensor_topics['radar'].append((topic, info.msg_type, info.message_count))
            elif 'sonar' in topic_lower or 'sonar' in msg_lower:
                sensor_topics['sonar'].append((topic, info.msg_type, info.message_count))
            elif 'imu' in topic_lower:
                sensor_topics['imu'].append((topic, info.msg_type, info.message_count))
            elif any(x in topic_lower for x in ['navsat', 'gps', 'fix']):
                sensor_topics['gps/navsat'].append((topic, info.msg_type, info.message_count))
            elif 'odom' in topic_lower:
                sensor_topics['odometry'].append((topic, info.msg_type, info.message_count))
            elif 'joint' in topic_lower:
                sensor_topics['joint_states'].append((topic, info.msg_type, info.message_count))
            elif any(x in topic_lower for x in ['sensor', 'data', 'reading']):
                sensor_topics['other_sensors'].append((topic, info.msg_type, info.message_count))
        
        # Print categorized results
        print(f"\nTotal topics: {len(all_topics)}")
        print(f"\n📊 SENSOR TOPICS FOUND:\n")
        
        for category, topic_list in sensor_topics.items():
            if topic_list:
                print(f"  {category.upper().replace('/', ' / ')}:")
                for topic, msg_type, count in topic_list:
                    print(f"    - {topic}")
                    print(f"      Type: {msg_type}")
                    print(f"      Messages: {count:,}")
        
        # Show all topics for reference
        print(f"\n📋 ALL TOPICS IN BAG:\n")
        for topic, msg_type, count in all_topics[:30]:  # Show first 30
            print(f"  {topic:50} {msg_type:30} ({count:,} msgs)")
        
        if len(all_topics) > 30:
            print(f"  ... and {len(all_topics) - 30} more topics")
        
        bag.close()
        return sensor_topics
        
    except ImportError:
        print("⚠ rosbag module not available. Install with: pip install rospkg")
        return None
    except Exception as e:
        print(f"⚠ Error reading bag file: {e}")
        return None

def check_csv_files():
    """Check what sensor data is available in CSV files"""
    print(f"\n{'='*70}")
    print("CHECKING CSV FILES FOR SENSOR DATA")
    print(f"{'='*70}\n")
    
    demo_dir = "demo"
    if not os.path.exists(demo_dir):
        print("⚠ demo/ directory not found")
        return
    
    csv_files = [f for f in os.listdir(demo_dir) if f.endswith('.csv')]
    
    sensor_files = {
        'lidar/laser': [],
        'imu': [],
        'gps/navsat': [],
        'odometry': [],
        'joint_states': [],
        'costmap': [],
        'other': []
    }
    
    for csv_file in sorted(csv_files):
        csv_lower = csv_file.lower()
        
        if any(x in csv_lower for x in ['laser', 'lidar', 'scan', 'point']):
            sensor_files['lidar/laser'].append(csv_file)
        elif 'imu' in csv_lower:
            sensor_files['imu'].append(csv_file)
        elif 'navsat' in csv_lower:
            sensor_files['gps/navsat'].append(csv_file)
        elif 'odom' in csv_lower:
            sensor_files['odometry'].append(csv_file)
        elif 'joint' in csv_lower:
            sensor_files['joint_states'].append(csv_file)
        elif 'costmap' in csv_lower:
            sensor_files['costmap'].append(csv_file)
        else:
            sensor_files['other'].append(csv_file)
    
    print("CSV Files by Category:\n")
    for category, files in sensor_files.items():
        if files:
            print(f"  {category.upper().replace('/', ' / ')} ({len(files)} files):")
            for f in files[:5]:  # Show first 5
                file_path = os.path.join(demo_dir, f)
                size = os.path.getsize(file_path) / 1024  # KB
                print(f"    - {f} ({size:.1f} KB)")
            if len(files) > 5:
                print(f"    ... and {len(files) - 5} more")
            print()

def analyze_costmap_laser():
    """Analyze costmap files to understand laser sensor usage"""
    print(f"\n{'='*70}")
    print("ANALYZING COSTMAP LASER CONFIGURATION")
    print(f"{'='*70}\n")
    
    laser_param_file = "demo/move_base-global_costmap-obstacles_laser-parameter_updates.csv"
    
    if os.path.exists(laser_param_file):
        import pandas as pd
        try:
            df = pd.read_csv(laser_param_file)
            print("Laser Obstacle Layer Configuration:")
            print(f"  File: {laser_param_file}")
            print(f"  Records: {len(df)}")
            if len(df) > 0:
                print(f"\n  Sample configuration:")
                print(f"  {df.iloc[0].to_string()}")
        except Exception as e:
            print(f"  ⚠ Error reading: {e}")
    else:
        print("  ⚠ Costmap laser parameter file not found")

def main():
    print("="*70)
    print("SENSOR DATA ANALYSIS")
    print("="*70)
    
    # Check CSV files
    check_csv_files()
    
    # Analyze costmap
    analyze_costmap_laser()
    
    # Check bag files
    bag_files = [
        'Husky.bag',
        'themaze.bag',
        'subset.bag',
        'vel.bag'
    ]
    
    print(f"\n{'='*70}")
    print("CHECKING ROS BAG FILES")
    print(f"{'='*70}")
    
    found_sensors = {}
    
    for bag_file in bag_files:
        if os.path.exists(bag_file):
            size_mb = os.path.getsize(bag_file) / (1024 * 1024)
            print(f"\n📦 {bag_file} ({size_mb:.1f} MB)")
            
            sensors = check_bag_file(bag_file)
            if sensors:
                found_sensors[bag_file] = sensors
        else:
            print(f"\n⚠ {bag_file} not found")
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}\n")
    
    all_sensor_types = set()
    for bag, sensors in found_sensors.items():
        for category, topics in sensors.items():
            if topics:
                all_sensor_types.add(category)
    
    if all_sensor_types:
        print("✅ Sensor types found in bag files:")
        for sensor_type in sorted(all_sensor_types):
            print(f"  - {sensor_type}")
    else:
        print("⚠ No sensor topics found (may need rosbag module)")
    
    print("\n" + "="*70)
    print("Analysis complete!")
    print("="*70)

if __name__ == "__main__":
    main()

