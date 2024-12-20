import os
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import requests
import chardet
import argparse

# Configure environment variables
API_URL = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
AIPROXY_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIzZjEwMDAyMDBAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.c_ieapzcD3tOD0nRj72aaoR9GTPy1cW-d8xfq3QvpZk"
if not AIPROXY_TOKEN:
    raise ValueError("AIPROXY_TOKEN is not set. Please set it in your environment or in the script.")

# Helper function to interact with the LLM
def ask_llm(prompt):
    try:
        headers = {
            "Authorization": f"Bearer {AIPROXY_TOKEN}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500
        }
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Error in LLM interaction: {e}"

# Function to generate visualizations
def generate_visualizations(data, output_dir):
    image_paths = []

    # Correlation heatmap for numeric data
    numeric_data = data.select_dtypes(include=[np.number])
    if not numeric_data.empty:
        plt.figure(figsize=(8, 6))
        sns.heatmap(numeric_data.corr(), annot=True, cmap="coolwarm", fmt=".2f")
        heatmap_path = os.path.join(output_dir, "correlation_heatmap.png")
        plt.title("Correlation Heatmap")
        plt.savefig(heatmap_path)
        plt.close()
        image_paths.append(heatmap_path)

    # Histogram for each numeric column
    for col in numeric_data.columns:
        plt.figure()
        sns.histplot(data[col].dropna(), kde=True, bins=20)
        plt.title(f"Distribution of {col}")
        hist_path = os.path.join(output_dir, f"{col}_histogram.png")
        plt.savefig(hist_path)
        plt.close()
        image_paths.append(hist_path)

    return image_paths

# Function to load CSV file with encoding detection
def load_csv_with_encoding(csv_file):
    try:
        # Detect encoding
        with open(csv_file, 'rb') as f:
            result = chardet.detect(f.read())
            encoding = result['encoding']

        print(f"Detected file encoding: {encoding}")

        # Load the CSV with detected encoding
        data = pd.read_csv(csv_file, encoding=encoding)
        return data
    except Exception as e:
        print(f"Error loading CSV file: {e}")
        return None

# Main function
def main(csv_file):
    # Load the CSV file
    data = load_csv_with_encoding(csv_file)
    if data is None:
        return

    # Perform generic analysis
    summary = data.describe(include="all")
    missing_values = data.isnull().sum()

    # Send data structure and summary to LLM for insights
    prompt = (
        f"I have a dataset with the following structure:\n"
        f"Columns: {data.columns.tolist()}\n"
        f"First few rows:\n{data.head().to_string()}\n"
        f"Summary statistics:\n{summary.to_string()}\n"
        f"Missing values:\n{missing_values.to_string()}\n"
        "Provide insights, suggested analyses, and potential next steps."
    )
    llm_insights = ask_llm(prompt)

    # Generate visualizations
    output_dir = os.getcwd()
    image_paths = generate_visualizations(data, output_dir)

    # Create README.md
    readme_path = os.path.join(output_dir, "README.md")
    with open(readme_path, "w") as f:
        f.write("# Automated Analysis Report\n\n")
        f.write("## Data Summary\n\n")
        f.write(summary.to_markdown() + "\n\n")
        f.write("## Missing Values\n\n")
        f.write(missing_values.to_markdown() + "\n\n")
        f.write("## Insights from LLM\n\n")
        f.write(llm_insights + "\n\n")
        f.write("## Visualizations\n\n")
        for image_path in image_paths:
            image_name = os.path.basename(image_path)
            f.write(f"![{image_name}]({image_name})\n")

    print(f"Analysis complete. Results saved to {readme_path}.")

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Run automated analysis on a CSV dataset.")
    parser.add_argument("csv_file", help="Path to the dataset CSV file")

    # Parse arguments and call main function
    args = parser.parse_args()
    main(csv_file=args.csv_file)
