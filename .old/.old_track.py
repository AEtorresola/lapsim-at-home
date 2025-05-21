
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

class TrackSegment:
    def __init__(self, segment_type, length, curvature):
        self.type = segment_type.strip().lower()  # "left", "right", "straight"
        self.length = length  # meters
        self.curvature = curvature  # 1/m (positive for left, negative for right)

    def simulate_segment(self, current_x, current_y, current_angle, step_size=1.0):
        """Simulate movement through the segment and update position and angle."""
        x_points = [current_x]
        y_points = [current_y]

        if self.type == "straight":
            # Move straight in the current direction
            dx = self.length * np.cos(current_angle)
            dy = self.length * np.sin(current_angle)
            current_x += dx
            current_y += dy
            x_points.append(current_x)
            y_points.append(current_y)
        else:
            # Curved segment: calculate the arc
            radius = 1 / abs(self.curvature)
            theta = self.length / radius  # Angle in radians

            # Determine the center of the circle
            if self.curvature > 0:  # Left turn
                center_x = current_x - radius * np.sin(current_angle)
                center_y = current_y + radius * np.cos(current_angle)
            else:  # Right turn
                center_x = current_x + radius * np.sin(current_angle)
                center_y = current_y - radius * np.cos(current_angle)

            # Generate points along the arc
            num_steps = int(np.ceil(theta / (step_size / radius)))
            delta_theta = theta / num_steps
            for _ in range(num_steps):
                if self.curvature > 0:  # Left turn
                    current_angle += delta_theta
                else:  # Right turn
                    current_angle -= delta_theta
                current_x = center_x + radius * np.cos(current_angle + np.pi/2) if self.curvature > 0 else center_x + radius * np.cos(current_angle - np.pi/2)
                current_y = center_y + radius * np.sin(current_angle + np.pi/2) if self.curvature > 0 else center_y + radius * np.sin(current_angle - np.pi/2)
                x_points.append(current_x)
                y_points.append(current_y)

        return x_points, y_points, current_x, current_y, current_angle


class Track:
    def __init__(self, segments):
        self.segments = segments  # List of TrackSegment objects

    @classmethod
    def from_csv(cls, file_path):
        """Load track segments from a CSV and create a Track object."""
        segments = []
        df = pd.read_csv(file_path)
        for _, row in df.iterrows():
            segment_type = row['Type']
            length = row['Section Length']
            curvature = row['Corner Radius']
            segments.append(TrackSegment(segment_type, length, curvature))
        return cls(segments)

    def plot_full_track(self):
        """Simulate and plot the entire track."""
        # Initialize car position and direction
        current_x, current_y = 0.0, 0.0
        current_angle = 0.0  # Start facing the x-axis

        # Initialize lists to store all points
        all_x_points = [current_x]
        all_y_points = [current_y]

        # Simulate each segment
        for segment in self.segments:
            x_points, y_points, current_x, current_y, current_angle = segment.simulate_segment(current_x, current_y, current_angle)
            all_x_points.extend(x_points[1:])  # Skip the first point (duplicate of the last point of the previous segment)
            all_y_points.extend(y_points[1:])

        # Plot the full track
        plt.figure(figsize=(10, 6))
        plt.plot(all_x_points, all_y_points, 'b-', linewidth=2, label='Track Centerline')
        plt.scatter(all_x_points[0], all_y_points[0], color='green', label='Start', zorder=3)
        plt.scatter(all_x_points[-1], all_y_points[-1], color='red', label='End', zorder=3)
        plt.xlabel('X Position (m)')
        plt.ylabel('Y Position (m)')
        plt.title('Full Track Layout')
        plt.grid()
        plt.axis('equal')  # Ensure aspect ratio is 1:1
        plt.legend()
        plt.show()
