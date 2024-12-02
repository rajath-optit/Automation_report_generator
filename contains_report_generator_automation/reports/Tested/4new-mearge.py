import pandas as pd
import xlsxwriter
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

def read_input_file(file_name):
    file_extension = file_name.split('.')[-1].lower()
    if file_extension == 'csv':
        return pd.read_csv(file_name)
    elif file_extension in ['xls', 'xlsx']:
        return pd.read_excel(file_name)
    else:
        raise ValueError("Unsupported file format. Please provide a CSV or Excel file.")

def filter_and_categorize(df):
    # Categorize based on 'title'
    categorized_data = {}
    for category, services in categories.items():
        categorized_data[category] = df[df['title'].isin(services)]
    
    # Filter based on 'status'
    compliant_data = df[df['status'] != 'alarm']
    non_compliant_data = df[df['status'] == 'alarm']
    
    return compliant_data, non_compliant_data, categorized_data

def analyze_data(df):
    # Handle missing or infinite values
    df['priority'].fillna('Unknown', inplace=True)
    df.replace([float('inf'), -float('inf')], pd.NA, inplace=True)

    # Map status to binary 'is_open_issue'
    df['is_open_issue'] = df['status'].apply(lambda x: 1 if x == 'alarm' else 0)

    # Filter open and closed issues
    open_issues = df[df['is_open_issue'] == 1]
    closed_issues = df[df['is_open_issue'] == 0]
    
    # Group by service title and priority
    open_summary = open_issues.groupby(['title', 'priority']).size().reset_index(name='open_issues_count')

    return open_issues, closed_issues, open_summary

def create_simplified_report_with_pivot(report_file, final_report_file):
    # Read the input data
    df = read_input_file(report_file)

    # Filter and categorize the data
    compliant_data, non_compliant_data, categorized_data = filter_and_categorize(df)

    # Analyze the data
    open_issues, closed_issues, open_summary = analyze_data(df)

    with pd.ExcelWriter(final_report_file, engine='xlsxwriter') as writer:
        # Write the 'no_open_issues' and 'open_issues' sheets
        no_open_issues_df = df[df['is_open_issue'] == 0]
        open_issues_df = df[df['is_open_issue'] == 1]

        no_open_issues_df.to_excel(writer, sheet_name='no_open_issues', index=False)
        open_issues_df.to_excel(writer, sheet_name='open_issues', index=False)

        # Initialize a list to collect summary data for open issues
        summary_data = []
        sr_no = 1
        for service in categories.keys():
            service_df = open_issues_df[open_issues_df['title'].isin(categories[service])]
            service_grouped = service_df.groupby(
                ['title', 'recommendation', 'control_description', 'priority'], as_index=False
            ).agg({'is_open_issue': 'sum'})

            # Add grouped data to summary table
            for _, row in service_grouped.iterrows():
                summary_data.append({
                    'Sr No': sr_no,
                    'Service': row['title'],
                    'Recommendation': row['recommendation'],
                    'Description': row['control_description'],
                    'Open Issues': row['is_open_issue'],
                    'Priority': row['priority']
                })
                sr_no += 1

        # Convert the summary data to a DataFrame
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='summary', index=False)

        # Apply color formatting to the 'summary' sheet
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

        # Create 'summary2' sheet (controls with 0 open issues)
        summary2_data = []
        sr_no = 1
        for service in categories.keys():
            service_df = no_open_issues_df[no_open_issues_df['title'].isin(categories[service])]
            service_grouped = service_df.groupby(
                ['title', 'recommendation', 'control_description', 'priority'], as_index=False
            ).agg({'is_open_issue': 'sum'})

            # Add grouped data to summary2 table (controls with 0 open issues)
            for _, row in service_grouped.iterrows():
                summary2_data.append({
                    'Sr No': sr_no,
                    'Service': row['title'],
                    'Recommendation': row['recommendation'],
                    'Description': row['control_description'],
                    'Open Issues': row['is_open_issue'],
                    'Priority': row['priority']
                })
                sr_no += 1

        # Convert the summary2 data to a DataFrame
        summary2_df = pd.DataFrame(summary2_data)
        summary2_df.to_excel(writer, sheet_name='summary2', index=False)

        # Apply color formatting to the 'summary2' sheet
        worksheet2 = writer.sheets['summary2']
        for row_num, row in enumerate(summary2_df.values, start=1):
            priority = row[5]
            if priority == 'High':
                worksheet2.write(row_num, 5, row[5], red_format)
            elif priority == 'Medium':
                worksheet2.write(row_num, 5, row[5], orange_format)
            elif priority == 'Low':
                worksheet2.write(row_num, 5, row[5], yellow_format)

        # Create 'analysis' sheet (pivot table for open issues)
        analysis_df = pd.pivot_table(
            open_issues_df, 
            values='is_open_issue', 
            index=['title'], 
            aggfunc='sum', 
            fill_value=0
        )
        analysis_df.to_excel(writer, sheet_name='analysis')

        # Create a graph for open issues in 'analysis' sheet
        worksheet_analysis = writer.sheets['analysis']
        chart = workbook.add_chart({'type': 'column'})
        chart.add_series({
            'name': 'Open Issues',
            'categories': f'=analysis!$A$2:$A${len(analysis_df)+1}',
            'values': f'=analysis!$B$2:$B${len(analysis_df)+1}'
        })
        worksheet_analysis.insert_chart('D2', chart)

        # Create 'analysis2' sheet (pivot table for closed issues)
        analysis2_df = pd.pivot_table(
            no_open_issues_df, 
            values='is_open_issue', 
            index=['title'], 
            aggfunc='sum', 
            fill_value=0
        )
        analysis2_df.to_excel(writer, sheet_name='analysis2')

        # Create a graph for closed issues in 'analysis2' sheet
        worksheet_analysis2 = writer.sheets['analysis2']
        chart2 = workbook.add_chart({'type': 'column'})
        chart2.add_series({
            'name': 'Closed Issues',
            'categories': f'=analysis2!$A$2:$A${len(analysis2_df)+1}',
            'values': f'=analysis2!$B$2:$B${len(analysis2_df)+1}'
        })
        worksheet_analysis2.insert_chart('D2', chart2)

    print(f"Final report with pivot tables, charts, and summary sheets saved as {final_report_file}")

