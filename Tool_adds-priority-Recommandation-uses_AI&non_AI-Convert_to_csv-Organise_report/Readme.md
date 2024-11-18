## Overview

Here's a brief description of each file, explaining what it does and how it contributes to the overall process of integrating columns in the PowerPipe report:

---

### **1. `csv_convertor.py`**  
This file handles the conversion of different file formats into CSV. It ensures that all input files are in a standard format for further processing.

### **2. `centralfile.csv`**  
This is a reference CSV file that may contain central data or the base for the conversion process. It is used as a common input file for various tools in the workflow.

### **3. `optimizer_locked[do_not_touch]`**  
A protected folder containing critical data that should not be altered. This folder stores optimized and pre-processed files for priority assignments and recommendations.

### **4. `ex1/1_priority_expe.csv`, `ex1/2_priority_expe.csv`, `ex1/3_priority_expe.csv`**  
These files contain the pre-defined priority levels (1, 2, and 3) for specific controls. They are used to assign priority ratings and recommendations to each control in the final report.

### **5. `priority_locked`**  
This folder holds sensitive or locked priority data, ensuring that critical information is not accidentally altered or overwritten during processing.

### **6. `priority_seperater_file_tool`**  
This tool separates input data into distinct files based on priority levels, making it easier to organize and filter report data according to urgency and importance.

### **7. `3_contol_pcr.py`**  
A Python script that processes control-related data, possibly focusing on PCR (Process Control Recommendations). It aids in managing controls, ensuring they are aligned with regulatory requirements and recommendations.

### **8. `centralfile.csv` (duplicate)**  
A repeated reference file used across various scripts and tools, ensuring that data is consistently sourced from a central location.

### **9. `input_file_priority.csv`**  
This file contains the input data with controls and priorities. It is used by various scripts to match priority levels and recommendations to controls.

### **10. `PowerPipeControls_PRC.csv`**  
A file containing PowerPipe controls and their associated recommendations. This file is integrated into the final report, alongside the generated priorities and recommendations.

### **11. `priority_filter_tool_level1.py`**  
This script filters the priority data at the first level, helping to segregate critical controls and streamline the reporting process.

### **12. `priority_filter_tool_level2.py`**  
An enhanced filtering tool, refining the priority data further and ensuring that only the most relevant data is included in the final output.

### **13. `reports/report_filter_tool`**  
A directory containing tools used to filter and organize report data. These tools ensure that the final reports meet the required compliance and security standards.

### **14. `1_report_optimizer_filter.py`**  
A script that filters and optimizes reports, refining them for clarity and accuracy before final output.

### **15. `1_report_optimizer_PCR.py`**  
This script optimizes the report related to PCR (Process Control Recommendations), ensuring that all necessary controls and recommendations are presented.

### **16. `report_optimizer.py`**  
This script provides the final optimization of the report, integrating recommendations, priorities, and controls, ensuring everything is presented in the correct format.

### **17. `Al_integrated_priority_and_recommandation_adder_with_sensitivity_mask.py`**  
This is an AI-powered script that integrates priorities and recommendations with the added feature of sanitizing sensitive data (e.g., customer information), ensuring compliance and security before adding recommendations.

### **18. `Al_integrated_priority_and_recommandation_adder.py`**  
A similar AI-based script but without the data sanitization step. It generates recommendations and assigns priorities based on the control data provided.

### **19. `opt_non_Al_priority_recommandation_adder.py`**  
This is a non-AI version that performs the same tasks (adding priorities and recommendations) but does not use AI. It relies on static data or predefined logic to generate the required outputs.

---

### **Purpose in PowerPipe Report Integration:**

These tools and scripts are designed to automate and streamline the process of adding priorities and recommendations to the PowerPipe report. Specifically, the AI-based tools (such as `Al_integrated_priority_and_recommandation_adder.py`) enhance the report by automatically generating detailed, actionable recommendations for engineers, while the non-AI tools (`opt_non_Al_priority_recommandation_adder.py`) provide a more manual, predefined approach.

Together, they ensure that each control is assigned a priority, recommendations are generated, and sensitive data is sanitized before integrating this information into the PowerPipe report. This leads to better-organized, more efficient, and compliant reports that adhere to security and cloud governance standards.

-----------------------------------------------------------------------------------------------------------------
# AI_PR_Adder
This project includes two Python scripts designed to process and enhance cloud security compliance reports by generating prioritized recommendations and costs. Both scripts integrate OpenAI's GPT model for automated recommendation generation, but they differ in handling sensitive data and data sanitization.

### Scripts:

1. **`2_z_AI_integrated_priority_and_recommendation_adder.py`**  
   This script processes a report, assigns priorities, and generates recommendations using OpenAI's GPT model. It does not include data sanitization but is simpler and more direct in its approach.

2. **`3_z_AI_integrated_priority_and_recommendation_adder_with_sensitivity_mask.py`**  
   This script adds a sanitization step to the process, ensuring that sensitive data (e.g., `customer_id`, `account_id`, `email`) is removed before generating recommendations. It also passes both the control title and control description to the AI model for more detailed recommendations. 

---

## 1. `2_z_AI_integrated_priority_and_recommendation_adder.py`

### Description:
This script reads a given compliance report, loads external priority data, and assigns priorities and recommendations to the report based on predefined criteria. Missing recommendations are generated using OpenAI's GPT model. After processing, the report is saved with additional data and can be separated into different files based on priority.

### Key Features:
- **Loads priority data** from external CSV files for three priority levels.
- **Generates recommendations** for missing recommendations using GPT-4.
- **Generates a final report** with priorities, recommendations, and costs.
- **User interaction** to optionally create separate files for each priority.
  
### Requirements:
- Python 3.x
- Libraries: `pandas`, `openai`, `shutil`
  
### Setup:
1. Install the required libraries:
   ```bash
   pip install pandas openai
   ```

2. Place your report and priority files in the appropriate folders:
   - Report file (CSV format) to be processed.
   - Priority files (CSV format) for priorities 1, 2, and 3.

3. Run the script:
   ```bash
   python 2_z_AI_integrated_priority_and_recommendation_adder.py
   ```

### Functionality:
- The script will:
  1. Load the report and external priority files.
  2. Match and assign priorities and recommendations.
  3. Generate missing recommendations using GPT-4.
  4. Save the updated report and optionally create separate files for each priority.

---

## 2. `3_z_AI_integrated_priority_and_recommendation_adder_with_sensitivity_mask.py`

### Description:
This script performs the same basic functionality as Script 2 but includes an additional step to **sanitize the report data** by removing sensitive information. It also provides more detailed recommendations by passing both the control title and control description to the AI model.

### Key Features:
- **Sanitizes data** by removing sensitive columns such as `customer_id`, `account_id`, and `email`.
- **More detailed recommendations** by passing both the control title and description to the AI model.
- **Generates and processes reports** with priorities and recommendations similar to Script 2.

### Requirements:
- Python 3.x
- Libraries: `pandas`, `openai`, `shutil`
  
### Setup:
1. Install the required libraries:
   ```bash
   pip install pandas openai
   ```

2. Place your report and priority files in the appropriate folders:
   - Report file (CSV format) to be processed.
   - Priority files (CSV format) for priorities 1, 2, and 3.

3. Run the script:
   ```bash
   python 3_z_AI_integrated_priority_and_recommendation_adder_with_sensitivity_mask.py
   ```

### Functionality:
- The script will:
  1. Load the report and external priority files.
  2. **Sanitize** the report by removing sensitive columns.
  3. Match and assign priorities and recommendations.
  4. Generate missing recommendations using GPT-4, passing both the control title and description.
  5. Save the updated report and optionally create separate files for each priority.

---

## Comparison between Script 2 and Script 3

| Feature                                       | `2_z_AI_integrated_priority_and_recommendation_adder.py` | `3_z_AI_integrated_priority_and_recommendation_adder_with_sensitivity_mask.py` |
|-----------------------------------------------|---------------------------------------------------------|-------------------------------------------------------------------------------|
| **Data Sanitization**                         | Not included                                              | Sensitive data (e.g., `customer_id`, `account_id`, `email`) is removed       |
| **Recommendation Generation**                 | Based on control title and description                    | Based on control title, description, and control description                  |
| **Data Columns Processed**                    | Processes all available columns in the report            | Removes unnecessary or sensitive columns from the report                       |
| **Primary Use Case**                          | Simple and direct report enhancement                      | Enhanced security and privacy by removing sensitive data before processing   |

---

## Conclusion

- **Script 2** is ideal if you need a **simpler solution** for assigning priorities and generating recommendations.
- **Script 3** is better suited for **secure environments** where privacy and data sanitization are critical, as it removes sensitive columns before processing the report.

Choose the script that best suits your needs based on the level of security and data handling required.

---

## Notes
- Ensure you have access to the OpenAI API for generating recommendations using GPT-4.
- Review and adjust the list of sensitive columns in Script 3 as per your use case (e.g., adding or removing columns based on your report data).
