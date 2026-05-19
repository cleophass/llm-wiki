# CHANGES

## Problème
- L'audit d'ingestion a montré l'absence de schéma wiki explicite.
- Résultat : dérive de granularité (pages trop micro, doublons, sections trop courtes).
- Traçabilité insuffisante de la boucle Scout → Plan → Executor pour le portfolio.

## Solution
1. Ajout d'un schéma wiki AIMO (9 types de pages + règles de granularité).
2. Refactor du prompt Scout avec garde-fous explicites et recherche regex.
3. Normalisation des titres (unicode) et ids déterministes (slug-only).
4. Opération `delete_page` avec justification obligatoire et exécution déterministe.
5. Boucle d'ingestion migrée vers LangChain + traces LangSmith optionnelles.

## Résultat attendu
- Granularité maîtrisée et cohérente avec les entités immobilières.
- Moins de doublons grâce à la désambiguïsation systématique.
- Sections plus denses (seuil minimum) et pages plus stables.
- Suppressions auditées et contrôlées via `delete_page`.
- Traçabilité complète des appels LLM, tools et exécution du plan.
