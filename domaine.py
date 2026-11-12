# Domaine de l'application : les données et les règles des grands jeux.
# Pas de print ni d'input ici : en cas de problème, on lève une ErreurJeu
# et c'est l'interface (tui.py) qui affiche le message.
#
# Code écrit avec l'aide de Claude (Anthropic), avec l'accord de la professeure.

from datetime import timedelta

DUREE_CRENEAU = timedelta(minutes=20)


class ErreurJeu(Exception):
    pass


class Equipe:
    def __init__(self, nom):
        self.nom = nom


class Poste:
    def __init__(self, nom, attente=False):
        self.nom = nom
        self.attente = attente  # True seulement pour le poste d'attente au QG


class Creneau:
    def __init__(self, debut):
        self.debut = debut
        self.fin = debut + DUREE_CRENEAU

    def __str__(self):
        return f"{self.debut:%Hh%M}-{self.fin:%Hh%M}"

    def contient(self, instant):
        """Indique si l'instant tombe pendant ce créneau (début compris, fin exclue)."""
        return self.debut <= instant < self.fin

    def a_commence(self, instant):
        """Indique si ce créneau a déjà commencé à cet instant."""
        return instant >= self.debut


class Passage:
    # Une équipe qui se trouve à un poste pendant un créneau
    def __init__(self, equipe, poste, creneau):
        self.equipe = equipe
        self.poste = poste
        self.creneau = creneau
        self.score = None  # pas encore de score annoncé


class LigneClassement:
    # Une ligne du classement : le rang, l'équipe et son total de points
    def __init__(self, rang, equipe, total):
        self.rang = rang
        self.equipe = equipe
        self.total = total


class Classement:
    def __init__(self, equipes, passages):
        self.equipes = equipes
        self.passages = passages

    def lignes(self):
        """Calcule le classement des équipes à partir des scores encodés (F-05).

        PRE : self.equipes est une liste d'Equipe ; chaque passage de
              self.passages a un score None ou entier de 0 à 10.
        POST : renvoie une nouvelle liste de LigneClassement, une par équipe
               de self.equipes, triée par total décroissant.
               Le total d'une équipe est la somme de ses scores encodés
               (0 si elle n'en a aucun ; les scores None sont ignorés).
               Le rang vaut 1 + le nombre d'équipes qui ont un total
               strictement plus grand : des équipes à égalité ont le même
               rang (ex aequo, QO-02) et gardent l'ordre de self.equipes.
               self.equipes et self.passages ne sont pas modifiées.
        RAISES : rien.
        """
        totaux = []
        for equipe in self.equipes:
            total = 0
            for p in self.passages:
                if p.equipe is equipe and p.score is not None:
                    total += p.score
            totaux.append((equipe, total))
        # Le tri de Python est stable : à égalité, l'ordre des équipes est gardé
        totaux.sort(key=lambda paire: paire[1], reverse=True)

        lignes = []
        for position, (equipe, total) in enumerate(totaux, start=1):
            if lignes and total == lignes[-1].total:
                rang = lignes[-1].rang  # ex aequo avec l'équipe précédente
            else:
                rang = position
            lignes.append(LigneClassement(rang, equipe, total))
        return lignes


class GrandJeu:
    def __init__(self, nom, debut, fin):
        if fin <= debut:
            raise ErreurJeu("l'heure de fin doit être après l'heure de début.")
        self.nom = nom
        self.debut = debut
        self.fin = fin
        self.equipes = []
        self.postes = []
        self.positions = []  # les postes + le poste d'attente s'il y en a un
        self.creneaux = []
        self.passages = []

    def ajouter_equipe(self, nom):
        nom = self.verifier_nom(nom, self.equipes)
        self.equipes.append(Equipe(nom))

    def ajouter_poste(self, nom):
        nom = self.verifier_nom(nom, self.postes)
        self.postes.append(Poste(nom))

    def verifier_nom(self, nom, deja_la):
        """Nettoie un nom d'équipe ou de poste et vérifie qu'il est utilisable.

        PRE : nom est une chaîne (str) ; deja_la est une liste d'objets qui ont
              un attribut nom de type str (les équipes ou les postes du jeu).
        POST : renvoie nom sans les espaces du début et de la fin. Ce nom n'est
               pas vide et il est différent, sans tenir compte des majuscules,
               du nom de chaque élément de deja_la. deja_la n'est pas modifiée.
        RAISES : ErreurJeu si le nom nettoyé est vide ;
                 ErreurJeu si un élément de deja_la porte déjà ce nom
                 (majuscules ignorées).
        """
        nom = nom.strip()
        if nom == "":
            raise ErreurJeu("le nom ne peut pas être vide.")
        for element in deja_la:
            if element.nom.lower() == nom.lower():
                raise ErreurJeu(f"« {nom} » existe déjà.")
        return nom

    def calculer_rotation(self):
        # Rotation en décalage : au créneau t, l'équipe i va à la position
        # (i + t) % nombre de positions. Deux équipes ne sont donc jamais
        # au même poste en même temps, et personne ne refait un poste.
        nb_equipes = len(self.equipes)
        nb_postes = len(self.postes)
        if nb_equipes == 0 or nb_postes == 0:
            raise ErreurJeu("il faut au moins une équipe et un poste.")
        if nb_equipes > nb_postes + 1:
            raise ErreurJeu(f"{nb_equipes} équipes pour {nb_postes} postes, c'est trop. "
                            "Il faut au maximum une équipe de plus que de postes.")

        positions = list(self.postes)
        if nb_equipes > nb_postes:
            positions.append(Poste("Attente (QG)", attente=True))

        # Un créneau par position au maximum, sans dépasser l'heure de fin
        creneaux = []
        debut = self.debut
        while len(creneaux) < len(positions) and debut + DUREE_CRENEAU <= self.fin:
            creneaux.append(Creneau(debut))
            debut = debut + DUREE_CRENEAU
        if len(creneaux) == 0:
            raise ErreurJeu("le jeu est trop court pour un créneau de 20 minutes.")

        passages = []
        for t in range(len(creneaux)):
            for i in range(nb_equipes):
                poste = positions[(i + t) % len(positions)]
                passages.append(Passage(self.equipes[i], poste, creneaux[t]))

        self.positions = positions
        self.creneaux = creneaux
        self.passages = passages

    def a_une_rotation(self):
        return len(self.passages) > 0

    def passages_de(self, equipe):
        return [p for p in self.passages if p.equipe is equipe]

    def equipe_au_poste(self, poste, creneau):
        for p in self.passages:
            if p.poste is poste and p.creneau is creneau:
                return p.equipe
        return None  # personne à ce poste pendant ce créneau

    def classement(self):
        """Renvoie les lignes du classement, recalculé à partir des scores actuels."""
        return Classement(self.equipes, self.passages).lignes()
