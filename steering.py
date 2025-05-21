
import math

class SteeringSystem:
    """
    Calculates front wheel steering angles based on Ackermann, Anti-Ackermann,
    or parallel steering principles.
    """

    def __init__(
        self,
        wheelbase: float,
        track_width_front: float,
        max_steering_angle_inner_wheel_rad: float,
        ackermann_percentage: float = 1.0,
    ):
        """
        Initializes the steering system.

        Args:
            wheelbase (float): The distance between the front and rear axles (L).
            track_width_front (float): The distance between the centers of the
                                       front wheels (T).
            max_steering_angle_inner_wheel_rad (float): Maximum steering angle
                in radians that the inner wheel can achieve at 100% steering input.
                Must be > 0 and < pi/2.
            ackermann_percentage (float, optional): Defines the steering geometry.
                1.0 for full Ackermann.
                0.0 for parallel steering.
                -1.0 for full Anti-Ackermann.
                Defaults to 1.0.
        """

        if not (
            0 < max_steering_angle_inner_wheel_rad < math.pi / 2.0
        ):
            raise ValueError(
                "Max steering angle (radians) for inner wheel must be "
                "positive and less than pi/2 (90 degrees)."
            )
        if not (-1.0 <= ackermann_percentage <= 1.0):
            raise ValueError(
                "Ackermann percentage must be between -1.0 and 1.0."
            )

        self.wheelbase = wheelbase
        self.track_width_front = track_width_front
        self.max_steer_angle_rad = max_steering_angle_inner_wheel_rad
        self.ackermann_percentage = ackermann_percentage

    def get_wheel_angles(
        self, steering_input_percentage: float
    ) -> tuple[float, float]:
        """
        Calculates the steering angles for the front left and front right tires.

        Args:
            steering_input_percentage (float): Steering input from -1.0
                (full left) to 1.0 (full right). 0.0 means straight.

        Returns:
            tuple[float, float]: (front_left_angle_rad, front_right_angle_rad)
                                 Angles are in radians.
                                 Positive angle: wheel steered to the right.
                                 Negative angle: wheel steered to the left.
        """
        if not (-1.0 <= steering_input_percentage <= 1.0):
            raise ValueError(
                "Steering input percentage must be between -1.0 and 1.0."
            )

        if steering_input_percentage == 0.0:
            return 0.0, 0.0

        steer_sign = math.copysign(1.0, steering_input_percentage)
        abs_input = abs(steering_input_percentage)

        # Target angle for the inner wheel based on input percentage
        # This is delta_i in Ackermann formulas
        delta_inner_target_rad = abs_input * self.max_steer_angle_rad

        if delta_inner_target_rad == 0.0: # Should be caught by initial check
            return 0.0, 0.0

        # Calculate pure Ackermann outer wheel angle (delta_o)
        # cot(delta_o) = cot(delta_i) + T / L
        # delta_o = arccot(cot(delta_i) + T/L)
        
        # cot(delta_i)
        # Note: max_steer_angle_rad is < pi/2, so delta_inner_target_rad is < pi/2
        # tan(delta_inner_target_rad) will not be zero unless delta_inner_target_rad is zero (handled)
        cot_delta_inner = 1.0 / math.tan(delta_inner_target_rad)

        # cot(delta_i) + T / L
        # This term will be positive since cot_delta_inner > 0 and T/L > 0
        val_for_arccot_outer = cot_delta_inner + (
            self.track_width_front / self.wheelbase
        )
        
        # delta_o = arccot(val_for_arccot_outer) = arctan(1 / val_for_arccot_outer)
        # Since val_for_arccot_outer > 0, delta_outer_ackermann_rad will be in (0, pi/2)
        # Also, delta_outer_ackermann_rad < delta_inner_target_rad for T/L > 0
        delta_outer_ackermann_rad = math.atan(1.0 / val_for_arccot_outer)
        
        # Ackermann effect: difference between inner and outer wheel angles in pure Ackermann
        # ackermann_effect_rad = delta_inner - delta_outer (will be positive)
        ackermann_effect_rad = (
            delta_inner_target_rad - delta_outer_ackermann_rad
        )

        # Actual outer wheel angle based on ackermann_percentage
        # delta_outer_actual = delta_inner - (ack_perc * ack_effect)
        # If ack_perc = 1.0 (Ackermann): delta_outer_actual = delta_outer_ackermann_rad
        # If ack_perc = 0.0 (Parallel):  delta_outer_actual = delta_inner_target_rad
        # If ack_perc = -1.0 (Anti):    delta_outer_actual = delta_inner + ack_effect
        #                                                 = 2*delta_inner - delta_outer_ackermann
        delta_outer_actual_rad = (
            delta_inner_target_rad
            - self.ackermann_percentage * ackermann_effect_rad
        )

        # Assign angles with correct sign based on steering direction
        angle_inner_wheel_signed = steer_sign * delta_inner_target_rad
        angle_outer_wheel_signed = steer_sign * delta_outer_actual_rad

        if steering_input_percentage > 0:  # Turning Right
            # Right wheel is inner, Left wheel is outer
            front_right_angle_rad = angle_inner_wheel_signed
            front_left_angle_rad = angle_outer_wheel_signed
        else:  # Turning Left (steering_input_percentage < 0)
            # Left wheel is inner, Right wheel is outer
            front_left_angle_rad = angle_inner_wheel_signed # steer_sign is negative
            front_right_angle_rad = angle_outer_wheel_signed # steer_sign is negative

        return front_left_angle_rad, front_right_angle_rad

