# Guide d'Utilisation de DataSweep

Ce guide vous aidera à utiliser **DataSweep** efficacement. Il détaille les étapes nécessaires pour configurer les critères de suppression, prévisualiser les fichiers concernés, analyser l'espace disque, rechercher et supprimer des doublons, ainsi que planifier des tâches automatisées.

## 1. Installation

1. Assurez-vous d'avoir Python 3.6 ou supérieur installé sur votre système
2. Installez les dépendances requises :
   ```bash
   pip install -r requirements.txt
   ```
3. Lancez le programme :
   ```bash
   python source/Projet.py
   ```

## 2. Interface Principale

L'interface principale de DataSweep comprend :

- Un menu principal avec les options suivantes :
  - Effacer avec des critères
  - Supprimer les doublons
  - Analyser l'espace disque
  - Planifier une tâche

- Une barre de statut en bas de la fenêtre affichant :
  - L'état actuel du programme
  - Une barre de progression pour les opérations longues

- Un mode sombre/clair accessible via le menu "Affichage"

## 3. Fonctionnalités

### 3.1 Suppression avec Critères

1. Sélectionnez "Effacer avec des critères" dans le menu principal
2. Configurez les paramètres :
   - Dossier cible
   - Date de référence (format AAAA-MM-JJ)
   - Extensions de fichiers
   - Taille minimale
   - Exceptions
3. Cliquez sur "Prévisualiser" pour voir les fichiers concernés
4. Confirmez la suppression si tout est correct

### 3.2 Suppression des Doublons

1. Sélectionnez "Supprimer les doublons"
2. Choisissez le dossier à analyser
3. Cliquez sur "Rechercher les doublons"
4. Vérifiez la liste des doublons trouvés
5. Confirmez la suppression

### 3.3 Analyse de l'Espace Disque

1. Sélectionnez "Analyser l'espace disque"
2. Choisissez le dossier à analyser
3. Cliquez sur "Analyser"
4. Consultez les résultats :
   - Statistiques en temps réel
   - Graphiques d'utilisation
   - Distribution des fichiers par type
5. Exportez les résultats au format PDF, Excel ou CSV

### 3.4 Planification de Tâches

1. Sélectionnez "Planifier une tâche"
2. Configurez la tâche :
   - Dossier cible
   - Type de tâche
   - Fréquence (quotidienne, hebdomadaire, mensuelle)
   - Heure d'exécution
   - Options avancées (rétention, notifications)
3. Cliquez sur "Planifier"
4. Vérifiez la liste des tâches planifiées

## 4. Raccourcis Clavier

- `Ctrl+Q` : Quitter l'application
- `Ctrl+N` : Effacer avec des critères
- `Ctrl+D` : Supprimer les doublons
- `Ctrl+A` : Analyser l'espace disque
- `Ctrl+P` : Planifier une tâche
- `Ctrl+M` : Retour au menu principal
- `F5` : Rafraîchir le tableau de bord
- `F1` : Afficher le manuel

## 5. Conseils d'Utilisation

- Toujours vérifier la prévisualisation avant de confirmer une suppression
- Utiliser les exceptions pour protéger des fichiers importants
- Exporter régulièrement les rapports pour garder une trace des opérations
- Configurer des notifications pour les tâches planifiées importantes
- Utiliser le mode sombre en conditions de faible luminosité