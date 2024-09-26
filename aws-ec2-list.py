#!/usr/bin/env python3

import boto3
from botocore.exceptions import ClientError
from tabulate import tabulate

# Function to list AWS profiles
def get_all_profiles():
    session = boto3.Session()
    return session.available_profiles

# Function to get EC2 instances for a given profile
def list_ec2_instances(profile):
    try:
        session = boto3.Session(profile_name=profile)
        ec2 = session.client('ec2')
        
        # Describe instances
        response = ec2.describe_instances()
        
        # Extract useful information
        instances = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                state = instance['State']['Name']
                instance_type = instance['InstanceType']
                public_ip = instance.get('PublicIpAddress', 'None')
                private_ip = instance.get('PrivateIpAddress', 'None')
                name = 'None'
                
                # Get instance name from tags if exists
                if 'Tags' in instance:
                    for tag in instance['Tags']:
                        if tag['Key'] == 'Name':
                            name = tag['Value']
                
                instances.append({
                    'Instance ID': instance_id,
                    'Name': name,
                    'State': state,
                    'Type': instance_type,
                    'Private IP': private_ip,
                    'Public IP': public_ip,
                    'Launch Time': instance['LaunchTime']
                })
        
        return instances
    except ClientError as e:
        print(f"Error fetching instances for profile {profile}: {e}")
        return []

# Function to stop an EC2 instance
def stop_instance(profile, instance_id):
    try:
        session = boto3.Session(profile_name=profile)
        ec2 = session.client('ec2')
        ec2.stop_instances(InstanceIds=[instance_id])
        print(f"Stopping instance {instance_id}...")
    except ClientError as e:
        print(f"Error stopping instance {instance_id}: {e}")

# Function to start an EC2 instance
def start_instance(profile, instance_id):
    try:
        session = boto3.Session(profile_name=profile)
        ec2 = session.client('ec2')
        ec2.start_instances(InstanceIds=[instance_id])
        print(f"Starting instance {instance_id}...")
    except ClientError as e:
        print(f"Error starting instance {instance_id}: {e}")

# Function to reboot an EC2 instance
def reboot_instance(profile, instance_id):
    try:
        session = boto3.Session(profile_name=profile)
        ec2 = session.client('ec2')
        ec2.reboot_instances(InstanceIds=[instance_id])
        print(f"Rebooting instance {instance_id}...")
    except ClientError as e:
        print(f"Error rebooting instance {instance_id}: {e}")

# Function to terminate an EC2 instance
def terminate_instance(profile, instance_id):
    try:
        session = boto3.Session(profile_name=profile)
        ec2 = session.client('ec2')
        ec2.terminate_instances(InstanceIds=[instance_id])
        print(f"Terminating instance {instance_id}...")
    except ClientError as e:
        print(f"Error terminating instance {instance_id}: {e}")

# Main function to display instances and manage them
def manage_instances(profile):
    instances = list_ec2_instances(profile)
    
    if not instances:
        print(f"No instances found for profile {profile}.")
        return

    # Display instances in a table
    print(f"\nInstances for profile: {profile}")
    print(tabulate(instances, headers="keys", tablefmt="grid"))

    # Ask user for input to manage instances
    while True:
        action = input("\nEnter action (start/stop/reboot/terminate) or 'q' to quit: ").strip().lower()

        if action == 'q':
            print("Exiting...")
            break

        if action in ['start', 'stop', 'reboot', 'terminate']:
            instance_id = input("Enter Instance ID to manage: ").strip()
            
            if action == 'start':
                start_instance(profile, instance_id)
            elif action == 'stop':
                stop_instance(profile, instance_id)
            elif action == 'reboot':
                reboot_instance(profile, instance_id)
            elif action == 'terminate':
                confirm = input(f"Are you sure you want to terminate {instance_id}? This cannot be undone (y/n): ").strip().lower()
                if confirm == 'y':
                    terminate_instance(profile, instance_id)
                else:
                    print("Termination aborted.")
        else:
            print("Invalid action. Please enter start, stop, reboot, terminate, or 'q' to quit.")

# Function to handle 'all' profiles option
def manage_all_profiles():
    profiles = get_all_profiles()
    for profile in profiles:
        print(f"\nManaging instances for profile: {profile}")
        manage_instances(profile)

if __name__ == "__main__":
    profiles = get_all_profiles()
    
    print("Available AWS profiles:")
    for idx, profile in enumerate(profiles, start=1):
        print(f"{idx}. {profile}")
    
    choice = input("\nSelect a profile by number (or enter 'all' to manage all profiles): ").strip().lower()

    if choice == 'all':
        manage_all_profiles()
    else:
        try:
            profile_idx = int(choice) - 1
            profile = profiles[profile_idx]
            manage_instances(profile)
        except (ValueError, IndexError):
            print("Invalid selection. Exiting...")
