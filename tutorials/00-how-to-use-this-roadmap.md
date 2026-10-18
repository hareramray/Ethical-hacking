# 00. Turn the curriculum into practical skill

[Index](README.md) | [Complete source curriculum](curriculum/00-how-to-use-this-roadmap.md) | [Original roadmap](../roadmaps/00-how-to-use-this-roadmap.md)

## What you will build

This tutorial creates a learning system: a baseline, a dependency map, four planned sessions, one completed experiment, and a proficiency tracker. No prior security knowledge is required. Use a text editor and a private folder. Commands below use PowerShell and only create a new learning folder. If it already exists, choose another name before running them.

Ethical security work combines permission, technical reasoning, evidence, and repair. Finding an unusual response is the start of an investigation. You must establish the expected behavior, show the specific difference, explain its consequence, and verify a correction. That is why this course repeatedly uses the same learning loop:

> Explain normal behavior → construct an example → identify a boundary → test a controlled failure → preserve evidence → fix → retest → teach the result.

Coverage and proficiency answer different questions. Coverage asks whether a topic has been encountered. Proficiency asks whether you can perform a task independently. Reading every page does not automatically establish mastery, and needing a prerequisite does not mean the course has failed.

## 1. Establish an honest baseline

Write a paragraph describing your equipment, available weekly hours, previous programming or administration experience, and one possible role. Replace labels with demonstrations. “I can explain a file's owner and permissions” is observable; “intermediate Linux” is not. If you have no role preference, complete the shared foundation and compare a web and infrastructure capstone later.

Try this diagnostic without researching first: explain how a browser opens a local page, identify the serving process, name the account running it, locate its log, change a harmless page, and restore it. You do not have to succeed. Mark the first unknown step and identify whether it concerns networking, operating systems, files, or application behavior. Keep the original explanation for later comparison.

Create a private notebook structure:

```powershell
$learningRoot = Join-Path $PWD 'learning-notes'
New-Item -ItemType Directory -Path $learningRoot -ErrorAction Stop
'notes','lab-config','synthetic-data','evidence','reports' | ForEach-Object {
    New-Item -ItemType Directory -Path (Join-Path $learningRoot $_) -ErrorAction Stop
}
```

Expected result: five subdirectories inside `learning-notes`. The parent-creation command fails if the folder already exists; inspect existing content before choosing to reuse it. This is useful behavior because a tutorial should not silently overwrite your earlier work.

Store actual credentials in a password manager. Keep private client records, raw captures, authentication tokens, and personal files outside a public repository. A private Git repository is useful for sanitized notes and source code, but privacy settings do not turn Git into an appropriate vault for every kind of evidence. Deleted commits may still exist in clones or history.

## 2. Follow dependencies instead of opening random courses

Use the numbered tutorials as a route. Start with authorization and lab construction (01–02), then computing, networks, operating systems, programming, and security principles (03–08). Continue with assessment and vulnerability research (09–10), while learning reporting in 23. Add applications and infrastructure (11–16) and defensive visibility (20). Select depth in 17–19, 21–22, or an earlier infrastructure/application area. Finish integrated work in 24–25 and keep tools and templates in 26–27 available throughout.

The specialization overview also links to dedicated specialist subjects. Treat those as branches from the shared foundation, not as topics that disappear because you selected a different primary role. Learn their purpose and prerequisites at awareness depth; select deeper practice when your work calls for it.

For any difficult item, make this table:

| Desired skill | Prerequisite | Evidence you already have |
| --- | --- | --- |
| Verify API ownership | HTTP request/response | Annotated local request |
| Verify API ownership | Identity versus authorization | Two-user access matrix |
| Verify API ownership | Data model and routing | Diagram connecting route to record |
| Explain a denied file read | Process identity and permissions | User/mode prediction table |

An empty evidence cell becomes a short prerequisite exercise. Keep one main learning thread and a small backlog. Switching topics whenever an exercise becomes uncomfortable hides the gap rather than closing it. Useful pairings include Linux with Bash, networking with captures, programming with application security, and every practical lab with logs and a short report.

## 3. Assign a meaningful depth

Core topics support general assessment and should reach independent practice. A track is a chosen specialization needing sustained depth. Awareness means you can explain the mechanism, identify its prerequisites, and recognize when specialist help is needed. It does not require building an entire operating system before learning a web authorization check.

| Level | Observable evidence | Example |
| --- | --- | --- |
| 0: new | No explanation or exercise yet | You have only seen “ACL” in a list |
| 1: explain | Explain behavior and boundary without notes | Describe why identity affects access |
| 2: guided | Complete and interpret a lab with hints | Follow a permission walkthrough |
| 3: independent | Diagnose an unfamiliar variation and verify repair | Find the wrong parent-directory permission |
| 4: extend | Explain edge cases and create useful regression checks | Cover group changes, inheritance, and alternate routes |

Target level 3 for practical core skills and initially level 1 for awareness. Record the assistance you needed; this makes the tracker honest and tells you what to repeat. A guided success is progress, but silently renaming it independent removes useful information.

## 4. Work one complete lesson

Use file integrity as a small first example. The protected asset is a synthetic configuration file. The expected behavior is that restoring the original bytes restores the original digest. A digest is a fingerprint of bytes, not proof of who supplied those bytes.

Run this in the new learning folder:

```powershell
$fixture = Join-Path $learningRoot 'synthetic-data\settings.txt'
[IO.File]::WriteAllText($fixture, "mode=demo`n", [Text.UTF8Encoding]::new($false))
$originalBytes = [IO.File]::ReadAllBytes($fixture)
$before = (Get-FileHash -LiteralPath $fixture -Algorithm SHA256).Hash
[IO.File]::WriteAllText($fixture, "mode=changed`n", [Text.UTF8Encoding]::new($false))
$changed = (Get-FileHash -LiteralPath $fixture -Algorithm SHA256).Hash
[IO.File]::WriteAllBytes($fixture, $originalBytes)
$restored = (Get-FileHash -LiteralPath $fixture -Algorithm SHA256).Hash
[pscustomobject]@{ ChangeDetected=($before -ne $changed); RestoreMatches=($before -eq $restored) }
```

Predict the two booleans before executing. Both should be `True`. Save the prediction, output, environment, and explanation. This exercise changes one file you just created, restores it, and tests that restoration; it does not assess real host configuration.

If restoration fails, compare the actual bytes, encoding, newline convention, and path. An editor may save a byte-order mark or convert LF to CRLF. Those are hypotheses; inspect them rather than repeatedly copying the same command. If the file is missing, confirm `$fixture` and the current directory before changing anything.

Now vary the experiment: change only the final newline. Explain why text that looks nearly identical can produce a different digest. Repeat tomorrow without reopening the command block. That delayed reconstruction is stronger evidence of retention than immediately repeating the same pasted text.

## 5. Record observations separately from interpretations

Use this completed note as a model:

```text
Objective: detect and reverse a synthetic configuration change.
Environment: Windows guest; PowerShell version recorded separately.
Prediction: changed bytes change SHA-256; original bytes restore it.
Observation: ChangeDetected=True; RestoreMatches=True.
Interpretation: this experiment preserved the original file bytes.
Limitation: it did not test permissions, backup storage failure, or provenance.
Correction: none needed; next exercise adds a newline-only change.
Evidence: transcript plus before/after digests, without unrelated files.
```

A screenshot can supplement evidence, but does not replace commands, identities, inputs, and interpretations. Include date with time zone, tool versions, target identity, uncertainty, remediation, and retest in larger notes. When another learner can reproduce your result from the record, your communication is improving alongside your technical skill.

## 6. Use help and troubleshoot deliberately

When stuck, classify the problem before seeking a solution. A missing prerequisite needs explanation; an environment fault needs repair; an incorrect hypothesis needs a discriminating test; a misunderstood tool needs documentation. Capture the exact error and smallest failing example. Reinstalling everything can erase the evidence and leave the mistaken mental model unchanged.

Use progressively specific hints: installed help, architecture reference, conceptual hint, then worked solution. Record the hint that changed your understanding. Repeat later from a clean baseline and vary one condition. If the new version fails, revise the explanation instead of treating the original success as a universal rule.

For documentation, locate version applicability, prerequisites, privileges, input syntax, defaults, side effects, limits, and rollback. A command copied from another operating system or release may be syntactically valid yet operate on a different object. Sources and assumptions belong in notes so you can update them when tools change.

## 7. Plan four sessions and review evidence

| Session | Concrete task | Saved output |
| --- | --- | --- |
| 1 | Write scope for your own lab and classify five actions | One-page rules of engagement |
| 2 | Construct isolated environment and restore one change | Inventory, diagram, restore evidence |
| 3 | Explain bytes, process identity, and local service flow | Annotated observations |
| 4 | Repeat one lab without instructions and repair a new fault | Short finding and fix/retest record |

End each session with five sentences: what you can explain, what you demonstrated, what contradicted your prediction, what remains uncertain, and the smallest next experiment. Add topic, depth, proficiency, evidence link, last-practiced date, mistake, and next action to your tracker.

For an integrated review, remove the announced vulnerability type, set a small time budget, and require a report. This checks whether you can choose a method instead of recognizing a familiar lesson title. Judge incomplete coverage honestly: “not tested” is more useful than an unsupported “secure.”

## Practice and answer guidance

1. You watched a complete networking course but cannot explain a local connection. Which level fits? **Guidance:** reading alone does not establish level 1; demonstrate an explanation, then attempt a small lab.
2. A file hash matches after restoration. Did you prove the whole backup works? **Guidance:** only those bytes matched; accounts, permissions, dependencies, recovery keys, and external state remain separate checks.
3. You used a walkthrough successfully. What next? **Guidance:** mark guided, delay, reconstruct without help, and change an assumption.
4. API work stalls at cookies and sessions. What next? **Guidance:** put HTTP/session mechanics into the prerequisite backlog and produce a traced local request before adding assessment tools.

You can move forward when four sessions have concrete outputs, your tracker distinguishes awareness from independence, one note contains prediction/observation/correction/explanation, sources and unknowns are recorded, and you have completed a delayed repeat. Keep updating this system as your scope grows.
