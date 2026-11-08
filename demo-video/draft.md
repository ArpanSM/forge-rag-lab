# 45-second client proof film — RAG Lab

**Status:** revised draft for review · **Target:** Upwork portfolio card and proposal attachment
**Primary:** 45 s · 1920×1080 · 30 fps · H.264/AAC · burned-in captions
**Teaser:** 22 s proposal autoplay · 1:1 mobile crop
**Email cut:** 60 s, only when you can send a link or a follow-up
**Audience:** SaaS documentation and support teams, compliance and fintech knowledge bases,
internal-helpdesk teams, and agencies maintaining a RAG assistant.
**One-line promise:** A RAG assistant that shows the exact page and block behind every claim —
and refuses to answer when the evidence is missing.
**What the client should think at the end:** “This is the person who can tell me why my assistant
is confidently wrong, fix it, and prove the fix.”

## Why this version

The first draft was still a product tour with a client-friendly voice. It showed two failures and
four metrics, and it saved “why me” for the last ten seconds. That is too much for a proposal
attachment.

This version follows one rule: **one failure, one fix, one metric, one why-me, one CTA.** The
unanswerable question is the failure. Abstention plus citation is the fix. Correct abstention is
the metric. The “why me” arrives at 0:25, not 0:43. The stale-version case moves to the 60-second
email cut.

## What the listings ask for

- LangGraph/RAG fix listing: stale policy documents outrank current ones, citations point at the
  wrong page, and a retried write duplicates a database row.
- Production RAG listing: hybrid search, tenant isolation, citations, prompt-injection safeguards
  and evaluation.
- RAG audit listings: reproduce the bad answers, separate retrieval from generation, and rank the
  fixes.

Source: the workspace `docs/upwork_job_matches*.md` and the RAG entries in
`forge-roadmap/research/`.

## Positioning

**Problem the client recognizes.** A RAG assistant sounds fluent and cites nothing useful. It
answers from an old policy, points at the wrong page, or invents a command the docs retired. Nobody
knows it is wrong until a customer does.

**The fear underneath it.** The client already shipped a demo that looked good. They do not need
another chatbot; they need to know which failures are retrieval, which are generation, and which
are evaluation gaps.

**Why you.** You make the failure visible before you fix it: a baseline/fixed toggle, claim-level
citations, explicit abstention and an 80-question evaluation with a failure gallery. The client can
see the method, not just the output.

**The one proof number.** Correct abstention: **0.800 → 1.000** on 80 questions. That is the
cleanest proof that the fixed pipeline stops inventing answers. Keep citation coverage off the
45-second cut; it belongs in the 60-second email version and the README.

**Proof-of-concept framing.** Say it early and keep it on the end card: “This proof of concept uses
a synthetic Helios corpus. The same method applies to your documentation.” That is the bridge from
your demo to their corpus.

**Production signals, not a production claim.** Show the eval harness, baseline/fixed comparison,
tenant isolation and the failure gallery — the habits a client wants in a production build. Do not
call the hosted fixture a production service. Do not claim “no hallucinations.” Say “evidence-first
and measured.”

## The 45-second script

| Time | Picture | Voiceover | On-screen text |
|---|---|---|---|
| 0:00–0:05 | A real answer card with a red “source not found” chip. Hold on the unsupported claim. | Has your assistant ever answered from an old policy, or cited a page that doesn’t exist? | **Has this happened to you?** |
| 0:05–0:10 | Pull back to the chat page. Small label: “synthetic Helios corpus.” | This proof of concept uses synthetic docs; the method applies to yours. | **Proof of concept · synthetic corpus** |
| 0:10–0:18 | Split screen. Baseline invents a retired install command. Fixed pipeline shows the abstention state. | Ask something the docs don’t contain. The baseline invents a command. The fixed pipeline says: I can’t answer that. | **Baseline invents · fixed abstains** |
| 0:18–0:25 | Ask an answerable question. The answer lands with claim-level citations; open the drawer and highlight the block. | Every claim cites a version, a page, and a block. Open it and the exact source is highlighted. | **Version · page · block** |
| 0:25–0:33 | The three-step engagement strip over the health report: Reproduce → Measure → Fix + regression gate. | I can reproduce this on your corpus, separate retrieval from generation, and give you a ranked fix list with a before/after evaluation. | **Reproduce → Measure → Fix + gate** |
| 0:33–0:39 | One metric, large: correct abstention 0.800 → 1.000. Failure gallery behind it. | Correct abstention goes from 0.800 to 1.000. | **0.800 → 1.000 abstention** |
| 0:39–0:45 | End card: title, GitHub URL, proof-of-concept line. | Send me three bad answers. I’ll tell you which are retrieval, generation, or evaluation failures. | **Send 3 bad answers** · `github.com/ArpanSM/forge-rag-lab` · **Proof of concept · method applies to your docs** |

**Word count:** about 109 (≈145 wpm). Record at 0.96–1.00, with a clear pause after the opening
question and before the metric. Do not rush the citation drawer.

## What to capture

- **Opening:** a real answer with a citation to a page that does not exist, or an unsupported claim.
  Do not use a mock.
- **Split screen:** the baseline’s invented command next to the fixed abstention state. Label both.
- **Cited answer:** one answer with claim-level citation chips.
- **Citation drawer:** exact document title, version, page, block and highlighted quote.
- **Metric:** the health report cropped to the abstention row, plus a one-second failure-gallery
  flash.
- **End card:** GitHub URL and “Proof of concept · method applies to your docs.”

Use the hosted fixture app for the visuals. It is the real UI, but label it “fixture-mode demo.”
If you show the live API, record it separately and label it “local API,” not a hosted service.

## The why-me beat

The eight seconds at 0:25 are the turn of the film. Do not fill them with a stack list. Show a
three-step engagement:

> **1 Reproduce the failures · 2 Measure retrieval vs generation · 3 Fix + regression gate**

That tells the client what hiring you looks like. The tools and architecture belong in the README.

## Production notes

- **Voice:** your own voice first. If you use TTS, use the existing LFM3 male voice; the current
  read is clear but a little flat.
- **Music:** a quiet pulse under the voice. No drop on the metric; let the number land.
- **Captions:** burned in, high contrast, one or two lines. The viewer may be muted.
- **Split screen:** label the baseline clearly. Never let a viewer think the broken answer is the
  product.
- **Pacing:** one idea per 5–8 seconds. Hold the metric for at least 3 seconds.
- **Screen:** 1920×1080, clean browser profile, no bookmarks or terminal.
- **Audio:** −14 LUFS integrated, −1.5 dBTP; AAC 192 kbps.
- **Export:** H.264 High, 30 fps, `+faststart`, under 100 MB.
- **End card:** at least 4 seconds; the URL, CTA and proof-of-concept line readable on a phone.

## 22-second teaser

| Time | Beat |
|---|---|
| 0:00–0:04 | “Has your assistant ever answered from an old policy, or cited a page that doesn’t exist?” |
| 0:04–0:09 | Baseline invents; fixed abstains. |
| 0:09–0:14 | “I can reproduce this on your corpus and rank the fixes.” |
| 0:14–0:18 | “Correct abstention 0.800 to 1.000.” |
| 0:18–0:22 | “Send me three bad answers.” End card. |

For the 1:1 crop, keep the question, the split screen and the citation drawer in frame. Crop the
health table to the one headline row; do not shrink it to illegibility.

## 60-second email cut

Keep the 45-second film and add two beats:

- **After the citation drawer —** the stale-version proof: baseline answers from v2; fixed retrieves
  v3 and labels the old policy superseded.
- **After the one proof number —** citation coverage 0.797 → 1.000 and the eval harness. Keep the
  same “why me” and CTA.

Do not use the 60-second cut as the Upwork attachment. It is for email, a follow-up link, or a
proposal where the client has already asked for detail.

## What not to do

- Do not show two failures. Pick the unanswerable question; the stale version is the email cut.
- Do not show four metrics. Correct abstention is the one.
- Do not show the baseline’s wrong answer without a “baseline” label.
- Do not open with “RAG” or a vector-database logo. Open with the client’s bad answer.
- Do not claim “no hallucinations” or production readiness.
- Do not show an architecture diagram for more than two seconds.
- Do not end with “read the checklist.” End with “send me three bad answers.”

## Acceptance test

Show the 45-second cut to someone who owns a documentation or support assistant. Ask:

1. What failure does this fix?
2. How do you know the answer is supported?
3. What would you send this person first?

If they cannot answer all three, the film is still a product tour.

## Portfolio card copy

**Title:** RAG reliability lab — versioned citations, abstention and an 80-question evaluation

**Short description:** A proof of concept over versioned product documentation that cites the exact
version, page and block, refuses unanswerable questions, and exposes the failures most demos hide.
Includes a baseline/fixed toggle, an 80-question evaluation, a failure gallery and a RAG audit
checklist. Synthetic corpus; development numbers, not a production benchmark.

**Proposal line:** Send me three bad answers from your assistant. I’ll tell you which are retrieval,
generation, or evaluation failures, and what I would fix first.
