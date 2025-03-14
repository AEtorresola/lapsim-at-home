
# track_testing.py
import unittest
import math
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import os
from track import Track, TrackSegment, DynamicGraph


class TestTrackSegment(unittest.TestCase):
    def test_track_segment_creation(self):
        segment = TrackSegment("Straight", 100)
        self.assertEqual(segment.segment_type, "Straight")
        self.assertEqual(segment.length, 100)
        self.assertIsNone(segment.corner_radius)

        segment = TrackSegment("Left", 50, 20)
        self.assertEqual(segment.segment_type, "Left")
        self.assertEqual(segment.length, 50)
        self.assertEqual(segment.corner_radius, 20)

    def test_track_segment_representation(self):
        segment = TrackSegment("Right", 75, 30)
        expected_representation = (
            "TrackSegment(type='Right', length=75, radius=30)"
        )
        self.assertEqual(repr(segment), expected_representation)


class TestTrack(unittest.TestCase):
    def test_track_creation(self):
        segments = [
            TrackSegment("Straight", 100),
            TrackSegment("Left", 50, 20),
            TrackSegment("Right", 75, 30),
        ]
        track = Track(segments)
        self.assertEqual(len(track.segments), 3)
        self.assertIsInstance(track.segments[0], TrackSegment)

    def test_from_csv_valid(self):
        # Assuming you have a valid CSV file named 'valid_track.csv' in the
        # same directory
        try:
            track = Track.from_csv("tracks/2021_michigan.csv")
            self.assertGreater(len(track.segments), 0)  # Check if segments are loaded
            self.assertIsInstance(track.segments[0], TrackSegment)
        except FileNotFoundError:
            self.fail("Valid track CSV file not found.")
        except Exception as e:
            self.fail(f"Error loading track from CSV: {e}")

    def test_from_csv_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            Track.from_csv("nonexistent_track.csv")

    def test_from_csv_empty_file(self):
        # Create an empty file
        with open("empty_track.csv", "w") as f:
            pass
        with self.assertRaises(ValueError):
            Track.from_csv("empty_track.csv")
        import os

        os.remove("empty_track.csv")

    def test_from_csv_missing_column(self):
        # Create a dummy CSV file with missing column
        csv_content = """Type,Section Length
Straight,100
Left,50
Right,75
"""
        with open("test_track.csv", "w") as f:
            f.write(csv_content)

        with self.assertRaises(ValueError):
            Track.from_csv("test_track.csv")

        # Clean up the dummy file
        import os

        os.remove("test_track.csv")

    def test_from_csv_invalid_segment_type(self):
        # Create a dummy CSV file with invalid segment type
        csv_content = """Type,Section Length,Corner Radius
Invalid,100,
Left,50,20
Right,75,30
"""
        with open("test_track.csv", "w") as f:
            f.write(csv_content)

        with self.assertRaises(ValueError):
            Track.from_csv("test_track.csv")

        # Clean up the dummy file
        import os

        os.remove("test_track.csv")

    def test_from_csv_invalid_length(self):
        # Create a dummy CSV file with invalid length
        csv_content = """Type,Section Length,Corner Radius
Straight,-100,
Left,50,20
Right,75,30
"""
        with open("test_track.csv", "w") as f:
            f.write(csv_content)

        with self.assertRaises(ValueError):
            Track.from_csv("test_track.csv")

        # Clean up the dummy file
        import os

        os.remove("test_track.csv")

    def test_from_csv_invalid_corner_radius(self):
        # Create a dummy CSV file with invalid corner radius
        csv_content = """Type,Section Length,Corner Radius
Straight,100,
Left,50,-20
Right,75,30
"""
        with open("test_track.csv", "w") as f:
            f.write(csv_content)

        with self.assertRaises(ValueError):
            Track.from_csv("test_track.csv")

        # Clean up the dummy file
        import os

        os.remove("test_track.csv")

    def test_construct_arc_valid(self):
        track = Track([])  # Empty track for testing
        center = (0, 0)
        start = (10, 0)
        arc_length = math.pi * 10  # Half circle with radius 10
        arc_x, arc_y = track.construct_arc(center, start, arc_length, num_points=1000)
        self.assertEqual(len(arc_x), 1000)
        self.assertEqual(len(arc_y), 1000)
        self.assertAlmostEqual(arc_x[0], 10)
        self.assertAlmostEqual(arc_y[0], 0)
        # Account for floating point errors by checking if the last point is
        # close to (-10, 0)
        self.assertTrue(np.isclose(arc_x[-1], -10, atol=1e-5))
        self.assertTrue(np.isclose(arc_y[-1], 0, atol=1e-5))

    def test_construct_arc_invalid_radius(self):
        track = Track([])  # Empty track for testing
        center = (0, 0)
        start = (0, 0)  # Same as center
        arc_length = 10
        with self.assertRaises(ValueError):
            track.construct_arc(center, start, arc_length)

    def test_interpolate_points_by_length(self):
        track = Track([])
        start = (0, 0)
        end = (10, 0)
        points = track.interpolate_points_by_length(start, end, steps_per_unit=1)
        self.assertEqual(len(points), 11)
        self.assertEqual(points[0], (0.0, 0.0))
        self.assertEqual(points[-1], (10.0, 0.0))
        self.assertAlmostEqual(points[5][0], 5.0)
        self.assertAlmostEqual(points[5][1], 0.0)


def run_tests():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestTrackSegment))
    suite.addTest(unittest.makeSuite(TestTrack))
    runner = unittest.TextTestRunner()
    runner.run(suite)


def plot_track_streamlit(track, initial_angle, steps_per_unit):
    """Plots the track using the DynamicGraph."""
    graph = DynamicGraph()
    points = track.plot_track(
        graph, initial_angle=initial_angle, steps_per_unit=steps_per_unit
    )
    st.pyplot(graph.fig)
    return points


def create_track_editor():
    """
    Creates the track editor using st.data_editor and manages the session state.
    This function is NOT cached.
    """
    st.subheader("Create New Track")
    track_name = st.text_input("Track Name", "new_track")

    # Initial data for the dataframe editor
    data = {
        "Type": ["Straight", "Left", "Right"],
        "Section Length": [100.0, 50.0, 75.0],
        "Corner Radius": [None, 20.0, 30.0],
    }
    df = pd.DataFrame(data)

    if "edited_df" not in st.session_state:
        st.session_state["edited_df"] = df

    edited_df = st.data_editor(st.session_state["edited_df"])
    st.session_state["edited_df"] = edited_df

    return track_name, edited_df


def save_track_to_csv(track_name, edited_df):
    """
    Validates the dataframe and saves the track to a CSV file.
    This function is NOT cached.
    """
    try:
        # Convert the dataframe to a list of TrackSegment objects
        segments = []
        for _, row in edited_df.iterrows():
            segment_type = row["Type"]
            length = float(row["Section Length"])
            corner_radius = (
                float(row["Corner Radius"])
                if not pd.isna(row["Corner Radius"])
                else None
            )

            if segment_type not in ("Straight", "Left", "Right"):
                st.error(f"Invalid segment type: {segment_type}")
                return False  # Indicate failure
            if length <= 0:
                st.error(f"Segment length must be positive: {length}")
                return False  # Indicate failure
            if (
                segment_type != "Straight"
                and (corner_radius is None or corner_radius <= 0)
            ):
                st.error("Corner radius must be positive for curved segments.")
                return False  # Indicate failure

            segment = TrackSegment(segment_type, length, corner_radius)
            segments.append(segment)

        # Create the Track object
        track = Track(segments)

        # Save the track to a CSV file
        file_path = os.path.join("tracks", f"{track_name}.csv")
        # Create a DataFrame from the list of segments
        data = []
        for segment in track.segments:
            data.append(
                {
                    "Type": segment.segment_type,
                    "Section Length": segment.length,
                    "Corner Radius": segment.corner_radius,
                }
            )
        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False)

        st.success(f"Track saved to {file_path}")
        return True  # Indicate success

    except Exception as e:
        st.error(f"Error saving track: {e}")
        return False  # Indicate failure



def main():
    st.sidebar.title("Track Testing")
    test_button = st.sidebar.button("Run Tests")
    if test_button:
        run_tests()

    st.sidebar.title("Track Management")

    # Initialize session state variable
    if "show_track_editor" not in st.session_state:
        st.session_state["show_track_editor"] = False

    create_track_button = st.sidebar.button("Create New Track")

    # Set session state to show the editor when the button is clicked
    if create_track_button:
        st.session_state["show_track_editor"] = True

    # Conditionally display the track editor
    if st.session_state["show_track_editor"]:
        track_name, edited_df = create_track_editor()
        if st.button("Save Track"):
            save_track_to_csv(track_name, edited_df)

    st.sidebar.title("Track Plotter")
    track_files = [f for f in os.listdir("tracks") if f.endswith(".csv")]
    if not track_files:
        st.warning("No track CSV files found in the 'tracks' directory.")
        return

    track_file = st.sidebar.selectbox("Select Track", track_files)
    initial_angle = st.sidebar.slider("Initial Angle (degrees)", 0, 360, 0)
    steps_per_unit = st.sidebar.slider("Steps Per Unit", 1, 10, 4)

    plot_button = st.sidebar.button("Plot Track")
    if plot_button:
        track_csv = os.path.join("tracks", track_file)
        try:
            track = Track.from_csv(track_csv)
            points = plot_track_streamlit(
                track, np.radians(initial_angle), steps_per_unit
            )
            st.subheader("Track Points")
            st.write(points)  # Display the list of points
        except Exception as e:
            st.error(f"Error loading or plotting track: {e}")

if __name__ == "__main__":
    # Create the 'tracks' directory if it doesn't exist
    if not os.path.exists("tracks"):
        os.makedirs("tracks")
    main()

