
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
            
            # Compute ranges; if all x or all y values are the same, set a base range.
            x_range = x_max - x_min if x_max != x_min else 1.0
            y_range = y_max - y_min if y_max != y_min else 1.0
            
            # To maintain 1:1 aspect, determine overall range.
            overall_range = max(x_range, y_range)
            # Calculate the center.
            mid_x = (x_min + x_max) / 2
            mid_y = (y_min + y_max) / 2
            
            # Add a margin (10% of the overall range) so points don't touch the edge.
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

class Track:
    def __init__(self, segments):
        self.segments = segments  # List of TrackSegment objects

    @classmethod
    def from_csv(cls, file_path):
        """Load track segments from a CSV and create a Track object."""
        segments = []
        df = pd.read_csv(file_path)
        for _, row in df.iterrows():
            current_segment = {}
            current_segment['segment_type'] = row['Type']
            current_segment['length'] = row['Section Length']
            current_segment['curvature'] = row['Corner Radius']
            segments.append(current_segment)
        return cls(segments)

    def construct_arc(self, center, start, arc_length, direction=1,num_points=10):
        """
        Construct an arc of a circle given:
        
        - center: A tuple (cx, cy) representing the center of the circle.
        - start: A tuple (sx, sy) representing the starting point of the arc.
                This point must lie on the circle.
        - arc_length: The length along the circumference of the arc.
                    (Can be positive for counterclockwise or negative for clockwise.)
        - num_points: The number of points to generate along the arc (default is 100).
        
        Returns:
        A tuple (arc_x, arc_y) where each is a NumPy array containing the x and y
        coordinates of the points along the arc.
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
        angles = np.linspace(start_angle, start_angle + direction*angular_sweep, num_points)
        
        # Compute the (x, y) coordinates of the arc.
        arc_x = cx + radius * np.cos(angles)
        arc_y = cy + radius * np.sin(angles)
        
        
        return arc_x, arc_y, angular_sweep


    def interpolate_points_by_length(self, start, end, steps_per_unit=4):
        """
        Returns a list of points [(x1, y1), ..., (x2, y2)] along the line
        between (x1, y1) and (x2, y2), with a density of steps_per_unit
        points per unit length.
        
        For example:
        - If the distance between the points is 1 and steps_per_unit is 4,
            the resulting list will have 5 points (4 segments).
        - If the distance is 3 and steps_per_unit is 4, the list will have
            13 points (12 segments).
        
        Parameters:
            x1, y1 : float
                Coordinates of the start point.
            x2, y2 : float
                Coordinates of the end point.
            steps_per_unit : int or float
                Number of steps per unit length.
        
        Returns:
            List of tuples representing the interpolated points.
        """
        x1,y1 = start
        x2,y2 = end
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
        
        #Position in meters, x, y
        current_x = 0 
        current_y = 0
        #angle in radians
        current_angle= initial_angle
        
        all_points = [(0,0),(0,0)]
        for index, segment in enumerate(self.segments):
            
            # First define the simple way straight segments work
            if segment['segment_type'] == 'Straight':
                
                # This just calculates how much it should move
                delta_x = np.cos(current_angle)*segment['length']
                delta_y = np.sin(current_angle)*segment['length']
                print(f"Segment {index} moved x={delta_x}, y={delta_y}")
                # This actually applies that movement to the current x
                
                start = (current_x,current_y)
                end = (current_x+delta_x, current_y+delta_y)
                
                straightline_points = self.interpolate_points_by_length(start, end, steps_per_unit=steps_per_unit)

                all_points.extend(straightline_points)

                current_x, current_y = end

            elif segment['segment_type'] == 'Left':
                
                # First calculate the curve radius center point
                # For a left turn, this implies that the next point is exactly 
                    # +90 degrees from the current position at a distance of one radius.
                    # Mathematically, this means: 
                center_radius_angle = current_angle + (np.pi)/2

                radius_x = current_x+np.cos(center_radius_angle)*segment['length']
                radius_y =current_y+ np.sin(center_radius_angle)*segment['length']

                
                # arc_points = [(x,y) for x,y in self.construct_arc((radius_x,radius_y), (current_x,current_y), segment['length'], num_points=10)]
                x_arc,y_arc, delta_angle = self.construct_arc((radius_x,radius_y), (current_x,current_y), segment['length'], num_points=round(segment['length']*steps_per_unit))
                
                all_arc = [(xp,yp) for xp,yp in zip(x_arc.tolist(),y_arc.tolist())]
                
                # import pdb; pdb.set_trace()
                current_angle += delta_angle

                all_points.extend(all_arc)

                current_x, current_y = all_arc[-1]

            elif segment['segment_type'] == 'Right':
                
                # First calculate the curve radius center point
                # For a left turn, this implies that the next point is exactly 
                    # +90 degrees from the current position at a distance of one radius.
                    # Mathematically, this means: 
                center_radius_angle = current_angle - (np.pi)/2

                radius_x = current_x +np.cos(center_radius_angle)*segment['length']
                radius_y =current_y +np.sin(center_radius_angle)*segment['length']
                
                print(f"Current Point is : ({(current_x,current_y)}). Center Radius : {(radius_x,radius_y)}")
                
                # arc_points = [(x,y) for x,y in self.construct_arc((radius_x,radius_y), (current_x,current_y), segment['length'], num_points=10)]
                x_arc,y_arc, delta_angle = self.construct_arc((radius_x,radius_y), (current_x,current_y), segment['length'], direction=-1, num_points=round(segment['length'])*steps_per_unit)
                

                all_arc = [(xp,yp) for xp,yp in zip(x_arc.tolist(),y_arc.tolist())]
                
                # import pdb; pdb.set_trace()
                current_angle -= delta_angle

                all_points.extend(all_arc)

                current_x, current_y = all_arc[-1]

 
            

        graph.add_points(all_points)



graph = DynamicGraph()
plt.show()
plt.ioff()
# graph.add_points([(x, np.sin(x)) for x in np.linspace(0, 4*np.pi, 50)])


# track = Track.from_csv("tracks/testing.csv")
track = Track.from_csv("tracks/2021_michigan.csv")

track.plot_track(graph, initial_angle=260)

import pdb;pdb.set_trace()



