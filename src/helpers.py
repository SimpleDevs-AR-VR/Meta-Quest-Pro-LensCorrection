import os
import datetime
import pandas as pd
from IPython.display import display, Markdown, Latex

# Converts the format of a local timestamp into unix seconds. Requires the datetime package
def timestamp_to_unix_seconds(x):
    date_format = datetime.datetime.strptime(x, "%Y-%m-%d %H:%M:%S.%f")
    unix_seconds = datetime.datetime.timestamp(date_format)
    return unix_seconds

# Converts the format of a local timestamp into unix milliseconds. 
# Requires the datatime package, and relies on `timestamp_to_unix_seconds()` function.
def timestamp_to_unix_milliseconds(x):
    unix_seconds = timestamp_to_unix_seconds(x)
    unix_milliseconds = int(unix_seconds * 1000)
    return unix_milliseconds

# Gets immediate child subdirectories
# Src: https://stackoverflow.com/questions/800197/how-to-get-all-of-the-immediate-subdirectories-in-python
def get_immediate_subdirectories(a_dir):
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]

# Get immediate child files
def get_immediate_files(a_dir):
    return [name for name in os.listdir(a_dir)
            if os.path.isfile(os.path.join(a_dir, name))]

# Basic pre-processing of EEG files. Does the following:
# 1. Reads the CSV file into a Pandas Dataframe
# 2. Removes rows where either the timestamp is NA or if the battery is NA
# 3. Converts the TimeStamp column to Unix Milliseconds
# 4. Converts provided electrode-channel columns from log power to power
def process_raw_eeg(
        src:str, 
        parse_na:bool = True,
        convert_log:bool = True,
        frequency_bands = ['Delta', 'Theta', 'Alpha', 'Beta', 'Gamma'],
        electrode_channels = ['AF7', 'AF8', 'TP9', 'TP10']):
    
    df = pd.read_csv(src)       # Read csv file into Dataframe
    if parse_na:                # If told to parse NA files, then it will here.
        df = df[~df['TimeStamp'].isna()]                                                        # Remove rows where timestamp is na
        df = df[~df['Battery'].isna()]                                                          # Remove battery rows - useless
    df['unix_ms'] = df['TimeStamp'].apply(lambda x: int(timestamp_to_unix_milliseconds(x)))     # TimeStamp => Unix Milliseconds
    if convert_log:             # If told to convert from log power to power, does that here
        orig_colnames = []
        new_colnames = []
        for band in frequency_bands:
            for channel in electrode_channels:
                orig_colname = f"{band}_{channel}"
                new_colname = f"{orig_colname}_Power"
                df[new_colname] = 10 ** df[orig_colname]
                orig_colnames.append(orig_colname)
                new_colnames.append(new_colname)
        col_rename_dict = {i:j for i,j in zip(new_colnames,orig_colnames)}
        df.drop(columns=orig_colnames, inplace=True)
        df.rename(columns=col_rename_dict, inplace=True)
    df.drop(columns=['TimeStamp', 'RAW_TP9', 'RAW_AF7', 'RAW_AF8', 'RAW_TP10', 'AUX_RIGHT'], inplace=True)  # Drop unecessary remaining columns
    return df                   # Return dataframe

# Given a Dataframe containing participants, filter out specific pedestrians
def filter_out_participants(df, participant_list, neural_list=None):
    df2 = df[~df['participant'].isin(participant_list)]
    df3 = df2
    if neural_list is not None and len(neural_list)>0:
        df3 = df2[~df2['neural_diagnosis'].isin(neural_list)]
    return df3

# Given a Dataframe containing trial participants and a global participants Dataframe, merge them to get participant details
def merge_participants(df, participants_df):
    return df.merge(participants_df, how='left', left_on='participant', right_on='participant')

# Given a Dataframe of trial data and a global participants Dataframe, both filter and merge
def merge_and_filter_participants(df, participants_df, participant_filter_list, neural_filter_list=None):
    df2 = merge_participants(df, participants_df)
    return filter_out_participants(df2, participant_filter_list, neural_filter_list)

# Given a Dataframe with participants' data already merged in, print out statistics
def participant_stats(df, print_df:bool=True):
    # Ensure to condense all rows into singular rows
    df2 = df.groupby(['participant'], as_index=False).first()

    # Count number of male/female
    display(Markdown('### Sex Statistics:'))
    print(df2['sex'].value_counts())

    # VR experience
    display(Markdown('### VR Statistics:'))
    print(df2['vr_experience'].value_counts(), '\n')
    print(df2['vr_frequency'].value_counts(), '\n')
    print(df2['vr_sickness'].value_counts())

    # Age Distribution
    display(Markdown('### Age Statistics:'))
    ages = df2['age']
    print(ages.value_counts(), '\n')
    print('Age Mean:', ages.mean(numeric_only=True))
    print('Age Median:', ages.median(numeric_only=True))    
    print('Age SD:', ages.std(numeric_only=True))

    # Occurence of corrective vision
    display(Markdown('### Vision Statistics:'))
    print(df2['corrective_vision'].value_counts(), '\n')
    print(df2['vision_condition'].value_counts())
    
    # Occurence of neural conditions
    display(Markdown('### Neural Statistics:'))
    print(df2['neural_diagnosis'].value_counts(), '\n')
    print(df2['neural_condition'].value_counts())

    if print_df:    
        display(Markdown('### Participant Data:'))
        display(df2)