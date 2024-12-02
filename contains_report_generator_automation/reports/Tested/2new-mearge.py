import pandas as pd
import os
from datetime import datetime
import xlsxwriter
import matplotlib.pyplot as plt

def read_input_file(report_file):
    """Read the input file (CSV or Excel)."""
    if report_file.endswith('.csv'):
        df = pd.read_csv(report_file)
    elif report_file.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(report_file)
    else:
        raise ValueError("Unsupported file format. Please provide a CSV or Excel file.")
    return df

def clean_data(df):
    """Clean the data by handling missing values and converting status."""
    df['priority'] = df['priority'].fillna('Medium')  # Fill missing priority with 'Medium'
    df['status'] = df['status'].fillna('Unknown')  # Fill missing status with 'Unknown'
    df['is_open_issue'] = df['status'].apply(lambda x: 1 if x == 'alarm' else 0)
    return df

def categorize_services(df):
    """Categorize services based on predefined categories."""
    categories = {
        "Security and Identity": ["IAM", "API Gateway", "Backup", "CloudFront", "GuardDuty", "SecurityHub", "Shield", "WAF"],
        "Compute": ["EC2", "Lambda", "Auto Scaling", "EKS", "ECS"],
        "Storage": ["S3", "EBS", "Backup", "Glacier"],
        "Network": ["VPC", "Route 53", "CloudFront", "Elastic Load Balancer", "API Gateway", "Direct Connect"],
        "Database": ["RDS", "DynamoDB", "Redshift", "ElastiCache", "DocumentDB"],
        "Other": ["CloudTrail", "CloudWatch", "Config", "IAM"]
    }
    
    categorized_data = {}
    for category, services in categories.items():
        categorized_data[category] = df[df['title'].isin(services)]
    
    return categorized_data

def analyze_data(df):
    """Perform analysis: Split data into open and no open issues, create summary tables."""
    open_issues = df[df['is_open_issue'] == 1]
    no_open_issues = df[df['is_open_issue'] == 0]

    summary_data = open_issues.groupby(['title', 'priority']).size().reset_index(name='open_issue_count')
    
    # Pivot Table Analysis: Number of open issues per service
    pivot_table = open_issues.pivot_table(index='title', columns='priority', aggfunc='size', fill_value=0)
    
    return open_issues, no_open_issues, summary_data, pivot_table

def create_charts(summary_data, filename):
    """Generate charts based on analysis data."""
    ax = summary_data.plot(kind='bar', x='title', y='open_issue_count', color='blue', title='Open Issues by Service and Priority')
    ax.set_xlabel("Service Title")
    ax.set_ylabel("Open Issue Count")
    plt.tight_layout()
    plt.savefig(f'{filename}_analysis_chart.png')
    plt.close()

def save_to_excel(categorized_data, open_issues, no_open_issues, summary_data, pivot_table, filename):
    """Save data to an Excel file with multiple sheets."""
    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
        # Write categorized data to separate sheets
        for category, data in categorized_data.items():
            data.to_excel(writer, sheet_name=category, index=False)

        # Write open and no open issues
        open_issues.to_excel(writer, sheet_name='open_issues', index=False)
        no_open_issues.to_excel(writer, sheet_name='no_open_issues', index=False)

        # Write summary data
        summary_data.to_excel(writer, sheet_name='summary_data', index=False)
        
        # Write pivot table
        pivot_table.to_excel(writer, sheet_name='pivot_table')

        # Add chart to the Excel file
        workbook = writer.book
        worksheet = workbook.add_worksheet('Analysis Chart')
        worksheet.insert_image('B2', f'{filename}_analysis_chart.png')

def main():
    # Ask the user to input the report file name
    report_file = input("Enter the report file name (e.g., aws_compliance_benchmark_all_controls_benchmark_vested_with_priorities.csv): ").strip()
    
    # Get the input file's base name (without path) and extension
    base_name = os.path.splitext(os.path.basename(report_file))[0]
    
    # Create a unique file name using a timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_file_name = f"{base_name}_simplified_report_with_pivot_{timestamp}.xlsx"
    
    # Set the output path to the reports directory
    reports_directory = os.path.dirname(os.path.abspath(__file__))  # Get the current script's directory
    final_report_file = os.path.join(reports_directory, unique_file_name)
    
    try:
        # Read and clean the input file
        df = read_input_file(report_file)
        df = clean_data(df)

        # Categorize the data into service categories
        categorized_data = categorize_services(df)

        # Perform analysis and get pivot table
        open_issues, no_open_issues, summary_data, pivot_table = analyze_data(df)

        # Generate and save charts
        create_charts(summary_data, base_name)

        # Save the final output to an Excel file
        save_to_excel(categorized_data, open_issues, no_open_issues, summary_data, pivot_table, final_report_file)

        print(f"Processing complete. Output saved to {final_report_file}")
    
    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
