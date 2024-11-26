import pandas as pd
import os
from datetime import datetime
import xlsxwriter

# Define service categories as before
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

def create_simplified_report_with_pivot(report_file, final_report_file):
    # Read input report file (CSV or Excel)
    if report_file.endswith('.csv'):
        df = pd.read_csv(report_file)
    elif report_file.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(report_file)
    else:
        raise ValueError("Unsupported file format. Please provide a CSV or Excel file.")
    
    # Ensure columns exist
    required_columns = ['status', 'priority', 'title', 'control_title', 'control_description']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise KeyError(f"Missing columns: {', '.join(missing_columns)}")

    # Ensure 'status' column is clean (convert to string if necessary)
    df['status'] = df['status'].astype(str)

    # Map status to "safe" or "open issue"
    df['is_open_issue'] = df['status'].apply(lambda x: 1 if x == 'alarm' else 0)

    # Replace numerical priority with words
    df['priority'] = df['priority'].map(priority_map).fillna(df['priority'])

    # Handle NaN and INF values (replace NaN and INF with default values)
    df['priority'] = df['priority'].fillna('No Priority')
    df['status'] = df['status'].fillna('Unknown')
    df.replace([float('inf'), -float('inf')], float('nan'), inplace=True)

    # Create a new Excel writer object to write multiple sheets
    with pd.ExcelWriter(final_report_file, engine='xlsxwriter') as writer:
        # Write the 'safe' and 'unsafe' DataFrames to separate sheets
        safe_df = df[df['status'] != 'alarm']
        unsafe_df = df[df['status'] == 'alarm']
        
        # Write the 'safe' and 'unsafe' sheets
        safe_df.to_excel(writer, sheet_name='safe', index=False)
        unsafe_df.to_excel(writer, sheet_name='unsafe', index=False)

        # Initialize a list to collect data for the final summary table
        summary_data = []
        sr_no = 1
        
        # Process each service and leave a one-line gap after each service
        for service in categories.keys():
            service_df = df[df['title'].isin(categories[service])]
            
            # Group by Control Title and sum Open Issues per title
            service_grouped = service_df.groupby(
                ['title', 'control_title', 'control_description', 'priority'], as_index=False
            ).agg({'is_open_issue': 'sum'})

            # Add grouped data to summary table
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
            
            # Insert a blank row to separate services (if we have added any data)
            if summary_data:
                summary_data.append({
                    'Sr No': '',
                    'Service': '',
                    'Control Title': '',
                    'Description': '',
                    'Open Issues': '',
                    'Priority': ''
                })

        # Convert the summary data to a DataFrame
        summary_df = pd.DataFrame(summary_data)

        # Write the summary table to the 'table' sheet
        summary_df.to_excel(writer, sheet_name='table', index=False)

        # Apply color formatting to the 'table' sheet
        workbook = writer.book
        worksheet = writer.sheets['table']

        # Define formats
        red_format = workbook.add_format({'bg_color': 'red', 'font_color': 'white'})
        orange_format = workbook.add_format({'bg_color': 'orange', 'font_color': 'white'})
        yellow_format = workbook.add_format({'bg_color': 'yellow', 'font_color': 'black'})
        green_format = workbook.add_format({'bg_color': 'lightgreen', 'font_color': 'black'})
        
        # Loop through the rows in 'table' sheet and apply color formatting
        for row_num, row in enumerate(summary_df.values, start=1):
            priority = row[5]
            if priority == 'High':
                worksheet.write(row_num, 5, row[5], red_format)
            elif priority == 'Medium':
                worksheet.write(row_num, 5, row[5], orange_format)
            elif priority == 'Low':
                worksheet.write(row_num, 5, row[5], yellow_format)

        # Create 'analysis' sheet (pivot table for open issues)
        analysis_df = pd.pivot_table(
            df, 
            values='is_open_issue', 
            index=['title'], 
            aggfunc='sum', 
            fill_value=0
        )
        analysis_df.to_excel(writer, sheet_name='analysis')

        # Create charts for graphing
        worksheet_analysis = writer.sheets['analysis']

        # Chart 1: Open Issues by Title
        chart1 = workbook.add_chart({'type': 'column'})
        chart1.add_series({
            'name': 'Open Issues',
            'categories': f'=analysis!$A$2:$A${len(analysis_df)+1}',
            'values': f'=analysis!$B$2:$B${len(analysis_df)+1}'
        })
        worksheet_analysis.insert_chart('D2', chart1)

        # Chart 2: Safe Controls (No Issues)
        safe_controls_pivot = pd.pivot_table(
            safe_df, 
            values='is_open_issue', 
            index=['title'], 
            aggfunc='count', 
            fill_value=0
        )
        safe_controls_pivot.to_excel(writer, sheet_name='safe_controls_analysis')

        # Add chart for safe controls
        worksheet_safe_analysis = writer.sheets['safe_controls_analysis']
        chart2 = workbook.add_chart({'type': 'column'})
        chart2.add_series({
            'name': 'Safe Controls (No Issues)',
            'categories': f'=safe_controls_analysis!$A$2:$A${len(safe_controls_pivot)+1}',
            'values': f'=safe_controls_analysis!$B$2:$B${len(safe_controls_pivot)+1}'
        })
        worksheet_safe_analysis.insert_chart('D2', chart2)

        # Create Pivot Table (additional one)
        pivot_table = pd.pivot_table(
            df, 
            values='status', 
            index=['title', 'control_title', 'control_description', 'region', 'account_id', 'resource', 'reason', 'description'], 
            columns=['priority'], 
            aggfunc='count', 
            fill_value=0
        )
        pivot_table.to_excel(writer, sheet_name='pivot_analysis')

        # ** New safe_controls sheet creation: **
        # Copy 'safe' sheet data into 'safe_controls'
        safe_controls_df = safe_df.copy()

        # Write the data into the 'safe_controls' sheet
        safe_controls_df.to_excel(writer, sheet_name='safe_controls', index=False)

        # Apply light green format to the 'priority' column in 'safe_controls' sheet
        worksheet_safe_controls = writer.sheets['safe_controls']
        light_green_format = workbook.add_format({'bg_color': 'lightgreen', 'font_color': 'black'})
        for row_num, row in enumerate(safe_controls_df.values, start=1):
            worksheet_safe_controls.write(row_num, 5, row[5], light_green_format)

# Main method to execute script
def main():
    # Prompt for the report file name
    report_file = input("Enter the report file name (e.g., aws_compliance_benchmark_all_controls_benchmark_vested_with_priorities.csv): ").strip()

    if not os.path.exists(report_file):
        print(f"Error: The file '{report_file}' does not exist.")
        return

    # Ask if the user wants to create the simplified report
    create_report = input("Do you want to create the simplified report with pivot table? (yes/no): ").strip().lower()

    if create_report == 'yes':
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        final_report_file = f"{os.path.splitext(report_file)[0]}_simplified_report_with_pivot_{timestamp}.xlsx"

        try:
            create_simplified_report_with_pivot(report_file, final_report_file)
            print(f"Final report with pivot table and charts saved as {final_report_file}")
        except Exception as e:
            print(f"An error occurred: {e}")
    else:
        print("Report creation skipped.")

if __name__ == "__main__":
    main()
