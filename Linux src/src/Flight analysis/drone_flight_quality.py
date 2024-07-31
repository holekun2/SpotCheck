import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from utils import Utilities

class Plotter:
    def __init__(self):
        pass

    def plot_flight_data(self, x_positions, y_positions, current_flight_data, current_category, estimated_center, estimated_radius, inner_radius):
        # Extract yaw data from current_flight_data
        yaw_data = [data['Flight Yaw Degree'] for data in current_flight_data]

        # Calculate drone headings
        drone_headings = Utilities.calculate_drone_heading(x_positions, y_positions, yaw_data)

        # Calculate angle differences
        angle_differences = Utilities.calculate_angle_differences(x_positions, y_positions, drone_headings, estimated_center, inner_radius)

        # Find the index of the maximum angle difference
        max_diff_index = np.argmax(angle_differences)

        # Plot the results
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))

        # Plot on ax1
        num_points = len(x_positions)
        colors = plt.cm.viridis(np.linspace(0, 1, num_points))
        ax1.scatter(x_positions, y_positions, c=colors, label='Points')

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
        num_points = len(x_coords)
        colors = plt.cm.viridis(np.linspace(0, 1, num_points))
        ax2.scatter(x_coords, y_coords, c=colors, label='Yaw Angles')

        for i in range(len(x_coords)):
            if i < len(x_coords) - 1:
                ax2.plot([x_coords[i], x_coords[i+1]], [y_coords[i], y_coords[i+1]], c=colors[i])
            else:
                ax2.plot([x_coords[i], x_coords[0]], [y_coords[i], y_coords[0]], c=colors[i])

        sm = plt.cm.ScalarMappable(cmap=plt.cm.viridis, norm=plt.Normalize(vmin=0, vmax=num_points))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax2, label='Flight Order')

        ax2.annotate('Start', xy=(x_coords[0], y_coords[0]), xytext=(x_coords[0]+0.1, y_coords[0]+0.1),
                    arrowprops=dict(facecolor='black', arrowstyle='->'))
        
        ax2.legend()

        plt.show()

    def plot_tower_flight_3d(self, current_flight_data, current_category):
        x_positions = [data['GPS Longitude'] for data in current_flight_data]
        y_positions = [data['GPS Latitude'] for data in current_flight_data]
        z_positions = [data['Relative Altitude'] for data in current_flight_data]

        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(111, projection='3d')

        num_points = len(x_positions)
        colors = plt.cm.viridis(np.linspace(0, 1, num_points))
        ax.scatter(x_positions, y_positions, z_positions, c=colors, marker='o', label='Flight Path')

        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.set_zlabel('Relative Altitude')
        ax.set_title(f'3D Tower Flight Path - {current_category}')
        ax.legend()

        plt.tight_layout()
        plt.show()
