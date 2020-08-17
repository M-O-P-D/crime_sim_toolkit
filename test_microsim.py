# %%

import os
import crime_sim_toolkit.microsim as Microsim


simulation_0 = Microsim.Microsimulator()

data_dir = './crime_sim_toolkit/tests/'

simulation_0.load_data(# we specify the seed year, this is the year from which crime probabilities are determined
                       seed_year = 2017,
                       # a string to the directory where your police data is (police data explained above)
                       police_data_dir = os.path.join(data_dir,'testing_data/test_microsim/sample_vic_data_WY2017.csv'),
                       # a string to the directory where the population for the seed year is
                       # this is a synthetic population generated using SPENSER 
                       seed_pop_dir = os.path.join(data_dir,'testing_data/test_microsim/sample_seed_pop.csv'),
                       # the demographic columns for the seed synthetic population
                       spenser_demographic_cols = ['DC1117EW_C_SEX','DC1117EW_C_AGE','DC2101EW_C_ETHPUK11'],
                       # the columns that correspond to the demographic data in the police data
                       police_demographic_cols = ['sex','age','ethnicity']
                       )

print(simulation_0.seed_population.head())

print(simulation_0.crime_data.head())

simulation_0.load_future_pop(# the directory to where synthetic populations are
                             synthetic_population_dir=os.path.join(data_dir, 'testing_data/test_microsim/test_future_pop'),
                             # which years population the user wishes to load
                             year=2019,
                             # the demographic columns within the dataset
                             demographic_cols=['DC1117EW_C_SEX','DC1117EW_C_AGE','DC2101EW_C_ETHPUK11'])

print(simulation_0.future_population.head())

# %%

simulation_0.generate_probability_table()

simulation_0.transition_table.head()
#print(dir(simulation_0))
# %% 

simulation_output = simulation_0.run_simulation(future_population = simulation_0.future_population)

simulation_output.head()



# %%
