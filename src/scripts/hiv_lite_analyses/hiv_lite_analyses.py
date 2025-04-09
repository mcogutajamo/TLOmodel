# Importing necessary libraries
from tlo import Date,Simulation,logging
from tlo.methods import demography, hiv_lite
from tlo.analysis.utils import parse_log_file
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

outputpath = Path('./outputs')
resourcefilepath = Path('./resources')
# Defining the start and end dates
start_date = Date(ts_input=2010, year=1, month=1)
end_date = Date(ts_input=2020, year=1, month=1)
log_config = {
    'filename': "hiv_lite_logs",
    'directory': outputpath,
    'custom_levels': {
        "*": logging.WARNING,
        "tlo.methods.hiv_lite": logging.INFO,
    },
}

# resourcefilepath = Path()
sim = Simulation(start_date=start_date, seed=0, log_config=log_config)
print(resourcefilepath)
# Registering all the required modules for the simulation
sim.register(
    demography.Demography(resourcefilepath=resourcefilepath),
    hiv_lite.HivLite(resourcefilepath=resourcefilepath),
    )

sim.make_initial_population(n=20000)
sim.simulate(end_date=end_date)
logs = parse_log_file(sim.log_filepath)
df = logs['tlo.methods.hiv_lite']['hiv_infection_cases']
df['year'] = df.date.dt.year

print(df)
df = df.set_index('year')
df.drop("date", axis=1, inplace=True)
df.plot.bar(stacked=True)
plt.title('HIV Infection Cases Over Time')
plt.xlabel('Year')
plt.ylabel('Number of Cases')
plt.xticks(rotation=45)
plt.tight_layout()
# Save the plot to a file
plt.savefig('hiv_infection_cases_over_time.png', bbox_inches='tight')
plt.show()