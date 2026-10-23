# Expert Review: Sampling, Administration, and Scoring Guide

**Status: proposed protocol EV-1.0.** Recruitment, topic-packet preparation, questionnaire administration, expert ratings, and agreement analysis have not been completed by this revision. The completed activity is the automated four-configuration experiment. No expert results are supplied or inferred.

## 1. Freeze the evidence before recruitment and rating

The proposed review will use Conservative / seed 42 for both representations from `results/experiments/four_configuration_tuning/`. The source has 7,832 modeling units from 2,118 source documents, including 597 whole-document fallback units. Four tuning configurations and three seeds were evaluated automatically; experts will review a sample from the selected primary runs, not all configurations or all 171 primary topics.

Record the experiment manifest hash, source hash, run and model identifiers, configuration, seed, questionnaire version, draft-label version, and packet version. No model or source changes are required to prepare this documentation. Ratings must remain linked to the exact output version seen by the reviewer.

Prepare draft labels from the current run's keywords and source text using the same procedure for both models. Describe them as researcher-proposed labels, not labels generated or validated by legal experts. Do not reuse topic titles from the earlier Initial run merely because the topic number matches. The existing `configs/temporal_topic_titles.json` relates to older outputs; topic numbers are not stable identities across runs.

Before distribution, the researchers will complete the participant information/consent materials, responsible contact details, withdrawal arrangements, access controls, and retention/deletion arrangements according to institutional requirements. Approval will not be presumed. Actual respondent identities, signed consent, contact details, and raw identifiable comments must not be committed to the public GitHub repository.

## 2. Select four topics per model using the same rules

These rules are proposed in advance; the blank registers do not represent a completed sample.

1. Exclude topic -1 from the topic inventory. For every other topic, sum `fractional_documents` from `document_weighted_prevalence.csv` across all years. Rank descending by this mass, breaking ties by numeric topic ID. This gives one unit of total mass per source document across its topics; do not rank solely by section count.
2. Select the largest-mass topic as the **high-prevalence** case.
3. Divide the remaining ranked list into an upper half and a lower half, placing the extra entry in the upper half if the list length is odd. Freeze these two pools before drawing either random topic.
4. Using a fresh random-number generator initialized to sampling seed **42 for each model**, select one topic uniformly from the upper pool and one uniformly from the lower pool. Log the exact pool, sorted order, generator/software, seed, and selected IDs. These are the **random upper-half** and **random lower-half** cases; their themes will not be chosen by the researchers.
5. For each remaining topic, find its membership-Jaccard match in the saved seed-42-versus-43 and seed-42-versus-44 alignment tables. An unmatched primary topic contributes zero for that comparison. Select the remaining topic with the smallest mean of those two Jaccards, breaking ties by numeric topic ID, as the **stability-risk** case. This is a sampling criterion, not an expert score or proof of poor legal quality.
6. Record all four roles, the selection values, and any deviation in `sampling_register.csv`. Never replace a difficult topic just because its examples look poor. A genuinely unusable packet will be documented and handled consistently before rating; the reason and any replacement rule will be approved and recorded rather than hidden.

There will be eight topic packets, not 171. This diagnostic sample deliberately mixes prevalence, random selection, and difficulty. It is not a simple random sample, and neither its rating proportions nor its preference votes will be generalized to all topics or all ordinances. The same sampling roles make the workload comparable; they do not make the selected themes identical across models.

## 3. Select three assigned examples per topic

Use the current run's full `section_topics.csv`, not only `representative_sections.csv`, because the latter contains only high-ranked examples. Before using an excerpt, verify its source reference and context.

- **Representative:** select the highest-membership-strength assigned unit, breaking ties by ordinance ID and section ID. If the strength field is absent, select a seeded random unit and explicitly record that no strength ranking was available.
- **Random:** select a seeded random remaining unit, preferring a different parent document and a different year from the first example when that combination exists. Otherwise prefer a different document, and then any remaining distinct unit. Record the pool and selection.
- **Lower-ranked:** among remaining units from unused parent documents where possible, select the lowest membership strength; break ties by source-unit identifiers. If strengths are absent or all eligible strengths are tied, use a seeded random remaining unit and mark it as random, not as an established borderline assignment.

For random example selection, use seed 42 with a documented stable order of model, topic, and unit identifiers. The lower-ranked example is a diagnostic candidate, not a known error. HDBSCAN membership strength is not calibrated legal confidence. Record the rule, strength when available, unit type, source reference, and resolved year in `excerpt_register.csv`.

Do not manufacture a third distinct unit or a second year. If fewer than three distinct units exist, include those available, record the shortfall, and show it to reviewers. Where documents are fallbacks, label them as such. Do not treat three excerpts as proof of coherence throughout a cluster.

For readability, display a short verbatim passage, normally about 100–200 words, with access to the full unit and surrounding source context. This is a display target, not an automatic truncation rule: keep qualifications, exceptions, and cross-references needed to understand the provision, or supply a longer passage. Mark omissions, distinguish extracted text from any researcher transcription, and disclose unreadable text. The original source and page locator will be checked manually; do not fabricate PDF page numbers from model section IDs.

## 4. Assemble equivalent packets

Each packet will contain:

- Neutral system code X or Y and packet ID; draft label; questionnaire/packet version.
- Up to ten nonempty c-TF-IDF keywords in their saved rank order. Do not improve one model's list through unrecorded manual pruning.
- Three selected assigned examples, identified as representative/random/lower-ranked-or-random, with source references, resolved years, unit types, and full-context access.
- Two other same-model topic summaries for B5. Select the two with the greatest Jaccard overlap of their displayed keyword sets, excluding -1 and the reviewed topic; break ties by topic ID. Show labels and keywords, and explain that this is a limited comparison panel, not evidence of semantic equivalence. If all overlaps are zero, disclose that fact to the researchers and describe the entries simply as comparison topics. B5 may be NA if the supplied information is insufficient.
- An annual table and line chart of document-weighted shares for all observed years, with zeros distinguished from unavailable data, a clearly labeled percentage axis, and the number of source documents per year. Retain unassigned units in the denominator; selected topic lines need not sum to 100%. Use the same axes and conventions within a genuinely comparable pair of displays; otherwise label different scales explicitly.
- Year-specific keywords from `yearly_topic_keywords.csv`, identified as generated lexical summaries, and source examples from relevant years when available. Do not fill a missing year-topic keyword list with invented words or infer absence from a missing list.
- A short, neutral trend description that the reviewer can accept or challenge, plus an explanation of archive coverage, source-year assignments, and the difference between a fractional share and a whole-ordinance count.

Use the same space allowance and evidence rules for both systems. A label based only on keywords will be marked as such if source review could not support a better label. Similarity summaries and annual keyword tables may be appendices to avoid crowding the main card.

The annual source-document counts in this experiment are: 2016—174; 2017—204; 2018—249; 2019—266; 2020—165; 2021—233; 2022—279; 2023—218; 2024—298; 2025—32. These are modeled source documents, not independently established totals of all ordinances enacted. Different text versions sharing an ordinance number remain distinct source documents under the existing preparation.

## 5. Keep model comparison fair and manageable

The researchers will hold the X/Y-to-model key separately from participant-facing files. A fixed mapping may be used across reviewers; presentation order will alternate X-first and Y-first where possible. Do not change the meaning of a system code during an individual's review. Packet filenames must not reveal the algorithm inadvertently. Masking will reduce expectations but will not guarantee blindness.

Aim for a small panel of two to three suitably experienced reviewers; report the actual participation. No minimum years, degree, job title, or already-recruited individual is asserted. Document relevant expertise, potential conflicts, and coverage limitations.

Plan two sessions of four cards, about 30–45 minutes each, subject to a preliminary readability/workload check. That check will not count as completed expert validation. If changes are needed, revise and freeze the instrument before collecting formal ratings. Do not silently shorten the sample after seeing unfavorable scores. Partially completed reviews will remain usable at the item level, with missingness reported.

Reviewers will rate independently first. Collect profile information once, topic ratings eight times, and the final comparative judgment once. Log clarifications without suggesting answers. Discussion after independent submission may clarify evidence, but original ratings and disagreements must remain traceable.

### Practical Google Forms setup

Use three linked forms rather than expecting a form to loop automatically:

1. **Profile/consent form:** study information, consent, reviewer code, A1–A5. End the form if consent is declined. Collect email only if justified and explained; do not make public response summaries available.
2. **Topic form:** reviewer code, packet ID/version, neutral system code, B1–B6, C1–C4, D1–D4, E1–E2, and comment/NA-reason fields. Send one prefilled link per packet. Use multiple-choice grids with columns 1, 2, 3, 4, 5, and NA, or individual multiple-choice items. Do not force a substantive rating for every row. Allow separate submissions for different packets.
3. **Final comparison form:** E3–E10, completed after the packets. Include the insufficient-information option for respondents who saw only one system.

The item-bank CSV is a copying/building guide, not a claim that Google Forms natively imports arbitrary CSV files. No online form has been created or launched by this revision. For paper use, print Section A and the final comparison once, and copy the two topic-form pages for each packet; attach the corresponding materials.

## 6. Rating and item-to-dimension map

All 16 rated statements use the same five-point agreement scale and separate NA option. Higher values are favorable. The concern comments and action suggestions are qualitative, not reverse-scored ratings.

| Dimension | Items | Number of items |
|---|---|---:|
| Legal Coherence, including source support | B1, B4, C1, C2, C3, C4 | 6 |
| Thematic Relevance | B3, B5, B6 | 3 |
| Label Appropriateness | B2 | 1 |
| Temporal Interpretation | D1, D2, D3, D4 | 4 |
| Overall Research Quality of supplied outputs | E1, E2 | 2 |

Every item contributes to only one dimension. Do not add the dimensions into a grand score or treat overlapping aspects of usefulness as independent evidence of model superiority. Label Appropriateness is a single-item judgment, not a multi-item reliability scale. Background, preference, and free-text questions are not part of the numerical dimensions.

The existing pipeline's blank five-dimension expert templates are not completed assessments and will remain unchanged. This expanded instrument uses item-level records; the current modeling scripts do not automatically score its responses. Dimension summaries may be derived in a documented spreadsheet using the procedure below.

## 7. Response data and analysis

Use the blank long-format `response_template.csv`: one row per expected reviewer × packet version × rated item. Its supplied header has no participant rows. Keep original form exports immutable, with any cleaned dataset derived separately.

- Valid response: numeric integer 1–5; status `valid`.
- Explicit NA: empty numeric rating; status `NA`; retain the reason when given.
- Blank or unreturned item: empty numeric rating; status `missing`.
- Out-of-range values or duplicate submissions: check with the source record or reviewer where appropriate; record the decision. Never select the more favorable duplicate response automatically.
- Exclude NA and missing values from numeric calculations, but count them separately against the expected responses. Never impute them as 0 or 3. If there are no valid observations, return unavailable, not zero.

For each item within each model/topic, report counts at 1–5, median, available-response mean, minimum/maximum where useful, and valid/NA/missing counts. The mean is the sum of valid ratings divided by their count; the median and distributions preserve the ordinal interpretation.

For reviewer r, topic t, and dimension d with its fixed item set I(d):

- Compute the reviewer-topic dimension mean only if every item in I(d) has a valid numeric response.
- Average those complete reviewer-topic means equally across eligible reviewers to obtain the topic-dimension mean.
- Average eligible topic-dimension means equally across the sampled topics for a model-level descriptive mean. Report how many of the four topics and how many reviewers contribute; do not weight by cluster size or by the number of answered rows.
- Retain all available individual item responses even when a dimension is incomplete. Report the reason for incomplete dimensions; complete-case summaries may be selective and should not conceal missing evidence.
- For a paired reviewer-level model comparison on a dimension, include only reviewers with complete scores for all four topics in both models. For each such reviewer, average the four topic scores within X and within Y and describe the paired difference. If no reviewer qualifies, state that the paired summary is unavailable; retain side-by-side descriptive results with their denominators and the qualitative comparison.

The paired unit is the reviewer, not a claim that topic 0 in one model equals topic 0 in another. The small diagnostic sample does not justify a population-level accuracy estimate, a definitive model winner, or an automatic significance test.

## 8. Interpretation and review flags

Retain the original numerical band boundaries, but explicitly label them as study-defined descriptive rules:

| Unrounded mean | Description |
|---|---|
| Greater than 4.20 through 5.00 | Excellent / strongly favorable assessed quality |
| Greater than 3.40 through 4.20 | Good / favorable assessed quality |
| Greater than 2.60 through 3.40 | Mixed or neutral; requires examination |
| Greater than 1.80 through 2.60 | Poor / unfavorable assessed quality |
| 1.00 through 1.80 | Very poor / strongly unfavorable assessed quality |

The original table showed rounded ranges such as 4.21–5.00. Explicit continuous intervals remove gaps for unrounded means. Keep full precision for category assignment and flags; when rounding could make a boundary unclear, show additional digits or state the category explicitly.

Retain the original **topic-dimension mean below 3.00** review flag. Do not call it a validated cutoff, an accuracy threshold, or a pass/fail standard established by prior research. A value below 3.00 can also fall in the middle descriptive band; the band describes the result and the flag specifies an action. Exactly 3.00 is neutral and not flagged numerically, not proof of acceptance. An incomplete dimension has no numerical flag outcome and is marked insufficient assessment, not passed.

The old middle description, “Acceptable but needs improvement,” is changed to “Mixed or neutral; requires examination” to avoid interpreting the scale midpoint as expert approval. No other new numeric quality threshold is introduced. Serious source contradictions, meaningful disagreement, missing materials, or misleading interpretations will be examined regardless of score. Preserve their comments even when other reviewers rate the topic highly.

## 9. Inter-rater agreement without invented results

For each rated item, compare only independent numeric ratings on the same packet version. For each topic with at least two raters, form all unordered rater pairs. Report:

- **Exact agreement:** pairs with identical ratings / all valid pairs.
- **Within-one-point agreement:** pairs whose ratings differ by at most one / all valid pairs.
- The numerator and denominator, item, model, and packet coverage.

Do not create a pair from a missing/NA rating or from different topics or versions. With more than two reviewers, pairwise observations share raters and are not independent. These proportions will be descriptive agreement summaries, not chance-corrected reliability coefficients. No agreement cutoff or result is specified in advance. If only one reviewer participates, agreement is not calculable. If the panel requires a formal ordinal coefficient later, that addition will need a documented method and software decision; it must not be improvised or reported as already measured.

## 10. Qualitative feedback, revisions, and reporting

Code feedback by concern: label, coherence/membership, relevance/distinctness, breadth/narrowness, source/OCR/segmentation, date assignment, temporal claim, presentation, or other. Preserve the respondent's wording privately and use source-linked, non-identifying summaries in the thesis. A comment may address more than one category.

The feedback log will record the coded reviewer, packet/item/source, concern, proposed correction, researcher decision and rationale, required recalculation, re-review status, and resulting version. Do not make automatic merges or deletions based solely on a low score or majority vote. Examine source evidence, including dissenting observations.

Label-only changes do not alter assignments; record them separately. Reassignment, merging/splitting, preprocessing, or year changes will require rerunning affected quantitative and temporal calculations and preparing new review materials. Original ratings will remain attached to the original packet version. Any second review will be reported separately; absent re-review, label the revised result as not yet reviewed. Feedback used to retune a model is developmental input, not independent held-out validation.

The final account will state who participated in non-identifying terms, how much was reviewed, incomplete responses, rating distributions, disagreements, proposed corrections, actions taken, and unresolved limitations. Expert judgments will complement automated evidence about coherence, diversity, coverage, stability, and temporal sensitivity; they will not be converted into those metrics or presented as proof of objective correctness.
