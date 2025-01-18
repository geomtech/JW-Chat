
def get_publication(reference):
    if 'lff' in reference:
        return 'Vivez pour toujours - Cours bilique interactif'
    elif 'nwt' in reference:
        return 'Bible - Traduction du Monde Nouveau'
    elif 'w' in reference:
        return 'Tour de Garde'
    elif 'g' in reference:
        return 'Réveillez-vous !'
    else:
        return 'Autre publication (' + reference + ')'