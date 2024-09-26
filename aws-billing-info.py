#!/usr/bin/env python3

import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
from tabulate import tabulate

def get_billing_info(profile):
    """Retrieve billing information for a given AWS profile."""
    try:
        session = boto3.Session(profile_name=profile)
        ce = session.client('ce')

        # Get the current date and first day of the month
        current_date = datetime.now().strftime('%Y-%m-%d')
        first_day_of_month = datetime.now().replace(day=1).strftime('%Y-%m-%d')
        end_of_month = (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        # Get cost for the current month
        cost_response = ce.get_cost_and_usage(
            TimePeriod={'Start': first_day_of_month, 'End': current_date},
            Granularity='MONTHLY',
            Metrics=['UnblendedCost']
        )
        month_to_date_cost = float(cost_response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount'])

        # Get forecast for the rest of the month
        forecast_response = ce.get_cost_forecast(
            TimePeriod={'Start': current_date, 'End': end_of_month.strftime('%Y-%m-%d')},
            Metric='UNBLENDED_COST',
            Granularity='MONTHLY'
        )
        forecast = float(forecast_response['Total']['Amount'])

        return {
            'Profile': profile,
            'Month-to-Date Cost': f"${month_to_date_cost:.2f}",
            'Forecast': f"${forecast:.2f}",
            'Estimated Amount Due': f"${forecast:.2f}"
        }

    except ClientError as e:
        return {'Profile': profile, 'Error': str(e)}

def main(profiles):
    """Retrieve and display billing information for given profiles."""
    billing_data = []
    
    for profile in profiles:
        billing_info = get_billing_info(profile)
        billing_data.append(billing_info)
    
    # Display the billing data in tabular format
    if billing_data:
        print(tabulate(billing_data, headers="keys", tablefmt="grid"))
    else:
        print("No billing information available.")

if __name__ == "__main__":
    import sys

    # Check if any profiles are provided as command-line arguments
    if len(sys.argv) < 2:
        print("Usage: ./aws_billing_info.py <profile1> [profile2] [profile3] ...")
        sys.exit(1)

    # Get the list of profiles from command-line arguments
    profiles = sys.argv[1:]
    main(profiles)

