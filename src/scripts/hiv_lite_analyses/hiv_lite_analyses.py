# Importing necessary libraries
from tlo import Date,Simulation
from tlo.methods import demography, hiv_lite
from pathlib import Path
import pandas as pd

outputpath = Path('./outputs')
resourcefilepath = Path('./resources')
# Defining the start and end dates
start_date = Date(ts_input=2010, year=1, month=1)
end_date = Date(ts_input=2012, year=1, month=1)

# resourcefilepath = Path()
sim = Simulation(start_date=start_date, seed=0, log_config=None)
print(resourcefilepath)
# Registering all the required modules for the simulation
sim.register(
    demography.Demography(resourcefilepath=resourcefilepath),
    hiv_lite.HivLite(resourcefilepath=resourcefilepath),
    )

sim.make_initial_population(n=1000)
sim.simulate(end_date=end_date)