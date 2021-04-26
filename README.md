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