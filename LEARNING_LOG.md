# Learning Log – AI Process Assistant

Jurnal de învățare: ce am făcut la fiecare pas, de ce, ce alternative am avut
și ce am învățat.

---

## Pasul 1 – Structura proiectului (2026-11-03)

### Ce am făcut
Am creat scheletul proiectului:

| Element | Rol |
|---|---|
| `docs/` | Documentele interne fictive, adică singura „sursă de adevăr” a agentului |
| `prompts/` | Prompturile de sistem, versionate (`v1.txt`, `v2.txt`) |
| `src/` | Codul: agentul (`agent.py`) și evaluarea (`evaluate.py`) |
| `tests/` | Cazurile de test (întrebări + răspunsuri așteptate) |
| `results/` | Rezultatele rulărilor (CSV-uri, comparația V1 vs V2) |
| `README.md` | Documentația proiectului, în engleză |
| `LEARNING_LOG.md` | Acest jurnal |
| `requirements.txt` | Dependențele (doar `anthropic`) |
| `.gitignore` | Ține în afara git-ului `.env`, mediul virtual și cache-ul |

### De ce
- **Separarea responsabilităților:** datele, logica, prompturile, testele și rezultatele
  stau separat, deci pot schimba una fără să le afectez pe celelalte.
- **Prompturile în fișiere separate:** pot compara V1 cu V2 ca text, iar istoria lor
  se vede în git. Așa promptul devine un artefact testabil, nu un string ascuns în cod.
- **`.gitignore` de la început:** securitatea se face din prima zi, nu după ce o cheie
  a ajuns deja pe GitHub.
- **O singură dependență:** cod ușor de citit și de explicat.

### Alternative luate în calcul
- **LangChain / LlamaIndex:** utile la volume mari de documente, dar adaugă
  abstracții. Cu 3 documente scurte le pot pune direct în prompt.
- **Bază de date vectorială (RAG cu embeddings):** necesară la sute de documente.
  Aici ar fi complexitate fără beneficiu. O menționez ca „next step” pentru producție.
- **Prompturile ca variabile în cod:** mai simplu, dar nu mai pot versiona și compara
  ușor prompturile.

---

## Decizie: Google Gemini (free tier) în loc de Anthropic Claude (2026-11-03)

### Ce am făcut
- Am înlocuit SDK-ul `anthropic` cu SDK-ul oficial Google `google-genai` în `requirements.txt`.
- Cheia API se citește acum din variabila de mediu `GEMINI_API_KEY`, la fel: niciodată în cod sau în git.
- Am adăugat `src/check_setup.py`, un script care verifică pe rând: cheia există, SDK-ul e instalat,
  ce modele sunt disponibile și dacă un apel de test merge.

### De ce
- **Cost zero:** Google AI Studio oferă o cheie gratuită, fără card bancar. E suficient pentru un proiect de portofoliu.
- **Verificarea setup-ului separat:** dacă ceva nu merge, aflu exact ce (cheie, pachet sau model)
  înainte să scriu agentul. Altfel aș depana trei probleme deodată.
- **Lista de modele cerută de la API:** numele modelelor Gemini se schimbă des, iar unele „preview” dispar.
  Nu ghicesc un nume, ci întreb API-ul.

### Limitările variantei gratuite (de știut!)
- **Limite de cereri** pe minut și pe zi, diferite pe proiect și pe model. Le văd în AI Studio.
  → În `evaluate.py` voi pune pauze între apeluri.
- **Datele din varianta gratuită pot fi folosite de Google** pentru îmbunătățirea produselor.
  → OK pentru documente fictive, NU OK pentru date reale de firmă.

### Alternative luate în calcul
- **Anthropic Claude:** planul inițial, dar cere credit plătit.
- **Model local (Ollama):** gratuit și privat, dar cere un calculator puternic, iar modelele mici
  halucinează mai mult, deci rezultatele ar fi mai slabe.
- **Azure OpenAI:** cel mai apropiat de ecosistemul Microsoft 365, dar cere abonament Azure.

---

## Setup verificat + alegerea modelului (2026-11-03)

### Ce am făcut
- Am creat mediul virtual `.venv`, am instalat `google-genai` și am rulat `src/check_setup.py`.
- Am testat 4 modele cu câte un apel scurt:

| Model | Rezultat | Ce înseamnă |
|---|---|---|
| `gemini-3.8-flash` | ❌ 503 UNAVAILABLE | Cel mai nou model e supraîncărcat (multă cerere pe varianta gratuită) |
| `gemini-3.5-flash` | ✅ | **Ales pentru agent** |
| `gemini-3.5-flash-lite` | ✅ | Rezervă: mai rapid, mai ieftin, posibil mai puțin precis |
| `gemini-2.5-flash` | ❌ 404 NOT_FOUND | Model retras pentru utilizatorii noi |

### De ce `gemini-3.5-flash`
- **Merge stabil acum.** Cel mai nou model nu ajută dacă dă eroare jumătate din timp.
- **Versiune fixată, nu alias.** `gemini-flash-latest` poate trece pe ascuns la alt model, iar atunci
  scorurile V1 și V2 n-ar mai fi comparabile, pentru că s-ar fi schimbat două lucruri deodată (promptul și modelul).
  Într-un test corect schimb **o singură variabilă**.

### Lecții
- **Am întâlnit erori reale de producție:** 503 (server ocupat, temporar), 404 (model retras),
  plus 429 (limită de cereri), pe care o voi întâlni probabil la evaluare.
  → Codul agentului va avea **retry cu așteptare** (reîncearcă de câteva ori, cu pauze tot mai mari).
- **Modelele AI au ciclu de viață:** un model folosit azi poate fi retras peste câteva luni.
  În producție trebuie monitorizate anunțurile de deprecation și re-rulate testele pe modelul nou
  înainte de schimbare (regression testing).

### Actualizare: modelul final este `gemini-3.5-flash-lite`
Am trecut de la `gemini-3.5-flash` la `gemini-3.5-flash-lite`.
- **Avantaje:** mai rapid și, de obicei, cu limite gratuite mai generoase. Evaluarea face multe apeluri
  (20 de întrebări × fiecare versiune de prompt, plus judge-ul), deci contează.
- **Compromis:** un model „lite” poate respecta mai slab instrucțiunile din prompt (de ex. „răspunde doar din
  documente”). Pentru proiect asta e chiar util: V1 va avea probabil mai multe erori vizibile, iar
  îmbunătățirea din V2 se va putea măsura mai clar.
