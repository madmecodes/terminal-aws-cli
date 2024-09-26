#!/usr/bin/env python3

import boto3
from botocore.exceptions import ClientError
import argparse
from datetime import datetime, timedelta
from tabulate import tabulate
import calendar

def get_cost_and_usage(ce_client, start_date, end_date, granularity='MONTHLY'):
    """Retrieve cost and usage data for the specified date range."""
    try:
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date,
                'End': end_date
            },
            Granularity=granularity,
            Metrics=['UnblendedCost'],
            GroupBy=[
                {'Type': 'DIMENSION', 'Key': 'SERVICE'}
            ]
        )
        return response['ResultsByTime']
    except ClientError as e:
        print(f"Error retrieving cost data: {str(e)}")
        return None

def get_cost_forecast(ce_client, start_date, end_date):
    """Retrieve cost forecast for the specified date range."""
    try:
        response = ce_client.get_cost_forecast(
            TimePeriod={
                'Start': start_date,
                'End': end_date
            },
            Metric='UNBLENDED_COST',
            Granularity='MONTHLY'
        )
        return response['Total']['Amount']
    except ClientError as e:
        print(f"Error retrieving cost forecast: {str(e)}")
        return None

def format_cost(cost):
    """Format cost as a string with two decimal places."""
    return f"${float(cost):.2f}"
def analyze_costs(profile, days):
    """Analyze and display comprehensive cost data for the specified profile."""
    session = boto3.Session(profile_name=profile)
    ce_client = session.client('ce')

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    print(f"Analyzing costs for profile '{profile}' from {start_date} to {end_date}")

    # Current period analysis
    results = get_cost_and_usage(ce_client, start_date.isoformat(), end_date.isoformat())
    if not results:
        return

    total_cost = 0
    services = {}

    for result in results:
        for group in result['Groups']:
            service = group['Keys'][0]
            cost = float(group['Metrics']['UnblendedCost']['Amount'])
            total_cost += cost
            services[service] = services.get(service, 0) + cost

    # Sort services by cost (descending)
    sorted_services = sorted(services.items(), key=lambda x: x[1], reverse=True)

    # Prepare data for tabulate
    table_data = [
        [service, format_cost(cost), f"{(cost/total_cost)*100:.2f}%"]
        for service, cost in sorted_services
    ]
    table_data.append(["TOTAL", format_cost(total_cost), "100.00%"])

    # Print table
    print("\nCurrent Period Cost Breakdown:")
    print(tabulate(table_data, headers=["Service", "Cost", "% of Total"], tablefmt="grid"))

    # Additional insights
    print("\nComprehensive Cost Insights:")
    print(f"1. Total cost for the past {days} days: {format_cost(total_cost)}")
    print(f"2. Number of services used: {len(services)}")
    print(f"3. Most expensive service: {sorted_services[0][0]} ({format_cost(sorted_services[0][1])})")
    print(f"4. Least expensive service: {sorted_services[-1][0]} ({format_cost(sorted_services[-1][1])})")

    # Calculate daily average cost
    daily_avg = total_cost / days
    print(f"5. Daily average cost: {format_cost(daily_avg)}")

    # Previous month's cost
    first_day_prev_month = (end_date.replace(day=1) - timedelta(days=1)).replace(day=1)
    last_day_prev_month = end_date.replace(day=1) - timedelta(days=1)
    prev_month_results = get_cost_and_usage(ce_client, first_day_prev_month.isoformat(), last_day_prev_month.isoformat())
    if prev_month_results:
        prev_month_cost = sum(float(result['Groups'][0]['Metrics']['UnblendedCost']['Amount']) if result['Groups'] else 0 for result in prev_month_results)
        print(f"6. Previous month's total cost: {format_cost(prev_month_cost)}")

    # Current month-to-date cost
    first_day_current_month = end_date.replace(day=1)
    current_month_results = get_cost_and_usage(ce_client, first_day_current_month.isoformat(), end_date.isoformat())
    if current_month_results:
        current_month_cost = sum(float(result['Groups'][0]['Metrics']['UnblendedCost']['Amount']) if result['Groups'] else 0 for result in current_month_results)
        print(f"7. Current month-to-date cost: {format_cost(current_month_cost)}")

    # Forecast for the rest of the month
    last_day_current_month = end_date.replace(day=calendar.monthrange(end_date.year, end_date.month)[1])
    forecast = get_cost_forecast(ce_client, (end_date + timedelta(days=1)).isoformat(), last_day_current_month.isoformat())
    if forecast:
        total_forecast = current_month_cost + float(forecast)
        print(f"8. Forecasted cost for this month: {format_cost(total_forecast)}")

    # Year-to-date cost
    first_day_of_year = end_date.replace(month=1, day=1)
    ytd_results = get_cost_and_usage(ce_client, first_day_of_year.isoformat(), end_date.isoformat())
    if ytd_results:
        ytd_cost = sum(float(result['Groups'][0]['Metrics']['UnblendedCost']['Amount']) if result['Groups'] else 0 for result in ytd_results)
        print(f"9. Year-to-date cost: {format_cost(ytd_cost)}")

    # Cost trend (comparing with previous period)
    if days >= 60:
        prev_period_start = start_date - timedelta(days=days)
        prev_period_results = get_cost_and_usage(ce_client, prev_period_start.isoformat(), start_date.isoformat())
        if prev_period_results:
            prev_period_cost = sum(float(result['Groups'][0]['Metrics']['UnblendedCost']['Amount']) if result['Groups'] else 0 for result in prev_period_results)
            cost_change = ((total_cost - prev_period_cost) / prev_period_cost) * 100 if prev_period_cost > 0 else 0
            print(f"10. Cost trend: {'Increase' if cost_change > 0 else 'Decrease'} of {abs(cost_change):.2f}% compared to previous {days} days")

def main():
    parser = argparse.ArgumentParser(description="Analyze AWS service costs for a profile.")
    parser.add_argument("profile", help="AWS profile name")
    parser.add_argument("--days", type=int, default=30, help="Number of past days to analyze (default: 30)")
    args = parser.parse_args()

    analyze_costs(args.profile, args.days)

if __name__ == "__main__":
    main()