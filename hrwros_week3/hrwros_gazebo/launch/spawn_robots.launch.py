from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription, TimerAction, RegisterEventHandler
from launch_ros.actions import Node, PushRosNamespace
from launch.substitutions import Command, PathJoinSubstitution, LaunchConfiguration
from launch_ros.substitutions import FindPackageShare
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.event_handlers import OnProcessExit
from my_python_utils import some_utility


def generate_robot_group(robot_name, robot_type, robot_parent, urdf_file,
                         vacuum_gripper_prefix, gripper_plugin_name,
                         x, y, z, yaw=None, joints=None):
    """Generate a group of nodes for a single robot."""
    robot_prefix = robot_name
    description_command = some_utility.generate_description_command(
        'hrwros_support',
        urdf_file,
        f'robot_type:={robot_type} ',
        f'robot_prefix:={robot_prefix} ',
        f'vacuum_gripper_prefix:={vacuum_gripper_prefix} ',
        f'gripper_plugin_name:={gripper_plugin_name} ',
        f'robot_parent:={robot_parent} '
    )

    return GroupAction(
        actions=[
            PushRosNamespace(robot_name),
            some_utility.generate_robot_state_publisher(
                robot_name, description_command, ns_robot=robot_name),
            some_utility.generate_spawner_node(
                entity_name=robot_name,
                topic=f'/{robot_name}/robot_description',
                x=x, y=y, z=z, yaw=yaw,
            ),
            # *generate_controller_spawner_node(robot_prefix, description_command)
        ])


def generate_launch_description():
    """Generate the launch description for the robots."""
    robot_config = some_utility.load_config_file(
        "hrwros_gazebo", "robot_config.yaml")
    robot1 = robot_config['robot_groups']['robot1']
    robot2 = robot_config['robot_groups']['robot2']
    return LaunchDescription([

        # Group for Robot 1
        generate_robot_group(
            robot_name=robot1['robot_name'],
            robot_type=robot1['robot_type'],
            robot_parent=robot_config['robot_parent'],
            urdf_file=robot1['urdf_file'],
            vacuum_gripper_prefix=robot1['vacuum_gripper_prefix'],
            gripper_plugin_name=robot1['gripper_plugin_name'],
            x=robot1['x'], y=robot1['y'], z=robot1['z'],
            joints=robot1['joints'],
        ),

        # Group for Robot 2
        generate_robot_group(
            robot_name=robot2['robot_name'],
            robot_type=robot2['robot_type'],
            robot_parent=robot_config['robot_parent'],
            urdf_file=robot2['urdf_file'],
            vacuum_gripper_prefix=robot2['vacuum_gripper_prefix'],
            gripper_plugin_name=robot2['gripper_plugin_name'],
            x=robot2['x'], y=robot2['y'], z=robot2['z'], yaw=robot2['yaw'],
            joints=robot2['joints'],
        ),

    ])
