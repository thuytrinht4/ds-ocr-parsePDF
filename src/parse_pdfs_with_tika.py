#!/usr/bin/env python
# -*- coding: utf-8 -*-
import csv
import glob
import os
import re
import sys
import pandas as pd
import matplotlib
matplotlib.use('AGG')
import matplotlib.pyplot as plt
pd.options.display.mpl_style = 'default'

from tika import parser

input_path = "/data"

def create_df(pdf_content, content_pattern, line_pattern, column_headings):
    """Create a Pandas DataFrame from lines of text in a PDF.

    Arguments:
    pdf_content -- all of the text Tika parses from the PDF
    content_pattern -- a pattern that identifies the set of lines
    that will become rows in the DataFrame
    line_pattern -- a pattern that separates the agency name or revenue source
    from the dollar values in the line
    column_headings -- the list of column headings for the DataFrame
    """
    list_of_line_items = []
    # Grab all of the lines of text that match the pattern in content_pattern
    content_match = re.search(content_pattern, pdf_content, re.DOTALL)
    # group(1): only keep the lines between the parentheses in the pattern
    content_match = content_match.group(1)
    # Split on newlines to create a sequence of strings
    content_match = content_match.split('\n')
    # Iterate over each line
    for item in content_match:
        # Create a list to hold the values in the line we want to retain
        line_items = []
        # Use line_pattern to separate the agency name or revenue source
        # from the dollar values in the line
        line_match = re.search(line_pattern, item, re.I)
        # Grab the agency name or revenue source, strip whitespace, and remove commas
        # group(1): the value inside the first set of parentheses in line_pattern
        agency = line_match.group(1).strip().replace(',', '')
        # Grab the dollar values, strip whitespace, replace dashes with 0.0, and remove $s and commas
        # group(2): the value inside the second set of parentheses in line_pattern
        values_string = line_match.group(2).strip().\
        replace('- ', '0.0 ').replace('$', '').replace(',', '')
        # Split on whitespace and convert to float to create a sequence of floating-point numbers
        values = map(float, values_string.split())
        # Append the agency name or revenue source into line_items
        line_items.append(agency)
        # Extend the floating-point numbers into line_items so line_items remains one list
        line_items.extend(values)
        # Append line_item's values into list_of_line_items to generate a list of lists;
        # all of the lines that will become rows in the DataFrame
        list_of_line_items.append(line_items)
    # Convert the list of lists into a Pandas DataFrame and specify the column headings
    df = pd.DataFrame(list_of_line_items, columns=column_headings)
    return df

def create_plot(df, column_to_sort, x_val, y_val, type_of_plot, plot_size, the_title):
    """Create a plot from data in a Pandas DataFrame.

    Arguments:
    df -- A Pandas DataFrame
    column_to_sort -- The column of values to sort
    x_val -- The variable displayed on the x-axis
    y_val -- The variable displayed on the y-axis
    type_of_plot -- A string that specifies the type of plot to create
    plot_size -- A list of 2 numbers that specifies the plot's size
    the_title -- A string to serve as the plot's title
    """
    # Create a figure and an axis for the plot
    fig, ax = plt.subplots()
    # Sort the values in the column_to_sort column in the DataFrame
    df = df.sort_values(by=column_to_sort)
    # Create a plot with x_val on the x-axis and y_val on the y-axis
    # type_of_plot specifies the type of plot to create, plot_size
    # specifies the size of the plot, and the_title specifies the title
    df.plot(ax=ax, x=x_val, y=y_val, kind=type_of_plot, figsize=plot_size, title=the_title)
    # Adjust the plot's parameters so everything fits in the figure area
    plt.tight_layout()
    # Create a PNG filename based on the plot's title, replace spaces with underscores
    pngfile = the_title.replace(' ', '_') + '.png'
    # Save the plot in the current folder
    plt.savefig(pngfile)

# In the Expenditures table, grab all of the lines between Totals and General Government
expenditures_pattern = r'Totals\n+(Legislative, Judicial, Executive.*?)\nGeneral Government:'

# In the Revenues table, grab all of the lines between 2015-16 and either Subtotal or Total
revenues_pattern = r'\d{4}-\d{2}\n(Personal Income Tax.*?)\n +[Subtotal|Total]'

# For the expenditures, grab the agency name in the first set of parentheses
# and grab the dollar values in the second set of parentheses
expense_pattern = r'(K-12 Education|[a-z,& -]+)([$,0-9 -]+)'

# For the revenues, grab the revenue source in the first set of parentheses
# and grab the dollar values in the second set of parentheses
revenue_pattern = r'([a-z, ]+)([$,0-9 -]+)'

# Column headings for the Expenditures DataFrames
expense_columns = ['Agency', 'General', 'Special', 'Bond', 'Totals']

# Column headings for the Revenues DataFrames
revenue_columns = ['Source', 'General', 'Special', 'Total', 'Change']

# Iterate over all PDF files in the folder and process each one in turn
for input_file in glob.glob(os.path.join(input_path, '*.pdf')):
    # Grab the PDF's file name
    filename = os.path.basename(input_file)
    print(filename)
    # Remove .pdf from the filename so we can use it as the name of the plot and PNG
    plotname = filename.strip('.pdf')

    # Use Tika to parse the PDF
    parsedPDF = parser.from_file(input_file)
    # Extract the text content from the parsed PDF
    pdf = parsedPDF["content"]
    # Convert double newlines into single newlines
    pdf = pdf.replace('\n\n', '\n')

    # Create a Pandas DataFrame from the lines of text in the Expenditures table in the PDF
    expense_df = create_df(pdf, expenditures_pattern, expense_pattern, expense_columns)
    # Create a Pandas DataFrame from the lines of text in the Revenues table in the PDF
    revenue_df = create_df(pdf, revenues_pattern, revenue_pattern, revenue_columns)
    print(expense_df)
    print(revenue_df)

    # Print the total expenditures and total revenues in the budget to the screen
    print("Total Expenditures: {}".format(expense_df["Totals"].sum()))
    print("Total Revenues: {}\n".format(revenue_df["Total"].sum()))

    # Create and save a horizontal bar plot based on the data in the Expenditures table
    create_plot(expense_df, "Totals", ["Agency"], ["Totals"], 'barh', [20,10], \
    plotname+"Expenditures")
    # Create and save a horizontal bar plot based on the data in the Revenues table
    create_plot(revenue_df, "Total", ["Source"], ["Total"], 'barh', [20,10], \
    plotname+"Revenues")