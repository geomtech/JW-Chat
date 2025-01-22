
def sanitize_reference(reference):
    return reference.replace('_F', '')


def get_publication(reference):
    title = f"Autre publication ({reference.upper()})"
    image = "/static/img/article.png"

    if 'lff' in reference:
        title = 'Vivez Pour Toujours'
        image = "/static/img/lff.png"
    elif 'nwt' in reference:
        title = 'Bible - Traduction du Monde Nouveau'
        image = "/static/img/bible.png"
    elif 'w' in reference:
        title = 'Tour de Garde'
    elif 'g' in reference:
        title = 'Réveillez-Vous !'
    elif 'mwb' in reference:
        title = "Cahier pour la réunion Vie chrétienne et ministère"
    elif 'dx20' in reference:
        title = 'Index 2020 des publications des Témoins de Jéhovah'
    elif 'syr' in reference:
        year = sanitize_reference(year)
        year = "20" + str(reference.split('syr')[1])

        title = "Rapport mondial des Témoins de Jéhovah pour l’année de service " + year
    elif "S-38" in reference:
        title = "Instructions pour la réunion Vie chrétienne et ministère"
    elif "es25" in reference:
        title = "Examinons les Écritures chaque jour"
    elif "scl" in reference:
        title = "Versets pour la vie chrétienne"
        image = "/static/img/bible.png"
    elif "bt" in reference:
        title = "Rends pleinement témoignage au sujet du royaume de Dieu"
    elif "lmd" in reference:
        title = "Allez et faites des disciples, avec amour"
    elif "th" in reference:
        title = "Applique-toi à la lecture et à l'enseignement"
    elif "rr" in reference:
        title = "Le culte pur de Jéhovah enfin rétabli !"


    return {
        "title": str(title),
        "image": str(image)
    }