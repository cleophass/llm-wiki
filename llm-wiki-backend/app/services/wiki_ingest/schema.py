WIKI_SCHEMA = """
# Schéma du wiki AIMO

Le wiki organise la connaissance immobilière en 9 types de pages.
Chaque page appartient à un et un seul type.

## Types de pages autorisés

1. **Bien** (`biens/`) — Un bien immobilier précis (appartement, maison, terrain).
   Une page par bien physique. Contient : adresse, surface, prix, état général, historique.
   Exemple : "Appartement 12 rue de la Paix, Riom"
   Anti-exemple : "Appartement de 80m²" (pas assez identifiant)

2. **Copropriété** (`copros/`) — Une copropriété (syndic, règlement, AG).
   Une page par copropriété. Contient : règlement, charges, votes récents, gros travaux.
   Exemple : "Copropriété 12 rue de la Paix"
   Anti-exemple : "AG du 15 mars" (c'est une source, pas une entité)

3. **Personne** (`personnes/`) — Une personne physique (vendeur, notaire, agent, voisin).
   Une page par personne identifiée. Contient : rôle, coordonnées, historique d'interactions.
   Exemple : "Philomène Rouyer (notaire)"
   Anti-exemple : "Les voisins" (collectif, pas identifiant)

4. **Organisation** (`organisations/`) — Agence, syndic, banque, administration.
   Une page par organisation. Contient : rôle dans le dossier, contacts, contrats.
   Exemple : "Mon Agence Familiale"
   Anti-exemple : "Les agences" (générique)

5. **Document** (`documents/`) — Une source structurée (DPE, AG, contrat, diagnostic).
   Une page par document source. Contient : type, date, émetteur, contenu clé.
   Exemple : "DPE Habitation D7 — 2025"
   Anti-exemple : "Les diagnostics" (collectif)

6. **Concept** (`concepts/`) — Notion technique transversale rencontrée dans plusieurs sources.
   Une page par concept récurrent. Contient : définition, contexte légal, variantes.
   Exemple : "Clause Airbnb dans un règlement de copropriété"
   Anti-exemple : "Le concept de propriété" (trop large)

7. **Décision** (`decisions/`) — Un choix acté avec contexte et date.
   Une page par décision majeure. Contient : décision, date, motivations, conséquences.
   Exemple : "Décision d'inclure les volets dans la négociation"
   Anti-exemple : "On verra demain" (pas acté)

8. **Risque** (`risques/`) — Un problème identifié avec niveau et statut.
   Une page par risque concret. Contient : description, niveau (faible/moyen/élevé), statut.
   Exemple : "Risque : compte travaux insuffisant"
   Anti-exemple : "Les risques" (catégorie, pas une instance)

9. **Travaux** (`travaux/`) — Des travaux planifiés, en cours ou réalisés.
   Une page par chantier. Contient : nature, coût estimé, statut, devis liés.
   Exemple : "Remplacement des volets roulants — appartement Riom"
   Anti-exemple : "Faire les travaux" (pas spécifique)

## Règles de granularité

**Règle 1 — Anti-fragmentation.** Un fait isolé (date, mesure, prix unique) n'est JAMAIS une page.
Il devient une section ou une ligne dans la page thématique correspondante.

**Règle 2 — Préférer étendre.** Avant de créer une nouvelle page pour une entité, recherche
les variantes du nom dans le wiki existant. Si une page proche existe, étends-la plutôt que
de créer un doublon.

**Règle 3 — Seuil minimum.** Ne crée pas une section avec moins de 3 lignes de contenu utile.
Si l'information ne tient pas en 3 lignes, intègre-la dans une section existante.

**Règle 4 — Niveau cohérent.** Un concept micro (mesure, date, coût) devient une section, pas
une page autonome. Une page représente toujours une entité identifiable et référencée par
plusieurs sources potentielles.
"""
