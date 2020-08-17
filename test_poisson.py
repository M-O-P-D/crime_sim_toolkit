# %%

import os

import crime_sim_toolkit.poisson_sim as Poisson_sim


sim_week = Poisson_sim.Poisson_sim(
                               # because of the data passed these are the LA we want
#                               LA_names=['Kirklees','Calderdale','Leeds','Bradford','Wakefield'], 
                               LA_names=['Bradford'], 
                               directory='./sample_data',
                               # this can either be Day or Week
                               timeframe='Day',
                               aggregate=True)
sim_week.data.head()

sim_week.data.to_csv("Bradford_poisson_sim.csv")


# %%

import scipy

scipy.stats.poisson(10).rvs(100)


# %%
# %%