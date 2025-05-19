#!/usr/bin/env python3

from time import sleep
from enum import Enum
from ev3dev2.motor import LargeMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, SpeedPercent, MediumMotor
from ev3dev2.sensor import INPUT_1, INPUT_4
from ev3dev2.sensor.lego import ColorSensor
from ev3dev2.sound import Sound

DEBUG = False

# line follower
NORMAL_FORWARD_SPEED = 6
LEADING_WHEEL_TURNING_SPEED = 8
SUPPORTING_WHEEL_TURNING_SPEED = -12

# transporter
ONE_WHEEL_TURNING_SPEED = 7
CORRECTION_DEGRE = 150
CORRECTION_SPEED = 20
TURN_AROUND_SPEED = 5

RIGHT_MOTOR = LargeMotor(OUTPUT_A)
LEFT_MOTOR = LargeMotor(OUTPUT_B)
GRABBER_MOTOR = MediumMotor(OUTPUT_C)

LEFT_COLOR_SENSOR = ColorSensor(INPUT_4)
RIGHT_COLOR_SENSOR = ColorSensor(INPUT_1)

state = 0
sound = Sound()

class Color(Enum):
    BLACK = "Black"
    WHITE = "White"
    RED = "Red"
    BLUE = "Blue"
    YELLOW = "Yellow"
    GREEN = "Green"
    UNKNOWN = "Unknown"

PICKUP_COLOR = Color.GREEN
DROP_COLOR = Color.RED

def debug_print(*args):
    if DEBUG:
        print(*args)

COLOR_BASES = {
    Color.RED:   (125, 35, 15),
    Color.BLUE:  (20, 80, 90),
    Color.BLACK: (22, 38, 20),
    Color.WHITE: (150, 225, 162),
    Color.GREEN: (17, 100, 30),
    Color.YELLOW: (170, 235, 33)
}

def get_color_from(sensor):
    sensor_color = sensor.rgb
    # debug_print("RGB values: ", sensor_color)

    def diff(color1, color2):
        return ((color1[0] - color2[0])**2 + (color1[1] - color2[1])**2 + (color1[2] - color2[2])**2)

    best_color = Color.UNKNOWN
    best_score = float('inf')

    for color, base in COLOR_BASES.items():
        score = diff(sensor.rgb, base)
        if score < best_score:
            best_score = score
            best_color = color

    # ignore
    if best_color not in [Color.BLACK, Color.WHITE, PICKUP_COLOR, DROP_COLOR]:
        best_color = Color.WHITE

    # correction
    red, green, blue = sensor_color
    if best_color == Color.GREEN and (green < 83 or red > 30):
        best_color = Color.WHITE

    return best_color

def update():
    global state

    left_color = get_color_from(LEFT_COLOR_SENSOR)
    right_color = get_color_from(RIGHT_COLOR_SENSOR)

    # debug_print("Colors before updating state: ", left_color, right_color)

    if (state == 0):
        follow_line(left_color, right_color)
        if (right_color == PICKUP_COLOR):
            RIGHT_MOTOR.on(SpeedPercent(0))
            LEFT_MOTOR.on(SpeedPercent(ONE_WHEEL_TURNING_SPEED))
            state = 1
        elif (left_color == PICKUP_COLOR):
            RIGHT_MOTOR.on(SpeedPercent(ONE_WHEEL_TURNING_SPEED))
            LEFT_MOTOR.on(SpeedPercent(0))
            state = 4

    # turning right
    elif (state == 1):
        if (left_color == Color.BLACK):
            state = 2

    elif (state == 2):
        if (left_color == Color.WHITE):
            state = 3

    elif (state == 3):
        if (left_color == Color.BLACK):
            LEFT_MOTOR.on(SpeedPercent(0))
            RIGHT_MOTOR.on_for_degrees(SpeedPercent(CORRECTION_SPEED), CORRECTION_DEGRE)
            state = 7

    # turning left
    elif (state == 4):
        if (right_color == Color.BLACK):
            state = 5

    elif (state == 5):
        if (right_color == Color.WHITE):
            state = 6

    elif (state == 6):
        if (right_color == Color.BLACK):
            RIGHT_MOTOR.on(SpeedPercent(0))
            LEFT_MOTOR.on_for_degrees(SpeedPercent(CORRECTION_SPEED), CORRECTION_DEGRE)
            state = 7

    # after turning
    elif (state == 7):
        follow_line(left_color, right_color)

        if (left_color == PICKUP_COLOR and right_color == PICKUP_COLOR):
            RIGHT_MOTOR.on(SpeedPercent(0))
            LEFT_MOTOR.on(SpeedPercent(0))

            sleep(0.5)
            sound.beep()
            sleep(0.5)

            grab_until_stall()
            sleep(0.025)

            RIGHT_MOTOR.on(SpeedPercent(-TURN_AROUND_SPEED))
            LEFT_MOTOR.on(SpeedPercent(TURN_AROUND_SPEED))
            state = 8

    # after grabbing
    elif (state == 8):
        if (right_color == Color.BLACK or left_color == Color.BLACK):
            RIGHT_MOTOR.on(SpeedPercent(0))
            LEFT_MOTOR.on(SpeedPercent(0))
            state = 9

    elif (state == 9):
        if (right_color == PICKUP_COLOR):
            right_color = Color.BLACK

        if (left_color == PICKUP_COLOR):
            left_color = Color.BLACK

        follow_line(left_color, right_color)

        if (left_color == Color.BLACK and right_color == Color.BLACK):
            RIGHT_MOTOR.on(SpeedPercent(0))
            LEFT_MOTOR.on(SpeedPercent(ONE_WHEEL_TURNING_SPEED))
            state = 10

    # stopped on black black, turning right
    elif (state == 10):
        if (left_color == Color.WHITE):
            state = 11

    elif (state == 11):
        if (left_color == Color.BLACK):
            LEFT_MOTOR.on(SpeedPercent(0))
            RIGHT_MOTOR.on_for_degrees(SpeedPercent(CORRECTION_SPEED), CORRECTION_DEGRE)
            state = 12

    # go to red
    elif (state == 12):

        follow_line(left_color, right_color)

        if (right_color == DROP_COLOR):
            RIGHT_MOTOR.on(SpeedPercent(0))
            LEFT_MOTOR.on(SpeedPercent(ONE_WHEEL_TURNING_SPEED))
            state = 13
        elif (left_color == DROP_COLOR):
            RIGHT_MOTOR.on(SpeedPercent(ONE_WHEEL_TURNING_SPEED))
            LEFT_MOTOR.on(SpeedPercent(0))
            state = 16

    # turning right
    elif (state == 13):
        if (left_color == Color.BLACK):
            state = 14

    elif (state == 14):
        if (left_color == Color.WHITE):
            state = 15

    elif (state == 15):
        if (left_color == Color.BLACK):
            LEFT_MOTOR.on(SpeedPercent(0))
            RIGHT_MOTOR.on_for_degrees(SpeedPercent(CORRECTION_SPEED), CORRECTION_DEGRE)
            state = 19

    # turning left
    elif (state == 16):
        if (right_color == Color.BLACK):
            state = 17

    elif (state == 17):
        if (right_color == Color.WHITE):
            state = 18

    elif (state == 18):
        if (right_color == Color.BLACK):
            RIGHT_MOTOR.on(SpeedPercent(0))
            LEFT_MOTOR.on_for_degrees(SpeedPercent(CORRECTION_SPEED), CORRECTION_DEGRE)
            state = 19

    # after turning
    elif (state == 19):
        follow_line(left_color, right_color)

        if (left_color == DROP_COLOR or right_color == DROP_COLOR):
            RIGHT_MOTOR.on(SpeedPercent(0))
            LEFT_MOTOR.on(SpeedPercent(0))
            release_until_stall()
            state = 20

    elif (state == 20):
        brake()
        sound.beep()
        sleep(0.1)
        sound.beep()
        state = 21

    # champions
    elif (state == 21):
        pass

    else:
        brake()
        sound.beep()

def follow_line( left_color, right_color):
    if left_color == Color.BLACK and right_color == Color.WHITE:
        RIGHT_MOTOR.on(SpeedPercent(LEADING_WHEEL_TURNING_SPEED))
        LEFT_MOTOR.on(SpeedPercent(SUPPORTING_WHEEL_TURNING_SPEED))
        # sleep(0.025)
    elif left_color == Color.WHITE and right_color == Color.BLACK:
        RIGHT_MOTOR.on(SpeedPercent(SUPPORTING_WHEEL_TURNING_SPEED))
        LEFT_MOTOR.on(SpeedPercent(LEADING_WHEEL_TURNING_SPEED))
        # sleep(0.025)
    else:
        RIGHT_MOTOR.on(SpeedPercent(NORMAL_FORWARD_SPEED))
        LEFT_MOTOR.on(SpeedPercent(NORMAL_FORWARD_SPEED))

def grab_until_stall():
    GRABBER_MOTOR.on(SpeedPercent(25))

    while True:
        if GRABBER_MOTOR.is_stalled:
            GRABBER_MOTOR.off(brake=False)
            break
        sleep(0.02)

def release_until_stall():
    GRABBER_MOTOR.on_for_degrees(SpeedPercent(50), -2950)

    #GRABBER_MOTOR.on(SpeedPercent(-25))
    #while True:
    #    if GRABBER_MOTOR.is_stalled:
    #        GRABBER_MOTOR.off(brake=False)
    #        break
    #    sleep(0.02)

def brake():
    RIGHT_MOTOR.off(brake=False)
    LEFT_MOTOR.off(brake=False)


def perform_transporting():
    sound = Sound()
    for _ in range(3):
        sound.beep()
        sleep(0.3)

    try:
        while True:
            sleep(0.01)

            # debug_print("Currently in state: ", state)
            update()
    except KeyboardInterrupt:
        brake()

if __name__ == "__main__":
    perform_transporting()
