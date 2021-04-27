# HFR Token Scraper

## Fonctionnement

Le token scraper va "lire" sur la blockchain BSC les nouveaux tokens disponibles sr PancakeSwap pour ensuite faire une série de vérifications:
* le contract est validé sur la BSC
* Le contract n'a pas les fonctions mint(), pause() ou transfernewun() (scams typiques)
* Le owner du contrat est soit une adresse "dead" soit un contrat
* Minimum 10 transactions sur les 10 dernières minutes

Le scraper n'est qu'une première étape pour trouver des coins - n'oubliez pas de faire le vérifications d'usage (holder, LP, etc...)

NOTE: pendant la transition vers PCS v2, les liens vers la LP peuvent être cassés, dans ce cas le mieux est de passer par Poocoin pour trouver la LP

## Installation

* Python 3.7.6+
* Dépendances dans le fichier requirements.txt
* Créer un fichier avec comme nom `.env` et à l'intérieur insérer une ligne: `API_KEY=XXX` (en remplacant le XXX avec votre clé BSCSCan)  - pour obtenir une clé il faut créer un compte (gratuit) sur BSCScan
* Lancer avec `python hfr_token_scrape_v2.py` et ensuite naviguer sur `127.0.0.1:5000` pour accéder au scraper

## HOWTO

Méthode d'installation et d'utilisation du scrapper sous W10

 
PREREQUIS : 
 - Télécharger et décompresser le scrapper
 - Installer Python (version > à 3.7). Le plus simple est de l'installler via le store windows 10.
 - Installer visual studio (Xcode pour les possesseur de mac);
 - Créer un compte sur BSCSCAN, et aller chercher son API Key

ACTIONS :

 - Dans le dossier où on a décompréssé le scrapper, créée un fichier .env et insérer à l'intérieur une ligne API_KEY=XXX, XXX étant votre API Key qu'il faut mettre entre guillemets.
 - Lancer powershell
 - Se placer dans le dossier du scrapper (commande CD C:\chemin du dossier)
 - Taper la commande PYTHON .\hfr_token-scrape_v2.py
 - La une série d'erreur va apparaître. Chaque fois qu'une erreur apparaît c'est qu'il manque une dépendance. Il faudra 
   l'installer, puis relancer la commande PYTHON .\hfr_token-scrape_V2.py jusqu'à ce qu'il n'y ai plus d'erreurs
 - Pour installer une dépendance, il suffit de lire le message d'erreur et de lancer la commande PIP INSTALL nomdeladépendance
 - Par exemple, si on a l'erreur "No module named 'aiohttp' ", il faudra taper PIP INSTALL aiohttp. 
 - Petite particularité pour dotenv. Si cela ne fonctionne pas installer à la place python-dotenv.
 - Quand tout est bon, vous devriez avoir un message du genre "Running on http://127.0.0.1.5000/"
 - Copier l'adresse http dans un navigateur et enjoy (le programme doit tourner, donc laisser powershell ouvert).



