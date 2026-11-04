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

---

## Pasul 3.4 – Legătura cu Power Automate și Microsoft Lists (2026-11-04)

### Ce reprezintă proiectul în Microsoft 365
| Proiectul meu | Echivalent în Microsoft 365 |
|---|---|
| `docs/` | Bibliotecă de documente SharePoint |
| `agent.py` + `prompts/v1.txt` | Agent Copilot Studio (SharePoint ca knowledge source + instructions) |
| `is_unanswered()` | Ramura „nu am găsit răspuns” din agent, care pornește un flux |
| `log_unanswered()` → CSV | Flux Power Automate: acțiunea „Create item” într-o listă Microsoft Lists |
| coloana `status` (New) | Coloană Choice în listă: New / In progress / Answered |

### Bucla închisă
Întrebare fără răspuns → item în listă + notificare Teams către HR → HR completează documentul în SharePoint →
agentul poate răspunde data viitoare. Indicator util: **% întrebări fără răspuns pe lună** (dacă scade,
documentația se îmbunătățește).

### De ce CSV în proiect
Nu am nevoie de o licență Microsoft 365 de firmă. Structura datelor e aceeași, deci pentru varianta reală
schimb doar interiorul lui `log_unanswered()` (trimite datele către un flux Power Automate în loc de CSV).

---

## Pasul 5 – Setul de teste (2026-11-04)

### Ce am făcut
`tests/test_cases.csv` cu 20 de întrebări:

| Categorie | Câte | Ce verifică | Comportament corect |
|---|---|---|---|
| normal (N01–N12) | 12 | Găsește informația corectă din toate cele 3 documente | Răspuns exact + sursa corectă |
| trap (T01–T04) | 4 | Inventează când nu știe? (concediu parental, salariu, muncă de acasă, VPN) | „I don't know” |
| ambiguous (A01–A04) | 4 | Observă că răspunsul depinde de situație? | Prezintă variantele sau cere detalii |

Coloane: `id, category, question, expected_answer, expected_source, must_contain`.
- `expected_answer`: răspunsul corect, pentru oameni.
- `must_contain`: cuvinte-cheie pentru verificarea automată (`;` = toate obligatorii, `|` = variante acceptate).

### De ce
- **Set fix de întrebări (golden dataset):** V1 și V2 sunt testate pe exact aceleași întrebări, deci diferența de scor vine
  doar din prompt.
- **Baremul scris din documente, NU din răspunsurile agentului:** altfel aș testa agentul cu el însuși și i-aș accepta
  greșelile. Sursa de adevăr e documentul.
- **Review manual al baremului:** am verificat câteva răspunsuri așteptate direct în documente (N05, N09).
  Și setul de teste poate avea greșeli.
- **Teste de regresie:** T01 (concediu parental) și T02 („Where do I get my salay?”, cu tot cu greșeala de tipar) vin din
  erorile găsite prin testare exploratorie. Odată găsită, o eroare devine test permanent.
- **Coloane în engleză:** consecvent cu restul proiectului. Fără diacritice în cod.

### Limite cunoscute ale verificării prin cuvinte-cheie
- Fals pozitiv: N04 caută „2”, care poate apărea și într-un răspuns greșit.
- Fals negativ: la întrebările ambigue, un răspuns bun de tipul „Ce document anume?” nu conține cifrele căutate.
→ De aceea adaug la pasul 6 și LLM-as-judge.

### Alternative luate în calcul
- **Mai multe întrebări (100+):** statistic mai solid, dar mai greu de verificat manual și consumă limita gratuită.
  20 e suficient pentru un prototip.
- **Întrebări generate automat de un LLM:** rapid, dar baremul ar trebui oricum verificat de un om, iar capcanele n-ar fi
  gândite pe golurile reale din documente.

---

## Pasul 6 – Evaluarea automată: `src/evaluate.py` (2026-11-04)

### Ce am făcut
- **6.1** Rulez agentul pe toate cele 20 de întrebări, refolosind funcțiile din `agent.py` (testez exact codul real).
  Pauză de 4 s între apeluri. O eroare la o întrebare nu oprește rularea (se notează „ERROR”).
- **6.2** Verificare automată: `check_keywords()` (`;` = toate obligatorii, `|` = variante) și `check_sources()`
  (acceptă numele fișierului, titlul sau ID-ul documentului). La capcane contează doar „I don't know”.
- **6.3** LLM-as-judge: un al doilea model primește rubrica (`prompts/judge.txt`), documentele, baremul și răspunsul,
  și întoarce JSON `{"reason": ..., "verdict": PASS/FAIL}`.
- **6.4** Scoruri pe categorii pentru ambele metode, lista dezacordurilor și a testelor picate:
  `results/run_v1.csv` (detalii) și `results/summary_v1.md` (rezumat).

### Rezultat V1
| Categorie | Verificare automată | LLM judge |
|---|---|---|
| normal | 12/12 (100%) | 12/12 (100%) |
| trap | **2/4 (50%)** | 1/2 (50%), 2 erori |
| ambiguous | 4/4 (100%) | 2/2 (100%), 2 erori |
| TOTAL | 18/20 (90%) | 15/16 (94%), 4 erori |

V1 e foarte bun la întrebări directe, dar pică jumătate din capcane (T01 concediu parental, T02 salariu).
Totalul de 90% ascunde exact cea mai gravă problemă, de aceea raportez pe categorii.

### LLM-as-judge: avantaje și limite (văzute în practică)
- ✅ **A prins ce n-au prins cuvintele-cheie:** într-o rulare, la A01 agentul a atribuit regula perioadei de probă
  documentului greșit. Verificarea automată a dat PASS, judge-ul FAIL, cu motivul corect.
- ✅ Judecă nuanțat (N09: a observat un detaliu lipsă, dar a considerat răspunsul suficient).
- ⚠️ **Nu e consecvent:** T01 a primit FAIL (Gemini Flash), apoi PASS (Gemma), pe același tip de răspuns.
  Cauza: rubrica e ambiguă pentru „trimite la alt document, dar nu spune «nu știu»”. Decizia finală e umană: FAIL,
  pentru că întrebarea nu ajunge în `unanswered.csv`.
- ⚠️ Costă apeluri în plus și depinde de disponibilitatea serverelor.

### Alegerea modelului pentru judge (decizie din date)
- `gemini-3.5-flash`: blocat după **20 de cereri/zi** (limita free tier). În plus, cererile erau contorizate la
  `gemini-3.6-flash`, deci Google redirecționează în fundal → nici un nume „fixat” nu garantează modelul.
- **`gemma-4-31b-it`** (ales): 14.400 de cereri/zi, altă familie decât agentul (mai puțină auto-favorizare),
  model deschis (poate rula și pe serverele unei firme). Dezavantaje: limită de 16K tokeni/minut (pauză de 15 s),
  servere instabile (multe erori 500/503, 4 evaluări eșuate), rulare de ~40 de minute.
- Judge-ul are 6 reîncercări (5, 10, 20, 40, 80 s). Erorile nu se numără ca FAIL, ci se raportează separat.

### Alte lecții
- **Non-determinism:** chiar cu `temperature=0`, agentul a răspuns diferit la A01 între două rulări.
  La 20 de întrebări, o întrebare = 5% din scor, deci diferențele mici între versiuni pot fi zgomot.
- **Am testat logica de scoring separat**, pe răspunsurile salvate și cu verdicte inventate, înainte de rularea lungă.
  Așa nu am pierdut timp și cotă API pe o greșeală de cod.
- **Problema CSV + Excel în România:** Excel așteaptă `;` ca separator. Import prin Data → From Text/CSV, cu UTF-8.

### Alternative luate în calcul
- **Doar verificare automată:** rapidă și gratuită, dar „oarbă” la sens (a ratat A01).
- **Doar LLM judge:** înțelege sensul, dar e inconsecvent, lent și uneori indisponibil.
- **Evaluare doar umană:** cea mai sigură, dar nu scalează. Folosesc omul doar pe dezacorduri.
- **Același model ca judge:** risc de auto-favorizare.

---

## Pasul 7 – Analiza erorilor și îmbunătățirea promptului: V1 → V2 → V3 (2026-11-04)

### Ce am făcut
1. **`--rejudge`**: re-evaluez doar rândurile unde judge-ul a avut eroare de server, fără să întreb agentul din nou
   (răspunsurile analizate rămân aceleași).
2. **Analiza erorilor V1** – refuzuri greșite: niciunul. Erori:
   E1 T01 trimite la alt document fără „I don't know” (nu ajunge în unanswered.csv);
   E2 T02 fapt înrudit prezentat ca răspuns (salariu → date bancare);
   E3 citare inconsecventă; E4 sursă greșit atribuită (A01, într-o rulare).
   Cauza comună: V1 spune CE să facă, dar nu definește CÂND un răspuns „nu e în documente”.
3. **V2**: reguli explicite pentru „I don't know” (inclusiv informații doar înrudite), format fix de citare
   `[Titlu, ID, section N]`, regulă pentru situații. Fiecare schimbare legată de o eroare observată.
4. **V3**: ordine de decizie A (răspunde) → B (întrebare vagă / depinde de situație: listează variantele și întreabă)
   → C („I don't know”). Trimitere la alt document doar dacă un document numește explicit subiectul.
5. **`src/compare.py`**: generează `results/comparison_vX_vs_vY.md` din rezultatele salvate: scoruri, întrebările
   reparate/stricate și diferența exactă între prompturi (`difflib`).

### Rezultate (verificare automată / judge)
| | V1 | V2 | V3 |
|---|---|---|---|
| normal | 100% / 100% | 100% / 100% | 100% / 100% |
| trap | **50%** / 75% | 100% / 75% | 100% / 100% |
| ambiguous | 100% / 100% | **75%** / **75%** | 100% / 100% |
| total | 90% / 95% | 95% / 90% | **100% / 100%** |

### Ce am învățat
- **O schimbare de prompt poate repara o eroare și crea alta.** V2 a reparat T01 și T02, dar a introdus:
  - T04: **halucinație nouă** („VPN e menționat în procedura IT” – fals), cauzată de permisiunea de a pomeni alt document.
    Doar judge-ul a prins-o, pentru că răspunsul conținea „I don't know”;
  - A03: **refuz greșit** (supra-prudență) la o întrebare vagă, dar la care se putea răspunde.
  → Le-am văzut doar pentru că am rulat din nou TOT setul (testare de regresie).
- **Ordinea contează în prompt:** o excepție pusă la finalul unei reguli n-a funcționat. O ordine de decizie
  explicită (A → B → C) a funcționat.
- **Smoke test înainte de rularea lungă:** 3 întrebări (~1 minut) au arătat că primul draft V3 nu repara A03,
  și că agentul scria eticheta internă „CASE B” în răspuns. Am corectat înainte de rularea de 40 de minute.
- **Am evitat overfitting-ul:** nu am copiat în prompt exemple din teste (de ex. „dacă te întreabă pe cine să contacteze…”).
- **Limita onestă:** V2 și V3 au fost scrise privind erorile pe ACELEAȘI 20 de întrebări, deci 100% e optimist.
  Corect ar fi un set nou de întrebări („held-out”), nefolosit la scrierea promptului.
- Agentul folosește acum `PROMPT_VERSION = "v3"`, cea mai bună versiune evaluată.

---

## Pasul 8 – README.md (2026-11-04)

### Ce am făcut
README în engleză, pentru cine descoperă proiectul pe GitHub: problem, solution, architecture (diagramă text + tabel fișiere),
how to run, test methodology, results V1/V2/V3, limitations, legătura cu SharePoint/Power Automate/Copilot Studio,
next steps.

### De ce așa
- Începe cu rezumatul și accentul pe **testare**, ce diferențiază proiectul de un simplu chatbot.
- Rezultatele sunt cifre măsurate, cu povestea erorilor și a regresiilor, nu doar scorul final.
- **Limitările sunt scrise deschis** (test set mic, prompt optimizat pe test set, judge inconsecvent, free tier).
  E mai convingător să le prezint eu decât să le descopere cititorul.
- Secțiunea Microsoft 365 leagă proiectul de uneltele Microsoft 365 (SharePoint, Power Automate, Copilot Studio).
