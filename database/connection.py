"""PostgreSQL connection handling and database schema initialization."""

import logging

import psycopg2

from config.settings import DB_CONFIG

logger = logging.getLogger(__name__)


class DatabaseConnection:
    def __init__(self):

        self.connection = None
        self.cursor = None
        self.last_error = None

    def connect(self) -> bool:
        try:
            self.connection = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.connection.cursor()
            self.last_error = None
            return True
        except Exception as exc:
            self.last_error = str(exc)
            logger.error("Database connection failed: %s", exc)
            return False

    def disconnect(self) -> None:
        if self.cursor and not self.cursor.closed:
            self.cursor.close()
        if self.connection and not self.connection.closed:
            self.connection.close()
        self.cursor = None
        self.connection = None

    def execute_query(self, query, params=None, commit=False):
        try:
            if not self.connection or self.connection.closed:
                if not self.connect():
                    return None

            self.cursor.execute(query, params or ())
            if commit:
                self.connection.commit()
            self.last_error = None
            return self.cursor
        except Exception as exc:
            if self.connection and not self.connection.closed:
                self.connection.rollback()
            self.last_error = str(exc)
            logger.error("Database query failed: %s", exc)
            return None

    def get_connection(self):
        if not self.connection or self.connection.closed:
            if not self.connect():
                return None
        return self.connection

def init_database():
    print("Initializing database...")
    conn = DatabaseConnection()
    if not conn.connect():
        print("Database connection failed.")
        return False

    try:
        conn.execute_query("""
            CREATE TABLE IF NOT EXISTS patient (
                id SERIAL PRIMARY KEY,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                national_code VARCHAR(10) UNIQUE NOT NULL,
                phone VARCHAR(15),
                face_encoding TEXT,
                image_path VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """, commit=True)
        print("Patient table ready.")

        conn.execute_query("""
            CREATE TABLE IF NOT EXISTS medication (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                description TEXT
            )
        """, commit=True)
        print("Medication table ready.")

        conn.execute_query("""
            CREATE TABLE IF NOT EXISTS patient_medication (
                id SERIAL PRIMARY KEY,
                patient_id INTEGER REFERENCES patient(id) ON DELETE CASCADE,
                medication_id INTEGER REFERENCES medication(id),
                dosage VARCHAR(50),
                schedule VARCHAR(100),
                start_date DATE,
                end_date DATE,
                times_per_day INTEGER DEFAULT 1,
                time_slots TEXT,
                notes TEXT,
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(patient_id, medication_id)
            )
        """, commit=True)
        print("Patient medication table ready.")

        conn.execute_query("""
            CREATE TABLE IF NOT EXISTS medication_intake (
                id SERIAL PRIMARY KEY,
                patient_medication_id INTEGER REFERENCES patient_medication(id) ON DELETE CASCADE,
                intake_date DATE NOT NULL,
                intake_time TIME NOT NULL,
                taken BOOLEAN DEFAULT FALSE,
                taken_at TIMESTAMP,
                notes TEXT,
                UNIQUE(patient_medication_id, intake_date, intake_time)
            )
        """, commit=True)
        print("Medication intake table ready.")

        conn.execute_query("""
            CREATE TABLE IF NOT EXISTS medication_interaction (
                id SERIAL PRIMARY KEY,
                medication1_id INTEGER REFERENCES medication(id),
                medication2_id INTEGER REFERENCES medication(id),
                severity VARCHAR(20),
                description TEXT
            )
        """, commit=True)
        print("Medication interaction table ready.")

        conn.execute_query("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL,
                full_name VARCHAR(200),
                email VARCHAR(150),
                specialty VARCHAR(150),
                patient_id INTEGER REFERENCES patient(id) ON DELETE CASCADE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """, commit=True)
        print("Users table ready.")

        conn.execute_query("""
            CREATE TABLE IF NOT EXISTS doctor_notes (
                id SERIAL PRIMARY KEY,
                patient_id INTEGER REFERENCES patient(id) ON DELETE CASCADE,
                doctor_id INTEGER REFERENCES users(id),
                note TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """, commit=True)
        print("Doctor notes table ready.")

        conn.execute_query("""
            CREATE TABLE IF NOT EXISTS appointments (
                id SERIAL PRIMARY KEY,
                patient_id INTEGER REFERENCES patient(id) ON DELETE CASCADE,
                doctor_id INTEGER REFERENCES users(id),
                visit_date DATE NOT NULL,
                visit_time TIME,
                status VARCHAR(20) DEFAULT 'scheduled',
                reason VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """, commit=True)
        print("Appointments table ready.")
        conn.execute_query("""
            CREATE TABLE IF NOT EXISTS notifications (
                id SERIAL PRIMARY KEY,
                patient_id INTEGER NOT NULL REFERENCES patient(id) ON DELETE CASCADE,
                notification_type VARCHAR(40) NOT NULL,
                title VARCHAR(150) NOT NULL,
                message TEXT NOT NULL,
                related_id INTEGER,
                is_read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """, commit=True)
        conn.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_notifications_patient_created
            ON notifications(patient_id, created_at DESC)
        """, commit=True)
        print("Notifications table ready.")

        try:
            conn.execute_query("""
                ALTER TABLE patient ADD COLUMN IF NOT EXISTS registered_by INTEGER REFERENCES users(id)
            """, commit=True)
            print("Patient registration owner column ready.")
        except Exception:
            pass

        extra_columns = [
            ("age", "INTEGER"),
            ("gender", "VARCHAR(20)"),
            ("height_cm", "NUMERIC(5,1)"),
            ("weight_kg", "NUMERIC(5,1)"),
            ("blood_group", "VARCHAR(5)"),
            ("address", "VARCHAR(255)"),
            ("emergency_contact", "VARCHAR(100)"),
        ]
        for col_name, col_type in extra_columns:
            try:
                conn.execute_query(
                    f"ALTER TABLE patient ADD COLUMN IF NOT EXISTS {col_name} {col_type}",
                    commit=True
                )
            except Exception:
                pass
        print("Patient demographic columns ready.")

        conn.execute_query("""
            ALTER TABLE patient_medication
            ADD COLUMN IF NOT EXISTS prescribed_by INTEGER
            REFERENCES users(id) ON DELETE SET NULL
        """, commit=True)
        print("Prescription doctor column ready.")

        check_query = "SELECT COUNT(*) FROM medication"
        result = conn.execute_query(check_query)
        count = result.fetchone()[0] if result else 0

        if count == 0:
            print("Inserting the initial medication catalog...")

            conn.execute_query("""
                INSERT INTO medication (name, description) VALUES
                -- Cardiovascular System (Blood Pressure, Cholesterol, Heart)
                ('Lisinopril', 'ACE inhibitor for hypertension and heart failure'),
                ('Amlodipine', 'Calcium channel blocker for high blood pressure and angina'),
                ('Metoprolol', 'Beta-blocker for hypertension, angina, and heart failure'),
                ('Atorvastatin', 'Statin for high cholesterol and cardiovascular protection'),
                ('Rosuvastatin', 'Statin for lowering LDL cholesterol and triglycerides'),
                ('Simvastatin', 'Statin for hyperlipidemia and cardiovascular risk reduction'),
                ('Losartan', 'ARB for hypertension and diabetic nephropathy'),
                ('Valsartan', 'ARB for hypertension and heart failure'),
                ('Carvedilol', 'Beta-blocker for heart failure and hypertension'),
                ('Hydrochlorothiazide', 'Thiazide diuretic for hypertension and edema'),
                ('Furosemide', 'Loop diuretic for edema and hypertension'),
                ('Spironolactone', 'Potassium-sparing diuretic for hypertension and heart failure'),
                ('Clopidogrel', 'Antiplatelet agent for prevention of thrombotic events'),
                ('Aspirin', 'Antiplatelet for cardiovascular prevention and pain relief'),
                ('Warfarin', 'Anticoagulant for prevention of thromboembolism'),
                ('Apixaban', 'Direct factor Xa inhibitor for stroke prevention in atrial fibrillation'),
                ('Rivaroxaban', 'Factor Xa inhibitor for DVT, PE, and stroke prevention'),
                ('Dabigatran', 'Direct thrombin inhibitor for stroke prevention'),
                ('Enalapril', 'ACE inhibitor for hypertension and heart failure'),
                ('Ramipril', 'ACE inhibitor for hypertension and heart protection after MI'),
                ('Candesartan', 'ARB for hypertension and heart failure'),
                ('Irbesartan', 'ARB for hypertension and diabetic nephropathy'),
                ('Telmisartan', 'ARB for hypertension and cardiovascular prevention'),
                ('Olmesartan', 'ARB for hypertension'),
                ('Felodipine', 'Calcium channel blocker for hypertension'),
                ('Nifedipine', 'Calcium channel blocker for hypertension and angina'),
                ('Diltiazem', 'Calcium channel blocker for hypertension and angina'),
                ('Verapamil', 'Calcium channel blocker for hypertension, angina, arrhythmias'),
                ('Bisoprolol', 'Beta-blocker for hypertension and heart failure'),
                ('Atenolol', 'Beta-blocker for hypertension and angina'),
                ('Propranolol', 'Beta-blocker for hypertension, migraine, anxiety'),
                ('Digoxin', 'Cardiac glycoside for heart failure and atrial fibrillation'),
                ('Nitroglycerin', 'Nitrate for angina pectoris'),
                ('Isosorbide Mononitrate', 'Nitrate for angina and heart failure'),
                ('Ezetimibe', 'Cholesterol absorption inhibitor for hyperlipidemia'),
                ('Fenofibrate', 'Fibrate for hypertriglyceridemia'),
                ('Gemfibrozil', 'Fibrate for hyperlipidemia'),
                ('Pravastatin', 'Statin for hyperlipidemia'),
                ('Fluvastatin', 'Statin for hyperlipidemia'),
                ('Pitavastatin', 'Statin for hyperlipidemia'),

                -- Diabetes and Endocrine System
                ('Metformin', 'Biguanide for type 2 diabetes - first-line treatment'),
                ('Glipizide', 'Sulfonylurea for type 2 diabetes - stimulates insulin release'),
                ('Glyburide', 'Sulfonylurea for type 2 diabetes'),
                ('Glimepiride', 'Sulfonylurea for type 2 diabetes'),
                ('Sitagliptin', 'DPP-4 inhibitor for type 2 diabetes'),
                ('Saxagliptin', 'DPP-4 inhibitor for type 2 diabetes'),
                ('Linagliptin', 'DPP-4 inhibitor for type 2 diabetes'),
                ('Empagliflozin', 'SGLT2 inhibitor for type 2 diabetes and heart failure'),
                ('Dapagliflozin', 'SGLT2 inhibitor for type 2 diabetes and heart failure'),
                ('Canagliflozin', 'SGLT2 inhibitor for type 2 diabetes'),
                ('Liraglutide', 'GLP-1 agonist for type 2 diabetes and weight management'),
                ('Semaglutide', 'GLP-1 agonist for type 2 diabetes and weight loss'),
                ('Dulaglutide', 'GLP-1 agonist for type 2 diabetes'),
                ('Exenatide', 'GLP-1 agonist for type 2 diabetes'),
                ('Pioglitazone', 'Thiazolidinedione for type 2 diabetes'),
                ('Rosiglitazone', 'Thiazolidinedione for type 2 diabetes'),
                ('Insulin Glargine', 'Long-acting insulin for type 1 and type 2 diabetes'),
                ('Insulin Detemir', 'Long-acting insulin for diabetes management'),
                ('Insulin Degludec', 'Ultra-long-acting insulin for diabetes'),
                ('Insulin Lispro', 'Rapid-acting insulin for mealtime control'),
                ('Insulin Aspart', 'Rapid-acting insulin analog'),
                ('Insulin Regular', 'Short-acting human insulin'),
                ('NPH Insulin', 'Intermediate-acting insulin'),
                ('Levothyroxine', 'Thyroid hormone replacement for hypothyroidism'),
                ('Methimazole', 'Antithyroid agent for hyperthyroidism'),
                ('Propylthiouracil', 'Antithyroid agent for hyperthyroidism'),
                ('Prednisone', 'Corticosteroid for inflammation and autoimmune conditions'),
                ('Hydrocortisone', 'Corticosteroid for adrenal insufficiency'),
                ('Dexamethasone', 'Potent corticosteroid for inflammation and immunosuppression'),

                -- Respiratory System (Asthma, COPD, Allergies)
                ('Albuterol', 'Short-acting beta agonist for asthma and COPD - rescue inhaler'),
                ('Salmeterol', 'Long-acting beta agonist for asthma and COPD maintenance'),
                ('Formoterol', 'Long-acting beta agonist for asthma and COPD'),
                ('Fluticasone', 'Inhaled corticosteroid for asthma prevention'),
                ('Budesonide', 'Inhaled corticosteroid for asthma and COPD'),
                ('Beclomethasone', 'Inhaled corticosteroid for asthma'),
                ('Mometasone', 'Inhaled corticosteroid for asthma'),
                ('Tiotropium', 'Long-acting anticholinergic for COPD'),
                ('Ipratropium', 'Short-acting anticholinergic for COPD and asthma'),
                ('Montelukast', 'Leukotriene receptor antagonist for asthma and allergies'),
                ('Zafirlukast', 'Leukotriene antagonist for asthma'),
                ('Theophylline', 'Methylxanthine for COPD and asthma'),
                ('Cromolyn Sodium', 'Mast cell stabilizer for asthma prevention'),
                ('Cetirizine', 'Antihistamine for allergies and hay fever'),
                ('Loratadine', 'Non-drowsy antihistamine for allergies'),
                ('Fexofenadine', 'Antihistamine for seasonal allergies'),
                ('Diphenhydramine', 'First-generation antihistamine for allergies and sleep'),
                ('Levocetirizine', 'Antihistamine for allergic rhinitis and urticaria'),
                ('Desloratadine', 'Antihistamine for allergies'),
                ('Bilastine', 'Antihistamine for allergic rhinitis and urticaria'),

                -- Central Nervous System (Pain, Depression, Anxiety, Seizures)
                ('Ibuprofen', 'NSAID for pain, fever, and inflammation'),
                ('Acetaminophen', 'Analgesic and antipyretic for mild to moderate pain'),
                ('Naproxen', 'NSAID for pain and inflammation'),
                ('Diclofenac', 'NSAID for arthritis and acute pain'),
                ('Celecoxib', 'COX-2 selective NSAID for arthritis and pain'),
                ('Meloxicam', 'NSAID for osteoarthritis and rheumatoid arthritis'),
                ('Tramadol', 'Opioid analgesic for moderate to severe pain'),
                ('Oxycodone', 'Opioid analgesic for severe pain'),
                ('Hydrocodone', 'Opioid analgesic for moderate to severe pain'),
                ('Morphine', 'Opioid analgesic for severe pain'),
                ('Codeine', 'Opioid analgesic for mild to moderate pain'),
                ('Gabapentin', 'Anticonvulsant for neuropathic pain and seizures'),
                ('Pregabalin', 'Anticonvulsant for neuropathic pain and fibromyalgia'),
                ('Sertraline', 'SSRI for depression, anxiety, and OCD'),
                ('Fluoxetine', 'SSRI for depression, OCD, and bulimia'),
                ('Citalopram', 'SSRI for depression'),
                ('Escitalopram', 'SSRI for depression and generalized anxiety'),
                ('Paroxetine', 'SSRI for depression, anxiety, and PTSD'),
                ('Venlafaxine', 'SNRI for depression and anxiety disorders'),
                ('Duloxetine', 'SNRI for depression, anxiety, and neuropathic pain'),
                ('Bupropion', 'NDRI for depression and smoking cessation'),
                ('Trazodone', 'Antidepressant for depression and insomnia'),
                ('Mirtazapine', 'Antidepressant for depression and appetite stimulation'),
                ('Amitriptyline', 'Tricyclic antidepressant for depression and neuropathic pain'),
                ('Nortriptyline', 'Tricyclic antidepressant for depression and pain'),
                ('Diazepam', 'Benzodiazepine for anxiety, seizures, and muscle spasms'),
                ('Lorazepam', 'Benzodiazepine for anxiety and seizures'),
                ('Alprazolam', 'Benzodiazepine for anxiety and panic disorder'),
                ('Clonazepam', 'Benzodiazepine for seizures and panic disorder'),
                ('Zolpidem', 'Non-benzodiazepine hypnotic for insomnia'),
                ('Eszopiclone', 'Non-benzodiazepine for insomnia'),
                ('Levetiracetam', 'Anticonvulsant for epilepsy'),
                ('Lamotrigine', 'Anticonvulsant for epilepsy and bipolar disorder'),
                ('Valproate', 'Anticonvulsant for epilepsy and bipolar disorder'),
                ('Topiramate', 'Anticonvulsant for epilepsy and migraine prevention'),
                ('Carbamazepine', 'Anticonvulsant for epilepsy and trigeminal neuralgia'),
                ('Phenytoin', 'Anticonvulsant for generalized tonic-clonic seizures'),
                ('Sumatriptan', 'Triptan for acute migraine attacks'),
                ('Rizatriptan', 'Triptan for acute migraine'),

                -- Antibiotics and Antimicrobials
                ('Amoxicillin', 'Penicillin antibiotic for bacterial infections'),
                ('Amoxicillin-Clavulanate', 'Penicillin with beta-lactamase inhibitor for resistant infections'),
                ('Cephalexin', 'First-generation cephalosporin for bacterial infections'),
                ('Cefdinir', 'Third-generation cephalosporin for respiratory and skin infections'),
                ('Cefuroxime', 'Second-generation cephalosporin for various infections'),
                ('Ceftriaxone', 'Third-generation cephalosporin for severe infections'),
                ('Azithromycin', 'Macrolide antibiotic for respiratory and skin infections'),
                ('Clarithromycin', 'Macrolide antibiotic for H. pylori and respiratory infections'),
                ('Erythromycin', 'Macrolide antibiotic for respiratory and skin infections'),
                ('Doxycycline', 'Tetracycline antibiotic for acne, respiratory, and tick-borne illnesses'),
                ('Minocycline', 'Tetracycline antibiotic for acne and respiratory infections'),
                ('Tetracycline', 'Antibiotic for acne and various infections'),
                ('Ciprofloxacin', 'Fluoroquinolone for urinary, respiratory, and GI infections'),
                ('Levofloxacin', 'Fluoroquinolone for respiratory and urinary infections'),
                ('Moxifloxacin', 'Fluoroquinolone for respiratory infections'),
                ('Metronidazole', 'Antibiotic for anaerobic bacteria and parasites'),
                ('Clindamycin', 'Lincosamide antibiotic for skin and soft tissue infections'),
                ('Vancomycin', 'Glycopeptide antibiotic for serious gram-positive infections'),
                ('Linezolid', 'Oxazolidinone for resistant gram-positive infections'),
                ('Nitrofurantoin', 'Antibiotic for urinary tract infections'),
                ('Trimethoprim-Sulfamethoxazole', 'Sulfonamide for urinary, respiratory, and GI infections'),
                ('Penicillin VK', 'Penicillin for streptococcal infections'),
                ('Dicloxacillin', 'Penicillin for staphylococcal infections'),
                ('Sulfasalazine', 'Sulfonamide for inflammatory bowel disease and rheumatoid arthritis'),
                ('Fosfomycin', 'Antibiotic for uncomplicated urinary tract infections'),

                -- Gastrointestinal System
                ('Omeprazole', 'Proton pump inhibitor for GERD and peptic ulcers'),
                ('Esomeprazole', 'PPI for GERD and erosive esophagitis'),
                ('Lansoprazole', 'PPI for GERD and gastric ulcers'),
                ('Pantoprazole', 'PPI for GERD and Zollinger-Ellison syndrome'),
                ('Rabeprazole', 'PPI for GERD and H. pylori eradication'),
                ('Famotidine', 'H2 blocker for GERD and peptic ulcers'),
                ('Ranitidine', 'H2 blocker for GERD and ulcers'),
                ('Cimetidine', 'H2 blocker for GERD and ulcers'),
                ('Ondansetron', 'Antiemetic for nausea and vomiting (especially chemotherapy)'),
                ('Metoclopramide', 'Prokinetic agent for gastroparesis and nausea'),
                ('Promethazine', 'Antiemetic and antihistamine for nausea and allergies'),
                ('Prochlorperazine', 'Antiemetic for nausea and vomiting'),
                ('Loperamide', 'Antidiarrheal agent for acute diarrhea'),
                ('Bismuth Subsalicylate', 'Antidiarrheal and antacid for traveler''s diarrhea'),
                ('Dicyclomine', 'Antispasmodic for irritable bowel syndrome'),
                ('Hyoscyamine', 'Anticholinergic for IBS and peptic ulcers'),
                ('Mesalamine', 'Aminosalicylate for ulcerative colitis and Crohn''s disease'),
                ('Lactulose', 'Osmotic laxative for constipation'),
                ('Polyethylene Glycol', 'Osmotic laxative for constipation'),
                ('Bisacodyl', 'Stimulant laxative for constipation'),
                ('Docusate', 'Stool softener for constipation'),
                ('Psyllium', 'Fiber supplement for constipation and cholesterol'),
                ('Rifaximin', 'Antibiotic for traveler''s diarrhea and hepatic encephalopathy'),

                -- Ophthalmic (Eye Medications)
                ('Latanoprost', 'Prostaglandin analog for glaucoma - increases aqueous outflow'),
                ('Travoprost', 'Prostaglandin analog for open-angle glaucoma'),
                ('Bimatoprost', 'Prostaglandin analog for glaucoma and eyelash growth'),
                ('Timolol', 'Beta-blocker eye drop for glaucoma'),
                ('Dorzolamide', 'Carbonic anhydrase inhibitor for glaucoma'),
                ('Brinzolamide', 'Carbonic anhydrase inhibitor for glaucoma'),
                ('Brimonidine', 'Alpha agonist for glaucoma'),
                ('Ketorolac', 'NSAID eye drop for postoperative inflammation'),
                ('Prednisolone Acetate', 'Corticosteroid eye drop for ocular inflammation'),
                ('Ciprofloxacin Eye Drops', 'Antibiotic eye drop for bacterial conjunctivitis'),
                ('Ofloxacin Eye Drops', 'Antibiotic eye drop for eye infections'),
                ('Moxifloxacin Eye Drops', 'Fluoroquinolone eye drop for bacterial conjunctivitis'),
                ('Tobramycin Eye Drops', 'Aminoglycoside antibiotic for eye infections'),
                ('Olopatadine', 'Antihistamine eye drop for allergic conjunctivitis'),
                ('Ketotifen', 'Mast cell stabilizer for allergic conjunctivitis'),
                ('Cyclosporine Eye Drops', 'Immunomodulator for dry eye disease'),

                -- Dermatological (Skin Medications)
                ('Tretinoin', 'Topical retinoid for acne and photoaging'),
                ('Adapalene', 'Topical retinoid for acne'),
                ('Benzoyl Peroxide', 'Antibacterial agent for acne'),
                ('Clindamycin Topical', 'Topical antibiotic for acne'),
                ('Isotretinoin', 'Oral retinoid for severe cystic acne'),
                ('Hydrocortisone Topical', 'Topical corticosteroid for inflammation and itching'),
                ('Triamcinolone Topical', 'Topical corticosteroid for dermatitis and psoriasis'),
                ('Clobetasol', 'Super-potent topical corticosteroid for psoriasis and dermatitis'),
                ('Calcipotriene', 'Vitamin D analog for psoriasis'),
                ('Tacrolimus Ointment', 'Calcineurin inhibitor for atopic dermatitis'),
                ('Ketoconazole Topical', 'Antifungal for tinea and seborrheic dermatitis'),
                ('Clotrimazole Topical', 'Antifungal for athlete''s foot and ringworm'),
                ('Terbinafine Topical', 'Antifungal for athlete''s foot and ringworm'),
                ('Silver Sulfadiazine', 'Antibacterial for burn wounds'),

                -- Additional Common Medications
                ('Allopurinol', 'Xanthine oxidase inhibitor for gout and hyperuricemia'),
                ('Colchicine', 'Anti-inflammatory for acute gout flares'),
                ('Febuxostat', 'Xanthine oxidase inhibitor for chronic gout'),
                ('Alendronate', 'Bisphosphonate for osteoporosis'),
                ('Risedronate', 'Bisphosphonate for osteoporosis'),
                ('Calcium Carbonate', 'Calcium supplement for bone health and antacid'),
                ('Vitamin D3', 'Vitamin D supplement for bone health and immunity'),
                ('Ferrous Sulfate', 'Iron supplement for iron deficiency anemia'),
                ('Folic Acid', 'Folate supplement for pregnancy and anemia prevention'),
                ('Cyanocobalamin', 'Vitamin B12 supplement for deficiency'),
                ('Potassium Chloride', 'Potassium supplement for hypokalemia'),
                ('Cyclobenzaprine', 'Muscle relaxant for acute musculoskeletal pain'),
                ('Baclofen', 'Muscle relaxant for spasticity'),
                ('Donepezil', 'Cholinesterase inhibitor for Alzheimer''s disease'),
                ('Memantine', 'NMDA antagonist for moderate to severe Alzheimer''s'),
                ('Levodopa-Carbidopa', 'Dopamine precursor for Parkinson''s disease'),
                ('Pramipexole', 'Dopamine agonist for Parkinson''s disease'),
                ('Enoxaparin', 'Low molecular weight heparin for DVT prophylaxis'),
                ('Heparin', 'Anticoagulant for acute thromboembolism'),
                ('Ticagrelor', 'P2Y12 inhibitor for acute coronary syndrome')
                ON CONFLICT (name) DO NOTHING
            """, commit=True)
            print("Medication catalog inserted.")

            print("Inserting medication interactions...")
            conn.execute_query("""
                INSERT INTO medication_interaction (medication1_id, medication2_id, severity, description)
                SELECT
                    m1.id, m2.id,
                    CASE
                        WHEN m1.name = 'Warfarin' AND m2.name IN ('Aspirin', 'Ibuprofen') THEN 'severe'
                        WHEN m1.name IN ('Atorvastatin', 'Simvastatin') AND m2.name = 'Clarithromycin' THEN 'severe'
                        WHEN m1.name IN ('Lisinopril', 'Losartan') AND m2.name = 'Spironolactone' THEN 'severe'
                        WHEN m1.name = 'Metformin' AND m2.name = 'Ibuprofen' THEN 'moderate'
                        WHEN m1.name IN ('Sertraline', 'Fluoxetine', 'Duloxetine') AND m2.name = 'Tramadol' THEN 'severe'
                        WHEN m1.name = 'Amoxicillin' AND m2.name = 'Warfarin' THEN 'moderate'
                        ELSE 'moderate'
                    END as severity,
                    CASE
                        WHEN m1.name = 'Warfarin' AND m2.name = 'Aspirin' THEN 'Increased risk of bleeding - avoid concurrent use unless directed by physician'
                        WHEN m1.name = 'Warfarin' AND m2.name = 'Ibuprofen' THEN 'Significantly increased bleeding risk. Avoid combination.'
                        WHEN m1.name = 'Atorvastatin' AND m2.name = 'Clarithromycin' THEN 'Increased risk of myopathy and rhabdomyolysis - avoid combination'
                        WHEN m1.name = 'Simvastatin' AND m2.name = 'Clarithromycin' THEN 'Significantly increased statin levels - increased myopathy risk'
                        WHEN m1.name = 'Lisinopril' AND m2.name = 'Spironolactone' THEN 'Hyperkalemia risk - monitor potassium levels'
                        WHEN m1.name = 'Losartan' AND m2.name = 'Spironolactone' THEN 'Increased risk of hyperkalemia - avoid combination'
                        WHEN m1.name = 'Metformin' AND m2.name = 'Ibuprofen' THEN 'Increased risk of lactic acidosis - caution in renal impairment'
                        WHEN m1.name = 'Sertraline' AND m2.name = 'Tramadol' THEN 'Risk of serotonin syndrome - avoid or monitor closely'
                        WHEN m1.name = 'Amoxicillin' AND m2.name = 'Warfarin' THEN 'Antibiotics may alter INR - monitor closely'
                        ELSE 'Potential drug interaction - monitor patient closely'
                    END as description
                FROM medication m1, medication m2
                WHERE m1.id < m2.id
                AND (
                    (m1.name = 'Warfarin' AND m2.name IN ('Aspirin', 'Ibuprofen')) OR
                    (m1.name IN ('Atorvastatin', 'Simvastatin') AND m2.name = 'Clarithromycin') OR
                    (m1.name IN ('Lisinopril', 'Losartan') AND m2.name = 'Spironolactone') OR
                    (m1.name = 'Metformin' AND m2.name = 'Ibuprofen') OR
                    (m1.name IN ('Sertraline', 'Fluoxetine', 'Duloxetine') AND m2.name = 'Tramadol') OR
                    (m1.name = 'Amoxicillin' AND m2.name = 'Warfarin')
                )
                ON CONFLICT DO NOTHING
            """, commit=True)
            print("Medication interactions inserted.")
        else:
            print(f"Medication catalog already contains {count} rows; insertion skipped.")

        print("Database initialization complete.")
        conn.disconnect()
        return True

    except Exception as e:
        print(f"Database initialization failed: {e}")
        conn.disconnect()
        return False
