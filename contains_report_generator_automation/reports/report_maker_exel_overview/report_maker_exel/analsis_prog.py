import pandas as pd
import os
from datetime import datetime

# Define service categories as before
categories = {
    'Security and Identity': ['IAM', 'ACM', 'KMS', 'GuardDuty', 'Secret Manager', 'Secret Hub', 'SSM'],
    'Compute': ['Auto Scaling', 'EC2', 'ECS', 'EKS', 'Lambda', 'EMR', 'Step Functions'],
    'Storage': ['EBS', 'ECR', 'S3', 'DLM', 'Backup'],
    'Network': ['API Gateway', 'CloudFront', 'Route 53', 'VPC', 'ELB', 'ElasticCache', 'CloudTrail'],
    'Database': ['RDS', 'DynamoDB', 'Athena', 'Glue'],
    'Other': ['CloudFormation', 'CodeDeploy', 'Config', 'SNS', 'SQS', 'WorkSpaces', 'EventBridge', 'Config']
}

def create_simplified_report_with_pivot(report_file, final_report_file):
    # Read input report file (CSV or Excel)
    if report_file.endswith('.csv'):
        df = pd.read_csv(report_file)
    elif report_file.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(report_file)
    else:
        raise ValueError("Unsupported file format. Please provide a CSV or Excel file.")
    
    # Filter out rows based on 'status' column (alarm goes to 'unsafe' sheet, others go to 'safe' sheet)
    unsafe_df = df[df['status'] == 'alarm']
    safe_df = df[df['status'] != 'alarm']

    # Create the Pivot Table
    pivot_table = pd.pivot_table(
        df, 
        values='status', 
        index=['title', 'control_title', 'control_description', 'region', 'account_id', 'resource', 'reason', 'description'], 
        columns=['priority'], 
        aggfunc='count', 
        fill_value=0
    )

    # Create a new Excel writer object to write multiple sheets
    with pd.ExcelWriter(final_report_file, engine='xlsxwriter') as writer:
        # Write the 'safe' and 'unsafe' DataFrames to separate sheets
        safe_df.to_excel(writer, sheet_name='safe', index=False)
        unsafe_df.to_excel(writer, sheet_name='unsafe', index=False)

        # Write the 'analysis' sheet with the Pivot Table
        pivot_table.to_excel(writer, sheet_name='analysis')

        # Create a summary table for open issues and prioritize them
        summary_data = []

        for service in categories.keys():
            service_df = df[df['title'].isin(categories[service])]
            for _, row in service_df.iterrows():
                open_issues = unsafe_df[unsafe_df['title'] == row['title']].shape[0]
                safe_issues = safe_df[safe_df['title'] == row['title']].shape[0]
                priority = row['priority']

                summary_data.append({
                    'Sr No': len(summary_data) + 1,
                    'Service': row['title'],
                    'Control Title': row['control_title'],
                    'Description': row['control_description'],
                    'Open Issues': open_issues,
                    'Priority': priority
                })

        summary_df = pd.DataFrame(summary_data)

        # Write the summary table to the 'table' sheet
        summary_df.to_excel(writer, sheet_name='table', index=False)
    
    print(f"Final report with pivot table saved as {final_report_file}")


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

    # Ask if the user wants to create the simplified report
    create_report = input("Do you want to create the simplified report with pivot table? (yes/no): ").strip().lower()
    if create_report == 'yes':
        try:
            create_simplified_report_with_pivot(report_file, final_report_file)
        except ValueError as e:
            print(e)
        except Exception as e:
            print(f"An error occurred: {e}")
    else:
        print("Report creation skipped.")


if __name__ == "__main__":
    main()
