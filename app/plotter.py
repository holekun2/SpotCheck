import numpy as np
import matplotlib.pyplot as plt
from .utils import Utilities
from typing import List, Tuple, Dict
import pandas as pd



class Plotter:
    def __init__(self):
        pass

    def plot_flight_data(self, x_positions: List[float], y_positions: List[float], 
                        current_flight_data: List[dict], current_category: str, 
                        estimated_center: Tuple[float, float], estimated_radius: float, 
                        inner_radius: float, failed_photos: List[str] = []):
        """Plots flight data with optional highlighting of failed photos.

        Args:
            x_positions (List[float]): List of x coordinates.
            y_positions (List[float]): List of y coordinates.
            current_flight_data (List[dict]): List of flight data dictionaries.
            current_category (str): Current flight category.
            estimated_center (Tuple[float, float]): Estimated center of the flight path.
            estimated_radius (float): Estimated radius of the flight path.
            inner_radius (float): Inner radius of the flight path.
            failed_photos (List[str], optional): List of filenames for failed photos. Defaults to [].
        """
        # Extract yaw data from current_flight_data
        yaw_data = [data['Flight Yaw Degree'] for data in current_flight_data]

        # Calculate drone headings
        drone_headings = Utilities.calculate_drone_heading(x_positions, y_positions, yaw_data)

        # Plot the results
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))

        # Plot on ax1
        num_points = len(x_positions)
        colors = plt.cm.viridis(np.linspace(0, 1, num_points))
        
        # Separate points based on failed photos
        failed_x = [x_positions[i] for i, data in enumerate(current_flight_data) if data['Unique Identifier'] in failed_photos]
        failed_y = [y_positions[i] for i, data in enumerate(current_flight_data) if data['Unique Identifier'] in failed_photos]
        
        # Plot all points
        ax1.scatter(x_positions, y_positions, c=colors, label='Points')
        
        # Highlight failed points in red
        ax1.scatter(failed_x, failed_y, color='red', label='Failed Photos')

        # Plot arrows for drone headings
        for i in range(num_points):
            ax1.arrow(x_positions[i], y_positions[i], 
                    drone_headings[i][0], drone_headings[i][1], 
                    head_width=0.05, head_length=0.05, fc=colors[i], ec=colors[i])

        # Plot the estimated center
        ax1.scatter(estimated_center[0], estimated_center[1], color='red', marker='*', label='Estimated Center')

        # Create a circle patch using the estimated center and radius
        outer_circle = plt.Circle(estimated_center, estimated_radius, color='r', fill=False)
        ax1.add_patch(outer_circle)

        # Create a circle patch using the estimated center and inner radius
        inner_circle = plt.Circle(estimated_center, inner_radius, color='g', fill=False)
        ax1.add_patch(inner_circle)

        ax1.set_xlabel('X Position')
        ax1.set_ylabel('Y Position')
        ax1.set_title(f'Flight {current_category} - Maximum Angle Difference Point')
        ax1.legend()
        ax1.grid(True)

        # Plot on ax2 (unit circle)
        ax2.set_aspect('equal')
        ax2.set_xlim([-1.1, 1.1])
        ax2.set_ylim([-1.1, 1.1])
        ax2.set_xlabel('X')
        ax2.set_ylabel('Y')
        ax2.set_title('Yaw Angle Spacing on Unit Circle')
        ax2.grid(True)

        # Convert yaw data to radians
        yaw_radians = [np.radians(yaw) for yaw in yaw_data]

        # Calculate the x and y coordinates on the unit circle
        x_coords = [np.cos(yaw) for yaw in yaw_radians]
        y_coords = [np.sin(yaw) for yaw in yaw_radians]

        # Plot the points on the unit circle
        ax2.scatter(x_coords, y_coords, c=colors)

        for i in range(len(x_coords)):
            if i < len(x_coords) - 1:
                ax2.plot([x_coords[i], x_coords[i+1]], [y_coords[i], y_coords[i+1]], c=colors[i])
            else:
                ax2.plot([x_coords[i], x_coords[0]], [y_coords[i], y_coords[0]], c=colors[i])

        sm = plt.cm.ScalarMappable(cmap=plt.cm.viridis, norm=plt.Normalize(vmin=0, vmax=num_points))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax2, label='Flight Order')

        ax2.legend()

        plt.show()


  



    def normalize_angle(self, angle):
        """Convert angle to 0-360 range"""
        return (angle + 360) % 360

    def plot_3d_flights(self, passfail_list: List[Dict], flight_data_df: pd.DataFrame, categories: List[List[str]]):
        fig = plt.figure(figsize=(15, 10))
        ax = fig.add_subplot(111, projection='3d')

        colors = plt.cm.rainbow(np.linspace(0, 1, len(categories)))
        
        # Initialize min and max values for normalization
        min_lon, max_lon = float('inf'), float('-inf')
        min_lat, max_lat = float('inf'), float('-inf')
        min_alt, max_alt = float('inf'), float('-inf')

        # First pass to find min and max values
        for category_group in categories:
            for category in category_group:
                category_data = [flight for flight in passfail_list if flight['Flight Category'] == category]
                for flight in category_data:
                    flight_photos = flight['Photos']
                    flight_df = flight_data_df[flight_data_df['Unique Identifier'].isin(flight_photos)]
                    
                    min_lon = min(min_lon, flight_df['GPS Longitude'].min())
                    max_lon = max(max_lon, flight_df['GPS Longitude'].max())
                    min_lat = min(min_lat, flight_df['GPS Latitude'].min())
                    max_lat = max(max_lat, flight_df['GPS Latitude'].max())
                    min_alt = min(min_alt, flight_df['Relative Altitude'].min())
                    max_alt = max(max_alt, flight_df['Relative Altitude'].max())

        # Function to normalize coordinates
        def normalize(value, min_val, max_val):
            return (value - min_val) / (max_val - min_val)

        # Convert meters to feet
        def meters_to_feet(meters):
            return meters * 3.28084

        for category_group, color in zip(categories, colors):
            for category in category_group:
                category_data = [flight for flight in passfail_list if flight['Flight Category'] == category]
                
                if not category_data:
                    continue

                for flight in category_data:
                    flight_photos = flight['Photos']
                    flight_df = flight_data_df[flight_data_df['Unique Identifier'].isin(flight_photos)]
                    
                    x_positions = [normalize(x, min_lon, max_lon) for x in flight_df['GPS Longitude'].tolist()]
                    y_positions = [normalize(y, min_lat, max_lat) for y in flight_df['GPS Latitude'].tolist()]
                    z_positions = [meters_to_feet(z) for z in flight_df['Relative Altitude'].tolist()]
                    yaw_angles = [self.normalize_angle(angle) for angle in flight_df['Flight Yaw Degree'].tolist()]
                    gimbal_angles = flight_df['Gimbal Pitch Degree'].tolist()

                    num_points = len(x_positions)
                    point_colors = plt.cm.viridis(np.linspace(0, 1, num_points))

                    # Plot the flight path
                    scatter = ax.scatter(x_positions, y_positions, z_positions, c=point_colors, marker='o', label=category)

                    # Add arrows for drone orientation
                    for i in range(num_points):
                        yaw_rad = np.radians(yaw_angles[i])
                        gimbal_rad = np.radians(gimbal_angles[i])
                        
                        # Calculate arrow direction
                        dx = np.sin(yaw_rad)
                        dy = np.cos(yaw_rad)
                        dz = np.tan(gimbal_rad)

                        # Normalize the vector
                        magnitude = np.sqrt(dx**2 + dy**2 + dz**2)
                        dx /= magnitude
                        dy /= magnitude
                        dz /= magnitude
                        
                        # Scale arrow length (adjust as needed)
                        arrow_length = 0.05  # Adjusted for normalized scale
                        
                        ax.quiver(x_positions[i], y_positions[i], z_positions[i],
                                dx * arrow_length, dy * arrow_length, dz * arrow_length,
                                color=point_colors[i], arrow_length_ratio=0.1)

        ax.set_xlabel('Normalized Longitude')
        ax.set_ylabel('Normalized Latitude')
        ax.set_zlabel('Altitude (feet)')
        ax.set_title('3D Flight Paths with Drone Orientation')
        ax.legend()

        plt.tight_layout()
        plt.show()

