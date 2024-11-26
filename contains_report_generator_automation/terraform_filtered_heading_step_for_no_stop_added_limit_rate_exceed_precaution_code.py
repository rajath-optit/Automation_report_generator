import os
import shutil
import pandas as pd
import openai
import time  # Import the time module for adding delays

# Set your OpenAI API key directly
openai.api_key = "add key"

def generate_recommendation(title, control_title, control_description):
    """
    Use OpenAI's GPT model to generate enhanced recommendations with detailed steps and closest reference links.
    """
    prompt = f"""
    You are a cloud compliance and security expert tasked with providing detailed recommendations for engineers.
    Consider the following title, control title, and description to generate a response:

    Title: {title}
    Control Title: {control_title}
    Description: {control_description}

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

def generate_terraform_script(title, control_title, control_description):
    """
    Use OpenAI's GPT model to generate Terraform automation scripts.
    """
    prompt = f"""
    You are a Terraform expert skilled in automating cloud infrastructure fixes.
    Based on the following information, generate Terraform code snippets that automate the remediation:

    Title: {title}
    Control Title: {control_title}
    Description: {control_description}

    Your task is to:
    1. Generate Terraform scripts that can be used to remediate the described issue.
    2. Provide appropriate comments to explain each part of the script.
    3. Ensure the script is complete and ready to use.

    Example format:
    ```
    resource "aws_service" "example" {{
        property_1 = "value_1"
        property_2 = "value_2"
        # Additional explanation of the code
    }}
    ```
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a Terraform automation expert."},
                {"role": "user", "content": prompt}
            ]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error generating Terraform script: {e}")
        return "No Terraform script available."

def save_progress(report_df, filename):
    """Save the current progress to a file."""
    filename = f"{filename.split('.')[0]}_in_progress.csv"
    report_df.to_csv(filename, index=False)
    print(f"Progress saved to {filename}")

def main(report_file):
    # Load report data
    report_df = pd.read_csv(report_file)

    # Initialize new columns for priorities, recommendations, cost, and Terraform script
    if 'priority' not in report_df.columns:
        report_df['priority'] = None
    if 'Recommendation Steps/Approach' not in report_df.columns:
        report_df['Recommendation Steps/Approach'] = None
    if 'COST' not in report_df.columns:
        report_df['COST'] = None
    if 'Terraform Automation Script' not in report_df.columns:
        report_df['Terraform Automation Script'] = None

    try:
        for index, row in report_df.iterrows():
            # Check if user wants to stop the process
            try:
                with open('stop_signal.txt', 'r') as f:
                    if f.read().strip().lower() == 'end':
                        print("\nProcessing interrupted by user.")
                        save_progress(report_df, report_file)
                        return
            except FileNotFoundError:
                pass  # If no stop_signal.txt, continue processing

            # Assign default values and generate recommendations/Terraform scripts if missing
            if pd.isna(row['priority']):
                report_df.at[index, 'priority'] = 3  # Default to priority 3
            if pd.isna(row['Recommendation Steps/Approach']):
                print(f"Generating recommendation for {row['control_title']}...")
                ai_recommendation = generate_recommendation(
                    row['title'], 
                    row['control_title'], 
                    row['control_description']
                )
                print(f"Generated recommendation: {ai_recommendation}")
                report_df.at[index, 'Recommendation Steps/Approach'] = ai_recommendation
                time.sleep(1)  # Add a delay of 1 second to comply with rate limits
            if pd.isna(row['Terraform Automation Script']):
                print(f"Generating Terraform script for {row['control_title']}...")
                terraform_script = generate_terraform_script(
                    row['title'], 
                    row['control_title'], 
                    row['control_description']
                )
                print(f"Generated Terraform script: {terraform_script}")
                report_df.at[index, 'Terraform Automation Script'] = terraform_script
                time.sleep(1)  # Add a delay of 1 second to comply with rate limits
            if pd.isna(row['COST']):
                report_df.at[index, 'COST'] = "Cost not provided"

    except Exception as e:
        print(f"Error during processing: {e}")
        save_progress(report_df, report_file)
        return

    # Save the updated report
    updated_report_file = f"{report_file.split('.')[0]}_with_priorities.csv"
    report_df.to_csv(updated_report_file, index=False)
    print(f"Report saved as {updated_report_file}")

    # Prompt to create separate files for each priority
    create_files = input("Do you want to create separate files for priorities 1, 2, and 3? (yes/no): ").strip().lower()
    if create_files == 'yes':
        create_priority_files(report_df, updated_report_file)

def create_priority_files(report_df, report_file):
    """Create separate files for each priority level."""
    reports_folder = 'reports'
    os.makedirs(reports_folder, exist_ok=True)
    
    # Map numeric priority to text labels
    priority_mapping = {1: "High", 2: "Medium", 3: "Low"}
    report_df['priority'] = report_df['priority'].map(priority_mapping)
    
    # Create separate files for each priority
    for priority, label in priority_mapping.items():
        priority_df = report_df[report_df['priority'] == label]
        if not priority_df.empty:
            new_file_name = f"{report_file.split('.')[0]}_priority_{label}.csv"
            priority_df.to_csv(new_file_name, index=False)
            print(f"Created file: {new_file_name}")
            shutil.move(new_file_name, os.path.join(reports_folder, new_file_name))
            print(f"Moved file to: {os.path.join(reports_folder, new_file_name)}")

if __name__ == "__main__":
    report_file = input("Enter the report file name: ").strip()
    main(report_file)
