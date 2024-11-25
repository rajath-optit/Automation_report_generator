import pandas as pd
import os
from datetime import datetime

def create_final_optimized_report(report_file, final_report_file):
    # Detect the file extension and read accordingly
    if report_file.endswith('.csv'):
        report_df = pd.read_csv(report_file)
    elif report_file.endswith(('.xls', '.xlsx')):
        report_df = pd.read_excel(report_file)
    else:
        raise ValueError("Unsupported file format. Please provide a CSV or Excel file.")
    
    # Columns that should always be included
    required_columns = [
        'title', 'control_title', 'control_description', 'region', 'account_id',
        'resource', 'reason', 'description', 'priority', 'Recommendation Steps/Approach', 'status'
    ]
    
    # Create the final DataFrame with only the necessary columns
    # Select only the columns present in the report file to avoid errors
    final_columns = [col for col in required_columns if col in report_df.columns]
    final_report_df = report_df[final_columns]
    
    # Save the final optimized report
    final_report_df.to_csv(final_report_file, index=False)
    print(f"Final optimized report saved as {final_report_file}")

def main():
    # Ask the user to input the report file name
    report_file = input("Enter the report file name (e.g., aws_compliance_benchmark_all_controls_benchmark_vested_with_priorities.csv): ").strip()
    
    # Get the input file's base name (without path) and extension
    base_name = os.path.splitext(os.path.basename(report_file))[0]
    
    # Create a unique file name using a timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_file_name = f"{base_name}_final_optimized_report_{timestamp}.csv"
    
    # Set the output path to the reports directory
    reports_directory = os.path.dirname(os.path.abspath(__file__))  # Get the current script's directory
    final_report_file = os.path.join(reports_directory, unique_file_name)

    # Ask if the user wants to create the final report
    create_report = input("Do you want to create the final optimized report? (yes/no): ").strip().lower()
    if create_report == 'yes':
        try:
            create_final_optimized_report(report_file, final_report_file)
        except ValueError as e:
            print(e)
        except Exception as e:
            print(f"An error occurred: {e}")
    else:
        print("Final report creation skipped.")

if __name__ == "__main__":
    main()
