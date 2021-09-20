#! /usr/bin/python3

import math
import struct

import geometry_msgs
import rclpy
import numpy as np
from geometry_msgs.msg import Quaternion, Twist, Vector3, Point
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import Imu


class PositionController(Node):

    robots = [
        {
            "name":"swarmsteve",
            "odom_node":None,
            "twist_node":None,
            "x":None,
            "y":None,
            "target_x":None,
            "target_y":None,
            "orientation":None
        },
        # {
        #     "name":"swarmtim",
        #     "odom_node":None,
        #     "twist_node":None,
        #     "x":None,
        #     "y":None,
        #     "target_x":None,
        #     "target_y":None,
        # }
    ]
    points = [(.120,-.094)]

    def __init__(self):
        super().__init__("Position_Controller")
        for robot in PositionController.robots:
            read_pos_callback = lambda msg: self.read_pos(msg,robot)
            robot["odom_node"] = self.create_subscription(Odometry,"/"+robot["name"]+"/odom",read_pos_callback,10)
            robot["twist_node"] = self.create_publisher(Twist, "/"+robot["name"]+"/cmd_vel",5)
        move_callback = lambda msg: self.move_to_point(msg.x,msg.y,robot)
        self.point_sub = self.create_subscription(Point,"move_to",move_callback,10)
        self.position = {}
        self.v_max = 0.5
        self.omega_max = 0.5
        self.target_pos = [None,None]

    def run(self):
        for point in PositionController.points:
            for robot in PositionController.robots:
                self.move_to_point(point[0],point[1],robot)

    def read_pos(self,msg,robot=None):
        if robot == None:
            self.position["x"] = msg.pose.pose.position.x
            self.position["y"] = msg.pose.pose.position.y
            self.position["orientation"] = msg.pose.pose.orientation
        else:
            robot["x"] = msg.pose.pose.position.x
            robot["y"] = msg.pose.pose.position.y
            robot["orientation"] = msg.pose.pose.orientation

        
    def rpy_from_quaternion(self,quaternion):
        x = quaternion.x
        y = quaternion.y
        z = quaternion.z
        w = quaternion.w

        sinr_cosp = 2 * (w * x + y * z)
        cosr_cosp = 1 - 2 * (x * x + y * y)
        roll = np.arctan2(sinr_cosp, cosr_cosp)

        sinp = 2 * (w * y - z * x)
        pitch = np.arcsin(sinp)

        siny_cosp = 2 * (w * z + x * y)
        cosy_cosp = 1 - 2 * (y * y + z * z)
        yaw = np.arctan2(siny_cosp, cosy_cosp)
        return roll, pitch, yaw

    def move_to_point(self,x,y,robot=None):
        
        if robot == None:
            self.target_pos[0] = x
            self.target_pos[1] = y
            current_x = self.position["x"]
            current_y = self.position["y"]
            orientation = self.position["orientation"]
            twist_pub = self.twist_pub
        else:
            robot["target_x"] = x
            robot["target_y"] = y
            current_x = robot["x"]
            current_y = robot["y"]
            orientation = robot["orientation"]
            twist_pub = robot["twist_node"]
            print()
        
        if not self.target_pos[0] == None and not self.target_pos[0] == None:
            self.get_logger().info("X: {x} Y: {y}".format(x=current_x, y=current_y))
            if np.sqrt((x - current_x)**2 + (x - current_y)**2) < .05:
                if robot == None:
                    self.target_pos[0] = None
                    self.target_pos[1] = None
                else:
                    robot["target_x"] = None
                    robot["target_y"] = None

                twist_msg = Twist()
                twist_msg.linear.x = 0.0
                twist_msg.angular.z = 0.0
                twist_pub.publish(twist_msg)
            else:
                delta_x = x - current_x
                delta_y = y - current_y
                theta = self.rpy_from_quaternion(orientation)[0]
                v = self.v_max*(delta_x*np.cos(theta) + delta_y*np.sin(theta))
                omega = self.omega_max*(2*np.arctan2(-np.sin(theta)*delta_x + np.cos(theta)*delta_y,v))/np.pi
                twist_msg = Twist()
                twist_msg.linear.x = v
                twist_msg.angular.z=omega
                twist_pub.publish(twist_msg)   

    def move_to_point_topic(self,msg):
        x = msg.x
        y = msg.y
        self.move_to_point(x,y)
    

def main(args=None):
    rclpy.init(args=args)
    controller = PositionController()
    rclpy.spin(controller)

