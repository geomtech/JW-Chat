# JW Chat

JW Chat est une application web qui utilise l'intelligence artificielle pour aider les utilisateurs à rechercher et étudier des publications de JW.ORG. L'application permet également de gérer les utilisateurs, les paiements et les sessions de chat.

## Fonctionnalités

- **Recherche AI** : Utilise l'API OpenAI pour rechercher des articles pertinents sur JW.ORG.
- **Gestion des utilisateurs** : Inscription, connexion, et gestion des utilisateurs avec des rôles administratifs.
- **Paiements** : Intégration avec Stripe pour gérer les paiements et les crédits des utilisateurs.
- **Chat en temps réel** : Utilise Flask-SocketIO pour permettre des sessions de chat en temps réel.

## Prérequis

Avant de commencer, assurez-vous d'avoir les éléments suivants installés sur votre machine :

- **Python 3.8+** : L'application nécessite Python version 3.8 ou supérieure.
- **pip** : L'outil de gestion des packages pour Python.
- **Git** : Pour cloner le dépôt.
- **Virtualenv** : Pour créer des environnements virtuels Python.
- **MongoDB** : Base de données NoSQL utilisée par l'application.
- **Redis** : Utilisé pour la gestion des sessions en temps réel.
- **Stripe Account** : Pour gérer les paiements.


## Installation

1. Clonez le dépôt :
    ```sh
    git clone https://github.com/geomtech/JW-Chat.git
    cd JW-Chat
    ```

2. Créez un environnement virtuel et activez-le :
    ```sh
    python -m venv venv
    source venv/bin/activate  # Sur Windows: venv\Scripts\activate
    ```

3. Installez les dépendances :
    ```sh
    pip install -r requirements.txt
    ```

4. Configurez les variables d'environnement nécessaires :
    ```sh
    export FLASK_APP=app.py
    export FLASK_ENV=development
    export SECRET_KEY=votre_cle_secrete
    export STRIPE_API_KEY=votre_cle_stripe
    export MONGODB_URL=votre_url_mongodb
    export REDIS_URL=votre_url_redis
    ```

5. Lancez l'application :
    ```sh
    flask run
    ```

## Utilisation

- Accédez à l'application via `http://127.0.0.1:5000`.
- Inscrivez-vous et connectez-vous pour accéder aux fonctionnalités.
- Utilisez le chat pour poser des questions et obtenir des réponses basées sur le site JW.ORG.

## Structure du projet

- `app.py` : Point d'entrée de l'application Flask.
- `blueprints/` : Contient les blueprints pour les différentes sections de l'application (admin, comptes).
- `static/` : Contient les fichiers statiques (CSS, JS).
- `templates/` : Contient les templates HTML.
- `utils/` : Contient les fonctions utilitaires.

## Contribuer

Les contributions sont les bienvenues ! Veuillez soumettre une pull request ou ouvrir une issue pour discuter des changements que vous souhaitez apporter.

## Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.
