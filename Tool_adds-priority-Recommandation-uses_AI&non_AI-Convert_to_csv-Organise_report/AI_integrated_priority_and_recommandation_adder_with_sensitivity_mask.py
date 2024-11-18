import pandas as pd
import os
import shutil
import openai

def generate_recommendation(control_title, description, control_description):
    """
    Use OpenAI's GPT model to generate enhanced recommendations with detailed steps and closest reference links.
    """
    prompt = f"""
    You are a cloud compliance and security expert tasked with providing detailed recommendations for engineers.
    Consider the following control title and description to generate a response:
    
    Control Title: {control_title}
    Description: {description}
    Control Description: {control_description}
    
    Your task is to:
    1. Focus on security priorities when assigning recommendations.
    2. Provide detailed, step-by-step instructions (as many steps as required) to ensure engineers have complete clarity and do not need to search for additional information.
    3. If no exact reference link is available, add the tag "Closest Reference Link" and include a relevant link to guide engineers.

    Format the response strictly as follows:
    Ensure [summary of compliance requirement]. 
    Steps: 
    1. [Detailed step 1 with clear, actionable instructions]
    2. [Detailed step 2 with clear, actionable instructions]
    3. [Additional detailed steps, if necessary, to fully implement the recommendation]
    # REF: [accurate link or "Closest Reference Link: <link>"]
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a cloud compliance and security expert."},
                {"role": "user", "content": prompt}
            ]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error generating recommendation: {e}")
        return "No recommendation available. # REF: Closest Reference Link: Not applicable."

def load_priority_data(priority_file):
    """Load priority data from a given CSV file."""
    if os.path.exists(priority_file):
        return pd.read_csv(priority_file)
    else:
        print(f"Error: The file {priority_file} does not exist.")
        return pd.DataFrame()

def sanitize_report_data(report_df):
    """Remove or mask sensitive data, ensuring only necessary columns are retained."""
    # Define columns that should remain (e.g., control_title, description, control_description)
    necessary_columns = ['control_title', 'description', 'control_description']
    
    # Ensure only the necessary columns are kept
    report_df = report_df[necessary_columns]
    
    # Optionally, mask or redact any sensitive data if necessary
    # e.g., if 'customer_id' or any other sensitive data exists, you can drop them.
    sensitive_columns = ['customer_id', 'account_id', 'email']  # Add any sensitive columns here
    
    # Drop sensitive columns if they exist
    report_df.drop(columns=[col for col in sensitive_columns if col in report_df.columns], inplace=True)
    
    return report_df

def create_priority_files(report_df, reports_folder):
    """Create separate files for each priority level and move them to the reports folder."""
    for priority in [1, 2, 3]:
        priority_df = report_df[report_df['priority'] == priority]
        if not priority_df.empty:
            new_file_name = f"{report_file.split('.')[0]}_priority_{priority}.csv"
            priority_df.to_csv(new_file_name, index=False)
            print(f"Created file: {new_file_name}")
            shutil.move(new_file_name, os.path.join(reports_folder, new_file_name))
            print(f"Moved file to: {os.path.join(reports_folder, new_file_name)}")

def move_report_to_folder(report_file, reports_folder):
    """Move the generated report to the reports folder."""
    shutil.move(report_file, os.path.join(reports_folder, report_file))
    print(f"Moved report to: {os.path.join(reports_folder, report_file)}")

def main(report_file):
    reports_folder = 'reports'
    os.makedirs(reports_folder, exist_ok=True)

    # Load priority data
    priority_files = [
        'optimizer_locked/ex1/1_priority_expe.csv',
        'optimizer_locked/ex1/2_priority_expe.csv',
        'optimizer_locked/ex1/3_priority_expe.csv'
    ]
    
    priority_data = [load_priority_data(file) for file in priority_files]

    # Load report data
    report_df = pd.read_csv(report_file)

    # Sanitize the report data to remove unnecessary or sensitive columns
    report_df = sanitize_report_data(report_df)

    # Initialize new columns for priorities, recommendations, and cost
    report_df['priority'] = None
    report_df['Recommendation Steps/Approach'] = None
    report_df['COST'] = None

    # Match and add priority data
    for priority_df, priority in zip(priority_data, [1, 2, 3]):
        if priority_df.empty:
            continue
        for index, row in priority_df.iterrows():
            control_title = row['control_title']
            recommendation = row.get('Recommendation Steps/Approach', "")
            cost = row.get('COST', "")

            if control_title in report_df['control_title'].values:
                report_df.loc[report_df['control_title'] == control_title, 
                              ['priority', 'Recommendation Steps/Approach', 'COST']] = [priority, recommendation, cost]

    # Handle missing recommendations using AI
    for index, row in report_df.iterrows():
        if pd.isna(row['priority']):
            report_df.at[index, 'priority'] = 3  # Default to priority 3
        if pd.isna(row['Recommendation Steps/Approach']):
            ai_recommendation = generate_recommendation(row['control_title'], row['description'], row['control_description'])
            report_df.at[index, 'Recommendation Steps/Approach'] = ai_recommendation
        if pd.isna(row['COST']):
            report_df.at[index, 'COST'] = "Cost not provided"

    # Save the updated report
    updated_report_file = f"{report_file.split('.')[0]}_with_priorities.csv"
    report_df.to_csv(updated_report_file, index=False)
    print(f"Report saved as {updated_report_file}")

    # Move the report file to the reports folder
    move_report_to_folder(updated_report_file, reports_folder)

    # Prompt for additional file creation
    create_files = input("Do you want to create separate files for priorities 1, 2, and 3? (yes/no): ").strip().lower()
    if create_files == 'yes':
        create_priority_files(report_df, reports_folder)

if __name__ == "__main__":
    report_file = input("Enter the report file name: ").strip()
    main(report_file)
