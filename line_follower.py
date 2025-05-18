#!/usr/bin/env python3

from time import sleep
from enum import Enum

from ev3dev2.motor import LargeMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, SpeedPercent

from ev3dev2.sensor import INPUT_2,INPUT_3
from ev3dev2.sensor.lego import ColorSensor
from ev3dev2.sound import Sound


NORMAL_FORWARD_SPEED = 10
LEADING_WHEEL_TURNING_SPEED = 10
SUPPORTING_WHEEL_TURNING_SPEED = -13

RIGHT_MOTOR = LargeMotor(OUTPUT_A)
LEFT_MOTOR = LargeMotor(OUTPUT_B)
GRABBER_MOTOR = LargeMotor(OUTPUT_C)

LEFT_COLOR_SENSOR = ColorSensor(INPUT_3)
RIGHT_COLOR_SENSOR = ColorSensor(INPUT_2)

class Color(Enum):
	BLACK = "Black"
	WHITE = "White"
	UNKNOWN = "Unknown"


def debug_colors():
	print("Left sensor detected color: " + str(LEFT_COLOR_SENSOR.rgb) + ", it is said to be " + str(LEFT_COLOR_SENSOR.color_name))
	print("Right sensor detected color: " + str(RIGHT_COLOR_SENSOR.rgb) + ", it is said to be " + str(RIGHT_COLOR_SENSOR.color_name))


def go_forward():
	RIGHT_MOTOR.on(SpeedPercent(NORMAL_FORWARD_SPEED))
	LEFT_MOTOR.on(SpeedPercent(NORMAL_FORWARD_SPEED))


def brake():
	RIGHT_MOTOR.off(brake=True)
	LEFT_MOTOR.off(brake=True)


def get_color_from(sensor):
	red, green, blue = sensor.rgb

	if red > 90 and green > 170 and blue > 100:
		return Color.WHITE

	if red < 35 and green < 65 and blue < 35:
		return Color.BLACK

	if sensor.color_name in ["Black", "Brown"]:
		return Color.BLACK

	if sensor.color_name in ["White", "Yellow", "Blue", "Green"]:
		return Color.WHITE

	return Color.UNKNOWN


def turn_left():
	RIGHT_MOTOR.on(SpeedPercent(LEADING_WHEEL_TURNING_SPEED))
	LEFT_MOTOR.on(SpeedPercent(SUPPORTING_WHEEL_TURNING_SPEED))

def turn_right():
	RIGHT_MOTOR.on(SpeedPercent(SUPPORTING_WHEEL_TURNING_SPEED))
	LEFT_MOTOR.on(SpeedPercent(LEADING_WHEEL_TURNING_SPEED))


def follow_line():
	sound = Sound()

	for _ in range(3):
		sound.beep()
		sleep(0.3)

	while True:
		try:
			sleep(0.005)
			left_color = get_color_from(LEFT_COLOR_SENSOR)
			right_color = get_color_from(RIGHT_COLOR_SENSOR)
			# debug_colors()

			if left_color == Color.BLACK and right_color == Color.BLACK:
				# print("Both sensors are on black, we are on the intersection!")
				go_forward()
			elif left_color == Color.BLACK and right_color == Color.WHITE:
				turn_left()
			elif left_color == Color.WHITE and right_color == Color.BLACK:
				turn_right()
			else:
				go_forward()
		except KeyboardInterrupt:
			brake()
			exit()

if __name__ == "__main__":
	follow_line()
