
import csv
import os
from datetime import date
from datetime import datetime
from time import sleep
import random
import pickle
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from selenium.common.exceptions import NoSuchElementException

def save_txt(data, file_path):
    with open(file_path, "w", encoding='utf8') as f:
        f.write(data)

def read_txt(file_path):
    with open(file_path, 'r', encoding='utf8') as f:
        content = f.read()
    return content

def save_variable(filename, variable):
    with open(filename, 'wb') as f:
        pickle.dump(variable, f)

def load_variable(filename):
    with open(filename, 'rb') as f:
        loaded_list = pickle.load(f)
    return loaded_list

def update_news_csv_files(file, output_file):
    data = {}
    merged_data = []

    # Read data from the first file
    with open(output_file, 'r', encoding='utf8') as csv_file1:
        reader1 = csv.DictReader(csv_file1)
        for row in reader1:
            time = row['Time']
            publisher = row['Publisher']
            content = row['Contents']  # Additional field 'Name'
            link = row['Link']  # Additional field 'Name'
            data[(time, publisher)] = [content, link]  # Use (time, name) as a dictionary key

    # Read data from the second file and merge
    with open(file, 'r', encoding='utf8') as csv_file2:
        reader2 = csv.DictReader(csv_file2)
        for row in reader2:
            time = row['Time']
            publisher = row['Publisher']
            content = row['Contents']  # Additional field 'Name'
            link = row['Link']  # Additional field 'Name'
            key = (time, publisher)  # Create a key using (time, name)
            if key in data:
                if not(link in data[key][1]):
                    data[(time, publisher+'*')] = [content, link]
            else:
                data[key] = [content, link]

    # Create a sorted list of merged data
    #sorted_data = sorted(data.items(), key=lambda x: x[0], reverse=True)
    sorted_data = sorted(data.items(), key=lambda x: datetime.strptime(x[0][0], '%d-%B-%Y'), reverse=True)

    # Prepare the data for writing to the output file
    for (time, publisher), content in sorted_data:
        merged_data.append({'Time': time, 'Publisher': publisher, 'Contents': content[0], 'Link': content[1]})  # Include 'Name' in the merged data

    # Write the merged data to the output file
    with open(output_file, 'w', newline='', encoding='utf8') as merged_file:
        fieldnames = ['Time', 'Publisher', 'Contents', 'Link']  # Include 'Name' in the fieldnames
        writer = csv.DictWriter(merged_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(merged_data)

    print(f"Merged data saved to {output_file}.")

def update_conv_csv_files(file, output_file):
    data = {}
    merged_data = []

    # Read data from the first file
    with open(output_file, 'r', encoding='utf8') as csv_file1:
        reader1 = csv.DictReader(csv_file1)
        for row in reader1:
            time = row['Time']
            publisher = row['Publisher']
            content = row['Contents']  # Additional field 'Name'
            data[(time, publisher)] = content  # Use (time, name) as a dictionary key

    # Read data from the second file and merge
    with open(file, 'r', encoding='utf8') as csv_file2:
        reader2 = csv.DictReader(csv_file2)
        for row in reader2:
            time = row['Time']
            publisher = row['Publisher']
            content = row['Contents']  # Additional field 'Name'
            key = (time, publisher)  # Create a key using (time, name)
            if key in data:
                if not(content in data[key]):
                    data[key] += ' | ' + content
            else:
                data[key] = content

    # Create a sorted list of merged data
    sorted_data = sorted(data.items(), key=lambda x: datetime.strptime(x[0][0], '%d-%B-%Y'), reverse=True)

    # Prepare the data for writing to the output file
    for (time, publisher), content in sorted_data:
        merged_data.append({'Time': time, 'Publisher': publisher, 'Contents': content})  # Include 'Name' in the merged data

    # Write the merged data to the output file
    with open(output_file, 'w', newline='', encoding='utf8') as merged_file:
        fieldnames = ['Time', 'Publisher', 'Contents']  # Include 'Name' in the fieldnames
        writer = csv.DictWriter(merged_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(merged_data)

    print(f"Merged data saved to {output_file}.")

def contains_word(string, target):
    string_lower = string.lower()  # Convert the string to lowercase
    word_lower = target.lower()  # Convert the word to lowercase

    if word_lower in string_lower:
        return True
    else:
        return False

def split_text(input_text, max_length=10000):
    if len(input_text) <= max_length:
        return [input_text]

    split_strings = []
    start = 0
    end = max_length

    while start < len(input_text):
        split_strings.append(input_text[start:end])
        start = end
        end += max_length

    return split_strings

def read_csv_as_prompt(filepath, target=None, row_limit=None, reverse=False, select=None):
    data = []
    with open(filepath, 'r', encoding='utf8') as file:
        reader = csv.reader(file)
        if target is not None:
            for i, row in enumerate(reader):
                if (i == 0) or (target in row[0]):
                    data.append(row)       
        else:
            for row in reader:
                data.append(row)                    

    if reverse:
        data = [data[0]] + list(reversed(data[1:]))     

    if row_limit is not None:
        data_limited = []
        for i, row in enumerate(data):
            if i < row_limit+1:
                data_limited.append(row)

    data = data_limited         

    if select is not None:
        data_selected = []
        for d_row in data:
            data_selected.append([d_row[ind] for ind in select])
        return '{}'.format(data_selected)
    else:
        return '{}'.format(data)

def read_csv(file_path):
    data_list = []
    with open(file_path, 'r', newline='') as csvfile:
        csvreader = csv.DictReader(csvfile)
        for row in csvreader:
            data_list.append(row)
    return data_list

def save_csv(fieldnames, data, file_path):

    with open(file_path, mode='w', newline='', encoding='utf8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow({fieldnames[i]: row[fieldnames[i]] for i in range(len(fieldnames))})

def check_exists_by_xpath(driver, xpath):
    try:
        driver.find_element_by_xpath(xpath)
    except NoSuchElementException:
        return False
    return True

def check_exists_by_css_selector(driver, selector):
    try:
        driver.find_element_by_css_selector(selector)
    except NoSuchElementException:
        return False
    return True
