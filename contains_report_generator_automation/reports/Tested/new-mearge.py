import pandas as pd
import xlsxwriter
import matplotlib.pyplot as plt

def read_input_file(file_name):
    """Read the input CSV or Excel file."""
    if file_name.endswith('.csv'):
        return pd.read_csv(file_name)
    elif file_name.endswith('.xlsx'):
        return pd.read_excel(file_name)
    else:
        raise ValueError("Unsupported file format. Please provide a CSV or Excel file.")

def categorize_services(df):
    """Categorize data into different service categories."""
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

def clean_data(df):
    """Clean the data by handling missing values and converting status."""
    df.fillna({'priority': 'Medium'}, inplace=True)
    df['is_open_issue'] = df['status'].apply(lambda x: 1 if x == 'alarm' else 0)
    return df

def analyze_data(df):
    """Perform analysis: Split data into open and no open issues, create summary tables."""
    open_issues = df[df['is_open_issue'] == 1]
    no_open_issues = df[df['is_open_issue'] == 0]

    summary_data = open_issues.groupby(['title', 'priority']).size().reset_index(name='open_issue_count')
    
    # Pivot Table Analysis: Number of open issues per service
    pivot_table = open_issues.pivot_table(index='title', columns='priority', aggfunc='size', fill_value=0)
    
    return open_issues, no_open_issues, summary_data, pivot_table

def create_charts(analysis_data, filename):
    """Generate charts based on analysis data."""
    # Generate bar chart for the open issues by service and priority
    analysis_data.plot(kind='bar', x='title', y='open_issue_count', color='blue', title='Open Issues by Service and Priority')
    plt.savefig(f'{filename}_analysis_chart.png')
    plt.close()

def save_to_excel(df, categorized_data, open_issues, no_open_issues, summary_data, pivot_table, filename):
    """Save data to an Excel file with multiple sheets."""
    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
        # Write filtered data to sheets
        categorized_data['Security and Identity'].to_excel(writer, sheet_name='Security and Identity')
        categorized_data['Compute'].to_excel(writer, sheet_name='Compute')
        categorized_data['Storage'].to_excel(writer, sheet_name='Storage')
        categorized_data['Network'].to_excel(writer, sheet_name='Network')
        categorized_data['Database'].to_excel(writer, sheet_name='Database')
        categorized_data['Other'].to_excel(writer, sheet_name='Other')
        
        # Write open and no open issues
        open_issues.to_excel(writer, sheet_name='open_issues')
        no_open_issues.to_excel(writer, sheet_name='no_open_issues')

        # Write summary data
        summary_data.to_excel(writer, sheet_name='summary_data')
        
        # Write pivot table
        pivot_table.to_excel(writer, sheet_name='pivot_table')
        
        # Add charts to the Excel file
        workbook = writer.book
        worksheet = workbook.add_worksheet('Analysis Chart')
        worksheet.insert_image('B2', f'{filename}_analysis_chart.png')

def main():
    # Get the input file name
    file_name = input("Enter the input file name (CSV or Excel): ")

    # Read the input file
    try:
        df = read_input_file(file_name)
    except ValueError as e:
        print(e)
        return

    # Filter and categorize data
    categorized_data = categorize_services(df)

    # Clean and prepare data for analysis
    df = clean_data(df)

    # Analyze the data
    open_issues, no_open_issues, summary_data, pivot_table = analyze_data(df)

    # Generate and save charts
    create_charts(summary_data, file_name)

    # Save the final output to an Excel file
    output_file = f"processed_{file_name.split('.')[0]}.xlsx"
    save_to_excel(df, categorized_data, open_issues, no_open_issues, summary_data, pivot_table, output_file)

    print(f"Processing complete. Output saved to {output_file}")

if __name__ == "__main__":
    main()
