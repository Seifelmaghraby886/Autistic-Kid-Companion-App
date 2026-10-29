# WANEES — Evidence Base

How each feature maps to a recognized **evidence-based practice (EBP)** for
autism, per the National Clearinghouse on Autism Evidence and Practice
(NCAEP, UNC) — the 28-practice list distilled from 972 peer-reviewed studies
(1990–2017), and its 2020 update.

> Framework: NCAEP / National Professional Development Center on ASD.
> See: CAPTAIN EBP matrix (captain.ca.gov) and AFIRM modules (afirm.fpg.unc.edu).

---

## 1. Feature → EBP map

| App feature | NCAEP evidence-based practice | Note |
|---|---|---|
| Visual Schedule | **Visual Supports (VS)** | The classic first-line support: predictability lowers anxiety |
| **First-Then board** *(new)* | **Visual Supports + Reinforcement (R)** | Foundational sequence support: "First task, then reward" |
| Reward stars (token economy) | **Reinforcement (R)** / Token Economy | Cross-activity: games, calm, AAC, journal all award stars |
| AAC pictogram builder | **Augmentative & Alternative Communication (AAC)** | Non-verbal children compose + speak sentences |
| Communication board | **AAC / Functional Communication Training (FCT)** | Fast access to core needs vocabulary |
| Social stories generator | **Social Narratives (SN)** | AI-personalized to the child's situation |
| Social coach scenarios | **Social Skills Training (SST)** | Low-pressure role-play with options + explanation |
| Task tutorials (step-by-step) | **Task Analysis (TA) + Video/Visual Modeling** | Skills broken into small narrated steps |
| Calm Zone (breathing, comfort) | **Self-Management / emotion-regulation strategies** | Offered proactively when the camera sees distress |
| Feelings thermometer | **Self-Management (SM)** | Self-rating arousal; feeds the suggestion engine |
| Mood journal | **Self-Management (SM)** | Emotion labeling + tracking; parent-visible trends |
| Visual timer | **Visual Supports (VS)** | Time made concrete; transition preparation |
| Transition helper | **Visual Supports / priming** | Pre-warning before activity changes |
| Emotion-aware conversation | **Technology-Aided Instruction & Intervention (TAII)** | The whole app is a TAII delivery vehicle |
| Whole-app voice + camera loop | **TAII + Naturalistic Intervention** | Interaction embedded in the child's natural play |

## 2. Why the intelligence bus matters clinically

Isolated activities are weaker than connected ones. The context engine gives:

- **Generalization support** — the companion references a game win inside a
  conversation ("you matched all the feelings earlier!"), helping skills
  transfer across contexts (a known weak point in ASD interventions).
- **Reinforcement consistency** — one token economy across every activity,
  as ABA practice recommends, instead of per-screen scoring.
- **Antecedent-based logic** — the home card proactively suggests the Calm
  Zone when sensor + self-report data show rising arousal (antecedent-based
  intervention, another NCAEP practice).

## 3. What the research says about robots (Phase II)

- Robot-assisted intervention meta-analyses report gains in joint attention
  and engagement vs. screen-only delivery — embodiment increases motivation
  for many autistic children (Pennisi et al. 2016; Saleh et al. 2021).
- ASD-Chat (arXiv:2409.01867, IEEE 2024): LLM-driven dialogue matched a human
  interventionist on outcomes with N=12 autistic children, with longer and
  more frequent child utterances.
- Existing commercial robots (QTrobot $3.5–4.5K, Milo $5.8K, Kaspar research-
  only) confirm demand but are English-first and clinic-priced — the gap
  WANEES targets (Egyptian Arabic, home use, affordable).

## 4. Ethics guardrails already implemented

- Companion, **not** clinician: no diagnosis, no prescriptions.
- Uncertainty → defer: low-confidence emotion reads trigger a gentle
  question, never an assumption (confidence gate).
- Data belongs to the family: local SQLite, parent-controlled export/delete,
  PIN-gated dashboard, no raw video stored.
- Neurodiversity-affirming tone: no punishment mechanics, no negative
  reinforcement anywhere in the app.

## 5. Sources

1. NCAEP / Steinbrenner et al. (2020). *Evidence-Based Practices for
   Children, Youth, and Young Adults with Autism.* UNC Chapel Hill.
2. CAPTAIN (2022). *EBP Matrix Definitions.*
   <https://www.captain.ca.gov/documents/EBP%20MATRIX%20DEFINITIONS%202020%20REV%20FEB%202022.pdf>
3. AFIRM modules — Visual Supports, Reinforcement, Social Narratives.
   <https://afirm.fpg.unc.edu>
4. Deng, Lai et al. (2024). *ASD-Chat.* arXiv:2409.01867 (IEEE).
5. Pennisi et al. (2016). *Autism and social robotics: a systematic review.*
   Autism Research 9(2).
6. LuxAI (2023). *How QTrobot delivers evidence-based practices.*
   <https://luxai.com/blog/how-qtrobot-for-autism-delivers-evidence-based-practices-for-intervention-and-education/>
