import sqlite3

# Connexion à la base de données (crée le fichier s'il n'existe pas)
conn = sqlite3.connect('radeec.db')
cursor = conn.cursor()

# Définition de la table users avec consommation mensuelle intégrée
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        prenom TEXT NOT NULL,
        numero_de_compte TEXT NOT NULL,
        mois TEXT NOT NULL,
        consommation REAL NOT NULL,
        adresse TEXT NOT NULL
    )
''')

# Définition de la table factures
cursor.execute('''
    CREATE TABLE IF NOT EXISTS factures (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_de_compte TEXT NOT NULL,
        mois TEXT NOT NULL,
        montant REAL NOT NULL,
        statut TEXT NOT NULL,
        date_paiement TEXT
    )
''')

# Fonction pour ajouter un enregistrement d'utilisateur avec consommation mensuelle
def ajouter_utilisateur(nom, prenom, numero_de_compte, mois, consommation, adresse):
    cursor.execute('''
        INSERT INTO users (nom, prenom, numero_de_compte, mois, consommation, adresse)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (nom, prenom, numero_de_compte, mois, consommation, adresse))
    conn.commit()

# Fonction pour ajouter une facture
def ajouter_facture(numero_de_compte, mois, montant, statut, date_paiement=None):
    cursor.execute('''
        INSERT INTO factures (numero_de_compte, mois, montant, statut, date_paiement)
        VALUES (?, ?, ?, ?, ?)
    ''', (numero_de_compte, mois, montant, statut, date_paiement))
    conn.commit()

# Exemple d'ajout d'un utilisateur avec des consommations mensuelles
ajouter_utilisateur("Ahmed", "El Mansouri", "123456", "2023-07", 20.5, "123 Rue de la Paix, settat")
ajouter_utilisateur("Ahmed", "El Mansouri", "123456", "2023-08", 25.1, "123 Rue de la Paix, settat")
ajouter_utilisateur("Fatima", "Zahi", "654321", "2023-07", 18.7, "456 Avenue Mohammed V, settat")
ajouter_utilisateur("Fatima", "Zahi", "654321", "2023-08", 19.3, "456 Avenue Mohammed V, settat")
ajouter_utilisateur("Souad", "Zriouel", "112233", "2023-07", 22.4, "789 Boulevard Hassan II, settat")
ajouter_utilisateur("Souad", "Zriouel", "112233", "2023-08", 23.9, "789 Boulevard Hassan II, settat")

# Exemple d'ajout de factures
ajouter_facture("123456", "2024-08", 300.50, "Non payée")
ajouter_facture("123456", "2024-07", 325.75, "Payée", "2023-08-15")
ajouter_facture("654321", "2023-07", 200.00, "Payée", "2023-07-20")
ajouter_facture("654321", "2023-08", 210.00, "Non payée")

# Fermeture de la connexion
conn.close()
