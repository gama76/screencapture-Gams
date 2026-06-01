# Gestionnaire de screenshots

Application Windows avec interface graphique pour capturer, organiser et annoter des screenshots.

## Fonctionnalites

- Capture PNG horodatee
- Capture de tout l'ecran ou d'une zone selectionnee
- Raccourci global configurable, par defaut `Ctrl+Shift+S`
- Dossier de sortie configurable
- Couleur configurable pour le rectangle de selection de zone
- Theme clair ou sombre, sauvegarde automatiquement
- Historique automatique des images du dossier
- Apercu des images
- Copie d'une image dans le presse-papiers Windows
- Suppression d'une image depuis l'historique avec confirmation
- Edition: dessin, cadres colores, floutage de zone, recadrage, rotation, miroir, niveaux de gris
- Annulation dans l'editeur avec `Ctrl+Z`
- Logos d'annotation: numero, warning, interdit, info, valide
- Logos rendus avec anti-aliasing pour des bords plus propres

## Lancement

Version compilee actuelle:

```powershell
.\dist\GestionnaireScreenshots_v7\GestionnaireScreenshots_v7.exe
```

Lanceur recommande:

```powershell
.\lancer_exe.bat
```

Le lanceur ouvre automatiquement la version compilee la plus recente disponible.

Version Python:

```powershell
.\.venv\Scripts\python.exe screenshot_manager.py
```

Si les dependances doivent etre reinstallees:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Capture

Le mode choisi dans l'interface determine ce que fait le raccourci global:

- `Ecran complet`: capture tous les ecrans
- `Zone`: affiche une surcouche, puis sauvegarde le rectangle selectionne

Les boutons `Tout l'ecran` et `Selection zone` lancent directement un type de capture sans changer le raccourci.

## Configuration

Parametres sauvegardes dans `config.json`:

- dossier de capture
- raccourci global
- mode de capture
- couleur du rectangle de selection
- couleur par defaut de l'editeur
- theme clair/sombre

Exemples de raccourcis:

- `ctrl+shift+s`
- `alt+printscreen`
- `ctrl+alt+f9`

Apres modification, cliquez sur `Appliquer`.

## Edition

Depuis l'historique, selectionnez une image puis cliquez sur `Modifier l'image`.

Outils disponibles:

- `Dessin`: tracer librement sur l'image
- `Cadre`: tirer un rectangle colore
- `Flouter`: tirer un rectangle sur une zone a flouter
- `Recadrer`: selectionner une zone a conserver
- `Couleur`: choisir la couleur des annotations
- `Trait`: epaisseur du dessin ou du cadre
- `Taille logo`: taille des logos d'annotation
- `N`: compteur utilise uniquement par l'outil `Numero`
- `Annuler` ou `Ctrl+Z`: annule la derniere action de modification

Logos disponibles:

- `Numero`: place un rond numerote, puis incremente `N`
- `Warning`: place un pictogramme d'avertissement
- `Interdit`: place un symbole interdit
- `Info`: place un pictogramme info
- `Valide`: place un check vert

## Presse-Papiers

- `Copier l'image` copie l'image selectionnee dans l'historique
- `Copier` dans l'editeur copie l'image en cours de modification

L'image peut ensuite etre collee dans Paint, Word, Teams, Discord ou tout autre logiciel compatible.

## Suppression

Depuis l'historique, selectionnez une image puis cliquez sur `Supprimer`.

Une confirmation affiche le nom du fichier avant suppression definitive.
