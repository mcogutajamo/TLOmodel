# This is a Python script that implements a simplified version of the HIV model
from tlo import Module, Types,Parameter, Property, Population, Simulation, logging
from tlo.methods import Metadata
from pathlib import Path
import pandas as pd
from tlo.events import RegularEvent, PopulationScopeEventMixin

# Logging configuration
logger = logging.getLogger(__name__)
# Set the logging level to INFO
logger.setLevel(logging.INFO)

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
        'art_coverage': Parameter(Types.REAL, description='Rate of ART coverage'),
    }
    PROPERTIES = {
        'hl_hiv_status': Property(Types.STRING, description='HIV status of the individual'),
        'hl_on_art': Property(Types.BOOL, description='whether the individual is on ART or not'),
        'hl_hiv_infection_date': Property(Types.DATE, description='Date of HIV infection'),
        'hl_aids_status': Property(Types.STRING, description='AIDS status of the individual'),
        'hl_aids_date': Property(Types.DATE, description='Date of AIDS diagnosis'),
    }

    def read_parameters(self, data_folder: str | Path) -> None:
        """ read and assign values to your parameters"""
        param= self.parameters
        param['infection_rate'] = 0.03
        param['aids_progression_rate'] = 0.1
        param['art_coverage'] = 0.8   #coverage is actually the effectiveness of ART

    def initialise_population(self, population: Population)-> None:
        """ Initialise the HIV characteristics of the population"""
        df= population.props
        df.loc[df.is_alive, 'hl_hiv_status'] = 'Non-Reactive'   # Set initial HIV status to negative
        df.loc[df.is_alive, 'hl_hiv_infection_date'] = pd.NaT  # Set to NaT for individuals who are not infected
        df.loc[df.is_alive, 'hl_aids_status'] = 'Non-AIDS'  # Set initial AIDS status to negative
        df.loc[df.is_alive, 'hl_aids_date'] = pd.NaT  # Set to NaT for individuals who are not diagnosed with AIDS
        df.loc[df.is_alive, 'hl_on_art'] = False  # Set initial ART status to not on ART
    
        # print (f'hiv status before event {df}')

    def initialise_simulation(self, sim: Simulation)-> None:
        """ Include all events here"""
        sim.schedule_event(HivInfectionEvent(self),sim.date+ pd.DateOffset(months=1))  # Schedule the first infection event to one month later
        sim.schedule_event(HivAidsProgressionEvent(self),sim.date+ pd.DateOffset(months=1))  # Schedule the first AIDS progression event to one month later
        sim.schedule_event(HivLiteLoggingevent(self),sim.date+ pd.DateOffset(months=1))  # Schedule the first logging event to one month later

    def on_birth(self, mother_id: int, child_id: int):
        df = self.sim.population.props
        df.at[child_id, 'hl_hiv_status'] = 'Non-Reactive'  # Set initial HIV status to negative for newborns
        df.at[child_id, 'hl_hiv_infection_date'] = pd.NaT  # Set to NaT for newborns
        df.at[child_id, 'hl_aids_status'] = 'Non-AIDS'  # Set initial AIDS status to negative for newborns
        df.at[child_id, 'hl_aids_date'] = pd.NaT  # Set to NaT for newborns
        df.at[child_id, 'hl_on_art'] = False  # Set initial ART status to not on ART for newborns
        return super().on_birth(mother_id, child_id)

    def on_simulation_end(self)-> None:
        """ Include all the activities here"""
        df = self.sim.population.props
        # Only include HIV related columns for those who are alive
        df = df[['is_alive', 'hl_hiv_status', 'hl_hiv_infection_date', 'hl_aids_status', 'hl_aids_date']]
        df.to_excel(Path('./outputs/hiv_lite_output_2.xlsx'), index=False)  # Save the population data to an Excel file
        print(f'Final population data saved to {Path("./outputs/hiv_lite_output.xlsx")}')


class HivInfectionEvent(RegularEvent, PopulationScopeEventMixin):
    """ Event to handle HIV infection """
    def __init__(self, module: Module):
        super().__init__(module, frequency=pd.DateOffset(months=1))

    def apply(self, target):
        """"Include all the activities here"""
        df = self.module.sim.population.props
        
        selected_for_hiv_inf = df.loc[df.is_alive & (df.hl_hiv_status == 'Non-Reactive')]
        random_selection = self.module.rng.choice([True, False],
                                                  size=len(selected_for_hiv_inf), 
                                                  p=[self.module.parameters['infection_rate'], 
                                                     1 - self.module.parameters['infection_rate']])
        # Get index for those who are infected
        inf_index = selected_for_hiv_inf.index[random_selection]
        # index_for_infection = selected_for_hiv_inf.index[random_selection]
        df.loc[inf_index, 'hl_hiv_status'] = "Reactive"  # Update HIV status to Reactive
        df.loc[inf_index, 'hl_hiv_infection_date'] = self.module.sim.date  # Update the infection date

        # Start ART for individuals who are HIV positive
        selected_for_art = df.loc[df.is_alive & (df.hl_hiv_status == 'Reactive') & (df.hl_on_art == False)]
        start_art = self.module.rng.random_sample(size=len(selected_for_art)) < self.module.parameters['art_coverage']
        prog_index = selected_for_art.index[start_art]
        df.loc[prog_index, 'hl_on_art'] = True  # Update ART status to True
        
        # print(df.loc[df.is_alive])
# Creating class for progression to Aids
class HivAidsProgressionEvent(RegularEvent, PopulationScopeEventMixin):
    """ Event to handle progression to AIDS """
    def __init__(self, module: Module):
        super().__init__(module, frequency=pd.DateOffset(months=1))
        self.params = module.parameters

    def apply(self, population):
        """"Include all the activities here"""
        def selected_for_progression(df, progression_rate):
            random_selection = self.module.rng.choice([True, False],
                                                        size=len(df), 
                                                        p=[progression_rate, 1 - progression_rate])
            return df.index[random_selection]
        # Get the population data
        df = population.props

        selected_for_progression_not_art = df.loc[df.is_alive & 
                                                  (df.hl_hiv_status == 'Reactive') & 
                                                  (df.hl_on_art == False) &
                                                  (df.hl_hiv_infection_date + pd.DateOffset(months=3)< self.sim.date)] 
        selected_for_progression_art = df.loc[df.is_alive &
                                            (df.hl_hiv_status == 'Reactive') &
                                            (df.hl_on_art == True) &
                                            (df.hl_hiv_infection_date + pd.DateOffset(months=3)< self.sim.date)]
        # Get index for those who progress to AIDS
        aids_index_not_art = selected_for_progression(selected_for_progression_not_art,
                                                       self.params['aids_progression_rate'])
        aids_index_art = selected_for_progression(selected_for_progression_art,
                                                  self.params['aids_progression_rate']* (1-self.params['art_coverage']))
        all_aids_index = aids_index_not_art.append(aids_index_art)
        if len(all_aids_index) != 0:
            # Update the status of those who progress to AIDS
            df.loc[all_aids_index, 'hl_aids_status'] = "AIDS"
            df.loc[all_aids_index, 'hl_aids_date'] = self.module.sim.date
            # Update the HIV status to AIDS
            df.loc[all_aids_index, 'hl_hiv_status'] = "AIDS"
        
  

                    
        



        # df = self.module.sim.population.props
        # # Select individuals who are HIV positive for at least 3 months and not yet progressed to AIDS 
        # selected_for_aids = df.loc[(df.hl_hiv_status == 'Reactive') &
        #                            (df.hl_hiv_infection_date <= self.module.sim.date - pd.DateOffset(months=3)) &
        #                            (df.hl_hiv_status != 'AIDS')]
        # # Randomly select individuals to progress to AIDS
        # random_selection = self.module.rng.choice([True, False],
        #                                           size=len(selected_for_aids), 
        #                                           p=[self.module.parameters['aids_progression_rate'], 
        #                                              1 - self.module.parameters['aids_progression_rate']])
        # # Get index for those who progress to AIDS
        # aids_index = selected_for_aids.index[random_selection]
        # # Update the status of those who progress to AIDS
        # df.loc[aids_index, 'hl_aids_status'] = "AIDS"
        # df.loc[aids_index, 'hl_aids_date'] = self.module.sim.date
        # # Update the HIV status to AIDS
        # df.loc[aids_index, 'hl_hiv_status'] = "AIDS"
        # print(f' the date is {self.sim.date, df.loc[df.is_alive]}')

class HivLiteLoggingevent(RegularEvent, PopulationScopeEventMixin): 
    """ Event to handle logging """
    def __init__(self, module: Module):
        super().__init__(module, frequency=pd.DateOffset(months=12))

    def apply(self, population):
        """"Include all the activities here"""
        df = self.module.sim.population.props
        alive_indiv = df.loc[df.is_alive]
        indiv_0_14 = alive_indiv.loc[df.age_years.between(0, 14) & (df.hl_hiv_status == 'AIDS')]
        indiv_15_24 = alive_indiv.loc[df.age_years.between(15, 24) & (df.hl_hiv_status == 'AIDS')]
        indiv_25_34 = alive_indiv.loc[df.age_years.between(25, 34) & (df.hl_hiv_status == 'AIDS')]
        indiv_35_44 = alive_indiv.loc[df.age_years.between(35, 44) & (df.hl_hiv_status == 'AIDS')]
        indiv_45_54 = alive_indiv.loc[df.age_years.between(45, 54) & (df.hl_hiv_status == 'AIDS')]
        indiv_55_64 = alive_indiv.loc[df.age_years.between(55, 64) & (df.hl_hiv_status == 'AIDS')]
        indiv_65_plus = alive_indiv.loc[(df.age_years >= 65) & (df.hl_hiv_status == 'AIDS')]


        aids_cases_by_age_group = {
            'indiv_0_14': len(indiv_0_14),
            'indiv_15_24': len(indiv_15_24),
            'indiv_25_34': len(indiv_25_34),
            'indiv_35_44': len(indiv_35_44),
            'indiv_45_54': len(indiv_45_54),
            'indiv_55_64': len(indiv_55_64),
            'indiv_65_plus': len(indiv_65_plus)
            }
        

        logger.info(key = 'aids_cases', data = aids_cases_by_age_group, description = 'AIDs cases by age group')



    





        # # Only include HIV related columns for those who are alive
        # df = df[['is_alive', 'hl_hiv_status', 'hl_hiv_infection_date', 'hl_aids_status', 'hl_aids_date']]
        # df.to_excel(Path('./outputs/hiv_lite_output_2.xlsx'), index=False)  # Save the population data to an Excel file
        # print(f'Final population data saved to {Path("./outputs/hiv_lite_output.xlsx")}')
    
        