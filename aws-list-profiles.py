#!/usr/bin/env python3

import configparser
import os
import boto3
from botocore.exceptions import ClientError
from tabulate import tabulate

def get_account_id(profile):
    """Retrieve AWS Account ID for a given profile."""
    try:
        session = boto3.Session(profile_name=profile)
        sts = session.client('sts')
        return sts.get_caller_identity()["Account"]
    except ClientError as e:
        return f"Error: {str(e)}"

def get_aws_profiles():
    """Retrieve all AWS profiles from the config and credentials files."""
    config = configparser.ConfigParser()
    credentials = configparser.ConfigParser()
    
    # Read AWS config and credentials files
    config.read(os.path.expanduser("~/.aws/config"))
    credentials.read(os.path.expanduser("~/.aws/credentials"))
    
    profiles = []
    
    # Process profiles from config file
    for section in config.sections():
        if section.startswith("profile "):
            profile_name = section[8:]  # Remove "profile " prefix
            region = config[section].get("region", "Not set")
            account_id = get_account_id(profile_name)
            profiles.append({
                "Profile": profile_name,
                "Region": region,
                "Account ID": account_id
            })
    
    # Add or update profiles from credentials file
    for profile in credentials.sections():
        existing = next((p for p in profiles if p["Profile"] == profile), None)
        if not existing:
            region = "Not set"
            if profile in config:
                region = config[profile].get("region", "Not set")
            account_id = get_account_id(profile)
            profiles.append({
                "Profile": profile,
                "Region": region,
                "Account ID": account_id
            })
    
    return profiles

# def get_aws_profiles():
#     """Retrieve all AWS profiles from the config and credentials files."""
#     config = configparser.ConfigParser()
#     credentials = configparser.ConfigParser()
    
#     # Read AWS config and credentials files
#     config.read(os.path.expanduser("~/.aws/config"))
#     credentials.read(os.path.expanduser("~/.aws/credentials"))
    
#     profiles = []
    
#     # Process profiles from config file
#     for section in config.sections():
#         if section.startswith("profile "):
#             profile_name = section[8:]  # Remove "profile " prefix
#             region = config[section].get("region", "Not set")
#             account_id = get_account_id(profile_name)
#             profiles.append({
#                 "Profile": profile_name,
#                 "Region": region,
#                 "Account ID": account_id
#             })
    
#     # Add or update profiles from credentials file
#     for profile in credentials.sections():
#         existing = next((p for p in profiles if p["Profile"] == profile), None)
#         if existing:
#             existing["Access Key"] = credentials[profile].get("aws_access_key_id", "Not set")
#         else:
#             region = "Not set"
#             if profile in config:
#                 region = config[profile].get("region", "Not set")
#             account_id = get_account_id(profile)
#             access_key = credentials[profile].get("aws_access_key_id", "Not set")
            
#             # Mask all but the last 4 characters of the access key
#             if access_key != "Not set" and len(access_key) >= 4:
#                 masked_access_key = "*" * (len(access_key) - 4) + access_key[-4:]
#             else:
#                 masked_access_key = 'access_key'  # Handle case where access key is not set or too short

#             profiles.append({
#                 "Profile": profile,
#                 "Region": region,
#                 "Account ID": account_id,
#                 # "Access Key": masked_access_key[-4:]
#             })
    
#     return profiles

def main():
    profiles = get_aws_profiles()
    if profiles:
        print(tabulate(profiles, headers="keys", tablefmt="grid"))
    else:
        print("No AWS profiles found.")

if __name__ == "__main__":
    main()
