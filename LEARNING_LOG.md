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

---

## Git: versionarea proiectului (2026-11-03)

### Ce am făcut
- `git init -b main` a creat repository-ul local, cu ramura principală numită `main`.
- Am setat autorul commiturilor (`git config --global user.name / user.email`).
- Primul commit: „Step 1: project structure and Gemini setup”.
- Am verificat cu `git status` că `.venv` NU apare, deci `.gitignore` funcționează.

### De ce
- **Istoric clar:** câte un commit pe pas arată cum a evoluat proiectul (structură, documente, agent, V1, V2).
- **Prompturile versionate:** diferența dintre `prompts/v1.txt` și `v2.txt` se vede direct în git.
- **Siguranță:** pot reveni oricând la o versiune care mergea.

### De reținut
- Warning-ul „LF will be replaced by CRLF” e inofensiv. Windows și Linux marchează finalul de rând diferit
  (CRLF vs LF), iar git face conversia automat.
- Git nu urmărește foldere goale, doar fișiere. De aceea am pus `results/.gitkeep`.

---

## Pasul 2 – Documentele interne fictive (2026-11-03)

### Ce am făcut
Am creat 3 documente în engleză, în `docs/`, pentru firma fictivă **Contoso Business Services**:

| Fișier | ID | Conținut principal |
|---|---|---|
| `leave_policy.md` | HR-POL-004 | Zile de concediu, preaviz, aprobare, reportare, concediu medical, concedii speciale |
| `it_incident_reporting.md` | IT-PRO-012 | Canale de raportare, priorități P1–P4 cu timpi de răspuns, securitate, escaladare |
| `onboarding_guide.md` | HR-GUI-002 | Înainte de prima zi, programul primei zile, trainingurile, perioada de probă, cine ce face |

### De ce așa
- **Detalii concrete și verificabile** (24 de zile, 15 minute, interior 3100, 31 martie): fără date
  precise nu pot verifica automat dacă agentul a răspuns corect.
- **Goluri intenționate:** documentele pomenesc politici care NU există la noi (HR-POL-007 concediu parental,
  HR-POL-010 muncă hibrid, IT Service Catalogue). Din ele fac întrebări capcană, ca să văd dacă agentul
  spune „nu știu” sau inventează.
- **Răspunsuri care depind de context** (normă, vechime, prioritatea incidentului): din ele fac întrebările
  ambigue.
- **Trimiteri între documente:** onboarding-ul trimite la politica de concedii și la procedura IT. Asta testează
  dacă agentul combină și citează **mai multe surse**.
- **Metadate (ID, versiune, dată, responsabil):** permit citări precise și seamănă cu coloanele unei biblioteci
  de documente SharePoint.
- **Contoso + domeniul `.example`:** Contoso e firma fictivă din documentația Microsoft. `.example` e un domeniu
  rezervat oficial, deci emailurile nu pot aparține nimănui. Nu am folosit numele unei firme reale.

### Alternative luate în calcul
- **Documente reale de pe internet:** n-aș fi controlat ce conțin și ce lipsește, deci n-aș fi putut construi
  capcanele intenționat. În plus, pot fi probleme de drepturi de autor.
- **Documente generate fără planificare:** ar fi ieșit vagi și greu de testat.
- **Formate PDF/Word:** mai realiste, dar ar fi cerut o etapă de extragere a textului. Markdown e text simplu,
  cu structură (titluri, tabele) pe care modelul o înțelege bine.

---

## Pasul 3 (3.1–3.3) + Pasul 4 – Agentul și promptul V1 (2026-11-03)

### Ce am făcut
- **3.1** `load_documents()` citește toate fișierele `.md` din `docs/` într-un dicționar {nume fișier: text}.
- **4** `prompts/v1.txt`: un prompt intenționat simplu (baseline), cu 4 reguli: rol, doar din documente,
  citează sursa, spune „I don't know”.
- **3.2** `build_system_instruction()` pune regulile + documentele (în etichete `<document name="...">`) în promptul
  de sistem. `ask_gemini()` trimite întrebarea la `gemini-3.5-flash-lite` cu `temperature=0`
  și reîncearcă la erorile 429/500/503 (exponential backoff: 5s, 10s, 20s).
- **3.3** `is_unanswered()` caută „I don't know” în răspuns. `log_unanswered()` adaugă întrebarea în
  `results/unanswered.csv` (timestamp, question, prompt_version, status=New).

### De ce
- **Grounding, nu antrenare:** modelul nu e modificat. Primește documentele ca context la fiecare întrebare.
  Avantaje: documentele se pot actualiza oricând, agentul poate cita sursa, costă puțin.
  (Gemini nu ține minte nimic între apeluri, de aceea trimitem documentele de fiecare dată.)
- **Toate documentele în prompt (fără RAG):** ~2.500 de tokeni, mult sub limita modelului. RAG devine necesar la sute de documente.
- **`temperature=0`:** răspunsuri cât mai stabile între rulări, deci teste reproductibile.
- **Promptul în fișier separat:** V1 și V2 pot fi comparate fără să schimb codul.
- **`unanswered.csv`:** întrebările fără răspuns arată ce lipsește din documentație.

### Probleme observate deja în V1 (testare exploratorie)
1. **Refuz fără expresia exactă** – „How many days of parental leave?”: n-a inventat, dar n-a spus „I don't know”,
   deci întrebarea NU a fost salvată în CSV (fals negativ).
2. **Răspuns înrudit, dar irelevant** – „Where do I get my salary?”: a răspuns cu „încarcă datele bancare cu 3 zile
   înainte”. Faptul e adevărat, dar nu răspunde la întrebare, și nici nu a fost salvată în CSV.
   Mai periculos decât o halucinație clasică, pentru că are sursă și sună credibil.
3. **Citare vagă** – „Leave Policy” în loc de „HR-POL-004, secțiunea 4”.
4. Observație pozitivă: înțelege și întrebări cu greșeli de tipar („salay”).

### Alternative luate în calcul
- **Fine-tuning:** scump, iar informația se învechește. Nu poate cita sursa.
- **Detectarea „nu știu” cu un al doilea apel LLM:** mai robustă, dar dublează costul și numărul de apeluri.
  Încep cu varianta simplă și o îmbunătățesc doar dacă testele arată că e nevoie.
