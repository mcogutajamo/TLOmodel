# This is a Python script that implements a simplified version of the HIV model
from tlo import Module, Types,Parameter, Property, Population, Simulation
from tlo.methods import Metadata
from pathlib import Path
import pandas as pd
from tlo.events import RegularEvent, PopulationScopeEventMixin
class HivLite(Module):
    def __init__(self, resourcefilepath: str | Path = None):
        super().__init__()
    # Define metadata
    METADATA = {
        Metadata.DISEASE_MODULE
    }

    # Define the parameters for the HIV module
    PARAMETERS = {
        'infection_rate': Parameter(Types.REAL, description='Rate of HIV infection'),
        'aids_progression_rate': Parameter(Types.REAL, description='Rate of progression to AIDS'),
    }
    PROPERTIES = {
        'hl_hiv_status': Property(Types.STRING, description='HIV status of the individual'),
        'hl_hiv_infection_date': Property(Types.DATE, description='Date of HIV infection'),
    }

    def read_parameters(self, data_folder: str | Path) -> None:
        """ read and assign values to your parameters"""
        param= self.parameters
        param['infection_rate'] = 0.05
        param['aids_progression_rate'] = 0.1

    def initialise_population(self, population: Population)-> None:
        """ Initialise the HIV characteristics of the population"""
        df= population.props
        df.loc[df.is_alive, 'hl_hiv_status'] = 'negative'   # Set initial HIV status to negative
        df.loc[df.is_alive, 'hl_hiv_infection_date'] = pd.NaT  # Set to NaT for individuals who are not infected
        
        print (f'hiv status before event {df}')

    def initialise_simulation(self, sim: Simulation)-> None:
        """ Include all events here"""
        sim.schedule_event(HivInfectionEvent(self),sim.date+ pd.DateOffset(months=1))  # Schedule the first infection event to one month later
        


class HivInfectionEvent(RegularEvent, PopulationScopeEventMixin):
    """ Event to handle HIV infection """
    def __init__(self, module: Module):
        super().__init__(module, frequency=pd.DateOffset(months=1))

    def apply(self, target):
        """"Include all the activities here"""
        #Print the default dataframe
        print(f'the population dataframe is {self.module.sim.population.props}')
    