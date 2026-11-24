# Interface en terminal. C'est le seul fichier qui fait des print et des input.
# Lancement : python tui.py

from datetime import datetime

from domaine import GrandJeu, ErreurJeu

FIN_PAR_DEFAUT = datetime.strptime("17:30", "%H:%M")  # fin habituelle d'un grand jeu (EF-01.8)


def heure_actuelle():
    # Les heures du jeu n'ont pas de date (strptime les place le 1er janvier 1900) :
    # on ramène l'heure de l'ordinateur à ce même jour pour pouvoir les comparer.
    return datetime.strptime(datetime.now().strftime("%H:%M"), "%H:%M")


def demander_heure(question, defaut=None):
    """Demande une heure à l'utilisateur jusqu'à obtenir une réponse valide.

    PRE : question est une chaîne (str) ; defaut est None ou un datetime.
    POST : renvoie un datetime du 1er janvier 1900 à l'heure tapée.
           Sont acceptés « 14:00 », « 14h00 », « 14H00 », « 14h » (= 14h00)
           et « 9h5 » (= 09h05), avec ou sans espaces autour.
           Si la réponse est vide et que defaut n'est pas None, renvoie defaut.
           Après chaque réponse incomprise (vide sans défaut, « 25h », « midi »…),
           affiche un message d'aide et repose la question.
    RAISES : rien (une réponse incomprise est redemandée).
    """
    while True:
        texte = input(question).strip().lower()
        if texte == "" and defaut is not None:
            return defaut
        texte = texte.replace("h", ":")
        if texte.endswith(":"):
            texte = texte + "00"  # « 14h » veut dire 14h00
        try:
            return datetime.strptime(texte, "%H:%M")
        except ValueError:
            print("Je n'ai pas compris. Écris l'heure comme 14:00 ou 14h00.")


def demander_noms(question, ajouter):
    print("(laisse vide et appuie sur Entrée quand tu as fini)")
    while True:
        nom = input(question)
        if nom.strip() == "":
            return
        try:
            ajouter(nom)
        except ErreurJeu as erreur:
            print(f"Oups, {erreur}")


def preparer_jeu():
    print("\n--- Nouveau grand jeu ---")
    nom = input("Nom du jeu : ")
    while True:
        debut = demander_heure("Heure de début : ")
        fin = demander_heure("Heure de fin (Entrée = 17h30) : ", FIN_PAR_DEFAUT)
        try:
            jeu = GrandJeu(nom, debut, fin)
            break
        except ErreurJeu as erreur:
            print(f"Oups, {erreur}")

    print("\nLes équipes :")
    demander_noms("  Équipe : ", jeu.ajouter_equipe)
    print("\nLes postes :")
    demander_noms("  Poste : ", jeu.ajouter_poste)
    return jeu


def jeu_exemple():
    jeu = GrandJeu("La malédiction du capitaine Barbe-Grise",
                   datetime.strptime("14:00", "%H:%M"),
                   datetime.strptime("17:30", "%H:%M"))
    for nom in ["Loups", "Aigles", "Castors", "Renards", "Faucons", "Ours", "Lynx"]:
        jeu.ajouter_equipe(nom)
    for nom in ["Corde", "Boussole", "Énigme", "Course", "Nœuds", "Trésor"]:
        jeu.ajouter_poste(nom)
    return jeu


def lancer_rotation(jeu):
    try:
        jeu.calculer_rotation()
    except ErreurJeu as erreur:
        print(f"\nImpossible de faire la rotation : {erreur}")
        return
    premier = jeu.creneaux[0]
    dernier = jeu.creneaux[-1]
    print(f"\nC'est bon ! Rotation de « {jeu.nom} » prête, sans aucune collision.")
    print(f"{len(jeu.equipes)} équipes, {len(jeu.creneaux)} créneaux, "
          f"de {premier.debut:%Hh%M} à {dernier.fin:%Hh%M}.")


def lignes_par_equipe(jeu):
    lignes = ["===== PLANNING PAR ÉQUIPE ====="]
    for equipe in jeu.equipes:
        lignes.append("")
        lignes.append(equipe.nom)
        for passage in jeu.passages_de(equipe):
            lignes.append(f"  {passage.creneau}  {passage.poste.nom}")
    return lignes


def lignes_par_poste(jeu):
    # Une fiche par poste, pour que chaque animateur sache qui arrive et quand
    lignes = ["===== PLANNING PAR POSTE ====="]
    for poste in jeu.positions:
        lignes.append("")
        lignes.append(poste.nom)
        for creneau in jeu.creneaux:
            equipe = jeu.equipe_au_poste(poste, creneau)
            if equipe is None:
                lignes.append(f"  {creneau}  (libre)")
            else:
                lignes.append(f"  {creneau}  {equipe.nom}")
    return lignes


def lignes_suivi(jeu, maintenant):
    # Où est chaque équipe, où elle va ensuite, et l'état de chacune de ses épreuves
    creneau = jeu.creneau_a(maintenant)
    if creneau is None:
        lignes = [f"===== SUIVI À {maintenant:%Hh%M} : aucun créneau en cours ====="]
    else:
        lignes = [f"===== SUIVI À {maintenant:%Hh%M} : créneau {creneau} ====="]
    for equipe in jeu.equipes:
        actuel = jeu.passage_actuel(equipe, maintenant)
        suivant = jeu.passage_suivant(equipe, maintenant)
        ici = actuel.poste.nom if actuel is not None else "pas d'épreuve en cours"
        if suivant is None:
            ensuite = "plus rien"
        else:
            ensuite = f"{suivant.poste.nom} à {suivant.creneau.debut:%Hh%M}"
        lignes.append("")
        lignes.append(f"{equipe.nom} : maintenant {ici}, ensuite {ensuite}")
        for passage in jeu.passages_de(equipe):
            lignes.append(f"  {passage.creneau}  {passage.poste.nom:<14} {passage.etat(maintenant).value}")
    return lignes


def suivre_jeu(jeu):
    maintenant = demander_heure("Quelle heure est-il ? (Entrée = maintenant) ", heure_actuelle())
    print("\n".join(lignes_suivi(jeu, maintenant)))


def choisir_passage(jeu, maintenant):
    # d'abord les épreuves à noter, puis celles déjà notées (pour corriger)
    a_noter = jeu.passages_a_noter(maintenant)
    deja_notes = [p for p in jeu.passages if p.score is not None]
    choix_possibles = a_noter + deja_notes
    if len(choix_possibles) == 0:
        print("Aucune épreuve à noter pour l'instant.")
        return None
    print("\nÉpreuves à noter :")
    if len(a_noter) == 0:
        print("  (aucune)")
    for numero, p in enumerate(a_noter, start=1):
        print(f"  {numero:>2}. {p.creneau}  {p.equipe.nom} au poste {p.poste.nom}")
    if len(deja_notes) > 0:
        print("Épreuves déjà notées (pour corriger) :")
        for numero, p in enumerate(deja_notes, start=len(a_noter) + 1):
            print(f"  {numero:>2}. {p.creneau}  {p.equipe.nom} au poste {p.poste.nom} : {p.score} pts")
    texte = input("Numéro de l'épreuve (Entrée pour annuler) : ").strip()
    if texte == "":
        return None
    if not texte.isdigit() or not 1 <= int(texte) <= len(choix_possibles):
        print("Je n'ai pas compris, choisis un numéro de la liste.")
        return None
    return choix_possibles[int(texte) - 1]


def encoder_un_score(jeu):
    # F-04 : l'animateur donne le score par talkie, on l'encode ou on le corrige
    maintenant = demander_heure("Quelle heure est-il ? (Entrée = maintenant) ", heure_actuelle())
    passage = choisir_passage(jeu, maintenant)
    if passage is None:
        return
    if passage.score is not None:
        print(f"Score actuel : {passage.score}. Tape le nouveau score pour le corriger.")
    try:
        valeur = int(input("Score (0 à 10) : ").strip())
    except ValueError:
        print("Oups, le score doit être un nombre entier de 0 à 10.")
        return
    try:
        if passage.score is None:
            jeu.encoder_score(passage.equipe, passage.creneau, valeur, maintenant)
            print("Score enregistré.")
        else:
            jeu.corriger_score(passage.equipe, passage.creneau, valeur)
            print("Score corrigé.")
    except ErreurJeu as erreur:
        print(f"Oups, {erreur}")


def lignes_classement(jeu):
    lignes = ["===== CLASSEMENT ====="]
    for ligne in jeu.classement():
        lignes.append(f"  {ligne.rang:>2}. {ligne.equipe.nom:<12} {ligne.total:>3} pts")
    return lignes


def enregistrer(jeu):
    lignes = [jeu.nom, ""] + lignes_par_equipe(jeu) + [""] + lignes_par_poste(jeu)
    with open("planning.txt", "w", encoding="utf-8") as fichier:
        fichier.write("\n".join(lignes))
    print("Planning enregistré dans planning.txt, prêt à imprimer.")


def main():
    jeu = None
    while True:
        print("\n========== Grands jeux des Hérons ==========")
        print(" 1. Préparer un nouveau grand jeu")
        print(" 2. Charger l'exemple (7 équipes, 6 postes)")
        print(" 3. Voir le planning des équipes")
        print(" 4. Voir le planning des postes")
        print(" 5. Enregistrer le planning dans un fichier")
        print(" 6. Voir le classement")
        print(" 7. Suivre le jeu (où est chaque équipe)")
        print(" 8. Encoder ou corriger un score")
        print(" 0. Quitter")
        choix = input("Ton choix : ").strip()

        if choix == "0":
            print("À la prochaine, et bon jeu !")
            break
        elif choix == "1":
            jeu = preparer_jeu()
            lancer_rotation(jeu)
        elif choix == "2":
            jeu = jeu_exemple()
            lancer_rotation(jeu)
        elif choix in ["3", "4", "5", "6", "7", "8"] and (jeu is None or not jeu.a_une_rotation()):
            print("Il faut d'abord préparer un jeu (1) ou charger l'exemple (2).")
        elif choix == "3":
            print("\n".join(lignes_par_equipe(jeu)))
        elif choix == "4":
            print("\n".join(lignes_par_poste(jeu)))
        elif choix == "5":
            enregistrer(jeu)
        elif choix == "6":
            print("\n".join(lignes_classement(jeu)))
        elif choix == "7":
            suivre_jeu(jeu)
        elif choix == "8":
            encoder_un_score(jeu)
        else:
            print("Je n'ai pas compris, choisis un numéro du menu.")


if __name__ == "__main__":
    main()
