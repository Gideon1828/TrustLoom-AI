# ═══════════════════════════════════════════════════════════════════════════════
#                   TRUSTLOOM AI — ADD-ON MODULES DOCUMENTATION
#                         Upcoming Features & Enhancements
# ═══════════════════════════════════════════════════════════════════════════════

This file documents all planned add-on modules for the TrustLoom AI system.
These modules extend the core evaluation pipeline with explainability, actionable
feedback, downloadable reports, multi-candidate comparison, and visual analytics.

---

## ADD-ON MODULE INDEX

| #  | Module | File | Priority |
|----|--------|------|----------|
| 21 | XAI Engine | models/explainability_engine.py | 1st |
| 22 | Suggestion Engine | models/suggestion_engine.py | 2nd |
| 23 | PDF Report Generator | utils/report_generator.py | 3rd |
| 24 | Multi-Resume Comparison | Frontend + API Extension | 4th |
| 26 | Interview Question Generator | models/interview_generator.py | 5th |
| 27 | ATS Compatibility Score | models/ats_checker.py | 6th |

---

## MODULE 21 — Explainable AI (XAI) Engine--finished

File: models/explainability_engine.py
Priority: 1st — all other add-on modules depend on this
Effort: Medium
Impact: Very High

The Explainable AI Engine is the most foundational add-on module and must be
built before any of the others, since the PDF Report, Suggestion Engine, and
Multi-Resume Comparison all depend on the structured explanation data it
produces.

Its primary purpose is to transform raw numerical scores into transparent,
human-readable reasoning. For every score component in the pipeline — BERT,
LSTM, GitHub, LinkedIn, Portfolio, and Experience — the engine will generate
a clear sentence or paragraph that explains exactly why that particular score
was given to the freelancer.

The engine will contain three internal sub-components: an explanation builder
that maps score values and flag data to textual descriptions, a score reasoning
text generator that constructs natural language sentences from score thresholds
and component inputs, and a factor-to-human explanation mapper that translates
technical indicators (such as overlapping project count or BERT confidence
level) into plain language that a non-technical recruiter or client can
understand.

For example, if the LSTM detects overlapping project timelines above a certain
threshold, the engine will produce a statement such as: "High project overlap
was detected, which may indicate an unrealistic workload or copied project
timelines." If the BERT score is low due to vague language, it will explain:
"Resume language quality is below average — multiple instances of vague
phrasing and weak action verbs were found." If the GitHub validation returns
a low score, the explanation might read: "The provided GitHub profile has
very few public repositories and shows no recent commit activity."

This module will hook into the Final Scorer and expose its explanations as
additional fields in the existing API response from the /evaluate endpoint.
No new endpoint is required — the explanation data will be seamlessly embedded
into the current JSON response structure.

---

## MODULE 22 — Resume Improvement Suggestions Engine

File: models/suggestion_engine.py
Priority: 2nd — leverages existing flag data from BERT, LSTM, and Heuristic
Effort: Easy to Medium
Impact: High

The Suggestion Engine converts the system's existing detection capabilities
into concrete, actionable improvement advice for the freelancer being evaluated.
Rather than simply flagging an issue, this module tells the freelancer exactly
what to do to fix it and, where possible, quantifies how many trust points
could be gained by making that improvement.

The engine takes two inputs: the full list of aggregated flags produced by
the pipeline (BERT language flags, LSTM AI flags, and Heuristic flags), and
the structured explanations produced by the XAI Engine. From these inputs it
generates a prioritized list of specific improvement suggestions ranked by
potential score impact.

For language issues, instead of just flagging "weak action verbs detected",
the engine will suggest: "Replace phrases like 'worked on' or 'helped with'
with stronger ownership verbs such as 'Designed', 'Architected', 'Optimized',
or 'Delivered' to convey initiative and impact." For missing quantified
achievements, the suggestion will be: "Add measurable results to your
experience descriptions — for example, '40% reduction in load time',
'served 10,000+ daily users', or '$500K revenue impact' — to significantly
strengthen perceived credibility."

For heuristic issues, the engine will give practical link-related guidance
such as: "Adding a complete and active LinkedIn profile with skills,
endorsements, and work history can add up to 10 trust points." If portfolio
validation failed, it will advise: "Ensure your portfolio URL is publicly
accessible, loads without errors, and showcases real project work."

For experience mismatches, the suggestion will be specific: "Your claimed
Senior level requires at least 5 years of experience and 10+ projects. Your
resume currently reflects approximately 2 years and 4 projects — consider
selecting Mid-Level or enriching your resume with additional project history."

This module makes TrustLoom AI not just evaluative but constructive — helping
freelancers understand how to improve their profiles rather than simply
receiving a pass/fail score.

---

## MODULE 23 — Downloadable Professional PDF Report

File: utils/report_generator.py
API Endpoint: POST /generate-report
Priority: 3rd — all data (scores, explanations, suggestions) is now available
Effort: Easy
Impact: Very High (gives the system enterprise-grade presentation)

The PDF Report Generator produces a professionally formatted, downloadable
PDF document that summarizes the complete trust evaluation for a given
freelancer. This gives recruiters, clients, and hiring managers a polished,
shareable artifact that can be distributed to stakeholders without requiring
access to the web interface.

The report will be generated using a Python PDF library such as reportlab or
weasyprint and will follow a structured, branded layout. It will include a
header section showing the freelancer's name (if available), the evaluation
date, and the TrustLoom AI branding. Below the header, a prominent visual
section will display the final trust score alongside a gauge or progress bar
that visually indicates the score level and corresponding risk classification.

The body of the report will contain a detailed score breakdown section showing
each scoring component — BERT language score, LSTM trust score, GitHub
validation score, LinkedIn validation score, Portfolio validation score, and
Experience consistency score — alongside the explanation produced by the XAI
Engine for each one. This ensures the recruiter understands not just the
numbers but the reasoning behind them.

Following the score breakdown, the report will include a complete flags section
organized by category: Language Flags from BERT analysis, Pattern Flags from
LSTM inference, and Verification Flags from the Heuristic pipeline. Each flag
will be listed with its severity and a brief description.

The final section of the report will present the prioritized improvement
suggestions from the Suggestion Engine, allowing the report to serve a dual
purpose — both as an evaluation result for the recruiter and as a personal
improvement roadmap for the freelancer.

A new API endpoint, POST /generate-report, will accept either an evaluation
result object or a previously computed evaluation identifier, run the XAI and
Suggestion engines if not already run, and return the PDF as a downloadable
binary file attachment.

---

## MODULE 24 — Multi-Resume Comparison Mode

File: Frontend (React) + API Extension
Priority: 4th — scoring outputs are structured enough for comparison
Effort: Medium (primarily frontend work)
Impact: High

The Multi-Resume Comparison Mode allows users to submit two or three resumes
simultaneously and view their evaluation results presented side-by-side in a
structured comparison table. This is particularly useful for recruiters who
are evaluating multiple candidates for the same role and need a quick,
objective way to rank them.

No new AI model or backend scoring logic is required for this feature. Each
resume is evaluated independently through the existing /evaluate endpoint,
and the comparison is entirely a presentation layer that re-uses the structured
outputs already produced by the pipeline.

The frontend will allow users to upload two or three resumes at once through
an extended version of the file upload interface. After all evaluations
complete, a comparison table will render with one column per candidate and
one row per metric. The metrics displayed in the comparison will include:
Final Trust Score, Resume Score (BERT + LSTM combined), Heuristic Score,
individual BERT score, LSTM trust probability, GitHub validation score,
LinkedIn validation score, Portfolio validation score, Experience match result,
total detected overlapping projects, effective years of experience, and the
overall risk level and recommendation.

The table will use color-coded cells to make differences immediately visible —
green backgrounds for high scores, yellow for medium, and red for low — so
that a recruiter can instantly identify which candidate performs best in each
category without reading individual numbers carefully.

The table will also support basic sorting by any metric column and include
a summary banner at the top indicating which candidate received the highest
overall trust score. This makes the decision process faster and more
data-driven without requiring any additional AI computation.

---

## MODULE 26 — Interview Question Generator

File: models/interview_generator.py
API Endpoint: POST /generate-interview-questions
Priority: 6th — uses existing resume parsing and scoring data
Effort: Low
Impact: High

The Interview Question Generator automatically produces role-specific interview
questions tailored to each candidate's resume content, claimed skills, and
detected gaps. This transforms TrustLoom AI from a pure evaluation tool into
an active hiring assistant that helps recruiters conduct more effective
interviews.

The generator analyzes several data sources already available in the pipeline:
the parsed resume text, the extracted project list with technology stacks,
the claimed experience level, the detected skill keywords, and any flagged
inconsistencies or concerns from the BERT, LSTM, and Heuristic modules.

From these inputs, the engine produces four categories of interview questions:

Technical Skill Verification Questions are generated based on the technologies
mentioned in the resume. If a candidate claims expertise in React and Node.js,
the system will generate questions like: "Describe how you would implement
state management in a large React application" or "Explain your approach to
handling authentication in a Node.js API." The questions scale in difficulty
based on the claimed experience level — Senior-level claims receive more
architectural questions, while Mid-level claims receive more implementation-
focused questions.

Project Deep-Dive Questions are generated from the extracted project list.
For each significant project, the generator produces questions such as:
"Walk me through the challenges you faced on [Project Name] and how you
resolved them" or "What was the impact of your contribution to [Project Name]
and how did you measure success?" These questions help recruiters verify
that candidates can speak fluently about their claimed work.

Red Flag Clarification Questions are specifically generated when the system
detects inconsistencies or concerns. If overlapping project dates were
detected, the question might be: "I notice your resume shows [Project A] and
[Project B] running concurrently — can you describe how you managed working
on both simultaneously?" If vague language was flagged, the question becomes:
"Your resume mentions you 'helped with' the authentication system — could
you describe your specific technical contributions?"

Behavioral and Situational Questions are generated based on the role type
and experience level, drawing from a curated template library. Examples
include: "Describe a time when you had to learn a new technology quickly
to deliver a project" or "How do you handle disagreements with team members
about technical decisions?"

The API endpoint POST /generate-interview-questions accepts an evaluation
result or file ID and returns a structured JSON object containing 8-12
recommended questions organized by category, along with the reasoning behind
why each question was selected. An optional role_context parameter allows
recruiters to provide the target job description, which the generator uses
to further customize questions toward role-specific requirements.

This module has low implementation effort because it leverages existing
parsed data and uses template-based generation with intelligent slot-filling
rather than requiring any new AI model training.

---

## MODULE 27 — ATS Compatibility Score

File: models/ats_checker.py
API Endpoint: Integrated into /evaluate response
Priority: 7th — complements existing resume quality analysis
Effort: Medium
Impact: High

The ATS (Applicant Tracking System) Compatibility Score evaluates how well
a resume will parse and perform when processed by common enterprise hiring
systems such as Workday, Taleo, Greenhouse, and Lever. Many qualified
candidates are rejected by automated systems before a human ever sees their
resume — this module helps identify and fix formatting issues that cause
ATS parsing failures.

The checker performs several categories of analysis:

Structure and Formatting Analysis examines the document layout for ATS-hostile
patterns. Tables, text boxes, headers/footers, multi-column layouts, and
embedded images often cause parsing failures. The checker detects these
elements and flags them with specific warnings like: "Two-column layout
detected — ATS systems may scramble content order" or "Text embedded in
image/graphic — this content will not be parsed."

Section Header Recognition verifies that standard resume sections are
present and labeled with recognizable headings. ATS systems look for
keyword-based section markers like "Experience", "Education", "Skills",
and "Projects". Non-standard or creative headers like "My Journey" or
"What I've Built" may not be recognized. The checker provides mappings
like: "Consider changing 'Career Highlights' to 'Professional Experience'
for better ATS recognition."

Contact Information Extraction Test simulates parsing the candidate's
name, email, phone number, and LinkedIn URL from the document. If any of
these standard fields cannot be reliably extracted, the checker reports:
"Email address could not be extracted — ensure it appears as plain text
near the top of the document."

Keyword Density Analysis compares the resume content against common
role-specific keyword lists. For a Software Engineer resume, the checker
verifies presence of expected terms: programming languages, frameworks,
methodologies (Agile, Scrum), and common role verbs (developed, designed,
implemented, deployed). Low keyword density results in a suggestion:
"Consider adding more industry-standard terminology — ATS systems may rank
this resume lower for 'Software Engineer' roles."

File Format Compatibility assigns scores based on the uploaded format.
PDF files created from Word documents score highest. Image-based PDFs
(scanned documents) score lowest since they contain no extractable text.
DOCX files score well but may have compatibility issues with older ATS
versions. The checker recommends the optimal format if issues are detected.

Date and Duration Parsing Test verifies that employment dates are in
ATS-friendly formats. Standard formats like "Jan 2022 - Present" or
"2020 - 2023" parse reliably, while unconventional formats like
"January of twenty-twenty" or missing end dates cause parsing failures.

The ATS Compatibility Score is returned as a new field in the /evaluate
response:

```json
"ats_compatibility": {
  "score": 78,
  "grade": "B+",
  "issues": [
    {
      "category": "formatting",
      "severity": "medium",
      "message": "Two-column layout detected in skills section",
      "recommendation": "Convert to single-column format"
    },
    {
      "category": "keywords",
      "severity": "low",
      "message": "Low density of role-specific technical terms",
      "recommendation": "Add more technology keywords from job descriptions"
    }
  ],
  "parsing_confidence": {
    "name": "high",
    "email": "high",
    "phone": "medium",
    "experience_dates": "high"
  }
}
```

The frontend will display this as a secondary score widget alongside the
main Trust Score, with an expandable section showing specific ATS issues
and recommendations. This makes TrustLoom AI valuable not just for recruiters
evaluating candidates, but for candidates improving their own resumes before
submission.

---

## IMPLEMENTATION ORDER

The add-on modules must be built in sequence because each one depends on
the outputs of the previous:

Step 1 — XAI Engine must come first. It produces the structured explanation
data that every other add-on module consumes. Without it, the PDF report
has no explanations, the Suggestion Engine has no context, and the comparison
mode cannot show reasoning.

Step 2 — Suggestion Engine comes next. It consumes flag data (already
available) and XAI explanations (from Step 1) to produce prioritized
improvement advice. This data is needed by the PDF report.

Step 3 — PDF Report Generator comes after both the XAI Engine and Suggestion
Engine are complete, since the report is a compilation of scores, explanations,
flags, and suggestions — all of which must exist before the PDF can be built.

Step 4 — Multi-Resume Comparison can be developed independently of Steps 1-3
since it only requires the existing /evaluate endpoint to be called multiple
times. It is placed 4th simply because the earlier modules deliver higher
individual impact.

Step 5 — Interview Question Generator leverages existing parsed resume data,
extracted skills, and flag outputs to produce role-specific interview
questions. It has low effort since it uses template-based generation with
intelligent slot-filling rather than new AI model training.

Step 6 — ATS Compatibility Score can be developed in parallel with other
modules since it performs independent structural analysis of the uploaded
document. It is placed last because it adds complementary value rather than
being a dependency for other features.

---

## SCORING IMPACT SUMMARY

These six add-on modules do not change the core scoring formula. The trust
credibility.

What these modules add is transparency, usability, and presentation quality
on top of the existing scoring engine — making the system more trustworthy
to its own users, more useful to freelancers seeking to improve, and more
presentable to enterprise clients and academic evaluators.
