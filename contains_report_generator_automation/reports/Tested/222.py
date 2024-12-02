import pandas as pd
from datetime import datetime
import xlsxwriter
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

# Map numerical priorities to words
priority_map = {1: "High", 2: "Medium", 3: "Low"}

def read_file(report_file):
    """Attempt to read the file and handle errors."""
    try:
        if report_file.endswith('.csv'):
            df = pd.read_csv(report_file)
        elif report_file.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(report_file)
        else:
            raise ValueError("Unsupported file format. Please provide a CSV or Excel file.")
        
        return df
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: The file '{report_file}' was not found.")
    except ValueError as e:
        raise e
    except Exception as e:
        raise Exception(f"An error occurred while reading the file '{report_file}': {str(e)}")

def create_simplified_report(report_file, final_report_file):
    """Creates a simplified report with categorized data and compliant/non-compliant resources sheets."""
    df = read_file(report_file)
    
    # Filter rows based on 'status' column
    compliant_df = df[df['status'] != 'alarm']
    non_compliant_df = df[df['status'] == 'alarm']

    # Categorize data by services
    categorized_data = {category: df[df['title'].isin(services)] for category, services in categories.items()}

    with pd.ExcelWriter(final_report_file, engine='xlsxwriter') as writer:
        compliant_df.to_excel(writer, sheet_name='Compliant Resources', index=False)
        non_compliant_df.to_excel(writer, sheet_name='Non-Compliant Resources', index=False)
        for category, data in categorized_data.items():
            data.to_excel(writer, sheet_name=category, index=False)

    print(f"Report with categorized data saved as {final_report_file}")

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
    """Creates a report with pivot tables, graphs, and a summary table, including a new sheet for 'Safe/Well Architected' resources."""
    df = read_file(report_file)
    
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

    print(f"Full report with analysis and charts saved as {final_report_file}")
def main(report_file):
    # Generate unique filenames using timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    simplified_report_file = f"input_compliant_non_compliant_report_{timestamp}.xlsx"
    detailed_report_file = f"input_detailed_report_with_pivot_{timestamp}.xlsx"

    create_simplified_report(report_file, simplified_report_file)
    create_simplified_report_with_pivot(report_file, detailed_report_file)

if __name__ == "__main__":
    report_file = "/home/rajath.h@optit.india/Documents/python_experiment_panda/exper/experiment/priority_adder_program/reports/capitalmind_28_nov_with_priorities.xlsx"  # Replace with your actual file path
    main(report_file)
