#!/usr/bin/env python3

import pandas as pd
import numpy as np
import argparse

def process_data_and_write_summary(norm, raw, tax, tax_c, mixed, output_file):
    # Read the main data file without recognizing any comment characters
    df = pd.read_csv(norm, sep='\t', comment=None, header=0)
    df.rename(columns={df.columns[0]: 'ID'}, inplace=True)
    if 'taxonomy' in df.columns:
        df.drop(columns=['taxonomy'], inplace=True)

    # Read primary taxonomy file
    tax_df = pd.read_csv(tax, sep='\t', comment=None, header=0)
    tax_df.columns = ['ID', 'taxonomy', 'bitscore', 'per_ID', 'per_qcov']
    df = pd.merge(df, tax_df[['ID', 'taxonomy', 'per_ID', 'per_qcov']], on='ID', how='left')

    # Check if tax_c is provided and process it if available
    if tax_c and tax_c.lower() != 'null':
        tax_df_C = pd.read_csv(tax_c, sep='\t', comment=None, header=0)
        tax_df_C.columns = ['ID', 'c_taxonomy', 'confidence']
        df = pd.merge(df, tax_df_C, on='ID', how='left')
        excluded_columns = ['ID', 'taxonomy', 'per_ID', 'per_qcov', 'c_taxonomy', 'confidence', 'sequence']
    else:
        excluded_columns = ['ID', 'taxonomy', 'per_ID', 'per_qcov', 'sequence']

    # Calculate mean abundance using only numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.difference(excluded_columns)
    df['avg_abun'] = df[numeric_cols].mean(axis=1, skipna=True)

    # Check if mixed is provided and process it if available
    if mixed and mixed.lower() != 'null':
        top10_df = pd.read_csv(mixed, sep='\t', comment=None, header=None)
        df['mixed'] = np.where(df['ID'].isin(top10_df.iloc[:, 0]), 'yes', 'no')
    else:
        df['mixed'] = 'no'  # Default value if no mixed file is provided

    # Reorder columns
    if tax_c and tax_c.lower() != 'null':
        df = df.iloc[:, [0] + list(range(len(df.columns) - 8, len(df.columns))) + list(range(1, len(df.columns) - 8))]
    else:
        df = df.iloc[:, [0] + list(range(len(df.columns) - 6, len(df.columns))) + list(range(1, len(df.columns) - 6))]

    # Add row with total raw counts
    rawdf = pd.read_csv(raw, sep='\t', comment=None, header=0)
    rawdf.drop(columns=[rawdf.columns[0], 'taxonomy', 'Sequence'], inplace=True, errors='ignore')
    sums = rawdf.sum()

    if tax_c and tax_c.lower() != 'null':
        nd_columns = ['nd'] * 9
    else:
        nd_columns = ['nd'] * 7

    new_vector = pd.Series(nd_columns + sums.tolist(), index=df.columns)
    df = pd.concat([pd.DataFrame([new_vector]), df], ignore_index=True)

    # Drop the 'mixed' column only if mixed was not provided
    if not mixed or mixed.lower() == 'null':
        df.drop(columns=['mixed'], inplace=True)

    # Write dataframe to the specified output file
    df.to_csv(output_file, sep='\t', index=False, quoting=False)

def main():
    # Create an argument parser
    parser = argparse.ArgumentParser(description='Process data and write summary to file.')

    # Define command-line arguments
    parser.add_argument('norm', type=str, help='Path to the normalized data file')
    parser.add_argument('raw', type=str, help='Path to the raw data file')
    parser.add_argument('tax', type=str, help='Path to the primary taxonomy file')
    parser.add_argument('tax_c', type=str, nargs='?', default=None, help='Path to the classifier taxonomy file (optional, use "NULL" to skip)')
    parser.add_argument('mixed', type=str, nargs='?', default=None, help='Path to the top 10 mixed families file (optional, use "NULL" to skip)')
    parser.add_argument('output_file', type=str, help='Path to the output file')

    # Parse command-line arguments
    args = parser.parse_args()

    # Call the function with the arguments
    process_data_and_write_summary(args.norm, args.raw, args.tax, args.tax_c, args.mixed, args.output_file)

if __name__ == '__main__':
    main()
