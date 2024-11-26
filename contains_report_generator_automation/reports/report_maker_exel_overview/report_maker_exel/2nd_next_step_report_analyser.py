import pandas as pd
from datetime import datetime
import os

# Define service categories
categories = {
    'Security and Identity': ['IAM', 'ACM', 'KMS', 'GuardDuty', 'Secret Manager', 'Secret Hub', 'SSM'],
    'Compute': ['Auto Scaling', 'EC2', 'ECS', 'EKS', 'Lambda', 'EMR', 'Step Functions'],
    'Storage': ['EBS', 'ECR', 'S3', 'DLM', 'Backup'],
    'Network': ['API Gateway', 'CloudFront', 'Route 53', 'VPC', 'ELB', 'ElasticCache', 'CloudTrail'],
    'Database': ['RDS', 'DynamoDB', 'Athena', 'Glue'],
    'Other': ['CloudFormation', 'CodeDeploy', 'Config', 'SNS', 'SQS', 'WorkSpaces', 'EventBridge', 'Config']
}

def create_simplified_report(report_file, final_report_file):
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

    # Initialize a dictionary to hold DataFrames for each category
    categorized_data = {category: pd.DataFrame() for category in categories}
    
    # Process each category and filter relevant services
    for category, services in categories.items():
        categorized_data[category] = df[df['title'].isin(services)]

    # Create a new Excel writer object
    with pd.ExcelWriter(final_report_file, engine='xlsxwriter') as writer:
        # Write 'safe' and 'unsafe' DataFrames to separate sheets
        safe_df.to_excel(writer, sheet_name='safe', index=False)
        unsafe_df.to_excel(writer, sheet_name='unsafe', index=False)
        
        # Write each category DataFrame to a separate sheet
        for category, data in categorized_data.items():
            data.to_excel(writer, sheet_name=category, index=False)
    
    print(f"Final simplified report saved as {final_report_file}")

def main():
    # Ask the user to input the report file name
    report_file = input("Enter the report file name (e.g., aws_compliance_benchmark_all_controls_benchmark_vested_with_priorities.csv): ").strip()
    
    # Get the input file's base name (without path) and extension
    base_name = os.path.splitext(os.path.basename(report_file))[0]
    
    # Create a unique file name using a timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_file_name = f"{base_name}_simplified_report_{timestamp}.xlsx"
    
    # Set the output path to the reports directory
    reports_directory = os.path.dirname(os.path.abspath(__file__))  # Get the current script's directory
    final_report_file = os.path.join(reports_directory, unique_file_name)

    # Ask if the user wants to create the simplified report
    create_report = input("Do you want to create the simplified report? (yes/no): ").strip().lower()
    if create_report == 'yes':
        try:
            create_simplified_report(report_file, final_report_file)
        except ValueError as e:
            print(e)
        except Exception as e:
            print(f"An error occurred: {e}")
    else:
        print("Report creation skipped.")

if __name__ == "__main__":
    main()
