#!/usr/bin/env python3
"""
Live Feed Monitor for ROS Data Falsification Detection
Monitors ROS topics in real-time and detects falsified data
"""

import rospy
from geometry_msgs.msg import Twist, TwistStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu
from sensor_msgs.msg import JointState
from falsification_detector import FalsificationDetector, DetectionResult
from datetime import datetime
import json

class LiveMonitor:
    """
    Monitors ROS topics in real-time and detects falsified data
    """
    
    def __init__(self, threshold: float = 0.7):
        """Initialize live monitor"""
        self.detector = FalsificationDetector(window_size=10, threshold=threshold)
        
        # Current sensor data
        self.current_data = {
            'cmd_vel': {},
            'odometry': {},
            'imu': {},
            'joint_states': {},
            'timestamp': None
        }
        
        # Detection history
        self.detection_history = []
        self.alert_count = 0
        
        # Initialize ROS node
        rospy.init_node('falsification_detector', anonymous=True)
        
        # Subscribe to topics
        rospy.Subscriber('/cmd_vel', Twist, self.cmd_vel_callback)
        rospy.Subscriber('/odometry/filtered', Odometry, self.odom_callback)
        rospy.Subscriber('/imu/data', Imu, self.imu_callback)
        rospy.Subscriber('/joint_states', JointState, self.joint_callback)
        
        print("✓ Live monitor initialized")
        print("  Subscribed to:")
        print("    - /cmd_vel")
        print("    - /odometry/filtered")
        print("    - /imu/data")
        print("    - /joint_states")
    
    def cmd_vel_callback(self, msg: Twist):
        """Callback for velocity command messages"""
        self.current_data['cmd_vel'] = {
            'linear.x': msg.linear.x,
            'linear.y': msg.linear.y,
            'linear.z': msg.linear.z,
            'angular.x': msg.angular.x,
            'angular.y': msg.angular.y,
            'angular.z': msg.angular.z
        }
        self.current_data['timestamp'] = rospy.get_time()
        self.check_falsification()
    
    def odom_callback(self, msg: Odometry):
        """Callback for odometry messages"""
        self.current_data['odometry'] = {
            'twist.twist.linear.x': msg.twist.twist.linear.x,
            'twist.twist.linear.y': msg.twist.twist.linear.y,
            'twist.twist.linear.z': msg.twist.twist.linear.z,
            'twist.twist.angular.x': msg.twist.twist.angular.x,
            'twist.twist.angular.y': msg.twist.twist.angular.y,
            'twist.twist.angular.z': msg.twist.twist.angular.z,
            'pose.pose.position.x': msg.pose.pose.position.x,
            'pose.pose.position.y': msg.pose.pose.position.y,
            'pose.pose.position.z': msg.pose.pose.position.z
        }
        self.check_falsification()
    
    def imu_callback(self, msg: Imu):
        """Callback for IMU messages"""
        self.current_data['imu'] = {
            'linear_acceleration.x': msg.linear_acceleration.x,
            'linear_acceleration.y': msg.linear_acceleration.y,
            'linear_acceleration.z': msg.linear_acceleration.z,
            'angular_velocity.x': msg.angular_velocity.x,
            'angular_velocity.y': msg.angular_velocity.y,
            'angular_velocity.z': msg.angular_velocity.z,
            'orientation.x': msg.orientation.x,
            'orientation.y': msg.orientation.y,
            'orientation.z': msg.orientation.z,
            'orientation.w': msg.orientation.w
        }
        self.check_falsification()
    
    def joint_callback(self, msg: JointState):
        """Callback for joint state messages"""
        joint_data = {}
        
        # Extract wheel velocities (assuming 4 wheels)
        if len(msg.velocity) >= 4:
            for i in range(4):
                joint_data[f'velocity_{i}'] = msg.velocity[i]
        
        # Extract wheel positions
        if len(msg.position) >= 4:
            for i in range(4):
                joint_data[f'position_{i}'] = msg.position[i]
        
        # Extract wheel efforts
        if len(msg.effort) >= 4:
            for i in range(4):
                joint_data[f'effort_{i}'] = msg.effort[i]
        
        self.current_data['joint_states'] = joint_data
        self.check_falsification()
    
    def check_falsification(self):
        """Check for falsification using current data"""
        # Only check if we have at least cmd_vel data
        if not self.current_data['cmd_vel']:
            return
        
        # Get detection result
        result = self.detector.monitor_live_feed(self.current_data)
        
        # Store in history
        self.detection_history.append({
            'timestamp': result.timestamp,
            'is_falsified': result.is_falsified,
            'confidence': result.confidence,
            'anomalies': result.anomalies,
            'details': result.details
        })
        
        # Keep only recent history (last 100 detections)
        if len(self.detection_history) > 100:
            self.detection_history.pop(0)
        
        # Alert if falsified
        if result.is_falsified:
            self.alert_count += 1
            self.print_alert(result)
            
            # Optionally save alert to file
            self.save_alert(result)
    
    def print_alert(self, result: DetectionResult):
        """Print alert for falsified data"""
        print("\n" + "=" * 60)
        print("🚨 FALSIFICATION DETECTED!")
        print("=" * 60)
        print(f"Timestamp: {result.timestamp:.3f}")
        print(f"Confidence: {result.confidence:.2%}")
        print(f"Anomalies: {', '.join(result.anomalies)}")
        print(f"Total alerts: {self.alert_count}")
        print("=" * 60)
    
    def save_alert(self, result: DetectionResult):
        """Save alert to JSON file"""
        alert_data = {
            'timestamp': result.timestamp,
            'datetime': datetime.fromtimestamp(result.timestamp).isoformat(),
            'is_falsified': result.is_falsified,
            'confidence': result.confidence,
            'anomalies': result.anomalies,
            'details': result.details,
            'current_data': self.current_data
        }
        
        filename = f"alerts_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(filename, 'a') as f:
            f.write(json.dumps(alert_data) + '\n')
    
    def get_statistics(self) -> dict:
        """Get monitoring statistics"""
        if not self.detection_history:
            return {}
        
        total = len(self.detection_history)
        falsified = sum(1 for d in self.detection_history if d['is_falsified'])
        
        return {
            'total_detections': total,
            'falsified_count': falsified,
            'falsified_percentage': (falsified / total * 100) if total > 0 else 0,
            'alert_count': self.alert_count
        }
    
    def print_statistics(self):
        """Print monitoring statistics"""
        stats = self.get_statistics()
        if stats:
            print("\n" + "=" * 60)
            print("MONITORING STATISTICS")
            print("=" * 60)
            print(f"Total detections: {stats['total_detections']}")
            print(f"Falsified detections: {stats['falsified_count']} ({stats['falsified_percentage']:.1f}%)")
            print(f"Total alerts: {stats['alert_count']}")
            print("=" * 60)
    
    def run(self):
        """Run the monitor"""
        print("\n" + "=" * 60)
        print("LIVE FALSIFICATION DETECTOR")
        print("=" * 60)
        print("Monitoring ROS topics for falsified data...")
        print("Press Ctrl+C to stop")
        print("=" * 60 + "\n")
        
        # Print statistics every 10 seconds
        rate = rospy.Rate(0.1)  # 0.1 Hz = every 10 seconds
        
        try:
            while not rospy.is_shutdown():
                rate.sleep()
                self.print_statistics()
        except KeyboardInterrupt:
            print("\n\nStopping monitor...")
            self.print_statistics()
            print("Monitor stopped.")


def main():
    """Main function"""
    try:
        monitor = LiveMonitor(threshold=0.7)
        monitor.run()
    except rospy.ROSInterruptException:
        pass


if __name__ == "__main__":
    main()

