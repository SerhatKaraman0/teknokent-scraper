#!/usr/bin/env python3
"""
Script to merge all CSV files from teknokent scraper outputs into a single file.
"""

import pandas as pd
import os
import glob
from pathlib import Path

def merge_csv_files():
    """Merge all CSV files from the outputs directory into a single file."""
    
    # Base directory containing all the CSV files
    base_dir = "/Users/user/Desktop/Projects/teknokent_scraper/teknokent_scraper/teknokent_scraper/outputs"
    
    # Find all CSV files recursively
    csv_files = glob.glob(os.path.join(base_dir, "**/*.csv"), recursive=True)
    
    print(f"Found {len(csv_files)} CSV files to merge:")
    for file in csv_files:
        print(f"  - {file}")
    
    # List to store all dataframes
    all_dataframes = []
    
    # Read each CSV file and add a source column to track origin
    for csv_file in csv_files:
        try:
            # Get the directory name to use as a source identifier
            source_name = os.path.basename(os.path.dirname(csv_file))
            
            # Read the CSV file
            df = pd.read_csv(csv_file)
            
            # Add a source column to track which teknokent this data came from
            df['source_teknokent'] = source_name
            
            print(f"Loaded {len(df)} rows from {source_name}")
            all_dataframes.append(df)
            
        except Exception as e:
            print(f"Error reading {csv_file}: {e}")
    
    if all_dataframes:
        # Merge all dataframes
        merged_df = pd.concat(all_dataframes, ignore_index=True)
        
        # Remove any duplicate rows based on company name and location
        print(f"\nTotal rows before deduplication: {len(merged_df)}")
        merged_df = merged_df.drop_duplicates(subset=['company_name', 'company_location'], keep='first')
        print(f"Total rows after deduplication: {len(merged_df)}")
        
        # Sort by source_teknokent and company_name for better organization
        merged_df = merged_df.sort_values(['source_teknokent', 'company_name'])
        
        # Save the merged file
        output_file = os.path.join(base_dir, "merged_all_teknokent_companies.csv")
        merged_df.to_csv(output_file, index=False)
        
        print(f"\nMerged CSV saved to: {output_file}")
        print(f"Total unique companies: {len(merged_df)}")
        
        # Show summary by teknokent
        print("\nSummary by Teknokent:")
        summary = merged_df.groupby('source_teknokent').size().sort_values(ascending=False)
        for teknokent, count in summary.items():
            print(f"  {teknokent}: {count} companies")
            
        return output_file
    else:
        print("No CSV files could be read successfully.")
        return None

if __name__ == "__main__":
    merge_csv_files()