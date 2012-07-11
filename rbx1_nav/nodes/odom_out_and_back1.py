#!/usr/bin/env python

""" odom_out_and_back.py - Version 0.1 2012-03-24

    A basic demo of using the /odom topic to move a robot a given distance
    or rotate through a given angle.

    Created for the Pi Robot Project: http://www.pirobot.org
    Copyright (c) 2012 Patrick Goebel.  All rights reserved.

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.5
    
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details at:
    
    http://www.gnu.org/licenses/gpl.html
      
"""

import roslib; roslib.load_manifest('rbx1_nav')
import rospy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import PyKDL
from math import radians, copysign, sqrt, pow, pi
import threading

class OutAndBack():
    def __init__(self):
        # Give the node a name
        rospy.init_node('out_and_back', anonymous=False)

        # Set rospy to exectute a shutdown function when exiting       
        rospy.on_shutdown(self.shutdown)
        
        # Create a lock for reading odometry values
        self.lock = threading.Lock()

        # Publisher to control the robot's speed
        self.cmd_vel = rospy.Publisher('/cmd_vel', Twist)
        
        # How fast will we update the robot's movement?
        rate = 30
        
        # Set the equivalent ROS rate variable
        r = rospy.Rate(rate)
        
        # Set the forward linear speed to 0.2 meters per second 
        linear_speed = 0.2
        
        # Set the travel distance in meters
        goal_distance = 1.0

        # Set the rotation speed in radians per second
        angular_speed = 1.0
        
        # Set the rotation angle to Pi radians (180 degrees)
        goal_angle = pi

        # A variable to hold the current odometry values
        self.odom = Odometry()
        
        # Subscribe to the /odom topic to get odometry data.
        # Set the callback to the update_odom() function.
        rospy.Subscriber('/odom', Odometry, self.update_odom)
        
        # Wait for the /odom topic to become available
        rospy.wait_for_message('/odom', Odometry)
        
        # Wait until we actually have some data
        while self.odom == Odometry():
            rospy.sleep(0.5)
        
        # Loop once for each leg of the trip
        for i in range(2):
            # Initialize the movement command
            move_cmd = Twist()
            
            # Set the movement command to forward motion
            move_cmd.linear.x = linear_speed
            
            # Get the starting position values     
            x_start = self.odom.pose.pose.position.x
            y_start = self.odom.pose.pose.position.y
            
            # Keep track of the distance traveled
            distance = 0
            
            # Enter the loop to move along a side
            while distance < goal_distance and not rospy.is_shutdown():
                # Publish the Twist message and sleep 1 cycle         
                self.cmd_vel.publish(move_cmd)
                r.sleep()
        
                # Compute the Euclidean distance from the start
                with self.lock:
                    distance = sqrt(pow((self.odom.pose.pose.position.x - x_start), 2)
                                  + pow((self.odom.pose.pose.position.y - y_start), 2))

            # Stop the robot before the rotation
            move_cmd = Twist()
            self.cmd_vel.publish(move_cmd)
            rospy.sleep(1)
            
            # Set the movement command to a rotation
            move_cmd.angular.z = angular_speed
            
            # Track the last angle measured
            last_angle = self.odom_angle
            
            # Track how far we have turned
            turn_angle = 0
            
            while abs(turn_angle) < abs(goal_angle) and not rospy.is_shutdown():
                # Publish the Twist message and sleep 1 cycle         
                self.cmd_vel.publish(move_cmd)
                r.sleep()
                                
                with self.lock:
                    delta_angle = normalize_angle(self.odom_angle - last_angle)
                
                turn_angle += delta_angle
                last_angle = self.odom_angle
                
            # Stop the robot before the next leg
            move_cmd = Twist()
            self.cmd_vel.publish(move_cmd)
            rospy.sleep(1)
            
        # Stop the robot for good
        self.cmd_vel.publish(Twist())

    def update_odom(self, msg):
        with self.lock:
            self.odom = msg                            
            q = msg.pose.pose.orientation
            self.odom_angle = quat_to_angle(q)  
        
    def shutdown(self):
        # Always stop the robot when shutting down the node.
        rospy.loginfo("Stopping the robot...")
        self.cmd_vel.publish(Twist())
        rospy.sleep(1)
        
def quat_to_angle(quat):
        rot = PyKDL.Rotation.Quaternion(quat.x, quat.y, quat.z, quat.w)
        return rot.GetRPY()[2]
            
def normalize_angle(angle):
        res = angle
        while res > pi:
            res -= 2.0 * pi
        while res < -pi:
            res += 2.0 * pi
        return res
 
if __name__ == '__main__':
    try:
        OutAndBack()
    except:
        rospy.loginfo("Out-and-Back node terminated.")

