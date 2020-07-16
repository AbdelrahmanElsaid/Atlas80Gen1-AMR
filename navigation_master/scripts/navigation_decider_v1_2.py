#!/usr/bin/env python

import rospy
import numpy as np
import tf.transformations

from pygame import mixer
from std_msgs.msg import Bool, String
from geometry_msgs.msg import PolygonStamped, Twist
from nav_msgs.msg import Odometry

# "status" : "started / arrived / departed / suspended / resumed / cancelled / completed"
# "lifter" : "up / down"

class NavigationDeciderV1_2():
    def __init__(self):
        # Define Topics for publishing and subscribing messages
        self.battery_topic = rospy.get_param("~battery_topic")              # battery/percentage
        self.pose_topic = rospy.get_param("~pose_topic")                    # pf/pose/odom
        self.lifter_topic = rospy.get_param("~lifter_topic")                # lifter/status
        self.finish_turn_topic = rospy.get_param("~finish_turn_topic")      # turning_180/status
        self.finish_table_topic = rospy.get_param("~finish_table_topic")    # table_navi/status
        self.moving_topic = rospy.get_param("~moving_topic")                # low_level/twist_cmd_mux/output
        self.traj_topic = rospy.get_param("~traj_topic")                    # trajectory/current
        self.mission_topic = rospy.get_param("~mission_topic")              # atlas80/mission
        self.path_topic = rospy.get_param("~path_topic")                    # trajectory/new
        self.all_topic = rospy.get_param("~all_topic")                      # atlas80/all_status
        self.suspend_topic = rospy.get_param("~suspend_topic")              # suspend/input/navi
        self.check_resume_topic = rospy.get_param("~check_resume_topic")    # suspend/output
        self.init_turn_topic = rospy.get_param("~init_turn_topic")          # turning_180/init
        self.init_table_topic = rospy.get_param("~init_table_topic")        # table_navi/init
        self.init_lift_topic = rospy.get_param("~init_lift_topic")          # lifter/init
        self.check_drive_topic = rospy.get_param("~check_drive_topic")      # waypoint_navi/check_drive

        # Define Adjustable Parameters
        self.path_directory = rospy.get_param("~path_directory")
        self.wait_time = rospy.get_param("~wait_time")              # [sec]

        # Define Paths' File Name
        self.path_1 = self.path_directory + "/psa_home_A.traj"
        self.path_2 = self.path_directory + "/home_B.traj"
        self.path_3 = self.path_directory + "/psa_A_1.traj"
        self.path_4 = self.path_directory + "/A_2.traj"
        self.path_5 = self.path_directory + "/A_3.traj"
        self.path_6 = self.path_directory + "/B_1.traj"
        self.path_7 = self.path_directory + "/B_2.traj"
        self.path_8 = self.path_directory + "/B_3.traj"
        self.path_9 = self.path_directory + "/psa_1_home.traj"
        self.path_10 = self.path_directory + "/2_home.traj"
        self.path_11 = self.path_directory + "/3_home.traj"
        self.path_12 = self.path_directory + "/psa_A_C.traj"
        self.path_13 = self.path_directory + "/psa_C_home.traj"
        self.path_14 = self.path_directory + "/psa_C_A.traj"
        self.path_15 = self.path_directory + "/psa_A_home.traj"
        self.path_16 = self.path_directory + "/psa_home_C.traj"
        self.sound_file = "/home/atlas80-b/Desktop/countdown_10_seconds.ogg"

        # Internal Use Variables - Do not modify without consultation
        self.pub_rate = rospy.Rate(1)    # 0.5 [Hz] <---> 2 [sec]
        self.voltage_percent = "100.0"
        self.c_pose = np.array( [100.0, 100.0] )    # [m, m]
        self.yaw = 0.0    # [Deg]
        self.lifter = "0"
        self.moving = "0"
        self.location = "home"
        self.start_pt = np.array( [0.0, 0.0] )
        self.end_pt = np.array( [0.0, 0.0] )
        self.last_end_pt = np.array( [1000.0, 1000.0] )
        self.route = []
        self.action = []
        self.last_msg = ""
        self.counter = 0       #   1 - 1st_Route | 2 - 2nd_Route | 3 - 3rd_Route | 4 - Finish_Job
        self.safe = True       # battery level safe for doing delivery or not
        self.finish_wait = False    # finish waiting or not
        self.dist_tolerance = 1.0    # [m]
        self.time_counter = 0
        self.timer = self.wait_time * 1    # [count = sec * Hz]
        self.finish_action = True    # finish appointed action or not
        self.volume = 1.0
        self.play_counter = 1
        self.delivery_status = ""
        self.start_check = False    # when to start on checking
        self.start_counter = 0
        self.cmd = False
        self.finish_turn = False    # finish turning or not
        self.finish_lift = False    # finish lifting or not
#        self.finish_lift = False    # finish dropping or not
        self.finish_table = False   # finish table navi or not
        self.step_counter = 1    # Steps to do 1~3
        self.drop_counter = 0       # used to monitoring Command Once
        self.lift_counter = 0       # used to monitoring Command Once

        # Subscribers
        self.battery_sub = rospy.Subscriber(self.battery_topic, String, self.batteryCB, queue_size=1)
        self.pose_sub = rospy.Subscriber(self.pose_topic, Odometry, self.poseCB, queue_size=1)
        self.lifter_sub = rospy.Subscriber(self.lifter_topic, String, self.lifterCB, queue_size=1)
        self.finish_turn_sub = rospy.Subscriber(self.finish_turn_topic, String, self.finish_turnCB, queue_size=1)
        self.finish_table_sub = rospy.Subscriber(self.finish_table_topic, Bool, self.finish_tableCB, queue_size=1)
        self.moving_sub = rospy.Subscriber(self.moving_topic, Twist, self.movingCB, queue_size=1)
        self.traj_sub = rospy.Subscriber(self.traj_topic, PolygonStamped, self.trajCB, queue_size=1)
        self.mission_sub = rospy.Subscriber(self.mission_topic, String, self.missionCB, queue_size=1)
        self.check_resume_sub = rospy.Subscriber(self.check_resume_topic, Bool, self.check_resumeCB, queue_size=1)

        # Publishers
        self.path_pub = rospy.Publisher(self.path_topic, String, queue_size=1)
        self.all_pub = rospy.Publisher(self.all_topic, String, queue_size=1)
        self.suspend_pub = rospy.Publisher(self.suspend_topic, Bool, queue_size=1)
        self.init_turn_pub = rospy.Publisher(self.init_turn_topic, Bool, queue_size=1)
        self.init_table_pub = rospy.Publisher(self.init_table_topic, Bool, queue_size=1)
        self.init_lift_pub = rospy.Publisher(self.init_lift_topic, String, queue_size=1)
        self.check_drive_pub = rospy.Publisher(self.check_drive_topic, Bool, queue_size=1)

        mixer.init()
        self.sound = mixer.Sound(self.sound_file)

        # Main Loop
        self.adhoc_path_publisher()

    # Checking Battery Voltage (%), whether need to activate self-charging mode
    def batteryCB(self, msg):
        self.voltage_percent = msg.data

    # Checking Current Pose (x-pos, y-pos, yaw-angle)
    def poseCB(self, msg):
        self.c_pose = np.array( [msg.pose.pose.position.x, msg.pose.pose.position.y] )
        self.yaw = self.quaternion_to_angle(msg.pose.pose.orientation)

    # Checking Lifter Status (Top, Bottom)
    def lifterCB(self, msg):
        lifter_status = int(msg.data)
        if(lifter_status == 1):
            self.lifter = "1"    # Top
            if(self.start_check == True):
                self.finish_lift = True        # Done Lifting
            else:
                self.finish_lift = False       # On Going
        elif(lifter_status == 0):
            self.lifter = "0"    # Bottom
            if(self.start_check == True):
                self.finish_lift = True        # Done Dropping
            else:
                self.finish_lift = False       # On Going

    # Checking Status of 180' Turning
    def finish_turnCB(self, msg):
        if(int(msg.data) == 2):
            self.finish_turn = True     # Done 180' Turning
        elif(int(msg.data) == 1):
            self.finish_turn = False    # On Going

    # Checking Status of Table Navi
    def finish_tableCB(self, msg):
        if(msg.data == True):
            self.finish_table = True    # Done Table Navi
        elif(msg.data == False):
            self.finish_table = False   # On Going

    # Checking Moving Status (Moving, Stop)
    def movingCB(self, msg):
        if(msg.linear.x != 0.0 or msg.angular.z != 0.0):
            self.moving = "1"    # Moving
        else:
            self.moving = "0"    # Stop

    # Checking finish waiting (Resume being toggled)
    def check_resumeCB(self, msg):
        if(self.start_check == True):
            # If Resume is being toggled, finish_waiting = True
            if(msg.data == False):
                self.finish_wait = True

    # Checking the start-point and end-point of a selected path
    def trajCB(self, msg):
        self.start_pt = np.array( [msg.polygon.points[0].x, msg.polygon.points[0].y] )
        self.end_pt = np.array( [msg.polygon.points[-1].x, msg.polygon.points[-1].y] )

    # Receiving Mission from WebServer
    def missionCB(self, msg):
        if(self.last_msg != msg.data) and (msg.data != ""):
            route_action = []
            self.route = []
            self.action = []
            mission = msg.data.split(",")
            for i in xrange(len(mission)):
                route_action.append(mission[i].split("-"))
                self.route.append(route_action[i][0])
                self.action.append(int(route_action[i][1]))
            self.counter = 1
            self.location = "Shado_Home"
            self.delivery_status = "started"
        self.last_msg = msg.data

    # 1st - x_pos | 2nd - y_pos | 3rd - yaw | 4th - lifter | 5th - moving
    # 6th - voltage | 7th - delivery_status | 8th - location
    # All Robot Status Publisher
    def status_publisher(self):
        all_msg = str(self.c_pose[0]) +","+ str(self.c_pose[1]) +","+ str(self.yaw) +","+ self.lifter +","+ self.moving +","+ self.voltage_percent +","+ self.delivery_status +","+ self.location
        self.all_pub.publish(all_msg)

    # Adhoc Path Chooser
    def adhoc_path_publisher(self):
        while not rospy.is_shutdown():
            print "delivery_status :  " + str(self.delivery_status)
            print "finish_table :  " + str(self.finish_table)
            print "finish_lift :  " + str(self.finish_lift)
            print "finish_turn :  " + str(self.finish_turn)
            print "start_check :  " + str(self.start_check)
            # Publish vehicle status to the Web-Server-Handler
            self.status_publisher()
            # Check Mission Accomplished Status
            self.mission_done_checker()
            # Check Action Accomplished Status
            self.action_done_checker()
            print "finish_action : " + str(self.finish_action)
            # Skip below if action is not yet finished
            if(self.finish_action == False):
                continue
            # Check Battery Status
            self.battery_safe_checker()
            # Skip below if battery is lower than 40% and already finished the last mission
            if(self.safe == False and self.delivery_status == "completed"):
                continue
            # Depart from Home
            if(self.counter == 1 and len(self.route) >= 2):
                self.location = self.route[0]
                if(self.route[0] == "Psa_Home" and self.route[1] == "Psa_A"):
                    chosen_path = self.path_1
                elif(self.route[0] == "Psa_Home" and self.route[1] == "Psa_C"):
                    chosen_path = self.path_16
            # Heading to destination
            elif(self.counter == 2 and len(self.route) >= 2):
                if(self.route[0] == "Psa_A" and self.route[1] == "Psa_1"):
                    chosen_path = self.path_3
                elif(self.route[0] == "Psa_C" and self.route[1] == "Psa_A"):
                    chosen_path = self.path_14
                elif(self.route[0] == "Shado_A" and self.route[1] == "Shado_3"):
                    chosen_path = self.path_5
                elif(self.route[0] == "Shado_B" and self.route[1] == "Shado_1"):
                    chosen_path = self.path_6
                elif(self.route[0] == "Shado_B" and self.route[1] == "Shado_2"):
                    chosen_path = self.path_7
                elif(self.route[0] == "Shado_B" and self.route[1] == "Shado_3"):
                    chosen_path = self.path_8
                elif(self.route[0] == "Psa_A" and self.route[1] == "Psa_C"):
                    chosen_path = self.path_12
            # Returning Home
            elif(self.counter == 3 and len(self.route) == 1):
                if(self.route[0] == "Psa_1"):
                    chosen_path = self.path_9
                elif(self.route[0] == "Shado_2"):
                    chosen_path = self.path_10
                elif(self.route[0] == "Shado_3"):
                    chosen_path = self.path_11
                elif(self.route[0] == "Psa_C"):
                    chosen_path = self.path_13
                elif(self.route[0] == "Psa_A"):
                    chosen_path = self.path_15
            else:
                chosen_path = None
            if(chosen_path != None):
                self.path_pub.publish(chosen_path)
            print chosen_path
            self.check_drive_pub.publish(True)      # Allow vehicle continue moving with the given path
            self.finish_table = False    # Reset the finish_table after done each action
            self.finish_lift = False     # Reset the finish_lift after done each action
            self.finish_turn = False     # Reset the finish_turn after done each action
            self.pub_rate.sleep()

    # Check the Mission Accomplished Status
    def mission_done_checker(self):
        if(self.route != []):
            # 1st completeness (arrived 1st location)
            if(self.dist_checker(self.c_pose, self.end_pt) and self.counter == 1):
                self.counter = 2
                del self.route[0]
                self.delivery_status = "arrived"
                self.location = self.route[0]
                self.last_end_pt = self.end_pt
            # 2nd completeness (arrived 2nd location)
            elif(self.dist_checker(self.c_pose, self.end_pt) and self.counter == 2 and self.last_end_pt[0] != self.end_pt[0] and self.last_end_pt[1] != self.end_pt[1]):
                self.counter = 3
                del self.route[0]
                self.delivery_status = "arrived"
                self.location = self.route[0]
                self.last_end_pt = self.end_pt
            # 3rd completeness (back to home)
            elif(self.dist_checker(self.c_pose, self.end_pt) and self.counter == 3 and self.last_end_pt[0] != self.end_pt[0] and self.last_end_pt[1] != self.end_pt[1]):
                self.counter = 4 # Finish Job
                self.last_end_pt = np.array( [0.0, 0.0] )
                del self.route[0]
                self.location = "Psa_Home"
            else:
                self.counter = self.counter
        elif(self.route == [] and self.counter == 4):
            self.delivery_status = "completed"

    # Check the Action Accomplished Status
    def action_done_checker(self):
        if(len(self.action) >=1):
            # Stop & Wait
            if(self.action[0] == 3 and self.delivery_status == "arrived"):
                self.check_drive_pub.publish(False)
                print "Stop & Wait"
                # Suspend the vehicle upon arrival
                if(self.finish_wait == False):
                    self.finish_action = False
                    if(self.start_counter == 0):
                        self.toggle_suspend_resume()
                    # Use for delaying the checkCB()
                    if(self.start_counter == 3):
                        self.start_check = True
                    self.start_counter = self.start_counter + 1
                # Resume the vehicle after someone toggle "Resume"
                elif(self.finish_wait == True):
                    del self.action[0]
                    self.finish_wait = False
                    self.finish_action = True
                    self.delivery_status = "departed"
                    self.start_check = False
                    self.start_counter = 0
            # Stop & Go
            elif(self.action[0] == 4 and self.delivery_status == "arrived"):
                self.check_drive_pub.publish(False)
                print "Stop & Go"
                remaining_time = int((self.timer - self.time_counter)/1)
                # Suspend the vehicle during countdown
                if(self.time_counter < self.timer):
                    self.finish_action = False
                    if(self.time_counter == 0):
                        self.toggle_suspend_resume()
                    if(remaining_time == 11 and self.play_counter == 1):
                        self.sound.set_volume(self.volume)
                        self.sound.play()
                        self.play_counter = 0
                    self.time_counter = self.time_counter + 1
                # Resume the vehicle after finish countdown
                else:
                    self.time_counter = 0
                    if(self.time_counter == 0):
                        self.toggle_suspend_resume()
                    del self.action[0]
                    self.finish_action = True
                    self.delivery_status = "departed"
                    self.play_counter = 1
            # No Action
            elif(self.action[0] == 0):
                print "No Action"
                self.finish_action = True
                del self.action[0]
            # Pick Table --- Steps:  1st - Table Navi, 2nd - Lift Table, 3rd - Turning 180'
            elif(self.action[0] == 1 and self.delivery_status == "arrived"):
                self.check_drive_pub.publish(False)
                print "Pick Table"
                if(self.finish_table == False or self.finish_lift == False or self.finish_turn == False):
                    self.finish_action = False
                    # Initiating - Table Navi
                    if(self.step_counter == 1):
                        print "Step - 1"
                        self.init_table_pub.publish(True)
                        self.step_counter = 2
                    # Initiating - Lift Table
                    elif(self.step_counter == 2 and self.finish_table == True):
                        print "Step - 2"
                        self.init_table_pub.publish(False)
                        if(self.lift_counter == 0):
                            self.init_lift_pub.publish("1")    # lifting up
                        # Use for delaying the checking on lifterCB()
                        if(self.lift_counter == 3):
                            self.start_check = True
                            self.step_counter = 3
                        self.lift_counter = self.lift_counter + 1
                    # Initiating - Turning 180'
                    elif(self.step_counter == 3 and self.finish_table == True and self.finish_lift == True):
                        print "Step - 3"
                        self.init_lift_pub.publish("2")
                        self.init_turn_pub.publish(True)
                # Finish All Steps
                elif(self.finish_table == True and self.finish_lift == True and self.finish_turn == True):
                    print "All Steps Finished"
                    del self.action[0]
                    self.finish_action = True
                    self.delivery_status = "departed"
                    self.step_counter = 1
                    self.start_check = False
                    self.lift_counter = 0
                    self.init_table_pub.publish(False)
                    self.init_lift_pub.publish("2")
                    self.init_turn_pub.publish(False)
            # Drop Table --- Steps:  1st - Turning 180', 2nd - Drop Table
            elif(self.action[0] == 2 and self.delivery_status == "arrived"):
                self.check_drive_pub.publish(False)
                print "Drop Table"
                if(self.finish_turn == False or self.finish_lift == False):
                    self.finish_action = False
                    # Initiating - Turning 180'
                    if(self.step_counter == 1):
                        self.init_turn_pub.publish(True)
                        self.step_counter = 2
                    # Initiating - Drop Table
                    elif(self.step_counter == 2 and self.finish_turn == True):
                        self.init_turn_pub.publish(False)
                        if(self.drop_counter == 0):
                            self.init_lift_pub.publish("0")    # lowering down
                        # Use for delaying the checking on lifterCB()
                        if(self.drop_counter == 3):
                            self.start_check = True
                        self.drop_counter = self.drop_counter + 1
                # Finish All Steps
                elif(self.finish_turn == True and self.finish_lift == True):
                    del self.action[0]
                    self.finish_action = True
                    self.delivery_status = "departed"
                    self.step_counter = 1
                    self.start_check = False
                    self.drop_counter = 0
                    self.init_turn_pub.publish(False)
                    self.init_lift_pub.publish("2")
        self.pub_rate.sleep()

    # Check battery percentage, vehicle is not allowed to do the delivery when drop below certain %
    def battery_safe_checker(self):
        if(self.voltage_percent > 40.0):
            self.safe = True
        else:
            self.safe = False
        self.pub_rate.sleep()

    # Distance Checker, Checking whether distance between 2 points is within distance_tolerance or not
    def dist_checker(self, a, b):
        distance = np.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)
        if(distance <= self.dist_tolerance):
            return True
        else:
            return False

    # Trigger Suspend/Resume like a toggle button
    def toggle_suspend_resume(self):
        self.cmd = not self.cmd
        self.suspend_pub.publish(self.cmd)

    # Convert Quaternion to Angle
    def quaternion_to_angle(self, q):
	"""Convert a quaternion _message_ into an angle in radians.
	The angle represents the yaw.
	This is not just the z component of the quaternion."""
	x, y, z, w = q.x, q.y, q.z, q.w
	roll, pitch, yaw = tf.transformations.euler_from_quaternion((x, y, z, w))
	return yaw



if __name__=="__main__":
    rospy.init_node("navigation_decider_v1_2")
    NavigationDeciderV1_2()
    rospy.spin()