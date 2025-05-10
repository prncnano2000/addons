import sys
import random
import os # Importer le module os pour la gestion des chemins

def generate_medecin_xml_demo_data_to_file():
    """
    Génère le contenu XML des données de démonstration pour le modèle medecin
    et l'écrit dans un fichier spécifique.
    """
    module_name = "gestion_hospital"
    model_name = "gestion_hospital.medecin"
    # Chemin complet où enregistrer le fichier XML
    output_filepath = "/home/jordan/Bureau/odoo15/addons/gestion_hospital/demo/medecin_demo1.xml"

    print("--- Générateur de données de démo pour le modèle Médecin ---")
    print(f"Le fichier sera enregistré dans : {output_filepath}")

    while True:
        try:
            num_records_str = input("Combien d'enregistrements de médecins voulez-vous générer ? ")
            num_records = int(num_records_str)
            if num_records <= 0:
                print("Veuillez entrer un nombre positif.")
            else:
                break
        except ValueError:
            print("Entrée invalide. Veuillez entrer un nombre entier.")

    # Assurer que le répertoire de sortie existe
    output_dir = os.path.dirname(output_filepath)
    if not os.path.exists(output_dir):
        print(f"Le répertoire {output_dir} n'existe pas. Veuillez le créer manuellement.")
        return # Quitter si le répertoire n'existe pas

    try:
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(f'<?xml version="1.0" encoding="utf-8"?>\n')
            f.write(f'<odoo>\n')
            f.write(f'    <data noupdate="1">\n')

            prenoms = ["Dr. Sophie", "Dr. Antoine", "Dr. Camille", "Dr. David", "Dr. Emma", "Dr. Félix", "Dr. Léa", "Dr. Hugo", "Dr. Manon", "Dr. Nathan", "Dr. Claire", "Dr. Thomas"]
            noms = ["Petit", "Durand", "Leroy", "Moreau", "Garcia", "Lefevre", "Roux", "Fournier", "Dupont", "Dubois"]

            for i in range(1, num_records + 1):
                full_name = f"{random.choice(prenoms)} {random.choice(noms)} (Démo {i})"
                matricule_value = f"MED-GEN-{i:03}"
                record_id = f"medecin_demo_generated_{i}"

                f.write(f'        <record id="{module_name}.{record_id}" model="{model_name}">\n')
                f.write(f'            <field name="name">{full_name}</field>\n')
                f.write(f'            <field name="matricule">{matricule_value}</field>\n') # Inclusion nécessaire
                f.write(f'        </record>\n')

            f.write(f'    </data>\n')
            f.write(f'</odoo>\n')

        print(f"\nSuccessfully generated {num_records} records and saved to {output_filepath}")
        print("\nProchaines étapes :")
        print(f"1. Assurez-vous que le chemin '{output_filepath}' est correct et que le fichier existe.")
        print(f"2. Ajoutez 'demo/medecin_demo1.xml' à la clé 'demo' dans le fichier '__manifest__.py' de votre module '{module_name}'.")
        print("3. Redémarrez votre serveur Odoo.")
        print("4. Mettez à jour votre module dans Odoo en cochant 'Charger les données de démonstration'.")
        print("\nNote : Le champ 'matricule' a été inclus dans le fichier généré car il est requis et doit être unique dans votre modèle Medecin.")

    except IOError as e:
        print(f"Erreur lors de l'écriture du fichier {output_filepath}: {e}")
    except Exception as e:
        print(f"Une erreur inattendue s'est produite : {e}")


if __name__ == "__main__":
    generate_medecin_xml_demo_data_to_file()