
# track.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math


class DynamicGraph:
    def __init__(self, colormap="viridis"):
        # List to hold (x, y) points.
        self.points = []
        # Create the figure and axis.
        self.fig, self.ax = plt.subplots()
        # Activate interactive mode.
        plt.ion()
        # Store the colormap.
        self.colormap = plt.get_cmap(colormap)
        # Initialize an empty scatter plot.
        self.sc = self.ax.scatter([], [], c=[], cmap=self.colormap)
        # Optionally, add a colorbar.
        self.cb = self.fig.colorbar(self.sc, ax=self.ax)
        self.ax.set_title("Dynamic Graph of Points")
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        # Set initial equal aspect ratio.
        self.ax.set_aspect("equal", "box")

    def _update_plot(self):
        """Update the scatter plot and adjust the axis limits."""
        if self.points:
            # Convert list of tuples to a NumPy array.
            data = np.array(self.points)
            x = data[:, 0]
            y = data[:, 1]
            # Create a color value for each point based on its order.
            colors = np.linspace(0, 1, len(self.points))
            # Update the scatter plot data.
            self.sc.set_offsets(data)
            self.sc.set_array(colors)

            # Calculate bounds of the data.
            x_min, x_max = np.min(x), np.max(x)
            y_min, y_max = np.min(y), np.max(y)

            # Compute ranges; if all x or all y values are the same, set a base
            # range.
            x_range = x_max - x_min if x_max != x_min else 1.0
            y_range = y_max - y_min if y_max != y_min else 1.0

            # To maintain 1:1 aspect, determine overall range.
            overall_range = max(x_range, y_range)
            # Calculate the center.
            mid_x = (x_min + x_max) / 2
            mid_y = (y_min + y_max) / 2

            # Add a margin (10% of the overall range) so points don't touch the
            # edge.
            margin = 0.1 * overall_range
            half_range = overall_range / 2 + margin

            new_xlim = (mid_x - half_range, mid_x + half_range)
            new_ylim = (mid_y - half_range, mid_y + half_range)

            # Set the new axis limits.
            self.ax.set_xlim(new_xlim)
            self.ax.set_ylim(new_ylim)
            # Reaffirm equal aspect ratio.
            self.ax.set_aspect("equal", "box")

            # Redraw the canvas.
            self.fig.canvas.draw_idle()
            # Pause briefly to allow an update in interactive mode.
            plt.pause(0.1)

    def add_points(self, new_points):
        """
        Add new points to the graph and update it.

        Parameters:
            new_points: sequence of (x, y) tuples or lists.
        """
        # Validate new_points format.
        if not all(
            isinstance(pt, (list, tuple)) and len(pt) == 2 for pt in new_points
        ):
            raise ValueError("Each point must be a tuple or list of two numbers.")

        # Append the new points.
        self.points.extend(new_points)
        # Update the plot.
        self._update_plot()


class TrackSegment:
    """Represents a segment of the track."""

    def __init__(self, segment_type, length, corner_radius=None):
        """
        Initializes a TrackSegment object.

        Args:
            segment_type: Type of the segment ('Straight', 'Left', 'Right').
            length: Length of the segment (m).
            corner_radius: Radius of the corner (m), only applicable for curved
                           segments.
        """
        self.segment_type = segment_type
        self.length = length
        self.corner_radius = corner_radius

    def __repr__(self):
        return (
            f"TrackSegment(type='{self.segment_type}', length={self.length}, "
            f"radius={self.corner_radius})"
        )


class Track:
    """Represents the entire track as a sequence of segments."""

    def __init__(self, segments):
        """
        Initializes a Track object.

        Args:
            segments: A list of TrackSegment objects.
        """
        self.segments = segments  # List of TrackSegment objects
        # Define the coordinate system: x-axis points forward, y-axis points to
        # the left.
        self.coordinate_system = "x-forward, y-left"

    @classmethod
    def from_csv(cls, file_path):
        """
        Load track segments from a CSV and create a Track object.

        Args:
            file_path: Path to the CSV file.

        Returns:
            A Track object.
        """
        try:
            df = pd.read_csv(file_path)
        except FileNotFoundError:
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        except pd.errors.EmptyDataError:
            raise ValueError(f"CSV file is empty: {file_path}")
        except pd.errors.ParserError:
            raise ValueError(f"Error parsing CSV file: {file_path}")

        segments = []
        required_columns = ["Type", "Section Length", "Corner Radius"]
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(
                    f"Required column '{col}' not found in CSV file."
                )

        for index, row in df.iterrows():
            try:
                segment_type = row["Type"]
                length = float(row["Section Length"])
                corner_radius = (
                    float(row["Corner Radius"])
                    if not pd.isna(row["Corner Radius"])
                    else None
                )  # Allow None for straight segments

                if segment_type not in ("Straight", "Left", "Right"):
                    raise ValueError(
                        f"Invalid segment type '{segment_type}' in row {index}."
                    )
                if length <= 0:
                    raise ValueError(
                        f"Segment length must be positive in row {index}."
                    )
                if (
                    segment_type != "Straight"
                    and (corner_radius is None or corner_radius <= 0)
                ):
                    raise ValueError(
                        "Corner radius must be positive for curved segments "
                        f"in row {index}."
                    )

                segment = TrackSegment(segment_type, length, corner_radius)
                segments.append(segment)
            except ValueError as e:
                raise ValueError(f"Error processing row {index}: {e}")

        return cls(segments)

    def construct_arc(
        self, center, start, arc_length, direction=1, num_points=100
    ):
        """
        Construct an arc of a circle given:

        - center: A tuple (cx, cy) representing the center of the circle.
        - start: A tuple (sx, sy) representing the starting point of the arc.
                This point must lie on the circle.
        - arc_length: The length along the circumference of the arc.
                    (Can be positive for counterclockwise or negative for
                    clockwise.)
        - num_points: The number of points to generate along the arc (default is
                      100).

        Returns:
        A tuple (arc_x, arc_y) where each is a NumPy array containing the x and
        y coordinates of the points along the arc.
        """
        cx, cy = center
        sx, sy = start

        # Compute the radius from the center to the start.
        dx, dy = sx - cx, sy - cy
        radius = math.hypot(dx, dy)
        if radius == 0:
            raise ValueError("The center and starting point cannot be the same.")

        # Determine the starting angle from the center to the start point.

        start_angle = math.atan2(dy, dx)
        # Compute the angular sweep; arc_length = radius * angular_sweep
        angular_sweep = arc_length / radius

        # Generate an array of angles from the starting angle to the end angle.
        angles = np.linspace(
            start_angle, start_angle + direction * angular_sweep, num_points
        )

        # Compute the (x, y) coordinates of the arc.
        arc_x = cx + radius * np.cos(angles)
        arc_y = cy + radius * np.sin(angles)

        return arc_x, arc_y

    def interpolate_points_by_length(self, start, end, steps_per_unit=4):
        """
        Returns a list of points [(x1, y1), ..., (x2, y2)] along the line
        between (x1, y1) and (x2, y2), with a density of steps_per_unit
        points per unit length.

        Parameters:
            start : tuple(float, float)
                Coordinates of the start point.
            end : tuple(float, float)
                Coordinates of the end point.
            steps_per_unit : int or float
                Number of steps per unit length.

        Returns:
            List of tuples representing the interpolated points.
        """
        x1, y1 = start
        x2, y2 = end
        # Calculate the Euclidean distance between the two points.
        distance = math.hypot(x2 - x1, y2 - y1)

        # Determine the number of segments.
        # Ensure we have at least 1 segment to avoid division by zero.
        segments = max(1, round(distance * steps_per_unit))

        points = []
        # Interpolate points; there are segments+1 points from 0 to segments.
        for i in range(segments + 1):
            t = i / segments  # t ranges from 0.0 to 1.0
            x = x1 + t * (x2 - x1)
            y = y1 + t * (y2 - y1)
            points.append((float(x), float(y)))

        return points

    def plot_track(self, graph, initial_angle, steps_per_unit=4):
        """Plots the track using the DynamicGraph."""

        # Position in meters, x, y
        current_x = 0
        current_y = 0
        # angle in radians
        current_angle = initial_angle

        all_points = [(0, 0)]  # Start at the origin

        for index, segment in enumerate(self.segments):
            segment_type = segment.segment_type
            length = segment.length
            corner_radius = segment.corner_radius

            if segment_type == "Straight":
                # Calculate the end point of the straight segment
                delta_x = np.cos(current_angle) * length
                delta_y = np.sin(current_angle) * length
                end_x = current_x + delta_x
                end_y = current_y + delta_y

                # Interpolate points along the straight line
                straightline_points = self.interpolate_points_by_length(
                    (current_x, current_y),
                    (end_x, end_y),
                    steps_per_unit=steps_per_unit,
                )

                # Avoid duplicate start point and ensure smooth transitions
                if all_points:
                    last_point = all_points[-1]
                    new_points = [
                        p
                        for p in straightline_points
                        if math.hypot(p[0] - last_point[0], p[1] - last_point[1])
                        > 1e-6  # Adjust threshold as needed
                    ]  # Avoid duplicate start point
                else:
                    new_points = straightline_points

                all_points.extend(new_points)

                # Update current position
                current_x, current_y = end_x, end_y

            elif segment_type in ("Left", "Right"):
                if length > np.pi * corner_radius:
                    print(
                        f"Skipping full loop segment {index} {segment_type} "
                        f"{corner_radius} {length}"
                    )
                    # continue
                # Calculate the center of the arc
                direction = 1 if segment_type == "Left" else -1  # 1 for left, -1 for right
                radius = corner_radius  # Use the corner_radius directly
                center_x = current_x - direction * radius * np.sin(
                    current_angle
                )
                center_y = current_y + direction * radius * np.cos(
                    current_angle
                )

                # Construct the arc
                arc_x, arc_y = self.construct_arc(
                    (center_x, center_y),
                    (current_x, current_y),
                    length * direction,
                    num_points=int(length * steps_per_unit),
                )

                # Convert arc points to a list of tuples
                arc_points = [
                    (xp, yp) for xp, yp in zip(arc_x.tolist(), arc_y.tolist())
                ]

                # Avoid duplicate start point and ensure smooth transitions
                if all_points:
                    last_point = all_points[-1]
                    new_points = [
                        p
                        for p in arc_points
                        if math.hypot(p[0] - last_point[0], p[1] - last_point[1])
                        > 1e-6  # Adjust threshold as needed
                    ]
                else:
                    new_points = arc_points

                all_points.extend(new_points)

                # Update current position and angle
                current_x = arc_x[-1]
                current_y = arc_y[-1]
                angular_sweep = length / radius
                current_angle += direction * angular_sweep

            else:
                print(f"Unknown segment type: {segment_type}")

        graph.add_points(all_points)
        return all_points

# --- Main Script ---
def test_plot():
    graph = DynamicGraph()
    # Load track from CSV
    # track = Track.from_csv("tracks/2021_michigan.csv")
    # track = Track.from_csv("tracks/2021Michigan.csv")
    track = Track.from_csv("tracks/2021_michigan.csv")
    # Plot the track
    track.plot_track(graph, initial_angle=0)

    plt.show()


if __name__ == "__main__":
    test_plot()

