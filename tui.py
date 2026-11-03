from datetime import datetime

from domaine import GrandJeu, ErreurJeu


def demander_heure(question):
    while True:
        texte = input(question).strip().replace("h", ":")
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
        fin = demander_heure("Heure de fin : ")
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
        elif choix in ["3", "4", "5"] and (jeu is None or not jeu.a_une_rotation()):
            print("Il faut d'abord préparer un jeu (1) ou charger l'exemple (2).")
        elif choix == "3":
            print("\n".join(lignes_par_equipe(jeu)))
        elif choix == "4":
            print("\n".join(lignes_par_poste(jeu)))
        elif choix == "5":
            enregistrer(jeu)
        else:
            print("Je n'ai pas compris, choisis un numéro du menu.")


if __name__ == "__main__":
    main()