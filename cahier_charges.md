# 📘 Cahier des Charges : AI Research Assistant (Niveau PFE / AI Engineer)

## 🧾 1. Vue d'Ensemble
### 1.1 Objectif
Développer un **AI Research Assistant** de pointe, capable de :
* Comprendre et analyser des documents scientifiques complexes.
* Répondre aux questions des utilisateurs avec une haute précision.
* Fournir des citations fiables, vérifiables et traçables jusqu'à la source.

### 1.2 Utilisateurs Cibles
* 🎓 **Étudiants** (rédaction de mémoires, synthèses de cours).
* 🔬 **Chercheurs** (revue de littérature, extraction de données).
* 👨‍🏫 **Professeurs** (préparation de cours, correction et vérification).

---

## 🧠 2. Fonctionnalités Principales (Core Features)

### 📥 2.1 Upload & Parsing
* **Upload de fichiers** : Prise en charge des formats PDF (et potentiellement DOCX).
* **Extraction de texte** : Utilisation de `PyMuPDF` (rapidité) ou `pdfplumber` (précision).
* **Tracking** : Détection et sauvegarde des numéros de pages.
> **Annotation Technique :** *Les articles scientifiques contiennent souvent des tableaux complexes ou des formules. Envisage d'utiliser des bibliothèques comme `unstructured` ou `Nougat` (de Meta) spécialement entraînées pour parser les PDF académiques.*

### ✂️ 2.2 Chunking Intelligent
* **Taille des chunks** : 300 à 800 tokens.
* **Chevauchement (Overlap)** : 50 à 100 tokens pour ne pas couper le contexte.
* **Métadonnées attachées** : `page`, `doc_id`, `titre_document`, `section`.

### 🔎 2.3 Embeddings & 📦 Vector DB
* **Modèle d'embedding** : `sentence-transformers` (ex: *all-MiniLM-L6-v2* ou *BAAI/bge-m3* pour le multilingue).
* **Base de données vectorielle** : **ChromaDB**.
* **Stockage** : Chaque entrée contiendra le texte du chunk, son vecteur (embedding), et ses métadonnées.

### ❓ 2.4 Query System (RAG Pipeline)
1. L'utilisateur pose une question.
2. **Retrieval** : Récupération des *top-k* chunks les plus pertinents.
3. **Re-ranking** : Tri fin des résultats.
4. **Génération** : Envoi d'un prompt structuré au LLM.
5. **Output** : Réponse sourcée.

### 🧾 2.5 Citations Intelligentes
* Affichage de la **page exacte** et d'un **extrait (snippet)** de la source.
* *Bonus UI :* Mise en surbrillance (highlight) du texte directement dans une visionneuse PDF côté frontend.

### ⚡ 2.6 Streaming & Multi-Doc
* **Streaming** : Affichage de la réponse en temps réel (type ChatGPT) via l'API de Groq.
* **Multi-doc** : Possibilité d'interroger plusieurs PDFs simultanément ou d'appliquer des filtres de recherche (ex: "Cherche uniquement dans le doc A").

---

## 🤖 3. Système Multi-Agents (🔥 Advanced Feature)
L'utilisation d'un système multi-agents garantit une qualité de réponse digne d'un produit professionnel.

| Agent | Rôle et Responsabilités |
| :--- | :--- |
| 🔍 **Retriever** | Cherche l'information dans ChromaDB (Vector Search). |
| 📊 **Ranker** | Trie et sélectionne les meilleurs chunks (Hybrid Search). |
| ✍️ **Generator** | Rédige la réponse en se basant *uniquement* sur le contexte. |
| 🔗 **Citation** | Formate et insère les sources (pages, extraits) dans le texte. |
| 🛡️ **Critic** | Vérifie la réponse finale (détection d'hallucinations, cohérence). |

> **Annotation Technique :** *Pour orchestrer ces agents, regarde du côté de **LangGraph** ou **CrewAI**. Ce sont des frameworks parfaits pour créer des boucles de validation entre agents (ex: le Critic rejette la réponse et demande au Generator de refaire).*

---

## 🧱 4. Architecture Technique

* **Backend** : FastAPI (Python) - *Parfait pour l'asynchrone et les websockets (streaming).*
* **Frontend** : React (avec Tailwind CSS pour le design).
* **LLM** : Groq (Mixtral 8x7B ou LLaMA 3) - *Ultra-rapide.*
* **Base de données** : ChromaDB (Vector) + SQLite/PostgreSQL (si gestion d'utilisateurs).

---

## ⚠️ 5. Le Défi Critique : La limite de tokens de Groq (6000 tokens)
La gestion du contexte est cruciale pour la réussite de ce projet. Voici les stratégies obligatoires à implémenter :

1. **Smart Retrieval** : Récupérer max 3 à 5 chunks d'environ 500 tokens. (Total ~2500 tokens -> OK).
2. **Context Compression** : Si nécessaire, utiliser un LLM léger pour résumer un chunk avant de l'envoyer au LLM principal.
3. **Re-ranking (Hybride)** : Combiner la recherche sémantique (Embeddings) avec la recherche par mots-clés (BM25) pour ne garder que la crème de la crème.
4. **Sliding Window Memory** : Limiter l'historique de la conversation ou résumer les anciens échanges pour ne pas saturer le prompt avec les questions précédentes.
5. **Prompt Engineering Structuré** :
    ```text
    You are an expert research assistant.
    Use ONLY the context below to answer the user's question.
    If the answer is not in the context, say "I don't know based on the provided documents."

    Context:
    {context}

    Question:
    {question}

    Answer with strict citations (Doc Name, Page number).
    ```

---

## 🛡️ 6. Garantie Qualité (Comment être un "AI Engineer" pro)

* **Grounding (Ancrage)** : Strictement zéro invention. Le RAG doit être bridé par le prompt.
* **Critic Agent** : Un agent dédié qui relit la réponse et la compare aux chunks récupérés avant de l'afficher à l'utilisateur.
* **Score de confiance** : Calculé en fonction de la similarité cosinus des chunks trouvés et de l'approbation de l'agent Critic.

---

## 🚀 7. Bonus & Idées Supplémentaires (Niveau Startup)

### 💡 Ajouts issus du cahier des charges original :
* **Système d'évaluation (RAGAS)** : Tester la précision des réponses automatiquement (Faithfulness, Answer Relevance).
* **Dashboard Admin** : Suivi des performances, nombre de requêtes, latence (via LangSmith ou Phoenix).
* **Auth System** : Comptes utilisateurs (JWT / OAuth2).

### 💡 Nouvelles idées pour se démarquer (Différenciateurs) :
* **Export des citations (Format académique)** : Permettre à l'utilisateur d'exporter les sources au format BibTeX ou APA d'un simple clic.
* **Gestion de l'OCR (Vieux papiers)** : Intégrer `Tesseract` pour extraire le texte des PDF scannés (très fréquent en recherche).
* **Système de Cache (Redis)** : Si une question similaire a déjà été posée sur le même document, renvoyer la réponse en cache sans repasser par le LLM (économise des quotas Groq et réduit la latence à zéro).
* **Visualisation de graphe de connaissances** : Montrer les liens entre les différents documents uploadés.

---

### 🏁 Conclusion & Choix Techniques Finaux
* **DB** : ✅ ChromaDB (vs FAISS, car Chroma gère mieux les métadonnées et la persistance par défaut).
* **Architecture** : RAG Pipeline + Système Multi-Agents + Groq (Vitesse).
* **Focus principal** : Optimisation des tokens contextuels et lutte stricte contre les hallucinations.