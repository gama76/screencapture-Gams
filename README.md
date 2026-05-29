# Gestionnaire de screenshots

Application Python avec interface graphique pour capturer des screenshots dans un dossier configurable.

## Fonctionnalites

- Raccourci global configurable, par defaut `Ctrl+Shift+S`
- Dossier de sortie configurable
- Captures PNG horodatees
- Capture de tout l'ecran ou d'une zone selectionnee
- Couleur configurable pour le rectangle de selection de zone
- Theme clair ou sombre, sauvegarde automatiquement
- Historique automatique des images du dossier
- Apercu des images
- Copie de l'image selectionnee dans le presse-papiers
- Edition basique: dessin, cadre colore, logos numerotes, logos de signalisation, recadrage, rotation, miroir, niveaux de gris, sauvegarde, copie fichier ou presse-papiers

## Lancement

Version compilee:

```powershell
.\dist\GestionnaireScreenshots\GestionnaireScreenshots.exe
```

Ou:

```powershell
.\lancer_exe.bat
```

Version Python:

```powershell
.\.venv\Scripts\python.exe screenshot_manager.py
```

Si Pillow n'est pas installe:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Raccourcis

Entrez le raccourci sous forme texte, par exemple:

- `ctrl+shift+s`
- `alt+printscreen`
- `ctrl+alt+f9`

Cliquez ensuite sur `Appliquer`.

Le raccourci utilise le mode choisi dans l'interface:

- `Ecran complet` capture tous les ecrans
- `Zone` affiche une surcouche, puis sauvegarde le rectangle selectionne

Les boutons `Tout l'ecran` et `Selection zone` restent disponibles pour lancer directement un type de capture.

La couleur du rectangle de selection se regle depuis l'ecran principal.

Dans l'editeur, utilisez `Couleur`, puis le mode `Dessin` ou `Cadre`. `Trait` controle l'epaisseur du dessin ou du cadre.

Les boutons d'edition affichent maintenant un pictogramme. `Numero`, `Warning`, `Interdit`, `Info` et `Valide` placent un logo au clic sur l'image. `Taille logo` controle la taille des pictogrammes. Le champ `N` est un compteur separe utilise uniquement par `Numero`. Les logos sont rendus avec anti-aliasing pour des bords plus propres.

Le bouton `Copier l'image` copie l'image selectionnee dans le presse-papiers Windows. Dans l'editeur, le bouton `Copier` copie l'image modifiee en cours.
