# JW Chat

JW Chat est une application web qui utilise l'intelligence artificielle pour aider les utilisateurs à rechercher et étudier des publications de JW.ORG. L'application permet également de gérer les utilisateurs, les paiements et les sessions de chat.

## Fonctionnalités

- **Recherche AI** : Utilise l'API OpenAI pour rechercher des articles pertinents sur JW.ORG.
- **Gestion des utilisateurs** : Inscription, connexion, et gestion des utilisateurs avec des rôles administratifs.
- **Paiements** : Intégration avec Stripe pour gérer les paiements et les crédits des utilisateurs.
- **Chat en temps réel** : Utilise Flask-SocketIO pour permettre des sessions de chat en temps réel.

## Captures d'écrans

![image](https://github.com/user-attachments/assets/54a20c48-fbdb-41cb-bc5e-16f0927f5a4e)
![image](https://github.com/user-attachments/assets/e31b1638-7e55-4452-9f73-5a04f26da36a)
![image](https://github.com/user-attachments/assets/0ff3699b-6250-41b2-8f6b-eb3ffda25c97)
![image](https://github.com/user-attachments/assets/a227d8d0-ae25-439d-ab3f-7ba01fe06d66)
![image](https://github.com/user-attachments/assets/490f3ff6-b5f8-447d-adfb-64095fb99b65)

## Prérequis

Avant de commencer, assurez-vous d'avoir les éléments suivants installés sur votre machine :

- **Python 3.8+** : L'application nécessite Python version 3.8 ou supérieure.
- **pip** : L'outil de gestion des packages pour Python.
- **Git** : Pour cloner le dépôt.
- **Virtualenv** : Pour créer des environnements virtuels Python.
- **MongoDB** : Base de données NoSQL utilisée par l'application.
- **Redis** : Utilisé pour la gestion des sessions en temps réel.
- **Stripe Account** : Pour gérer les paiements.
- **Compte OpenAI** : Pour l'API OpenAI pour l'assistant et le paramétrer : [OPENAI.md](OPENAI.md)


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
    export OPENAI_API_KEY=""
    export BREVO_API_KEY=""
    export MONGODB_URL=""
    export SECRET_KEY=""
    export REDIS_URL=""
    export PORT=5000
    export STRIPE_API_KEY=""
    export STRIPE_PUBLIC_KEY=""
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
