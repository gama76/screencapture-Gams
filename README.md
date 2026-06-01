# Gestionnaire de screenshots

Application Windows avec interface graphique pour capturer, organiser et annoter des screenshots.

## Fonctionnalites

- Capture PNG horodatee
- Capture de tout l'ecran ou d'une zone selectionnee
- Raccourci global configurable, par defaut `Ctrl+Shift+S`
- Dossier de sortie configurable
- Par defaut, le dossier `screenshots` est cree en chemin relatif dans `./screenshots`
- Couleur configurable pour le rectangle de selection de zone
- Theme clair ou sombre, sauvegarde automatiquement
- Historique automatique des images du dossier
- Apercu des images
- Copie d'une image dans le presse-papiers Windows
- Suppression d'une image depuis l'historique avec confirmation
- Renommage d'une image depuis l'historique
- Edition: dessin, cadres colores, floutage de zone, recadrage, rotation, miroir, niveaux de gris
- Annulation dans l'editeur avec `Ctrl+Z`
- Logos d'annotation: numero, warning, interdit, info, valide
- Logos rendus avec anti-aliasing pour des bords plus propres
- Verification de mise a jour au demarrage via un manifeste distant

## Lancement

Version compilee actuelle:

```powershell
.\dist\GestionnaireScreenshots_v17\GestionnaireScreenshots_v17.exe
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
- URL du manifeste de mise a jour

Par defaut, `config.json` et `screenshots` sont crees dans `./`, c'est-a-dire le dossier depuis lequel l'application est lancee.

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

## Renommage

Depuis l'historique, selectionnez une image puis cliquez sur `Renommer`.

Le renommage conserve l'extension si vous ne la saisissez pas. Les caracteres interdits Windows sont refuses.

## Mises A Jour

L'application peut verifier automatiquement si une nouvelle version existe.

Depot configure par defaut:

```text
https://github.com/gama76/screencapture-Gams
```

Dans le champ `Mise a jour`, vous pouvez indiquer:

- l'URL du depot GitHub
- l'URL API GitHub `releases/latest`
- l'URL d'un manifeste JSON distant

Puis cliquez sur `Verifier`.
Si l'URL est sauvegardee, l'application refera la verification au prochain demarrage.

### Avec GitHub Releases

Publiez une release sur GitHub avec:

- un tag superieur a la version locale, par exemple `v0.13.0`
- un asset `.exe`, par exemple `GestionnaireScreenshots.exe`

L'application lit automatiquement:

- `tag_name` comme version
- le premier asset `.exe` comme fichier a telecharger
- le corps de la release comme notes

Si le message indique qu'aucune mise a jour exploitable n'a ete trouvee, verifiez:

- le depot GitHub est public
- au moins une release existe
- le tag de la release est superieur a la version locale, par exemple `v0.13.0`
- un fichier `.exe` est attache dans les assets de la release

### Avec Un Manifeste JSON

Format attendu:

```json
{
  "version": "0.12.0",
  "download_url": "https://exemple.com/GestionnaireScreenshots.exe",
  "notes": "Corrections et ameliorations"
}
```

Regles:

- `version` doit etre superieure a la version locale de l'application
- idealement, le tag GitHub doit correspondre a `APP_VERSION` dans `screenshot_manager.py`
- `download_url` doit pointer vers le nouvel `.exe`
- la mise a jour automatique fonctionne uniquement depuis la version compilee `.exe`
- apres telechargement, l'application se ferme, remplace l'exe courant, puis redemarre

Si la mise a jour se repropose en boucle, cela signifie generalement que la release GitHub a un tag plus recent que la version inscrite dans l'exe, ou que Windows n'a pas encore libere l'exe au moment du remplacement. L'application memorise maintenant la derniere version traitee et le script de remplacement attend que le fichier soit disponible.
