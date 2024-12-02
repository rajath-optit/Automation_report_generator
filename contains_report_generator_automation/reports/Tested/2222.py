import pandas as pd
import logging
from datetime import datetime
import xlsxwriter
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define service categories
categories = {
    'Security and Identity': ['IAM', 'ACM', 'KMS', 'GuardDuty', 'Secret Manager', 'Secret Hub', 'SSM'],
    'Compute': ['Auto Scaling', 'EC2', 'ECS', 'EKS', 'Lambda', 'EMR', 'Step Functions'],
    'Storage': ['EBS', 'ECR', 'S3', 'DLM', 'Backup'],
    'Network': ['API Gateway', 'CloudFront', 'Route 53', 'VPC', 'ELB', 'ElasticCache', 'CloudTrail'],
    'Database': ['RDS', 'DynamoDB', 'Athena', 'Glue'],
    'Other': ['CloudFormation', 'CodeDeploy', 'Config', 'SNS', 'SQS', 'WorkSpaces', 'EventBridge', 'Config']
}

# Map numerical priorities to words
priority_map = {1: "High", 2: "Medium", 3: "Low"}

def read_input_file(file_path):
    """Reads the input CSV or Excel file and returns the dataframe."""
    try:
        if file_path.endswith('.csv'):
            return pd.read_csv(file_path)
        elif file_path.endswith(('.xls', '.xlsx')):
            return pd.read_excel(file_path)
        else:
            raise ValueError("Unsupported file format. Please provide a CSV or Excel file.")
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {e}")
        raise

def create_summary_table(df, service_grouped, sr_no, summary_data):
    """Generate summary data for open or non-open issues"""
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
    return summary_data

def create_simplified_report_with_pivot(report_file, final_report_file):
    """Creates a report with pivot tables, graphs, and a summary table."""
    df = read_input_file(report_file)

    # Handle missing and infinite values
    df['priority'] = df['priority'].fillna('No Priority')
    df['status'] = df['status'].fillna('Unknown')
    df.replace([float('inf'), -float('inf')], float('nan'), inplace=True)

    # Ensure required columns exist
    required_columns = ['status', 'priority', 'title', 'control_title', 'control_description']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise KeyError(f"Missing columns: {', '.join(missing_columns)}")

    # Add 'is_open_issue' column for pivot tables
    df['is_open_issue'] = df['status'].apply(lambda x: 1 if x == 'alarm' else 0)
    df['priority'] = df['priority'].map(priority_map).fillna(df['priority'])

    # Add 'Safe/Well Architected' column
    df['safe_well_architected'] = df['status'].apply(lambda x: 'Safe/Well Architected' if x == 'ok' else 'Can be Ignored')

    # Ensure final report file includes .xlsx extension
    if not final_report_file.endswith('.xlsx'):
        final_report_file += '.xlsx'

    with pd.ExcelWriter(final_report_file, engine='xlsxwriter') as writer:
        # Separate data into open and closed issues
        no_open_issues_df = df[df['is_open_issue'] == 0]
        open_issues_df = df[df['is_open_issue'] > 0]
        no_open_issues_df.to_excel(writer, sheet_name='Closed Issues', index=False)
        open_issues_df.to_excel(writer, sheet_name='Open Issues', index=False)

        # Summary Table (for open issues)
        summary_data = []
        sr_no = 1
        for service in categories.keys():
            service_df = open_issues_df[open_issues_df['title'].isin(categories[service])]
            service_grouped = service_df.groupby(
                ['title', 'control_title', 'control_description', 'priority'], as_index=False
            ).agg({'is_open_issue': 'sum'})
            summary_data = create_summary_table(open_issues_df, service_grouped, sr_no, summary_data)

        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Open Issues Summary', index=False)

        # Summary Table 2 (for services with no open issues)
        summary2_data = []
        sr_no = 1
        for service in categories.keys():
            service_df = no_open_issues_df[no_open_issues_df['title'].isin(categories[service])]
            service_grouped = service_df.groupby(
                ['title', 'control_title', 'control_description', 'priority'], as_index=False
            ).agg({'is_open_issue': 'sum'})
            summary2_data = create_summary_table(no_open_issues_df, service_grouped, sr_no, summary2_data)

        summary2_df = pd.DataFrame(summary2_data)
        summary2_df.to_excel(writer, sheet_name='Closed Issues Summary', index=False)

        # Pivot Table for open issues
        analysis_df = pd.pivot_table(
            open_issues_df, 
            values='is_open_issue', 
            index=['title'], 
            aggfunc='sum', 
            fill_value=0
        )
        analysis_df.to_excel(writer, sheet_name='Open Issues Analysis')

        # Pivot Table for closed issues
        analysis2_df = pd.pivot_table(
            no_open_issues_df, 
            values='is_open_issue', 
            index=['title'], 
            aggfunc='sum', 
            fill_value=0
        )
        analysis2_df.to_excel(writer, sheet_name='Closed Issues Analysis')

        # Charts for pivot tables
        workbook = writer.book
        worksheet_analysis = writer.sheets['Open Issues Analysis']
        chart_analysis = workbook.add_chart({'type': 'column'})
        chart_analysis.add_series({
            'name': 'Open Issues',
            'categories': f'=Open Issues Analysis!$A$2:$A${len(analysis_df)+1}',
            'values': f'=Open Issues Analysis!$B$2:$B${len(analysis_df)+1}'
        })
        worksheet_analysis.insert_chart('D2', chart_analysis)

        worksheet_analysis2 = writer.sheets['Closed Issues Analysis']
        chart_analysis2 = workbook.add_chart({'type': 'column'})
        chart_analysis2.add_series({
            'name': 'Closed Issues',
            'categories': f'=Closed Issues Analysis!$A$2:$A${len(analysis2_df)+1}',
            'values': f'=Closed Issues Analysis!$B$2:$B${len(analysis2_df)+1}'
        })
        worksheet_analysis2.insert_chart('D2', chart_analysis2)

        # New sheet for Safe/Well Architected resources
        safe_architected_df = df[df['safe_well_architected'] == 'Safe/Well Architected']
        safe_architected_df.to_excel(writer, sheet_name='Safe Well Architected', index=False)

        # Create a pivot table for Safe/Well Architected
        safe_architected_analysis = pd.pivot_table(
            safe_architected_df, 
            values='safe_well_architected', 
            index=['title'], 
            aggfunc='count', 
            fill_value=0
        )
        safe_architected_analysis.to_excel(writer, sheet_name='Safe Well Architected Analysis')

        # Chart for Safe/Well Architected resources
        worksheet_safe = writer.sheets['Safe Well Architected Analysis']
        chart_safe = workbook.add_chart({'type': 'pie'})
        chart_safe.add_series({
            'name': 'Safe/Well Architected Resources',
            'categories': f'=Safe Well Architected Analysis!$A$2:$A${len(safe_architected_analysis)+1}',
            'values': f'=Safe Well Architected Analysis!$B$2:$B${len(safe_architected_analysis)+1}'
        })
        worksheet_safe.insert_chart('D2', chart_safe)

    logging.info(f"Final report with pivot tables, analysis, and charts saved as {final_report_file}")

# Main logic to get input/output file names
if __name__ == "__main__":
    # Prompt user for the input and output file paths
    report_file = input("Please enter the input report file name (including .xlsx or .csv extension): ")
    final_report_file = input("Please enter the output report file name (including .xlsx extension): ")

    # Generate report
    create_simplified_report_with_pivot(report_file, final_report_file)
