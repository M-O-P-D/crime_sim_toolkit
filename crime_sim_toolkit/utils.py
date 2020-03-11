"""
Utility functions for general use
"""

import pandas as pd
import numpy as np
from calendar import monthrange
import pkg_resources

resource_package = 'crime_sim_toolkit'

def counts_to_reports(counts_frame):
    """
    Function for converting Pandas dataframes of aggregated crime counts per timeframe (day/week)
    per LSOA per crime type into a pandas dataframe of individual reports
    """

    pri_data = validate_datetime(counts_frame)

    if 'Week' in pri_data.columns:
        time_res = 'Week'
    else:
        time_res = 'datetime'

    # first drop all instances where Counts == 0

    pri_data = pri_data[pri_data.Counts != 0]

    # generate a randomly allocated unique crime number
    # allocated per loop or cumulatively at the end based on final len?
    # take a row with count value > 0 return number of new rows with details as count value

    # empty list for rows to be added to for eventual concatenation
    concat_stack = []
    UID_col = []

    for idx, row in pri_data.iterrows():

        for count in range(row.Counts):

            if time_res == 'Week':

                concat_stack.append(row.loc[['datetime',time_res,'Crime_type','LSOA_code']].values)

                col_names = ['datetime',time_res,'Crime_type','LSOA_code']

                UID = str(row['LSOA_code'][:5]).strip() +\
                      str(row['datetime'].day).strip() +\
                      str(row['datetime'].month).strip() +\
                      str(row['Crime_type'][:2]).strip().upper() +\
                      str(count).strip()

                UID_col.append(UID)

            else:

                concat_stack.append(row.loc[['datetime','Crime_type','LSOA_code']].values)

                col_names = ['datetime','Crime_type','LSOA_code']

                UID = str(row['LSOA_code'][:5]).strip() +\
                      str(row['datetime'].day).strip() +\
                      str(row['datetime'].month).strip() +\
                      str(row['Crime_type'][:2]).strip().upper() +\
                      str(count).strip()

                UID_col.append(UID)


    reports_frame = pd.DataFrame(data=np.stack(concat_stack),
                 index=range(len(concat_stack)),
                 columns=col_names
                 )

    # create unique IDs from fragments of data
    reports_frame['UID'] = UID_col

    # reorder columns for ABM
    reports_frame = reports_frame[['UID'] + col_names]

    return reports_frame

def populate_offence(crime_frame):
    """
    Function for adding in more specific offense descriptions based on Police
    Recorded Crime Data tables.

    Profiled run on test data:
    # ver2
    CPU times: user 2min 19s, sys: 2.09 s, total: 2min 21s
    Wall time: 2min 21s
    """

    # format columns to remove spaces
    crime_frame.columns = crime_frame.columns.str.replace(' ','_')

    # initially load reference tables
    LSOA_pf_reference = pd.read_csv(pkg_resources.resource_filename(resource_package, 'src/LSOA_data/PoliceforceLSOA.csv'),
                                    index_col=0)

    descriptions_reference = pd.read_csv(pkg_resources.resource_filename(resource_package, 'src/prc-pfa-201718_new.csv'),
                             index_col=0)

    # test if the first instance in LSOA code is within police force frame?
    # if value is not in the list of police forces from reference frame
    # add police force column
    if crime_frame['LSOA_code'].unique().tolist()[0] not in LSOA_pf_reference.Police_force.tolist():

        crime_frame['Police_force'] = crime_frame.LSOA_code.map(lambda x: LSOA_pf_reference[LSOA_pf_reference['LSOA Code'].isin([x])].Police_force.tolist()[0])

    # else convert LSOA_code to Police_force column
    else:

        crime_frame['Police_force'] = crime_frame['LSOA_code']

    list_of_slices = []

    # for each police force within the passed crime reports data frame
    for police_force in crime_frame.Police_force.unique():

        # slice a frame for data in a specific police force
        shortened_frame = crime_frame[crime_frame['Police_force'] == police_force].copy()

        # create sliced frame of crime description proportions by police force
        descriptions_slice = descriptions_reference[descriptions_reference['Force_Name'].isin([police_force])]

        # create pivot table for random allocating weighting
        # this creates a table of offence description percentages for each Policeuk_Cat
        pivoted_slice = ((descriptions_slice.groupby(['Policeuk_Cat','Offence_Group','Offence_Description'])['Number_of_Offences'].sum() \
        / descriptions_slice.groupby(['Policeuk_Cat'])['Number_of_Offences'].sum())).reset_index()

        # add a Crime_description column that is generated by taking each Crime_type (Policeuk_cat)
        # and using np.random.choice to randomly allocate a Crime description for the given Crime_type
        # weighted by the percentages in the pivot table created above
        shortened_frame['Crime_description'] = shortened_frame['Crime_type'].map(lambda x: np.random.choice(
                                                                                 # specify list of choices of crime_descriptions for given crime_cat
                                                                                 pivoted_slice[pivoted_slice.Policeuk_Cat.str.lower().isin([x.lower()])].Offence_Description.tolist(),
                                                                                 # make one choice
                                                                                 1,
                                                                                 # specify weights for selecting Crime_description
                                                                                 # if there isn't a match between two dataframes (for anti-social behaviour)
                                                                                 # just use Crime_type as Crime Description
                                                                                 # outcome: all Anti-social behaviour cases have that as crime description
                                                                                 p = pivoted_slice[pivoted_slice.Policeuk_Cat.str.lower().isin([x.lower()])].Number_of_Offences.tolist())[0] if len(pivoted_slice[pivoted_slice.Policeuk_Cat.str.lower().isin([x.lower()])]) > 0 else x)

        shortened_frame.Crime_description = shortened_frame.Crime_description.str.lower()

        list_of_slices.append(shortened_frame)

    populated_frame = pd.concat(list_of_slices)

    return populated_frame


def validate_datetime(passed_dataframe):
    """
    Utility function to ensure passed dataframes datetime column is configured as
    datetime dtype.
    """

    try:

        if np.dtype('datetime64[ns]') not in passed_dataframe.dtypes:

            passed_dataframe['datetime'] = passed_dataframe['datetime'].apply(pd.to_datetime)

            print('Datetime column configured.')

    except KeyError:
        print('No datetime column detected. Dataframe unaltered.')

    validated_date_frame = passed_dataframe.copy()

    return validated_date_frame

def sample_perturb(counts_frame, crime_type, pct_change):
    """
    Utility function to increase the counts of specific crime types
    after sampling by a given percentage.
    Inputs : counts_frame, the counts of crime dataframe produced by sampler
             crime_type, string of crime type that we want to increase
                         counts for
             pct_change, the percentage change (negative or positive) of crime
                         counts desired.
    Outputs: new_counts_frame, identical dataframe passed but with increased
                               crime counts for specific crime type
    """

    new_counts_frame = counts_frame.copy()

    mask = (new_counts_frame.Crime_type == crime_type)

    mask_frame = new_counts_frame[mask]

    new_counts_frame.loc[mask,'Counts'] = round(mask_frame.Counts * pct_change, 0)

    # need to set new masked data to int
    new_counts_frame['Counts'] = new_counts_frame['Counts'].astype(int)

    return new_counts_frame

def days_in_month_dict(dataframe):
    """
    Simple function that takes a dataframe with Month column (as default in police uk data)
    and returns a dictionary of Month (year-mon format) with number of days in that month
    """

    date_lst = []

    days_in_month_lst = []

    date_dict = dict()

    for date in dataframe['Month'].unique().tolist():

        year = date.split('-')[0]

        month = date.split('-')[1]

        monthdays = monthrange(int(year), int(month))[1]

        date_lst.append(date)

        days_in_month_lst.append(monthdays)

        date_dict[date] = monthdays

    return date_dict
