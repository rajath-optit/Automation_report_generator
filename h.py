import pandas as pd
import os
import sys
from datetime import datetime
import xlsxwriter

# Define service categories
CATEGORIES = {
    'Security and Identity': ['IAM', 'ACM', 'KMS', 'GuardDuty', 'Secret Manager', 'Secret Hub', 'SSM'],
    'Compute': ['Auto Scaling', 'EC2', 'ECS', 'EKS', 'Lambda', 'EMR', 'Step Functions'],
    'Storage': ['EBS', 'ECR', 'S3', 'DLM', 'Backup'],
    'Network': ['API Gateway', 'CloudFront', 'Route 53', 'VPC', 'ELB', 'ElasticCache', 'CloudTrail'],
    'Database': ['RDS', 'DynamoDB', 'Athena', 'Glue'],
    'Other': ['CloudFormation', 'CodeDeploy', 'Config', 'SNS', 'SQS', 'WorkSpaces', 'EventBridge']
}

# Priority mapping
PRIORITY_MAP = {1: "High", 2: "Medium", 3: "Low"}
COLOR_MAP = {
    'High': '#FF0000',     # Red
    'Medium': '#FFA500',   # Orange
    'Low': '#FFFF00',      # Yellow
    'Safe': '#00FF00',     # Green
    'No Priority': '#C0C0C0'  # Gray
}

class AWSComplianceReporter:
    def __init__(self, input_file, priority_file="PowerPipeControls_Annotations.xlsx"):
        """
        Initialize the AWS Compliance Reporter
        
        Args:
            input_file (str): Path to the input CSV/Excel file
            priority_file (str, optional): Path to the priority annotations file
        """
        self.input_file = input_file
        self.priority_file = priority_file
        self.df = self._load_input_file()
        self.priority_df = self._load_priority_database()
        
    def _load_input_file(self):
        """
        Load input file with error handling
        
        Returns:
            pd.DataFrame: Loaded dataframe
        """
        try:
            if self.input_file.endswith(".csv"):
                return pd.read_csv(self.input_file, low_memory=False)
            elif self.input_file.endswith((".xlsx", ".xls")):
                return pd.read_excel(self.input_file, engine='openpyxl')
            else:
                raise ValueError("Unsupported file type. Use CSV or Excel.")
        except Exception as e:
            print(f"Error loading input file: {e}")
            sys.exit(1)

    def _load_priority_database(self):
        """
        Load priority database
        
        Returns:
            pd.DataFrame: Priority database
        """
        try:
            return pd.read_excel(self.priority_file)
        except Exception as e:
            print(f"Error loading priority database: {e}")
            sys.exit(1)

    def enrich_data(self):
        """
        Enrich input data with priority and recommendations
        
        Returns:
            pd.DataFrame: Enriched dataframe
        """
        for idx, row in self.df.iterrows():
            control_title = row.get("control_title", "")
            status = row.get("status", "")

            # Find matching priority row
            matching_row = self.priority_df[self.priority_df["control_title"] == control_title]

            if not matching_row.empty:
                priority = matching_row.iloc[0]["priority"]
                recommendation = matching_row.iloc[0]["Recommendation Steps/Approach"]

                # Assign priority and recommendation
                if status in ["ok", "info", "skip"]:
                    self.df.at[idx, "priority"] = "Safe"
                    self.df.at[idx, "Recommendation Steps/Approach"] = recommendation
                else:
                    self.df.at[idx, "priority"] = priority
                    self.df.at[idx, "Recommendation Steps/Approach"] = recommendation
            else:
                # Default values if no match
                self.df.at[idx, "priority"] = "No Priority"
                self.df.at[idx, "Recommendation Steps/Approach"] = "No recommendation available"

        return self.df

    def generate_comprehensive_report(self):
        """
        Generate comprehensive report with multiple analysis sheets
        """
        # Enrich data first
        enriched_df = self.enrich_data()

        # Generate unique filename
        base_name = os.path.splitext(os.path.basename(self.input_file))[0]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"{base_name}_comprehensive_report_{timestamp}.xlsx"

        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
            workbook = writer.book

            # Raw Data Sheet
            enriched_df.to_excel(writer, sheet_name='Raw Data', index=False)
            self._format_sheet(writer.sheets['Raw Data'], workbook)

            # Filter DataFrames
            no_issues_df = enriched_df[enriched_df['status'].isin(['ok', 'info', 'skip'])]
            open_issues_df = enriched_df[enriched_df['status'] == 'alarm']

            # No Issues and Open Issues Sheets
            no_issues_df.to_excel(writer, sheet_name='No Open Issues', index=False)
            open_issues_df.to_excel(writer, sheet_name='Open Issues', index=False)

            # Service Category Analysis
            self._create_service_category_analysis(open_issues_df, writer, workbook)

            # Priority Summary
            self._create_priority_summary(enriched_df, writer, workbook)

            # Pivot Analysis
            self._create_pivot_analysis(enriched_df, writer, workbook)

        print(f"Comprehensive report generated: {output_file}")

    def _create_service_category_analysis(self, open_issues_df, writer, workbook):
        """
        Create service category analysis sheet
        """
        service_summary = []
        sr_no = 1

        for service_category, services in CATEGORIES.items():
            category_df = open_issues_df[open_issues_df['title'].isin(services)]
            
            # Skip empty categories
            if category_df.empty:
                continue

            # Add category header
            service_summary.append({
                'Category': f'{service_category} Analysis',
                'Service': '', 'Control': '', 
                'Description': '', 'Open Issues': '', 
                'Priority': ''
            })

            # Aggregate by service and control
            grouped = category_df.groupby(['title', 'control_title', 'control_description', 'priority']).size().reset_index(name='open_issues')

            for _, row in grouped.iterrows():
                service_summary.append({
                    'Category': sr_no,
                    'Service': row['title'],
                    'Control': row['control_title'],
                    'Description': row['control_description'],
                    'Open Issues': row['open_issues'],
                    'Priority': row['priority']
                })
                sr_no += 1

            # Add blank row
            service_summary.append({
                'Category': '', 'Service': '', 'Control': '', 
                'Description': '', 'Open Issues': '', 'Priority': ''
            })

        service_summary_df = pd.DataFrame(service_summary)
        service_summary_df.to_excel(writer, sheet_name='Service Analysis', index=False)

    def _create_priority_summary(self, df, writer, workbook):
        """
        Create priority summary sheet with chart
        """
        priority_counts = df['priority'].value_counts()
        summary_df = priority_counts.reset_index()
        summary_df.columns = ['Priority', 'Count']

        # Add total row
        total_row = pd.DataFrame([['Total', summary_df['Count'].sum()]], columns=['Priority', 'Count'])
        summary_df = pd.concat([summary_df, total_row], ignore_index=True)

        summary_df.to_excel(writer, sheet_name='Priority Summary', index=False)
        worksheet = writer.sheets['Priority Summary']

        # Create column chart
        chart = workbook.add_chart({'type': 'column'})
        for idx, row in summary_df.iterrows():
            priority = row['Priority']
            if priority != 'Total':
                chart.add_series({
                    'name': priority,
                    'categories': '=\'Priority Summary\'!$A$2:$A$6',
                    'values': f'=\'Priority Summary\'!$B${idx+2}:$B${idx+2}',
                    'fill': {'color': COLOR_MAP.get(priority, '#000000')}
                })

        chart.set_title({'name': 'Priority Distribution'})
        chart.set_x_axis({'name': 'Priority'})
        chart.set_y_axis({'name': 'Count'})
        chart.set_legend({'position': 'bottom'})
        worksheet.insert_chart('D2', chart)

    def _create_pivot_analysis(self, df, writer, workbook):
        """
        Create pivot tables and analysis
        """
        # Pivot by Service
        service_pivot = pd.pivot_table(
            df, 
            index=['title'], 
            columns=['priority'], 
            aggfunc='size', 
            fill_value=0
        )
        service_pivot.to_excel(writer, sheet_name='Service Pivot')

        # Pivot by Control
        control_pivot = pd.pivot_table(
            df, 
            index=['control_title'], 
            columns=['priority'], 
            aggfunc='size', 
            fill_value=0
        )
        control_pivot.to_excel(writer, sheet_name='Control Pivot')

    def _format_sheet(self, worksheet, workbook):
        """
        Basic formatting for sheets
        """
        header_format = workbook.add_format({
            'bold': True, 
            'bg_color': '#4F81BD', 
            'font_color': 'white'
        })
        for col_num, value in enumerate(self.df.columns):
            worksheet.write(0, col_num, value, header_format)

def main():
    print("AWS Compliance Reporting Tool")
    
    # Input file selection
    input_file = input("Enter input compliance report file (CSV/Excel): ").strip()
    
    try:
        priority_file = input("Enter priority annotations file (default: PowerPipeControls_Annotations.xlsx): ").strip() or "PowerPipeControls_Annotations.xlsx"
        
        # Create reporter and generate report
        reporter = AWSComplianceReporter(input_file, priority_file)
        reporter.generate_comprehensive_report()

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
