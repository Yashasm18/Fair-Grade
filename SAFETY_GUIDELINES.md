# 🛡️ Safety & Responsible AI Guidelines

> FairGrade AI is classified as a **Sensitive AI** application because it directly impacts student assessment outcomes. This document outlines our safety policies, privacy commitments, and responsible AI design principles.

---

## 1. Student Privacy

### 1.1 Compliance Framework

FairGrade AI is designed with both **FERPA** (Family Educational Rights and Privacy Act) and **GDPR** (General Data Protection Regulation) principles in mind:

| Regulation | Principle | How FairGrade Complies |
|-----------|-----------|----------------------|
| **FERPA** | Student records must be protected from unauthorized disclosure | Answer sheets are processed **in-memory only** — never written to disk or stored in logs |
| **FERPA** | Parents/students have the right to inspect and amend records | AI grades are **advisory only** — teachers retain full control to accept or override |
| **GDPR Art. 5** | Data minimization | We collect only the image and teacher score; no student metadata is retained after processing |
| **GDPR Art. 17** | Right to erasure | No student PII is persisted — processing is stateless and ephemeral |
| **GDPR Art. 22** | Right not to be subject to automated decision-making | Our **Human-in-the-Loop** design ensures a human teacher makes every final grading decision |

### 1.2 PII Redaction Pipeline

Before any AI evaluation occurs, the **Privacy Agent** automatically strips the following identity markers using regex pattern matching:

- Student **Names**
- **Roll Numbers**
- **Student IDs**
- **ID Numbers**
- **Batch identifiers**

All fields are replaced with `[REDACTED]` tokens before the text reaches the Evaluation Agent. This prevents the AI from developing associations between identity markers and grading outcomes.

### 1.3 Data Flow Safeguards

```
Answer Sheet Image → OCR (in-memory) → PII Redaction → AI Evaluation → Response → Memory Released
                                                                              ↓
                                                                 No disk writes. No image storage.
                                                                 No student data in server logs.
```

- **No persistent image storage**: Uploaded answer sheet images are held in memory only during the evaluation request lifecycle.
- **No server-side logging of student content**: API logs capture request metadata (timestamps, status codes) but **never** student answers, names, or scores.
- **Firebase stores only aggregated metrics**: The Firestore database stores evaluation results (scores, bias percentages) but **not** the original answer sheet content or student identity information.

---

## 2. Preventing Harmful AI Feedback

### 2.1 AI Output Guardrails

FairGrade AI is designed to **never** produce harmful, discouraging, or discriminatory feedback to students:

| Risk | Mitigation |
|------|-----------|
| **Biased grading language** | The AI evaluates against a teacher-provided rubric only — no subjective commentary on student ability |
| **Discouraging feedback** | AI output is limited to: a numerical score, factual reasoning, and a confidence percentage. No qualitative judgments like "poor" or "disappointing" |
| **Hallucinated scores** | Each AI evaluation includes a **Confidence Score** (0–100%). Results below the confidence threshold are flagged for mandatory teacher review |
| **Over-reliance on AI** | The system is explicitly positioned as a "second opinion" — the teacher's judgment is always final |

### 2.2 Human-in-the-Loop (HITL) Design

The cornerstone of our Responsible AI approach:

1. **AI suggests** a score with reasoning and confidence level
2. **Teacher reviews** the AI recommendation alongside the original answer
3. **Teacher decides** — they can **Accept** the AI score or **Override** it with their own
4. **Override data** is logged to improve future bias detection accuracy

> ⚠️ **Critical Principle**: FairGrade AI **never autonomously changes a student's grade**. The AI is an advisor; the teacher is the decision-maker.

### 2.3 Bias Detection — Not Bias Accusation

Our system is intentionally designed to be **non-confrontational**:

- Results are framed as "grading inconsistencies," not "teacher errors"
- The Bias Agent provides a mathematical comparison (`|Teacher Score − AI Score| / 10 × 100`), not a moral judgment
- Severity labels (Low / Medium / High) are based on **objective thresholds**, not subjective assessments
- The analytics dashboard presents patterns **without attributing blame** to individual teachers

---

## 3. Model Safety & Reliability

### 3.1 Multi-Model Fallback

To ensure reliable and safe outputs, the pipeline implements graceful degradation:

```
gemini-2.5-flash → gemini-2.0-flash → gemini-2.0-flash-lite → gemini-2.5-flash-lite
```

Each fallback model is validated against the same safety criteria.

### 3.2 Granular Error Handling

Each agent in the pipeline has independent error handling:

- If the **OCR Agent** fails → the request returns an error (no blind guessing)
- If the **Privacy Agent** fails → the pipeline halts (PII protection is non-negotiable)
- If the **Evaluation Agent** fails → partial results are returned with a clear failure indicator
- If the **Bias Agent** fails → the teacher score is preserved; bias analysis is marked as unavailable

### 3.3 Content Safety

All prompts sent to Google Gemini include structured grading instructions. The model is:

- **Constrained to rubric-based evaluation** — no open-ended commentary
- **Instructed to return JSON** — preventing free-text responses that could contain inappropriate content
- **Scoped to educational content** — the system does not process or respond to non-educational material

---

## 4. Ethical Commitments

### 4.1 Transparency

- The bias detection formula is **published and documented** in our README
- AI confidence scores are always shown alongside AI grades
- Teachers can see the AI's reasoning for every score, not just the number

### 4.2 Fairness

- Identity redaction ensures the AI evaluates **content, not the student**
- The bias detection system applies the same thresholds and formula to every evaluation, regardless of school, subject, or student demographics
- We do not train custom models on student data — we use general-purpose Gemini models to avoid encoded dataset biases

### 4.3 Accountability

- Every AI evaluation and teacher override is logged in Firestore with timestamps
- The analytics dashboard allows administrators to audit grading patterns over time
- This safety document is maintained as part of the repository and versioned alongside the code

---

## 5. Incident Response

If a stakeholder (teacher, student, or administrator) reports that FairGrade AI produced a harmful, inaccurate, or biased result:

1. **Immediate**: The teacher can override the AI score via the HITL interface
2. **Investigation**: The evaluation is reviewed against the rubric and answer content
3. **Remediation**: If a systemic issue is identified, the affected agent is patched and re-tested
4. **Disclosure**: Material safety issues are documented in the repository's changelog

---

## 6. Contact

For safety concerns or privacy inquiries related to FairGrade AI, please open an issue on the [GitHub repository](https://github.com/Yashasm18/Fair-Grade) with the `safety` label.

---

<p align="center">
  <i>This document reflects FairGrade AI's commitment to Google's <a href="https://ai.google/responsibility/principles/">Responsible AI Principles</a> and the broader goal of safe, equitable AI in education.</i>
</p>
