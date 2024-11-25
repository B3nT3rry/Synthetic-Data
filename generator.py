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
                admission_date = pd.Timestamp(start_date) + pd.Timedelta(
                    days=np.random.randint(0, (pd.Timestamp(end_date) - pd.Timestamp(start_date)).days)
                )

                # Determisn admission type and specialty based on conditions
                if any(c in ['Coronary Heart Disease','Heart Failure'] for c in conditions):
                    specialty_weights = {'Cardiology': 0.06, 'General Medicine': 0.3, 'Other': 0.1}
                elif any(c in ['COPD','Asthma'] for c in conditions):
                    specialty_weights = {'Respiratory Medicine':0.06, 'General Medicine': 0.3, 'Other': 0.1}
                else:
                    specialty_weights = self.meta_conditions['specialties']

                spell = {
                    'nhs_number': patient['nhs_number'],
                    'spell_id': f'S{len(spells):06d}',
                    'admission_date': admission_date,
                    'admission_method': np.random.choice(
                        list(self.meta_conditions['admission_methods'].keys()),
                        p=list(self.meta_conditions['admission_methods'].values())
                    ),
                    'admission_source': np.random.choice(
                        list(self.meta_conditions['admission_source'].keys()),
                        p=list(self.meta_conditions['admission_source'].values())
                    ),
                    'specialty': np.random.choice(
                        list(specialty_weights.keys()),
                        p=[specialty_weights[k]/sum(specialty_weights.values()) for k in specialty_weights.keys()]
                    )
                }

                # generate length of stay based on admission type and conditions
                if spell['admission_method'] == 'Day Case':
                    los = 0 
                elif spell['admission_method']== ' Elective':
                    los = np.random.geometric(0.3)
                else: #Emergency
                    los = np.random.geometric(0.2)
                    if any(c in ['Heart Failure','Pneumonia'] for c in conditions):
                        los += np.random.geometric(0.15)

                spell['discharge_date'] = admission_date + pd.Timedelta(days=los)
                spell['length_of_stay'] = los

                spell['discharge_destination'] = np.random.choice(
                    list(self.meta_conditions['discharge_destination'].keys()),
                    p=list(self.meta_conditions['discharge_destination'].values())
                )

                #Add diagnosis codes 
                primary_diagnosis = self.generate_diagnosis_codes(conditions, spell['admission_method'])
                spell['primary_diagnosis'] = primary_diagnosis
                spell['secondary_diagnoses'] = ';'.join(self.generate.secondary_diagnoses(conditions, primary_diagnosis))

                #Add procedures if applicable
                spell['procedures'] = ';'.join(self.generate_procedures(
                    conditions,
                    spell['specialty'],
                    spell['admission_method']
                ))

                #Add critical care details if applicable
                if spell['admission_method'] == 'Emergency' and np.random.random() <0.15:
                    spell.update(self.generate_critical_care_stay(spell['admission_date'], los))

                spells.append(spell)

        return pd.DataFrame(spells)
    
    def generate_ae_attendances(self, patient_data, start_date, end_date):
        # Generate A&E attendance records
        attendances = []

        for _, patient in patient_data.iterrows():
            conditions = patient['condtions'].split(';') if patient['conditions'] != 'None' else []

            # Calculate number of A&E visits
            base_rate = 0.3
            condition_factor = len(conditions) * 0.1
            age_factor = max(0, (patient['age'] - 50) * 0.01)
            deprivation_factor = (11 - patient['imd_decile']) * 0.02

            num_visits = np.random.possion(
                base_rate + condition_factor + age_factor + deprivation_factor
            )

            for _ in range(num_visits):
                arrival_date = pd.Timestamp(start_date) + pd.Timedelta(
                    days=np.random.randint(0, (pd.Timestamp(end_date) - pd.Timestamp(start_date)).days)
                )

                # Determine arrival time ( more visits in the daytime and evening)
                hour = np.random.choice(24, p=self.generate_arrival_time_distribution())
                arrival_datetime = arrival_date + pd.Timedelta(hours=hour)

                attendance = {
                    'nhs_number': patient['nhs_number'],
                    'attendance_id': f'A{len(attendances):06d}',
                    'arrivale_datetime': arrival_datetime,
                    'arrival_mode': np.random.choice(
                        ['Ambulance', 'Self-presented','Other'],
                        p=[0.3, 0.65, 0.05]
                    ),
                    'reason': self.generate_ae_reason(conditions)
                }

                # Generate waiting time and treatment time
                attendance['waiting_time_mins'] = np.random.exponential(60) # average 1 hour wait 
                attendance['treatment_time_mins'] = np.random.exponential(120) # average 2 hour treatment

                # Determine outcome
                attendance['outcome'] = self.generate_ae_outcome(
                    conditions,
                    attendance['reason']
                )

                attendances.append(attendance)

        return pd.DataFrame(attendances)

    def generate_outpatient_appointments(self, patient_data, start_date, end_date):
        # Generate outpatient appointment records
        appointments = []

        for _, patient in patient_data.iterrows():
            conditions = patient['conditions'].split(';') if patient['conditions'] != 'None' else []

            # Calculate number of appointments based on conditions
            for condition in conditions:
                if condition == 'None':
                    continue

                # Number of appointments varies by condition
                if condition in ['Type 2 Diabetes', 'Heart Failure']:
                    num_appointments = np.random.poisson(4) # more frequent follow-up
                else:
                    num_appointments = np.random.poisson(2)

                for _ in range(num_appointments):
                    appointment_date = pd.Timestamp(start_date) + pd.Timedelta(
                        days=np.random.randint(0, (pd.Timestamp(end_date) - pd.Timestamp(start_date)).days)
                    )

                    specialty = self.get_condition_specialty(condition)

                    appointment = {
                        'nhs_number': patient['nhs_number'],
                        'appointment_id': f'0{len(appointments):06d}',
                        'appointment_date': appointment_date,
                        'specialty': specialty,
                        'appointment_type': np.random.choice(
                            ['New', 'Follow-up'],
                            p=[0.2, 0.8]
                        ),
                        'referral_source': 'GP' if np.random.random() <0.8 else 'Consultant', 
                        'attendance_status': np.random.choice(
                            ['Attended', 'DNA', 'Cancelled'],
                            p=[0.85, 0.10, 0.05]
                        )
                    }

                    appointments.append(appointment)
            
            return pd.DataFrame(appointments)
