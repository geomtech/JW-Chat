import requests

def send_admin_notification(user_email, brevo_api_key):
    url = "https://api.brevo.com/v3/smtp/email"
    payload = {
        "sender": {"name": "JW-Chat", "email": "no-reply@jw-ch.at"},
        "to": [{"email": "admin@jw-ch.at", "name": "Admin"}],
        "subject": "Nouvelle inscription d'utilisateur",
        "htmlContent": f"<html><body><p>Un nouvel utilisateur s'est inscrit avec l'adresse e-mail : {user_email}</p></body></html>"
    }
    headers = {
        "accept": "application/json",
        "api-key": brevo_api_key,
        "content-type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.status_code, response.json()
