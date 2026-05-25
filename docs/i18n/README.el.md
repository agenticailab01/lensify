# ProjectLens

> Προσαρμοστικός φακός έργου ενιαίας σάρωσης + κάψουλα βελτιστοποιημένου περιεχομένου με βάση τα tokens για κάθε βάση κώδικα. Εξοικονομεί 70-90% των tokens προσανατολισμού για AI-agents κωδικοποίησης.

[English](../../README.md) · [Svenska](README.sv.md) · **Ελληνικά** · [Română](README.ro.md)

## Τι είναι

Το ProjectLens είναι ένα plugin που με **μία σάρωση** (50-150 ms) μετατρέπει οποιαδήποτε βάση κώδικα σε:

1. **`LENS.html`** — μια σύνοψη μίας σελίδας που ένας άνθρωπος διαβάζει σε 30 δευτερόλεπτα
2. **`LENS.capsule.md`** — ένα μπλοκ περιβάλλοντος 800-3.600 tokens που ο AI agent σας απορροφά **αντί** να διαβάσει 30+ αρχεία
3. **30 προσαρμογείς framework** σε 8 πακέτα οικοσυστήματος (AI Apps, AI UIs, ML Core, Serving, Vector DB, Experiment, Enterprise, Notebooks)

## Εγκατάσταση

```bash
# Claude Code / Cowork — σύρετε το projectlens.plugin στη συνομιλία
# Cursor / VS Code Copilot / Codex / Gemini CLI — διακομιστής MCP
git clone https://github.com/agenticailab01/projectlens ~/projectlens
# Aider / scripts / CI — CLI
pip install projectlens
# Οποιοδήποτε εργαλείο διαβάζει αρχεία περιβάλλοντος — λειτουργία AGENTS.md
projectlens . --install-agents-md
```

## Βασικά χαρακτηριστικά

- **Προσαρμοστικό βάθος** (T1/T2/T3)
- **30 προσαρμογείς framework** — PyTorch, LangChain, FastAPI, Pinecone, κ.ά.
- **5 hooks συνεδρίας** (Claude Code)
- **Compactor συνομιλίας** — ανακτά 8-25k tokens στη μέση της συνεδρίας
- **Καθαρή stdlib** — μηδέν εξαρτήσεις runtime

## Άδεια

MIT.
