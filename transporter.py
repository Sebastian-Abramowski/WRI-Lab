#!/usr/bin/env python3

from time import sleep
from enum import Enum
from ev3dev2.motor import LargeMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, SpeedPercent, MediumMotor
from ev3dev2.sensor import INPUT_1, INPUT_4, INPUT_2
from ev3dev2.sensor.lego import ColorSensor, TouchSensor
from ev3dev2.sound import Sound

DEBUG = True

NORMAL_FORWARD_SPEED = 4
LEADING_WHEEL_TURNING_SPEED = 4
SUPPORTING_WHEEL_TURNING_SPEED = -7

RIGHT_MOTOR = LargeMotor(OUTPUT_A)
LEFT_MOTOR = LargeMotor(OUTPUT_B)
GRABBER_MOTOR = MediumMotor(OUTPUT_C)

LEFT_COLOR_SENSOR = ColorSensor(INPUT_4)
RIGHT_COLOR_SENSOR = ColorSensor(INPUT_1)
TOUCH_SENSOR = TouchSensor(INPUT_2)

class Color(Enum):
    BLACK = "Black"
    WHITE = "White"
    RED = "Red"
    BLUE = "Blue"
    UNKNOWN = "Unknown"

def debug_print(*args):
    if DEBUG:
        print(*args)

def get_color_from_V1(sensor):
    red, green, blue = sensor.rgb
    debug_print("RGB values: ", red, green, blue)

    if (red > 135 and green < 55 and blue < 45):
        return Color.RED

    if (red < 60 and green < 100 and blue > 100):
        return Color.BLUE

    if (red < 100 and green < 100 and blue < 100):
        return Color.BLACK

    if (red > 100 and green > 100 and blue > 100) or sensor.color_name in ["White", "Yellow"]:
        return Color.WHITE

    return Color.UNKNOWN

COLOR_BASES = {
    Color.RED:   (160, 40, 30),
    Color.BLUE:  (30, 60, 140),
    Color.BLACK: (20, 20, 20),
    Color.WHITE: (220, 220, 220),
}

def get_color_from_V2(sensor):
    red, green, blue = sensor.rgb
    debug_print("RGB values: ", red, green, blue)

    def avg_diff(color1, color2):
        return (abs(color1[0] - color2[0]) + abs(color1[1] - color2[1]) + abs(color1[2] - color2[2])) / 3

    best_color = Color.UNKNOWN
    best_score = float('inf')

    for color, base in COLOR_BASES.items():
        score = avg_diff(sensor.rgb, base)
        if score < best_score:
            best_score = score
            best_color = color

    return best_color


get_color_from = get_color_from_V2

class RobotState:
    def __init__(self, sound):
        self.state = 0
        self.sound = sound

    def update(self):
        left_color = get_color_from(LEFT_COLOR_SENSOR)
        right_color = get_color_from(RIGHT_COLOR_SENSOR)

        debug_print("Colors before updating state: ", left_color, right_color)

        if (self.state == 0):
            self._follow_line(left_color, right_color)

            if (right_color == Color.BLUE):
                RIGHT_MOTOR.on(SpeedPercent(0))
                LEFT_MOTOR.on(SpeedPercent(4))

                self.state = 1

            elif (left_color == Color.BLUE):
                RIGHT_MOTOR.on(SpeedPercent(4))
                LEFT_MOTOR.on(SpeedPercent(0))

                self.state = 4

        # turning right
        elif (self.state == 1):

            if (left_color == Color.BLACK):
                self.state = 2

        elif (self.state == 2):

            if (left_color == Color.WHITE):
                self.state = 3

        elif (self.state == 3):

            if (left_color == Color.BLACK):
                self.state = 7

        # turning left
        elif (self.state == 4):

            if (right_color == Color.BLACK):
                self.state = 5

        elif (self.state == 5):

            if (right_color == Color.WHITE):
                self.state = 6

        elif (self.state == 6):

            if (right_color == Color.BLACK):
                self.state = 7

        # after turning
        elif (self.state == 7):
            self._follow_line(left_color, right_color)

            if (left_color == Color.BLUE or right_color == Color.BLUE):
                RIGHT_MOTOR.on(SpeedPercent(0))
                LEFT_MOTOR.on(SpeedPercent(0))

                sleep(1)
                self.sound.beep()
                sleep(1)

                self.grab_until_stall()

                self.state = 8

        # after grabbing
        elif (self.state == 8):
            RIGHT_MOTOR.on(SpeedPercent(-10))
            LEFT_MOTOR.on(SpeedPercent(10))

            if (right_color == Color.BLACK):
                self.state = 9

        elif (self.state == 9):
            if (right_color == Color.BLUE):
                right_color = Color.BLACK

            if (left_color == Color.BLUE):
                left_color = Color.BLACK

            self._follow_line(left_color, right_color)

            if (left_color == Color.BLACK or right_color == Color.BLACK):
                RIGHT_MOTOR.on(SpeedPercent(0))
                LEFT_MOTOR.on(SpeedPercent(0))

                self.state = 10

        # stopped on black black, turning right
        elif (self.state == 10):
            RIGHT_MOTOR.on(SpeedPercent(0))
            LEFT_MOTOR.on(SpeedPercent(4))

            if (left_color == Color.WHITE):
                self.state = 11

        elif (self.state == 11):

            if (left_color == Color.BLACK):
                RIGHT_MOTOR.on(SpeedPercent(0))
                LEFT_MOTOR.on(SpeedPercent(0))

                self.state = 12

        # go to red
        elif (self.state == 12):

            self._follow_line(left_color, right_color)

            if (right_color == Color.RED):
                RIGHT_MOTOR.on(SpeedPercent(0))
                LEFT_MOTOR.on(SpeedPercent(4))

                self.state = 13

            elif (left_color == Color.RED):
                RIGHT_MOTOR.on(SpeedPercent(4))
                LEFT_MOTOR.on(SpeedPercent(0))

                self.state = 16

        # turning right
        elif (self.state == 13):

            if (left_color == Color.BLACK):
                self.state = 14

        elif (self.state == 14):

            if (left_color == Color.WHITE):
                self.state = 15

        elif (self.state == 15):

            if (left_color == Color.BLACK):
                self.state = 19

        # turning left
        elif (self.state == 16):

            if (right_color == Color.BLACK):
                self.state = 17

        elif (self.state == 17):

            if (right_color == Color.WHITE):
                self.state = 18

        elif (self.state == 18):

            if (right_color == Color.BLACK):
                self.state = 19

        # after turning
        elif (self.state == 19):
            self._follow_line(left_color, right_color)

            if (left_color == Color.RED or right_color == Color.RED):
                RIGHT_MOTOR.on(SpeedPercent(0))
                LEFT_MOTOR.on(SpeedPercent(0))

                self.release_until_stall()

                self.state = 20

        elif (self.state == 20):
            self.sound.beep()
            sleep(0.1)
            self.sound.beep()
            self.state = 21

        # champions
        elif (self.state == 21):
            pass

        else:
            self.brake()
            self.sound.beep()

    def _follow_line(self, left_color, right_color):
        if left_color == Color.BLACK and right_color == Color.BLACK:
            self._go_forward()
        elif left_color == Color.BLACK and right_color == Color.WHITE:
            self._turn_left()
        elif left_color == Color.WHITE and right_color == Color.BLACK:
            self._turn_right()
        else:
            self._go_forward()

    def _go_forward(self):
        RIGHT_MOTOR.on(SpeedPercent(NORMAL_FORWARD_SPEED))
        LEFT_MOTOR.on(SpeedPercent(NORMAL_FORWARD_SPEED))

    def _turn_left(self):
        RIGHT_MOTOR.on(SpeedPercent(LEADING_WHEEL_TURNING_SPEED))
        LEFT_MOTOR.on(SpeedPercent(SUPPORTING_WHEEL_TURNING_SPEED))

    def _turn_right(self):
        RIGHT_MOTOR.on(SpeedPercent(SUPPORTING_WHEEL_TURNING_SPEED))
        LEFT_MOTOR.on(SpeedPercent(LEADING_WHEEL_TURNING_SPEED))

    def grab_until_stall(self):
        GRABBER_MOTOR.on(SpeedPercent(30))

        while True:
            if GRABBER_MOTOR.is_stalled:
                GRABBER_MOTOR.off(brake=True)
                break
            sleep(0.1)

    def release_until_stall(self):
        GRABBER_MOTOR.on(SpeedPercent(-30))

        while True:
            if GRABBER_MOTOR.is_stalled:
                GRABBER_MOTOR.off(brake=False)
                break
            sleep(0.1)

    def brake(self):
        RIGHT_MOTOR.off(brake=False)
        LEFT_MOTOR.off(brake=False)


def perform_transporting():
    sound = Sound()
    for _ in range(3):
        sound.beep()
        sleep(0.3)

    robot = RobotState(sound)

    while True:
        try:
            sleep(0.005)

            if TOUCH_SENSOR.is_pressed:
                robot.brake()
                sound.beep()
                sleep(0.5)
                sound.beep()
                robot.state = 0

            debug_print("Currently in state: ", robot.state)
            robot.update()
        except KeyboardInterrupt:
            robot.brake()
            break

if __name__ == "__main__":
    perform_transporting()
