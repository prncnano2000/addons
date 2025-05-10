import sys
import random
import os

def generate_patient_xml_demo_data_only_name_strictly():
    """
    Génère le contenu XML des données de démonstration pour le modèle patient,
    STRICTEMENT avec uniquement le champ 'name', et l'écrit dans un fichier spécifique.
    AVERTISSEMENT SÉVÈRE : Cela va très probablement échouer à charger dans Odoo.
    """
    module_name = "gestion_hospital"
    model_name = "gestion_hospital.patient"
    output_filepath = "/home/jordan/Bureau/odoo15/addons/gestion_hospital/demo/patient_demo1.xml"

    print("--- Générateur de données de démo pour le modèle Patient (STRICTEMENT Uniquement Name) ---")
    print(f"Le fichier sera enregistré dans : {output_filepath}")

    print("\n")
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print("!! AVERTISSEMENT TRÈS SÉVÈRE : CE FICHIER XML NE CONTIENT STRICTEMENT QUE LE CHAMP 'name'.!!")
    print("!! VOTRE MODÈLE 'gestion_hospital.patient' REQUIERT DES CHAMPS UNIQUES (telephone, email)!!")
    print("!! ET D'AUTRES CHAMPS (date_naissance) POUR FONCTIONNER CORRECTEMENT.                  !!")
    print("!!                                                                                    !!")
    print("!! LE CHARGEMENT DE CE FICHIER DANS ODOO VA PRESQUE CERTAINEMENT CAUSER UNE ERREUR     !!")
    print("!! (Violation de contrainte d'unicité ou champ requis manquant).                      !!")
    print("!!                                                                                    !!")
    print("!! Ce script est généré EXCLUSIVEMENT SELON VOTRE DEMANDE SPÉCIFIQUE, malgré les risques.!!")
    print("!! Pour un fichier fonctionnel, utilisez le script précédent incluant les champs requis.!!")
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print("\n")

    while True:
        try:
            num_records_str = input("Combien d'enregistrements de patients voulez-vous générer (SACHANT que cela va probablement échouer au chargement) ? ")
            num_records = int(num_records_str)
            if num_records <= 0:
                print("Veuillez entrer un nombre positif.")
            else:
                break
        except ValueError:
            print("Entrée invalide. Veuillez entrer un nombre entier.")

    output_dir = os.path.dirname(output_filepath)
    if not os.path.exists(output_dir):
        print(f"Le répertoire {output_dir} n'existe pas. Veuillez le créer manuellement.")
        return

    try:
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(f'<?xml version="1.0" encoding="utf-8"?>\n')
            f.write(f'<odoo>\n')
            f.write(f'    <data noupdate="1">\n')

            prenoms = ["Alice", "Bob", "Charlie", "Diana", "Ethan", "Fiona", "George", "Hannah", "Ian", "Julia"]
            noms = ["Smith", "Jones", "Williams", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor", "Anderson"]

            for i in range(1, num_records + 1):
                full_name = f"{random.choice(prenoms)} {random.choice(noms)} Patient {i}"
                record_id = f"patient_demo_simple_strict_{i}" # ID légèrement modifié pour éviter conflit si autre fichier existe

                f.write(f'        <record id="{module_name}.{record_id}" model="{model_name}">\n')
                f.write(f'            <field name="name">{full_name}</field>\n') # STRICTEMENT uniquement le champ 'name'
                f.write(f'        </record>\n')

            f.write(f'    </data>\n')
            f.write(f'</odoo>\n')

        print(f"\nSuccessfully generated {num_records} records and saved to {output_filepath}")
        print("\nProchaines étapes :")
        print(f"1. Assurez-vous que le chemin '{output_filepath}' est correct et que le fichier existe.")
        print(f"2. Ajoutez 'demo/patient_demo1.xml' à la clé 'demo' dans le fichier '__manifest__.py' de votre module '{module_name}'.")
        print("3. Redémarrez votre serveur Odoo.")
        print("4. Tentez de mettre à jour votre module dans Odoo en cochant 'Charger les données de démonstration'.")
        print("\nRelisez l'avertissement ci-dessus. Le chargement de ce fichier va très probablement échouer.")


    except IOError as e:
        print(f"Erreur lors de l'écriture du fichier {output_filepath}: {e}")
    except Exception as e:
        print(f"Une erreur inattendue s'est produite : {e}")


if __name__ == "__main__":
    generate_patient_xml_demo_data_only_name_strictly()