### Sample Output

The output will display step-by-step feedback to the user, including progress tracking and error handling. Here’s an example of what the output might look like when running the script:

```plaintext
Enter the report file name: sample_report.csv

Error: File optimizer_locked/ex1/1_priority_expe.csv not found.
Error: File optimizer_locked/ex1/2_priority_expe.csv not found.
Error: File optimizer_locked/ex1/3_priority_expe.csv not found.
Processing controls: 100%|███████████████████████████████████████████████| 50/50 [00:02<00:00, 24.99it/s]
Consolidated report saved to: reports/sample_report_with_priorities.csv
Filtered headings file saved as: reports/sample_report_filtered_heading.csv
Do you want to create separate files for each priority? (yes/no): yes
Created priority file: reports/priority_High.csv
Created priority file: reports/priority_Medium.csv
Created priority file: reports/priority_Low.csv
```

### Explanation of Output:

- The program starts by asking for the **report file name**.
- It then loads the **priority files**. If any priority files are missing, it outputs an error message for each missing file.
- The **progress bar** (`tqdm`) tracks the process of handling missing data (e.g., generating recommendations, Terraform scripts).
- After processing, it saves the **consolidated report** and the **filtered headings file**.
- It then asks whether to create separate priority files for **High**, **Medium**, and **Low** priority levels, and creates them if the user confirms.
- Each action gives **feedback** about what has been completed.

---

### README Section for Script

#### Cloud Compliance Report Processor

This script processes cloud compliance reports and generates actionable recommendations and Terraform automation scripts. The script also allows the user to manage priorities and generate separate CSV files based on priority levels.

---

### Features:
- **Input Validation**: Ensures correct input for file names and options (yes/no).
- **API Integration**: Uses OpenAI’s GPT-4 model to generate detailed recommendations and Terraform automation scripts for cloud controls.
- **Progress Tracking**: Shows progress for lengthy operations using a progress bar (`tqdm`).
- **Graceful Interrupt Handling**: Supports interruptions and saves the current progress.
- **File Handling**: Automatically creates and saves priority-specific files for cloud compliance controls.
- **Data Filling**: Automatically fills missing fields in the report with default values or API-generated content.

### Requirements:
- Python 3.x
- Pandas
- OpenAI Python package (`openai`)
- tqdm (for progress bars)
  
You can install the necessary libraries via pip:
```bash
pip install pandas openai tqdm
```

### Setup:

1. Ensure your **OpenAI API key** is set up in the environment variables. If not, you can provide the key directly in the script, but using environment variables is recommended for security.

2. Place your **CSV report files** in the same directory or specify the correct paths when prompted.

3. Optionally, include **priority files** (`1_priority_expe.csv`, `2_priority_expe.csv`, `3_priority_expe.csv`) that contain information about priority mappings for cloud controls.

### Usage:

1. **Run the script**:
   ```bash
   python process_report.py
   ```

2. **Provide the Report File**: 
   The script will ask you for the name of the CSV file that contains the report data.

3. **Priority Files**:
   If priority files are missing, the script will notify you with error messages. These files are optional but can help categorize controls into High, Medium, and Low priority levels.

4. **Generating Recommendations and Terraform Scripts**:
   The script will attempt to fill missing data for each control by generating **recommendations** and **Terraform automation scripts** using the OpenAI API.

5. **Creating Separate Priority Files**:
   After processing the report, the script will ask whether you want to generate separate CSV files for each priority. You can answer with **yes** or **no**:
   - If **yes**, it will create three separate files: `priority_High.csv`, `priority_Medium.csv`, and `priority_Low.csv`.
   - If **no**, it will only create a consolidated report.

6. **Interrupt Handling**:
   If the script is interrupted (e.g., via `Ctrl+C`), it will gracefully save any progress made up until the interruption.

### Sample Output:

```plaintext
Enter the report file name: sample_report.csv

Error: File optimizer_locked/ex1/1_priority_expe.csv not found.
Error: File optimizer_locked/ex1/2_priority_expe.csv not found.
Error: File optimizer_locked/ex1/3_priority_expe.csv not found.
Processing controls: 100%|███████████████████████████████████████████████| 50/50 [00:02<00:00, 24.99it/s]
Consolidated report saved to: reports/sample_report_with_priorities.csv
Filtered headings file saved as: reports/sample_report_filtered_heading.csv
Do you want to create separate files for each priority? (yes/no): yes
Created priority file: reports/priority_High.csv
Created priority file: reports/priority_Medium.csv
Created priority file: reports/priority_Low.csv
```

### Important Notes:
- **Error Handling**: The script provides clear error messages if a file is missing or an invalid input is entered.
- **Custom Prompts**: You can customize the prompts used to generate recommendations and Terraform scripts by modifying the `generate_recommendation()` and `generate_terraform_script()` functions.
- **Performance**: The script is designed to handle large reports efficiently, with progress tracking during lengthy operations.

### License:
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

This README section will help users understand how to use the script and give them a better understanding of what to expect when running the program.
