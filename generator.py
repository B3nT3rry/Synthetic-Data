import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class datagenerator:
    def __init__(self, seed = 42):
        np.random.seed(seed)

        # Condtions and prevelance and risk factors
        self.meta_conditions = {
            'admission_methods': {
                'Emergency':0.55,
                'Elective':0.35,
                'Day Case':0.10
            },
            'admission_source': {
                'Usual residence':0.75,
                'Other NHS Hospital':0.15,
                'Care Home': 0.05,
                'Other': 0.05
             },
             'dischare_destination': {
                 'Usual residence':0.80,
                 'Other NHS Hospital':0.10,
                 'Care Home':0.07,
                 'Died':0.03
             },
             'specialties': {
                 'General Medicine': 0.25,
                 'General Surgery' : 0.15,
                 'Cardiology': 0.10,
                 'Orthopaedics': 0.10,
                 'Gastroenterology': 0.08,
                 'Respiratory Medicine': 0.07,
                 'Elderly Care': 0.10,
                 'Other': 0.15
             }
        }

        # ICD10 codes for common conditions
        self.icd10_codes = {
            'Hypertension': ['I10','I11','I12','I13','I15'],
            'Type 2 Diabetes': ['E11.0','E11.1','E11.2','E11.3','E11.4'],
            'Coronary Heart Disease': ['I20','I21','I22','I23','I25'],
            'Heart Failure': ['I50.0','I50.1','I50.9'],
            'COPD': ['J44.0','J44.1','J44.8','J44.9'],
            'Asthma': ['J45.0','J45.1','J45.8','J45.9'],
            'Pneumonia': ['J12','J13','J14','J15','J18'],
            'Fractures': ['S72','S82','S52','S62'],
            'Cancer': ['C50','C18','C34','C61','C67']
        }

        # OPCS Procedure codes
        self.opcs4_codes = {
            'Coronary Angiography': ['K63','K65'],
            'Hip Replacement': ['W37','W38','W39'],
            'Knee Replacement':['W40','W41','W42'],
            'Cholecytectomy': ['J18'],
            'Colonoscopy': ['H20','H22'],
            'Gastroscopy': ['G45'],
            'Cataract Surgery': ['C71','C72','C74'],
            'Cardac Pacemaker': ['K60','K61']
        }

        # A&E attendance reasons
        self.ae_reasons = {
            'Chest Pain': 0.15,
            'Breathing Difficulty': 0.12,
            'Abdominal Pain': 0.10,
            'Injury': 0.20,
            'Falls': 0.08,
            'Mental Health': 0.05,
            'Other Medical': 0.30
        }

        # Critical Care details 
        self.critical_care_types = {
            'Intensive Care': 0.50,
            'High Dependency': 0.30,
            'Coronary Care': 0.20
        }
    
    def generate_hospital_spells(self, patient_data, start_date, end_date):
        # Generate hospital spells (admissions) based on patient condition
        spells = []

        for _, patient in patient_data.iterrows():
            conditions = patient['conditions'].split(';') if patient['condtions'] != 'None' else []

            # Calculate number of admissions based on conditions and risk factors
            base_admission_rate = 0.2 # Base probability of any admission
            condition_factor = len(conditions) *0.1
            age_factor = max(0, (patient['age']-50)*0.01)
            deprivation_factor = (11 - patient['imd_decile'])*0.02

            num_admissions = np.random.poisson(
                base_admission_rate + condition_factor + age_factor + deprivation_factor
            )

            for _ in range(num_admissions):
                # Generate admission details