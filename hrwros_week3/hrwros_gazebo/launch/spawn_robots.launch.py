from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription, TimerAction
from launch_ros.actions import Node, PushRosNamespace
from launch.substitutions import Command, PathJoinSubstitution, LaunchConfiguration
from launch_ros.substitutions import FindPackageShare
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_description_command(package, urdf_file, *args):
    """Generate a command to process the robot's xacro file."""
    return Command([
        'xacro ',
        PathJoinSubstitution([FindPackageShare(package), 'urdf', urdf_file]),
        ' ',
        *args
    ])


def generate_robot_state_publisher(robot_prefix, description_command):
    """Create a robot_state_publisher node."""
    return Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        name=f'{robot_prefix}_state_publisher',
        parameters=[{'robot_description': description_command,
                     'tf_prefix': f'{robot_prefix}_'}],
        remappings=[('/robot_description', f'/{robot_prefix}_description')]
    )


def get_joint_state_publisher_node(robot_prefix):
    joint_state_publisher_params = PathJoinSubstitution([
        FindPackageShare('hrwros_support'),
        'config',
        'joint_states.yaml'
    ])

    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name=f'{robot_prefix}_joint_state_publisher',
        parameters=[joint_state_publisher_params],
        remappings=[
            ('/joint_states', f'/{robot_prefix}/joint_states'),
            ('/robot_description', f'/{robot_prefix}_description')  # Remap robot_description topic
        ]
    )
    return joint_state_publisher_node


def generate_spawner_node(name, entity_name, topic, x=None, y=None, z=None, yaw=None, joints=None):
    """Spawn the robot model in Gazebo."""
    arguments = ['-entity', entity_name, '-topic', topic]

    # Add positional arguments
    if x is not None:
        arguments.extend(['-x', str(x)])
    if y is not None:
        arguments.extend(['-y', str(y)])
    if z is not None:
        arguments.extend(['-z', str(z)])
    if yaw is not None:
        arguments.extend(['-Y', str(yaw)])

    # if joints:
    #     for joint, position in joints.items():
    #         arguments.extend(['-J', joint, str(position)])
            
    # Return the node
    return Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        output='screen',
        arguments=arguments
    )


def generate_controller_spawner_node(robot_prefix):
    """Spawn the controller for the robot."""
    # return Node(
    #     package='controller_manager',
    #     executable='spawner',
    #     name=f'{robot_prefix}_controller_spawner',
    #     arguments=[f'{robot_prefix}_joint_state_controller',
    #                f'{robot_prefix}_controller']
    # )
    arm_controller_name = f'{robot_prefix}_controller'
    joint_controller_name = f'{robot_prefix}_joint_state_controller'
    robot_yaml_file = PathJoinSubstitution([
        FindPackageShare('hrwros_gazebo'),
        'config',
        f'{arm_controller_name}.yaml'
    ])
    joint_state_yaml_file = PathJoinSubstitution([
        FindPackageShare('hrwros_gazebo'),
        'config',
        f'{joint_controller_name}.yaml'
    ])

    arm_node = Node(
        package='controller_manager',
        executable='spawner',
        name=f'{robot_prefix}_arm_controller_spawner',
        arguments=[arm_controller_name,
                   '-p', robot_yaml_file]
    )
    joint_node = Node(
        package='controller_manager',
        executable='spawner',
        name=f'{robot_prefix}_joint_controller_spawner',
        arguments=[joint_controller_name,
                   '-p', joint_state_yaml_file]
    )
    return [
        TimerAction(
            period=1.0,  # Wait 10 second to ensure Gazebo is fully started
            actions=[
                arm_node
            ]
        ),
        TimerAction(
            period=1.0,  # Wait 10 second to ensure Gazebo is fully started
            actions=[
                joint_node
            ]
        )
    ]


def generate_robot_group(robot_prefix, robot_type, urdf_file, vacuum_gripper_prefix, gripper_plugin_name, x, y, z, yaw=None, joints=None):
    """Generate a group of nodes for a single robot."""
    description_command = generate_description_command(
        'hrwros_support',
        urdf_file,
        f'robot_type:={robot_type} ',
        f'robot_prefix:={robot_prefix} ',
        f'vacuum_gripper_prefix:={vacuum_gripper_prefix} ',
        # f'robot_param:=/{robot_prefix}/{robot_prefix}_description ',
        f'gripper_plugin_name:={gripper_plugin_name}'
    )

    return GroupAction([
        # PushRosNamespace(robot_prefix),
        generate_robot_state_publisher(robot_prefix, description_command),
        get_joint_state_publisher_node(robot_prefix),
        generate_spawner_node(
            name=robot_prefix,
            entity_name=robot_prefix,
            topic=f'/{robot_prefix}_description',
            x=x, y=y, z=z, yaw=yaw,
            joints=joints
        ),
        # *generate_controller_spawner_node(robot_prefix)
    ])


def generate_launch_description():
    """Generate the launch description for the robots."""

    # Path to Gazebo launch file
    gazebo_launch_path = PathJoinSubstitution([
        FindPackageShare('gazebo_ros'),
        'launch',
        'gazebo.launch.py'
    ])
    return LaunchDescription([
        # Declare arguments
        DeclareLaunchArgument('robot1_prefix', default_value='robot1_'),
        DeclareLaunchArgument('robot2_prefix', default_value='robot2_'),
        DeclareLaunchArgument('robot1_type', default_value='ur10'),
        DeclareLaunchArgument('robot2_type', default_value='ur5'),
        DeclareLaunchArgument('vacuum_gripper1_prefix',
                              default_value='vacuum_gripper1_'),
        DeclareLaunchArgument('vacuum_gripper2_prefix',
                              default_value='vacuum_gripper2_'),
        DeclareLaunchArgument('gripper1_plugin_name',
                              default_value='gripper1'),
        DeclareLaunchArgument('gripper2_plugin_name',
                              default_value='gripper2'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(gazebo_launch_path)
        ),
        # Group for Robot 1
        generate_robot_group(
            robot_prefix='robot1',
            robot_type='ur10',
            urdf_file='robot_system/robot_system.xacro',
            vacuum_gripper_prefix='vacuum_gripper1_',
            gripper_plugin_name='gripper1',
            x=0.5, y=1.8, z=0.95,
            joints={
                'robot1_elbow_joint': 1.57,
                'robot1_shoulder_lift_joint': -1.57,
                'robot1_shoulder_pan_joint': 1.24,
                'robot1_wrist_1_joint': -1.57,
                'robot1_wrist_2_joint': -1.57,
            }
        ),

        # Group for Robot 2
        generate_robot_group(
            robot_prefix='robot2',
            robot_type='ur5',
            urdf_file='robot_system/robot_system.xacro',
            vacuum_gripper_prefix='vacuum_gripper2_',
            gripper_plugin_name='gripper2',
            x=-7.8, y=-1.5, z=0.7, yaw=1.57,
            joints={
                'robot2_elbow_joint': 1.57,
                'robot2_shoulder_lift_joint': -1.57,
                'robot2_shoulder_pan_joint': 1.24,
                'robot2_wrist_1_joint': -1.57,
                'robot2_wrist_2_joint': -1.57,
            }
        ),
    ])
