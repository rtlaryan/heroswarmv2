#! /usr/bin/python3
import struct

import adafruit_bmp280
import adafruit_lis3mdl
import adafruit_sht31d
import board
import rclpy
import smbus
import math
from adafruit_apds9960.apds9960 import APDS9960
from adafruit_lsm6ds.lsm6ds33 import LSM6DS33
from geometry_msgs.msg import Quaternion, Twist, Vector3
from rclpy.node import Node
from robot_msgs.msg import Enviornment, Light
from sensor_msgs.msg import IMU
from std_msgs.msg import Float64
from nav_msgs.msg import Odometry


class Controller(Node):

    def __init__(self) -> None:
        # Creates the control node
        super().__init__("robot_controller")
        # Arduino Device Address
        self.arduino = 0x8
        # Init the i2c buss
        self.light = False
        self.enviornment = False
        self.bus = board.I2C()
        self.IMU = LSM6DS33(self.bus)
        self.magnetometer = adafruit_lis2mdl.LIS2MDL(self.bus)
        self.light = APDS9960(self.bus)
        self.light.enable_gesture()
        self.bmp = adafruit_bmp280.Adafruit_BMP280_I2C(self.bus)
        self.humdity = adafruit_sht31d.SHT31D(self.i2c)
        self.twist_sub = self.create_subscription(Twist,"cmd_vel", self.read_twist,10)
        self.imu_pub = self.create_publisher(IMU,"imu",2)
        #self.mic_pub = self.create_publisher(Float64,"mic",2)
        if self.light:
            self.light_pub = self.create_publisher(Light,'light',2)
        if self.enviornment:
            self.enviornment_pub = self.create_publisher(Enviornment,"enviornment",2)
        self.prox_pub = self.create_publisher(Float64,"proximity",2)
        self.odom_pub = self.create_publisher(Odometry, "odom",2)
        # self.tmr = self.create_timer(timer_period, self.timer_callback)
        self.linear_x_velo = 0
        self.linear_y_velo = 0
        self.angular_z_velo = 0


    def pub_odom(self):
        # Creates the odom message
        odom_msg = Odometry()

        data = self.bus.read_i2c_block_data(self.arduino, 0)

       

        odom_data = []

        # Get odom data from arduino
        for index in range(5):
            bytes = bytearray()
            for i in range(4):
                bytes.append(data[4*index + i])
            odom_data.append(struct.unpack('f', bytes)[0])

        # Adds Twist data
        odom_msg.twist.twist.linear.x = data[3] * math.cos(data[2])
        odom_msg.twist.twist.linear.y = data[3] * math.sin(data[2])
        odom_msg.twist.twist.linear.z = 0
        
        odom_msg.twist.twist.angular.x = 0
        odom_msg.twist.twist.angular.y = 0
        odom_msg.twist.twist.angular.z = data[4]

        odom_msg.pose.pose.position.x = data[0]
        odom_msg.pose.pose.position.y = data[1]
        odom_msg.pose.pose.position.z = 0

        odom_msg.pose.pose.orientation

        self.odom_pub.publish(odom_msg)
        
    def read_twist(self,msg) -> None:
        # Reads ths twist message x linear velocity
        x_velo = msg.linear.x
        
        # Reads the twist message y linear velocity
        y_velo = msg.linear.y

        # Reads the twist message z angular velocity
        z_angular = msg.angular.z

        self.linearx_velo = x_velo

        self.linear=y_velo = y_velo

        self.angular_z_velo = z_angular

        # Logs the data
        self.get_logger().info("X Linear: {x} Y Linear: {y} Z Angular: {z}".format(x=x_velo,y=y_velo,z=z_angular))
        
        # Sends the velocity information to the feather board
        self.send_velocity([x_velo,y_velo,z_angular])

    def read_imu(self) -> None:
        # Creates the IMU message
        imu_msg = IMU()
        
        # Read the sensor
        acc_x, acc_y, acc_z = self.IMU.acceleration
        gyro_x, gyro_y, gyro_z = self.IMU.gyro


        # Sets the orientation parameters
        imu_msg.orientation.x = 0
        imu_msg.orientation.y = 0
        imu_msg.orientation.z = 0

        # Sets the angular velocity parameters
        imu_msg.angular_velocity.x = gyro_x
        imu_msg.angular_velocity.y = gyro_y
        imu_msg.angular_velocity.z = gyro_z

        # Sets the linear acceleration parameters
        imu_msg.linear_acceleration.x = acc_x
        imu_msg.linear_acceleration.y = acc_y
        imu_msg.linear_acceleration.z = acc_z

        # Publishes the message
        self.imu_pub.publish(imu_msg)
    
    # Remove DC bias before computing RMS.
    def mean(self,values):
        return sum(values) / len(values)


    def normalized_rms(self,values):
        minbuf = int(self.mean(values))
        samples_sum = sum(
            float(sample - minbuf) * (sample - minbuf)
            for sample in values
        )

        return math.sqrt(samples_sum / len(values))

    # def read_mic(self) -> None:
    #     # Creates the mic message
    #     mic_msg = Float64

    #     # Sets the meassage data value
    #     mic_msg.data = None

    #     # Publishes the message
    #     self.mic_pub.publish(mic_msg)

    
    def read_light(self) -> None:
        # Creates the light message
        light_msg = Light()

        # Sets the current rgbw value array
        light_msg.rgbw = self.light.color_data

        # Sets the gesture type
        light_msg.gesture.data = self.light.gesture()

        # Publishes the message
        self.light_pub.publish(light_msg)

    def read_enviornment(self) -> None:
        # Creates the enviornment message
        enviorn_msg = Enviornment()

        # Sets the temperature
        enviorn_msg.temp = self.bmp.temperature

        # Sets the pressure 
        enviorn_msg.pressure = self.bmp.pressure

        # Sets the humidity
        enviorn_msg.humidity = self.humidity.relative_humidity

        # Sets the altitude
        enviorn_msg.altitude = self.bmp.altitude

        # Publishes the message
        self.enviornment_pub.publish(enviorn_msg)

    def read_proximity(self) -> None:
        # Creates the proximity message
        proximity_msg = Float64()
        
        # Sets the proximity value
        proximity_msg.data = self.light.proximity

        # Publishes the message
        self.prox_pub.publish(proximity_msg)

        

    # Sending an float to the arduino
    # Message format []
    def send_velocity(self,values) -> None:
        byteList = []

        # Converts the values to bytes 
        for value in values:
            byteList += list(struct.pack('f', value))
        byteList.append(0)  # fails to send last byte over I2C, hence this needs to be added 

        # Writes the values to the bus
        self.bus.write_i2c_block_data(self.arduino, byteList[0], byteList[1:20])
    
    
        


def main(args=None):
    rclpy.init(args=args)
    controller = Controller()
    rclpy.spin(controller)
