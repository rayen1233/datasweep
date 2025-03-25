# Architecture Technique de DataSweep

## 1. Vue d'ensemble

**DataSweep** est un outil informatique conçu pour simplifier la gestion des fichiers sur un système. Il permet aux utilisateurs de :

- Supprimer des fichiers et dossiers selon des critères précis (date, extensions, taille, exceptions)
- Rechercher et supprimer des doublons dans un répertoire
- Analyser l'utilisation de l'espace disque par type de fichier
- Planifier des tâches automatisées pour une suppression régulière
- Exporter des rapports détaillés au format PDF, Excel ou CSV

Le programme repose sur une architecture modulaire, où chaque fonctionnalité est encapsulée dans des classes et méthodes distinctes pour garantir la clarté, la maintenabilité et la scalabilité du code.

## 2. Composants Principaux

### 2.1 Interface Graphique
- **Bibliothèques utilisées** : `tkinter`, `ttkthemes`
- **Rôle** : Offrir une interface utilisateur moderne et intuitive
- **Fonctionnalités principales** :
  - Navigation entre les différents modes (critères, doublons, analyse, planification)
  - Saisie ou sélection des paramètres
  - Prévisualisation des fichiers concernés
  - Mode sombre/clair pour une expérience utilisateur optimale
  - Tableau de bord avec statistiques en temps réel
  - Graphiques d'utilisation du disque
  - Export de rapports

### 2.2 Gestion des Fichiers et Dossiers
- **Bibliothèques utilisées** : `os`, `shutil`
- **Rôle** : Manipuler les fichiers et dossiers du système
- **Fonctionnalités principales** :
  - Parcours récursif des dossiers
  - Suppression des fichiers et dossiers
  - Calcul des tailles et statistiques
  - Gestion des erreurs et exceptions

### 2.3 Analyse et Filtrage
- **Bibliothèques utilisées** : `datetime`, `hashlib`, `matplotlib`, `pandas`
- **Rôle** : Analyser et filtrer les fichiers selon différents critères
- **Fonctionnalités principales** :
  - Calcul des empreintes MD5 pour les doublons
  - Analyse de l'espace disque par type de fichier
  - Génération de graphiques et statistiques
  - Export de rapports détaillés

### 2.4 Planification de Tâches
- **Bibliothèque utilisée** : `schedule`
- **Rôle** : Automatiser les tâches selon une fréquence définie
- **Fonctionnalités principales** :
  - Planification de tâches quotidiennes, hebdomadaires ou mensuelles
  - Sauvegarde des tâches planifiées
  - Exécution automatique à l'heure définie
  - Notifications de complétion

## 3. Organisation du Code

Le code est structuré en plusieurs parties :

1. **Classe principale (`ModernFileManager`)** :
   - Initialisation de l'interface graphique
   - Gestion des thèmes et styles
   - Coordination des différentes fonctionnalités

2. **Frames fonctionnels** :
   - Menu principal
   - Suppression avec critères
   - Recherche de doublons
   - Analyse de l'espace disque
   - Planification de tâches

3. **Gestion asynchrone** :
   - Utilisation de `asyncio` et `threading`
   - Opérations en arrière-plan
   - Mise à jour de l'interface en temps réel

4. **Validation et Sécurité** :
   - Vérification des chemins
   - Gestion des erreurs
   - Confirmation des actions critiques

## 4. Flux de Données

1. **Initialisation** :
   - Chargement des tâches planifiées
   - Configuration de l'interface
   - Démarrage du monitoring

2. **Opérations** :
   - Saisie des paramètres
   - Validation des entrées
   - Exécution des tâches
   - Mise à jour de l'interface

3. **Export** :
   - Génération des rapports
   - Sauvegarde des données
   - Notification des résultats