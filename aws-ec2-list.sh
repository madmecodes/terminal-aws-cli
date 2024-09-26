#!/bin/bash

# Function to list EC2 instances for a given profile
list_ec2_instances() {
    local profile=$1
    echo "Listing EC2 instances for profile: $profile"
    
    # Get the region from AWS configuration
    region=$(aws configure get region --profile "$profile")
    
    if [ -z "$region" ]; then
        echo "No region specified for profile $profile. Please configure a region."
        return
    fi
    
    # Use --no-cli-pager to disable paging
    aws ec2 describe-instances \
        --query 'Reservations[*].Instances[*].{
            InstanceID:InstanceId,
            Name:Tags[?Key==`Name`].Value | [0],
            Type:InstanceType,
            State:State.Name,
            PublicIP:PublicIpAddress,
            PrivateIP:PrivateIpAddress,
            LaunchTime:LaunchTime
        }' \
        --output table \
        --profile "$profile" \
        --region "$region" \
        --no-cli-pager
    echo ""
}

# Main script
if [ $# -eq 0 ]; then
    echo "Usage: $0 <profile1> [profile2] [profile3] ..."
    exit 1
fi

# Disable AWS CLI pager globally for this script
export AWS_PAGER=""

# Use a loop to collect all outputs
output=""
for profile in "$@"; do
    output+="$(list_ec2_instances "$profile")"
    output+="\n\n"
done

# Print all collected outputs at once
echo -e "$output"
