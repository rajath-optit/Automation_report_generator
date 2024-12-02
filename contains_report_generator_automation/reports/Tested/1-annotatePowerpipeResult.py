import pandas as pd
import os
import shutil

def load_priority_data(priority_file):
    """
    Load priority data from a given Excel file.
    """
    if os.path.exists(priority_file):
        return pd.read_excel(priority_file, sheet_name=0)  # Assuming data is in the first sheet
    else:
        print(f"Error: The file {priority_file} does not exist.")
        return None

def create_priority_files(report_df, reports_folder, base_name):
    """
    Create separate files for each priority level and move them to the reports folder.
    """
    for priority in [1, 2, 3]:
        priority_df = report_df[report_df['priority'] == priority]
        if not priority_df.empty:
            # Create a new file name based on priority
            new_file_name = f"{base_name}_priority_{priority}.xlsx"
            priority_df.to_excel(new_file_name, index=False)
            print(f"Created file: {new_file_name}")
            # Move the created file to the reports folder
            shutil.move(new_file_name, os.path.join(reports_folder, new_file_name))
            print(f"Moved file to: {os.path.join(reports_folder, new_file_name)}")

def move_report_to_folder(report_file, reports_folder):
    """
    Move the generated report to the reports folder.
    """
    shutil.move(report_file, os.path.join(reports_folder, report_file))
    print(f"Moved report to: {os.path.join(reports_folder, report_file)}")

def load_report_file(report_file):
    """
    Load the report file, handling both CSV and Excel formats.
    """
    file_extension = os.path.splitext(report_file)[1].lower()
    if file_extension == '.csv':
        return pd.read_csv(report_file)
    elif file_extension in ['.xls', '.xlsx']:
        return pd.read_excel(report_file)
    else:
        raise ValueError(f"Unsupported file format: {file_extension}. Please provide a .csv or .xlsx file.")

def main():
    # Define the reports folder
    reports_folder = 'reports'
    os.makedirs(reports_folder, exist_ok=True)  # Create the reports folder if it doesn't exist

    # Load priority data
    priority_file = 'PowerPipeControls_Annotations.xlsx'
    priority_data = load_priority_data(priority_file)

    if priority_data is None:
        print("Priority data file could not be loaded. Exiting.")
        return

    # Load report data
    report_file = input("Enter path to the Powerpipe report file along with extension: ").strip()
    if not os.path.exists(report_file):
        print(f"Error: The file {report_file} does not exist. Exiting.")
        return

    try:
        report_df = load_report_file(report_file)
    except ValueError as e:
        print(e)
        return

    # Initialize new columns for priorities, recommendations, and cost
    report_df['priority'] = None
    report_df['Recommendation Steps/Approach'] = None
    report_df['COST'] = None

    # Match and enrich report data based on control_title
    for index, row in priority_data.iterrows():
        control_title = row['control_title']
        recommendation = row.get('Recommendation Steps/Approach', 'No recommendation available.')
        cost = row.get('COST', 'Cost not provided')
        priority = int(row['priority'][-1]) if isinstance(row['priority'], str) and row['priority'].startswith('P') else None
        
        # Update report where control_title matches
        if control_title in report_df['control_title'].values:
            report_df.loc[report_df['control_title'] == control_title, 
                          ['priority', 'Recommendation Steps/Approach', 'COST']] = [priority, recommendation, cost]

    # Fill missing recommendations with default text
    report_df['Recommendation Steps/Approach'].fillna('No recommendation available.', inplace=True)
    report_df['COST'].fillna('Cost not provided', inplace=True)

    # Save the updated report
    base_name = report_file.split('.')[0]
    updated_report_file = f"{base_name}_annotated.xlsx"
    report_df.to_excel(updated_report_file, index=False)
    print(f"Report saved as {updated_report_file}")

    # Move the report file to the reports folder
    move_report_to_folder(updated_report_file, reports_folder)

    # Prompt for additional file creation
    create_files = input("Do you want to create separate files for priorities 1, 2, and 3? (yes/no): ").strip().lower()
    if create_files == 'yes':
        create_priority_files(report_df, reports_folder, base_name)

if __name__ == "__main__":
    main()
