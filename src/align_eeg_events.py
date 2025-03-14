"""""""""""""""
This file takes the gaze tracking data from a Unity Meta Quest Pro build and the EEG data from MindMonitor
to create an aligned version of EEG data and gaze tracking events. This system assumes that EEG data
was sampled at a lower rate than the gaze tracking events.
"""""""""""""""

# Basic Imports
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Custom helper functions
from helpers import timestamp_to_unix_seconds as unix_seconds # Timestamps to Unix Seconds
from helpers import timestamp_to_unix_milliseconds as unix_milliseconds # Timestamps to Unix Milliseconds

def AlignData(
    EEG_FILEPATH:str,
    EVENTS_FILEPATH:str,
    OUTPUT_EVENTS_FILEPATH:str,
    FBANDS = ['Theta', 'Alpha', 'Beta', 'Gamma'],
    ECHANNELS = ['AF7', 'AF8']
):
    
    # === PART 1: EEG DATA ===
    # Read EEG
    eeg_df = pd.read_csv(EEG_FILEPATH)
    # Remove NA rows
    eeg_df = eeg_df[~eeg_df['TimeStamp'].isna()] # Remove rows where timestamp is na
    eeg_df = eeg_df[~eeg_df['Battery'].isna()]   # Remove battery rows - useless
    # TimeStamp => Unix Milliseconds
    eeg_df['unix_ms'] = eeg_df['TimeStamp'].apply(lambda x: int(unix_milliseconds(x)))
    # Remove all TP channels, Accelerometer, Gyroscope, and raw data columns
    eeg_df = eeg_df.loc[:,~eeg_df.columns.str.contains('TP', case=False)]
    eeg_df = eeg_df.loc[:,~eeg_df.columns.str.contains('Accelerometer', case=False)]
    eeg_df = eeg_df.loc[:,~eeg_df.columns.str.contains('Gyro', case=False)]
    eeg_df = eeg_df.loc[:,~eeg_df.columns.str.contains('RAW', case=False)]
    eeg_df = eeg_df.loc[:,~eeg_df.columns.str.contains('AUX', case=False)]
    # Drop useless columns
    eeg_df.drop(columns=['TimeStamp', 'Elements', 'Battery', 'HeadBandOn'], inplace=True)


    # === PART 2: GAZE EVENTS DATA ===
    # Read Events
    events_df = pd.read_csv(EVENTS_FILEPATH)


    # === PART 3: ALIGNMENT
    """
    Need to align `unix_ms` in `events_df` with `unix_ms` from `eeg_df`. We know that `events_df` 
    is likely to be captured at a higher sampling rate. Therefore, it is likely that multiple, 
    consecutive rows in `events_df` will have the same EEG values. That's fine, but we need a 
    system to be able to look at each `unix_ms` in `events_df`, check which `unix_ms` is the 
    closest but smaller to that timestamp, and then join.
    """
    # Sort both dataframes by `unix_ms`
    eeg_df = eeg_df.sort_values(by='unix_ms')
    events_df = events_df.sort_values(by='unix_ms')
    # Use numpy searchsorted to find the closest smaller `unix_ms` from eeg_df for each timestamp in events_df
    indices = np.searchsorted(eeg_df['unix_ms'].values, events_df['unix_ms'].values, side='right') - 1
    # Ensure indices are within bounds
    indices = np.clip(indices, 0, len(eeg_df) - 1)
    # Add the closest smaller `unix_ms`
    events_df['closest_unix_ms'] = eeg_df['unix_ms'].iloc[indices].values
    # Add the corresponding values from eeg_df into events_df
    for band in FBANDS:
        for channel in ECHANNELS:
            colname = f"{band}_{channel}"
            events_df[colname] = 10 ** eeg_df[colname].iloc[indices].values
    # Calculate the max possible value
    maxs = []
    for band in FBANDS:
        for channel in ECHANNELS:
            colname = f"{band}_{channel}"
            max_value = events_df[colname].max()
            maxs.append(max_value)
    global_max = np.max(maxs)
    # Re-calcualte the relative values for each EEG column
    for band in FBANDS:
        for channel in ECHANNELS:
            in_colname = f"{band}_{channel}"
            out_colname = f"Rel_{band}_{channel}"
            events_df[out_colname] = (events_df[in_colname] / global_max) * 100
    # Cast relative values into ints
    for band in FBANDS:
        for channel in ECHANNELS:
            colname = f"Rel_{band}_{channel}"
            events_df[colname] = events_df[colname].astype('int')
    

    # === PART 4: OUTPUTS ===
    # Print output CSV to dictated output filepath without index
    events_df.to_csv(OUTPUT_EVENTS_FILEPATH, index=False)
    


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # REQUIRED
    parser.add_argument('eeg',
                        help='The footage that needs to have the cursor estimated on.')
    parser.add_argument('events',
                        help='The CSV file generated from the vr simulation that contains eye positions')
    parser.add_argument('output',
                        help='The filename of the combined csv file. Adding the csv extension is not necessary')

    # OPTIONAL
    parser.add_argument('-fb','--frequency_bands',
                        help='The list of frequency bands that must be included',
                        nargs='+', 
                        default=['Theta', 'Alpha', 'Beta', 'Gamma'])
    parser.add_argument('-ec','--electrode_channels',
                        help='The list of electrode channels that must be included', 
                        default=['AF7', 'AF8'])

    # Call the function
    args = parser.parse_args()
    AlignData(args.eeg, args.events, args.output, args.frequency_bands, args.electrode_channels)
    
    #EEG_FILEPATH = './samples/eeg_events/eeg.csv'
    #EVENTS_FILEPATH = './samples/eeg_events/events.csv'
    #OUTPUT_EVENTS_FILEPATH = './samples/eeg_events/eeg_events.csv'