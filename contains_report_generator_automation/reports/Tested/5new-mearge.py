import pandas as pd
import xlsxwriter
from datetime import datetime

# Define service categories
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
    categorized_data = {}
    for category, services in categories.items():
        categorized_data[category] = df[df['title'].isin(services)]
    
    compliant_data = df[df['status'] != 'alarm']
    non_compliant_data = df[df['status'] == 'alarm']
    
    return compliant_data, non_compliant_data, categorized_data

def analyze_data(df):
    df['priority'].fillna('Unknown', inplace=True)
    df.replace([float('inf'), -float('inf')], pd.NA, inplace=True)
    df['is_open_issue'] = df['status'].apply(lambda x: 1 if x == 'alarm' else 0)
    open_issues = df[df['is_open_issue'] == 1]
    closed_issues = df[df['is_open_issue'] == 0]
    open_summary = open_issues.groupby(['title', 'priority']).size().reset_index(name='open_issues_count')
    return open_issues, closed_issues, open_summary

def create_simplified_report_with_pivot(report_file, final_report_file, separated_services_file):
    df = read_input_file(report_file)
    compliant_data, non_compliant_data, categorized_data = filter_and_categorize(df)
    open_issues, closed_issues, open_summary = analyze_data(df)

    with pd.ExcelWriter(final_report_file, engine='xlsxwriter') as writer:
        no_open_issues_df = df[df['is_open_issue'] == 0]
        open_issues_df = df[df['is_open_issue'] == 1]

        no_open_issues_df.to_excel(writer, sheet_name='no_open_issues', index=False)
        open_issues_df.to_excel(writer, sheet_name='open_issues', index=False)

        summary_data = []
        sr_no = 1
        for service in categories.keys():
            service_df = open_issues_df[open_issues_df['title'].isin(categories[service])]
            service_grouped = service_df.groupby(
                ['title', 'recommendation', 'control_description', 'priority'], as_index=False
            ).agg({'is_open_issue': 'sum'})

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

        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='summary', index=False)

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

        analysis_df = pd.pivot_table(
            open_issues_df, 
            values='is_open_issue', 
            index=['title'], 
            aggfunc='sum', 
            fill_value=0
        )
        analysis_df.to_excel(writer, sheet_name='analysis')

        worksheet_analysis = writer.sheets['analysis']
        chart = workbook.add_chart({'type': 'column'})
        chart.add_series({
            'name': 'Open Issues',
            'categories': f'=analysis!$A$2:$A${len(analysis_df)+1}',
            'values': f'=analysis!$B$2:$B${len(analysis_df)+1}'
        })
        worksheet_analysis.insert_chart('D2', chart)

    print(f"Final report saved as {final_report_file}")

    with pd.ExcelWriter(separated_services_file, engine='xlsxwriter') as writer:
        alarm_data = df[df['status'] == 'alarm']
        separated_services = pd.pivot_table(
            alarm_data, 
            values='status', 
            index='title', 
            columns='priority', 
            aggfunc='count', 
            fill_value=0
        )
        separated_services.to_excel(writer, sheet_name='services_separated')

    print(f"Separated services file saved as {separated_services_file}")

if __name__ == "__main__":
    input_file = input("Enter the report file name (e.g., file.csv or file.xlsx): ").strip()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_report = f"FinalReport_{timestamp}.xlsx"
    separated_services = f"SeparatedServices_{timestamp}.xlsx"
    create_simplified_report_with_pivot(input_file, final_report, separated_services)
