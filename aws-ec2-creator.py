#!/usr/bin/env python3

import boto3
import botocore
import os
import sys
from botocore.exceptions import ClientError

def get_aws_profiles():
    session = boto3.Session()
    return session.available_profiles

def select_aws_profile():
    profiles = get_aws_profiles()
    print("Available AWS profiles:")
    for idx, profile in enumerate(profiles, start=1):
        print(f"{idx}. {profile}")
    
    while True:
        try:
            choice = int(input("\nSelect a profile by number: "))
            if 1 <= choice <= len(profiles):
                return profiles[choice - 1]
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def get_aws_regions(session):
    ec2 = session.client('ec2')
    regions = [region['RegionName'] for region in ec2.describe_regions()['Regions']]
    return regions

def select_aws_region(session):
    regions = get_aws_regions(session)
    print("\nAvailable AWS regions:")
    for idx, region in enumerate(regions, start=1):
        print(f"{idx}. {region}")
    
    while True:
        try:
            choice = int(input("\nSelect a region by number: "))
            if 1 <= choice <= len(regions):
                return regions[choice - 1]
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def create_security_group(ec2_client, vpc_id):
    while True:
        group_name = input("Enter a name for the new security group: ")
        description = input("Enter a description for the security group (press Enter for default): ").strip()
        if not description:
            description = f"Security group for {group_name}"

        try:
            response = ec2_client.create_security_group(
                GroupName=group_name,
                Description=description,
                VpcId=vpc_id
            )
            security_group_id = response['GroupId']
            print(f"Security Group created: {security_group_id}")

            # Add inbound rules
            while True:
                ingress_ports = input("Enter the inbound (ingress) ports to open (comma-separated, press Enter for default 22): ").strip()
                if not ingress_ports:
                    ingress_ports = "22"
                
                ports = [port.strip() for port in ingress_ports.split(',')]
                ip_permissions = []
                
                for port in ports:
                    try:
                        port = int(port)
                        ip_permissions.append({
                            'IpProtocol': 'tcp',
                            'FromPort': port,
                            'ToPort': port,
                            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                        })
                    except ValueError:
                        print(f"Invalid port number: {port}. Skipping.")
                
                if ip_permissions:
                    ec2_client.authorize_security_group_ingress(
                        GroupId=security_group_id,
                        IpPermissions=ip_permissions
                    )
                    print(f"Inbound rules added for ports: {', '.join(str(p['FromPort']) for p in ip_permissions)}")
                    break
                else:
                    print("No valid ports entered. Please try again.")

            # Add outbound rule
            egress_port = input("Enter the outbound (egress) port to open (press Enter for all traffic): ").strip()
            if egress_port:
                egress_port = int(egress_port)
                ec2_client.authorize_security_group_egress(
                    GroupId=security_group_id,
                    IpPermissions=[
                        {
                            'IpProtocol': 'tcp',
                            'FromPort': egress_port,
                            'ToPort': egress_port,
                            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                        }
                    ]
                )
                print(f"Outbound rule added for port {egress_port}")
            else:
                print("Default outbound rule (all traffic) will be used")

            return security_group_id
        except ClientError as e:
            print(f"Error creating security group: {e}")
            retry = input("Do you want to try again? (y/n): ").lower().strip()
            if retry != 'y':
                sys.exit(1)
def manage_key_pair(ec2_client):
    use_existing = input("Do you want to use an existing key pair? (y/n): ").lower().strip()
    
    if use_existing == 'y':
        key_pairs = ec2_client.describe_key_pairs()['KeyPairs']
        print("\nAvailable key pairs:")
        for idx, key in enumerate(key_pairs, start=1):
            print(f"{idx}. {key['KeyName']}")
        
        while True:
            try:
                choice = int(input("\nSelect a key pair by number: "))
                if 1 <= choice <= len(key_pairs):
                    return key_pairs[choice - 1]['KeyName']
                else:
                    print("Invalid selection. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number.")
    else:
        key_name = input("Enter a name for the new key pair: ")
        try:
            response = ec2_client.create_key_pair(KeyName=key_name)
            private_key = response['KeyMaterial']
            
            # Save private key to file
            key_file = f"{key_name}.pem"
            with open(key_file, 'w') as f:
                f.write(private_key)
            os.chmod(key_file, 0o400)
            
            print(f"New key pair '{key_name}' created and saved to {key_file}")
            return key_name
        except ClientError as e:
            print(f"Error creating key pair: {e}")
            sys.exit(1)

def create_ec2_instance(ec2_resource, image_id, instance_type, key_name, security_group_id):
    try:
        instances = ec2_resource.create_instances(
            ImageId=image_id,
            InstanceType=instance_type,
            KeyName=key_name,
            MinCount=1,
            MaxCount=1,
            SecurityGroupIds=[security_group_id]
        )
        instance = instances[0]
        print(f"EC2 instance {instance.id} created.")
        print("Waiting for instance to be running...")
        instance.wait_until_running()
        instance.load()
        print(f"Instance is now running. Public IP: {instance.public_ip_address}")
        return instance
    except ClientError as e:
        print(f"Error creating EC2 instance: {e}")
        sys.exit(1)

def main():
    profile = select_aws_profile()
    session = boto3.Session(profile_name=profile)
    
    region = select_aws_region(session)
    ec2_client = session.client('ec2', region_name=region)
    ec2_resource = session.resource('ec2', region_name=region)

    # Get default VPC
    default_vpc = list(ec2_resource.vpcs.filter(Filters=[{'Name': 'isDefault', 'Values': ['true']}]))[0]
    vpc_id = default_vpc.id

    security_group_id = create_security_group(ec2_client, vpc_id)
    key_name = manage_key_pair(ec2_client)

    # Select instance type
    instance_type = input("Enter the instance type (press Enter for t2.micro): ").strip()
    if not instance_type:
        instance_type = 't2.micro'

    # Get the latest Amazon Linux 2 AMI
    images = ec2_client.describe_images(
        Owners=['amazon'],
        Filters=[
            {'Name': 'name', 'Values': ['amzn2-ami-hvm-*-x86_64-gp2']},
            {'Name': 'state', 'Values': ['available']}
        ]
    )
    image_id = sorted(images['Images'], key=lambda x: x['CreationDate'], reverse=True)[0]['ImageId']

    instance = create_ec2_instance(ec2_resource, image_id, instance_type, key_name, security_group_id)
    
    print("\nEC2 Instance Details:")
    print(f"Instance ID: {instance.id}")
    print(f"Public IP: {instance.public_ip_address}")
    print(f"Private IP: {instance.private_ip_address}")
    print(f"Instance Type: {instance.instance_type}")
    print(f"Key Name: {instance.key_name}")

if __name__ == "__main__":
    main()