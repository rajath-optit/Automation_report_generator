import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import xlsxwriter
import os

# Function to read input files (CSV/Excel)
def read_input_file(file_name):
    file_extension = file_name.split('.')[-1].lower()
    if file_extension == 'csv':
        return pd.read_csv(file_name)
    elif file_extension in ['xls', 'xlsx']:
        return pd.read_excel(file_name)
    else:
        raise ValueError("Unsupported file format. Please provide a CSV or Excel file.")

# Categorizing services
def categorize_services(df):
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

# Filter and categorize
def filter_and_categorize(df, categories):
    compliant_data = df[df['status'] != 'alarm']
    non_compliant_data = df[df['status'] == 'alarm']
    
    categorized_data = categorize_services(df)
    
    return compliant_data, non_compliant_data, categorized_data

# Data analysis
def analyze_data(df):
    df['priority'].fillna('Unknown', inplace=True)
    df.replace([float('inf'), -float('inf')], pd.NA, inplace=True)
    
    df['is_open_issue'] = df['status'].apply(lambda x: 1 if x == 'alarm' else 0)
    
    open_issues = df[df['is_open_issue'] == 1]
    closed_issues = df[df['is_open_issue'] == 0]
    
    open_summary = open_issues.groupby(['title', 'priority']).size().reset_index(name='open_issues_count')
    
    return open_issues, closed_issues, open_summary

# Report Creation with Pivot and Analysis
def create_simplified_report_with_pivot(report_file, final_report_file):
    # Read input file
    df = read_input_file(report_file)
    
    categories = {
        'Security and Identity': ['IAM', 'ACM', 'KMS', 'GuardDuty', 'Secret Manager', 'Secret Hub', 'SSM'],
        'Compute': ['Auto Scaling', 'EC2', 'ECS', 'EKS', 'Lambda', 'EMR', 'Step Functions'],
        'Storage': ['EBS', 'ECR', 'S3', 'DLM', 'Backup'],
        'Network': ['API Gateway', 'CloudFront', 'Route 53', 'VPC', 'ELB', 'ElasticCache', 'CloudTrail'],
        'Database': ['RDS', 'DynamoDB', 'Athena', 'Glue'],
        'Other': ['CloudFormation', 'CodeDeploy', 'Config', 'SNS', 'SQS', 'WorkSpaces', 'EventBridge', 'Config']
    }
    
    # Analyze data
    open_issues, closed_issues, open_summary = analyze_data(df)
    
    # Create Excel file
    with pd.ExcelWriter(final_report_file, engine='xlsxwriter') as writer:
        # Writing filtered data to different sheets
        open_issues.to_excel(writer, sheet_name='open_issues', index=False)
        closed_issues.to_excel(writer, sheet_name='closed_issues', index=False)

        # Summary for open issues by service
        summary_data = []
        sr_no = 1
        for service in categories.keys():
            service_df = open_issues[open_issues['title'].isin(categories[service])]
            service_grouped = service_df.groupby(['title', 'control_title', 'control_description', 'priority'], as_index=False).agg({'is_open_issue': 'sum'})
            for _, row in service_grouped.iterrows():
                summary_data.append({
                    'Sr No': sr_no,
                    'Service': row['title'],
                    'Control Title': row['control_title'],
                    'Description': row['control_description'],
                    'Open Issues': row['is_open_issue'],
                    'Priority': row['priority']
                })
                sr_no += 1
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='summary', index=False)

        # Apply color formatting to the summary sheet
        workbook = writer.book
        worksheet = writer.sheets['summary']
        
        red_format = workbook.add_format({'bg_color': 'red', 'font_color': 'white'})
        orange_format = workbook.add_format({'bg_color': 'orange', 'font_color': 'white'})
        yellow_format = workbook.add_format({'bg_color': 'yellow', 'font_color': 'black'})
        
        for row_num, row in enumerate(summary_df.values, start=1):
            priority = row[5]
            if priority == 'High':
                worksheet.write(row_num, 5, row[5], red_format)
            elif priority == 'Medium':
                worksheet.write(row_num, 5, row[5], orange_format)
            elif priority == 'Low':
                worksheet.write(row_num, 5, row[5], yellow_format)
        
        # Pivot Table for open issues
        analysis_df = pd.pivot_table(open_issues, values='is_open_issue', index=['title'], aggfunc='sum', fill_value=0)
        analysis_df.to_excel(writer, sheet_name='analysis')
        
        # Create charts for analysis
        worksheet_analysis = writer.sheets['analysis']
        chart = workbook.add_chart({'type': 'column'})
        chart.add_series({
            'name': 'Open Issues',
            'categories': f'=analysis!$A$2:$A${len(analysis_df)+1}',
            'values': f'=analysis!$B$2:$B${len(analysis_df)+1}'
        })
        worksheet_analysis.insert_chart('D2', chart)
        
    print(f"Final report with pivot table, charts, and summary sheets saved as {final_report_file}")

# Main function to run the report creation
def main():
    report_file = input("Enter the report file name (e.g., aws_compliance_benchmark_all_controls_benchmark_vested_with_priorities.csv): ").strip()
    base_name = os.path.splitext(os.path.basename(report_file))[0]
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_file_name = f"{base_name}_simplified_report_with_pivot_{timestamp}.xlsx"
    
    reports_directory = os.path.dirname(os.path.abspath(__file__))
    final_report_file = os.path.join(reports_directory, unique_file_name)
    
    try:
        create_simplified_report_with_pivot(report_file, final_report_file)
    except ValueError as e:
        print(e)
    except KeyError as e:
        print(f"KeyError: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
