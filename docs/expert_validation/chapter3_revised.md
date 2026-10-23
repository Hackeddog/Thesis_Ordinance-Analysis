# Model Evaluation and Expert Validation

## Automated model evaluation

The study will interpret automated evaluation and expert validation as complementary sources of evidence. Automated measures describe properties of the generated topics and assignments, whereas expert judgments will examine whether the thematic and temporal interpretations are supported by ordinance content. Neither form of evaluation will be treated as a substitute for the other (9; 13; 15).

Model A (Lexical) represents the prepared text using TF-IDF followed by normalized singular value decomposition. Model B (Legal-BERT-based Semantic) uses frozen Legal-BERT embeddings obtained through content-token pooling across all chunks of each modeling unit. Both approaches use UMAP, HDBSCAN, and c-TF-IDF with the same eligible units and shared topic-keyword vocabulary. Modeling units consist of detected ordinance sections and explicitly identified whole-document fallbacks; they will not all be described as independently verified legal sections.

The completed parameter experiment evaluated Initial, Conservative, Fine-grained, and Coarse-grained configurations for each model using random seeds 42, 43, and 44. Quantitative evaluation includes the number of non-outlier topics, C_v coherence, topic diversity, assignment coverage, the complementary outlier rate, clustering stability, temporal sensitivity, and computational cost. Stability includes assignment-based agreement and explicit topic alignment across seeds. These measures have different meanings and will not be combined into an unspecified overall accuracy score. Results of the completed experiment will be reported in Chapter 4 rather than presented as expert-validation findings.

The provisional primary configuration is Conservative for both models, with seed 42 defining the primary topic identities. Expert review will examine sampled outputs from these frozen runs. It will not be represented as an expert assessment of every tuning configuration, nor will the provisional selection be described as legally validated before the review is completed.

## Expert validation: purpose and scope

Expert validation will assess the legal coherence, thematic relevance, label appropriateness, temporal interpretation, and practical usefulness of the generated topics. This review will be necessary because coherent or distinctive keywords may describe repeated legal wording, procedural material, or extraction artifacts rather than a substantively useful legislative theme. Expert assessment will examine the relationship between labels, keywords, assigned text, and the proposed interpretation, rather than merely whether a label sounds plausible.

The review will address the first research question by examining the meaning and usefulness of identified legislative and administrative topics. It will support the second research question by assessing whether descriptions of recurring, increasing, or decreasing topic shares are justified by the supplied annual data. Expert assessments of the two representations will complement, but will remain separate from, the automated comparisons in the third and fourth research questions. Reviewers will not be asked to verify coherence scores, clustering algorithms, computational performance, or other technical quantities that cannot be established from legal or policy expertise alone.

## Selection of reviewers

The researchers will purposively seek reviewers with relevant experience in legal research or practice, legislative drafting or administration, policy analysis, or the interpretation and use of local ordinances. Suitability will be assessed through the relevance of the person's work to the materials, rather than through a fixed minimum number of years or a mandatory professional title applicable to every role. Reviewers will not be limited to lawyers. Reviewers' fields of expertise, years of relevant experience, and familiarity with local legislative documents will be recorded.

A small panel, provisionally targeting two to three reviewers, will be sought subject to availability and the applicable institutional requirements. This is a proposed recruitment target, not a statement that participants have been identified or recruited. The actual number of participants, relevant backgrounds, and any limitations in subject coverage will be reported. Participation will be voluntary and based on informed consent; reviewers may omit an item or stop participation. Identifying information will be stored separately from coded research responses, and any necessary institutional permission or ethics clearance will be obtained before recruitment or data collection.

## Review materials and topic sampling

Before administering the questionnaire, the researchers will freeze the model outputs, topic identities, draft labels, review materials, sampling rules, and questionnaire version. A manageable sample of four topics per model, eight topics in total, will be prepared. Topic -1 will not be treated as a substantive topic. The selection will include a high-prevalence topic, a seeded random topic from the upper half of the remaining prevalence ranking, a seeded random topic from the lower half of the remaining ranking, and a topic with weak membership stability across seeds. The same selection rules will apply to both models. This design will include common themes, smaller themes, and potentially problematic groupings instead of selecting only favorable examples.

Prevalence for sampling will be ranked by total fractional-document mass: each source document will contribute a total weight of one, divided among the topics assigned to its units. For the difficult-topic selection, unmatched topics across seeds will receive zero membership overlap in the sampling calculation, not an invented expert score. The selected topics, selection reasons, randomization seed, and any departures from the planned procedure will be recorded. This purposive and stratified review will support diagnostic interpretation; it will not provide a statistically representative estimate of expert approval for the entire topic inventory.

Each topic packet will contain a neutral packet identifier, a clearly marked draft label, up to ten representative keywords, three assigned text examples, and source references. Examples will include a high-ranked representative, a randomly selected member, and a lower-ranked member when membership scores allow that distinction. Different parent documents and years will be preferred where available. Membership strength will not be described as a probability that an assignment is legally correct. Whole-document fallbacks and apparent OCR or segmentation limitations will be identified explicitly.

Each excerpt will include its source ordinance reference, modeling-unit identifier, resolved study year, and access to the complete source text and relevant context. Original PDF references and page numbers will be supplied only after they have been checked. If an original source cannot be located or read, that limitation will be disclosed rather than concealed by an unverified reference. Shortened excerpts will retain meaningful qualifications and cross-references, with omissions marked. Two potentially similar topics from the same model will be shown as comparison summaries for assessing distinctness; reviewers will not be asked to establish distinctness from the entire corpus.

Temporal materials will include the topic's document-weighted annual shares for 2016–2025, annual document denominators, relevant year-specific keywords and excerpts, and a short descriptive interpretation. A fractional share will not be labeled as the count of ordinances devoted exclusively to a topic. Unassigned units will remain in the denominator, and the displayed subset of topics will not be expected to sum to 100%. The year will be identified as the resolved study-year assignment; the January 1 timestamp used to construct yearly bins will not be presented as an actual enactment date. The materials will disclose that the available 2025 archive contains only 32 modeled source documents and that unequal archive coverage limits comparisons. A missing keyword list will not be represented as evidence that a topic did not exist.

## Validation dimensions and questionnaire

The questionnaire will retain the five dimensions of the existing methodology while specifying what reviewers can reasonably judge. The term content-based accuracy will refer to fidelity to the displayed source text and the reasonableness of the proposed grouping. It will not refer to supervised classification accuracy or agreement with ground-truth topic labels, which are not available.

| Dimension | Scope of expert judgment | Questionnaire items |
|---|---|---|
| Legal Coherence | Relatedness of keywords and assigned examples; source support; reasonable membership and scope without misleading combinations or divisions. | B1, B4, C1–C4 |
| Thematic Relevance | Relevance to Davao City ordinance content, distinctness from the supplied comparison topics, and usefulness for exploring legislative themes. | B3, B5, B6 |
| Label Appropriateness | Whether the draft label accurately describes the keywords and supplied ordinance examples. | B2 |
| Temporal Interpretation | Clarity of the annual presentation, support for changes in the displayed data, reasonable descriptive interpretation, and avoidance of unsupported causal or legal claims. | D1–D4 |
| Overall Research Quality | Overall usefulness of the supplied result and transparency of its evidence and limitations, within the reviewer's area of expertise. This will not constitute approval of the entire technical methodology. | E1, E2 |

Reviewers will use the following common response scale: 1—Strongly Disagree; 2—Disagree; 3—Neither Agree nor Disagree; 4—Agree; and 5—Strongly Agree. A separate Not Applicable / Unable to Assess option will be available for every rated item. A neutral rating will not be used as a substitute for insufficient evidence or expertise. All rated statements will be worded so that a higher score indicates a more favorable judgment; no reverse scoring will be required. Comments and source-linked examples will be invited, particularly where a topic is unclear, an assignment is questionable, or a temporal claim is unsupported.

## Administration and comparison of models

Reviewers will receive equivalent packet formats, the same number of sampled topics, the same rating criteria, and the same scope information for both models. Outputs will be identified by neutral system codes, with the lexical/semantic mapping retained by the researchers until the individual ratings are complete. The presentation order will be counterbalanced where practicable. Automated metric values, model recommendations, and algorithm names will not be displayed before rating, to reduce expectations based on those details. Such masking will not be described as a guarantee of double-blind review.

The researchers will check the clarity of the instructions and the burden of the packet before formal administration. Review will be planned as two sessions of four topic packets, provisionally allowing about 30–45 minutes per session; the actual burden will be checked rather than asserted as measured. The questionnaire may be completed through linked Google Forms or a printed response booklet. Expert background information will be collected once, topic ratings will be collected separately for each packet, and the overall comparison will be completed after both systems have been reviewed.

Reviewers will initially respond independently. Clarification will concern the meaning of the instructions or the location of evidence, not which answer is preferred. Any subsequent discussion will be documented without replacing the original independent ratings. The actual sample, completed packets, nonresponses, and administration deviations will be reported. Topic identifiers will remain model- and run-specific; similarly numbered topics will not be assumed to have the same meaning across models.

## Scoring and interpretation

Per-item summaries will show the number of valid responses, the frequencies of ratings 1–5, the median, the mean where reported, and separate counts of missing and Not Applicable / Unable to Assess responses. The available-response mean will be calculated as follows:

Mean rating = sum of valid numeric ratings / number of valid numeric ratings.

Missing and Not Applicable / Unable to Assess responses will not be coded as zero or as the neutral value three. When there are no valid ratings, the result will be reported as unavailable. Because the responses are ordinal and the panel will be small, response distributions and medians will accompany means; numerical differences will not automatically be interpreted as statistically or substantively important.

For each reviewer and topic, a dimension score will be calculated only when all items mapped to that dimension have numeric ratings. Otherwise, the dimension will be marked incomplete while its available item responses remain in the item summaries. Topic-level dimension means will give each eligible reviewer equal weight. Model-level dimension summaries will give each eligible sampled topic equal weight and will state the numbers of topics and reviewers contributing. These summaries will describe the selected packets, not all topics in the model. The single-item Label Appropriateness dimension will be identified as such; no internal-consistency coefficient will be asserted for it. No grand score across the five dimensions will be used to conceal a weak dimension.

Mean ratings will be described using the following study-defined categories, not externally validated acceptance criteria. The middle category will indicate a mixed or neutral judgment, rather than proof of acceptability.

| Unrounded mean M | Study-defined description |
|---|---|
| 4.20 < M ≤ 5.00 | Excellent: strongly favorable assessed quality |
| 3.40 < M ≤ 4.20 | Good: favorable assessed quality |
| 2.60 < M ≤ 3.40 | Mixed or neutral: requires examination; not automatic acceptance |
| 1.80 < M ≤ 2.60 | Poor: unfavorable assessed quality |
| 1.00 ≤ M ≤ 1.80 | Very poor: strongly unfavorable assessed quality |

A topic-dimension mean below 3.00 will trigger review under the study-defined decision rule. It will be applied to the unrounded mean, not to a displayed rounded value. A score of exactly 3.00 will not trigger this numerical rule, but will remain neutral rather than favorable validation. The middle descriptive band therefore may contain both flagged and unflagged scores. Missing information, conflicting judgments, or a documented source contradiction may also require review regardless of the mean. A high mean will not override a specific substantiated error.

Model comparisons will use the same items and will present model-specific distributions, dimension summaries, and comments together with their denominators. A paired reviewer-level summary will be presented only for reviewers with complete dimension ratings for all four sampled topics of both systems; all other available responses will remain in the descriptive item and topic tables. Differences will be interpreted as judgments of the sampled outputs, not estimates of model accuracy. A preference question will allow either system, both equally useful, neither, or insufficient information, with a reason.

If multiple experts rate the same packets, agreement will be described using the proportion of valid rating pairs that agree exactly and the proportion differing by no more than one scale point. Counts of contributing pairs will be reported, and unavailable ratings will be excluded from the relevant pairs. With a small panel and limited topic sample, these descriptions will not be labeled as established reliability coefficients or interpreted using an unsupported agreement threshold. If only one reviewer participates, inter-rater agreement will not be calculated.

## Treatment of expert feedback

The researchers will maintain a feedback and decision log containing the packet and source references, the reviewer's coded comment, the type of concern, the proposed action, and the reason for accepting, modifying, or not adopting a suggestion. Label corrections, problematic assignments, inappropriate combinations or subdivisions, temporal overinterpretation, and source-quality concerns will be distinguished. Disagreements will be retained and discussed rather than erased by an average or a forced consensus.

Changes will be versioned. A label-only revision will be documented without being misrepresented as a new clustering result. Changes to assignments, topic boundaries, preprocessing, or year information will require recalculation of the affected automated metrics and temporal summaries. Revised materials will be returned for further review where feasible; otherwise, their unreviewed status will be stated. Ratings obtained for an earlier packet will not be transferred automatically to changed outputs. If feedback informs further tuning, the review will be identified as developmental feedback rather than independent held-out validation.

The final discussion will integrate automated results and expert observations without equating them. Expert agreement will support the interpretability and source-grounded usefulness of the reviewed topics, but will not establish objective correctness of every assignment, citywide policy priorities, legislative intent, policy effectiveness, or real-world impact. The analysis will remain descriptive and will not constitute legal advice or a legally binding interpretation.
