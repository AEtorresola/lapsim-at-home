# car.py
import numpy as np


class Car:
    def __init__(self, mass, wheelbase, cg_front, cg_rear, cg_height, track_width, tire_radius, drag_coeff, downforce_coeff, frontal_area, rolling_resistance, tire_grip):
        self.mass = mass
        self.wheelbase = wheelbase
        self.cg_front = cg_front
        self.cg_rear = cg_rear
        self.cg_height = cg_height
        self.track_width = track_width
        self.tire_radius = tire_radius
        self.drag_coeff = drag_coeff
        self.downforce_coeff = downforce_coeff
        self.frontal_area = frontal_area
        self.rolling_resistance = rolling_resistance
        self.tire_grip = tire_grip
        
        # Driver inputs
        self.throttle_input = 0.0  # Throttle input (0.0 to 1.0)
        self.brake_input = 0.0      # Brake input (0.0 to 1.0)

    def set_driver_inputs(self, throttle, brake):
        self.throttle_input = throttle
        self.brake_input = brake

    def calculate_throttle_force(self):
        # Calculate the maximum traction force based on throttle input
        return self.throttle_input * self.tire_grip * self.mass * 9.81

    def calculate_brake_force(self):
        # Calculate the maximum braking force based on brake input
        return self.brake_input * self.tire_grip * self.mass * 9.81

    def calculate_motor_power(self, traction_force, velocity):
        return traction_force * velocity


