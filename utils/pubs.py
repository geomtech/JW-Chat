
def sanitize_reference(reference):
    return reference.replace('_F', '')


def get_publication(reference):
    if 'lff' in reference:
        return 'Vivez Pour Toujours'
    elif 'nwt' in reference:
        return 'Bible - Traduction du Monde Nouveau'
    elif 'w' in reference:
        return 'Tour de Garde'
    elif 'g' in reference:
        return 'Réveillez-Vous !'
    elif 'mwb' in reference:
        return "Cahier pour la réunion Vie chrétienne et ministère"
    elif 'dx20' in reference:
        return 'Index 2020 des publications des Témoins de Jéhovah'
    elif 'syr' in reference:
        year = sanitize_reference(year)
        year = "20" + str(reference.split('syr')[1])

        return "Rapport mondial des Témoins de Jéhovah pour l’année de service " + year
    elif "S-38" in reference:
        return "Instructions pour la réunion Vie chrétienne et ministère"
    elif "es25" in reference:
        return "Examinons les Écritures chaque jour"
    elif "scl" in reference:
        return "Versets pour la vie chrétienne"
    elif "bt" in reference:
        return "Rends pleinement témoignage au sujet du royaume de Dieu"
    elif "lmd" in reference:
        return "Allez et faites des disciples, avec amour"
    elif "th" in reference:
        return "Applique-toi à la lecture et à l'enseignement"
    elif "rr" in reference:
        return "Le culte pur de Jéhovah enfin rétabli !"
    else:
        return str(reference).upper()