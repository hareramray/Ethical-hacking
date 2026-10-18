# Tutorial: Telecom and radio-frequency security

[Index](../README.md) | [Full source curriculum](../curriculum/specializations/22-04-telecom-and-radio-frequency-security.md) | [Original roadmap](../../roadmaps/specializations/22-04-telecom-and-radio-frequency-security.md)

## Learn the layers with generated evidence

This tutorial starts with numerical samples and ends with an invented signaling trace. It uses no radio transmission, live carrier connection, subscriber information, unsolicited call, emergency number, or paid route. The objective is to distinguish signal quality, protocol correctness, authentication, authorization, and privacy. They are related questions with different evidence requirements.

RF research is not simply network testing with an antenna. Reception, recording, decoding, retention, and transmission are separate activities with separate authorization questions. Ownership of one endpoint, low power, or short range does not establish permission to affect other systems. Before any later physical RF exercise, obtain location-specific authorization and engineering controls from qualified specialists. The generated-data exercises here avoid those dependencies.

## 1. Turn a waveform into samples

Frequency measures cycles per second. Wavelength relates propagation speed to frequency. Amplitude describes signal magnitude; phase describes position within a cycle. Bandwidth describes a frequency span, not the same thing as center frequency. Noise and interference change what a receiver observes. Power ratios use `10 log10(P2/P1)` decibels; amplitude ratios use `20 log10(A2/A1)` only under the appropriate equal-impedance relationship.

Sampling converts a continuous-time model into values at discrete times. In the simple real-signal case, frequencies above half the sampling rate can appear as lower frequencies unless appropriately filtered. The following standard-library Python example produces two signals with identical samples:

```python
import math

rate = 8000
def samples(frequency, count=16):
    return [math.cos(2 * math.pi * frequency * n / rate)
            for n in range(count)]

a = samples(1000)
b = samples(7000)
print(all(abs(x - y) < 1e-10 for x, y in zip(a, b)))
```

Expected output is `True`. At this sample rate the chosen cosine examples alias. You cannot infer the original analog frequency from those samples alone. Change the rate to 20000 and compare again; the sequences now differ. This explains why recording metadata and front-end filtering matter.

Complex I/Q samples retain two components used to represent amplitude and phase relative to a reference. A recording therefore needs format, sample rate, center frequency when applicable, scaling, time reference, and processing history. A spectrum peak is evidence of energy, not a decoded identity or authenticated message. Modulation maps symbols onto changes in amplitude, frequency, phase, or combinations; demodulation estimates symbols from samples, then framing and protocol parsing interpret them.

Software-defined radio moves selected radio-processing functions into software operating on samples. This does not require transmitting: a flow graph can connect a generated source, filter, demodulator, and display entirely in memory. GNU Radio provides software signal-processing building blocks for this kind of study. [About GNU Radio](https://www.gnuradio.org/about/)

Add deterministic generated noise to the 1000 Hz samples and record the noise formula or seed. Clip values to a small range and compare how the waveform changes. Frequency offset, incorrect gain, filter choices, and missing synchronization can prevent decoding even when there is no security defect. Keep the original sample list unchanged and analyze copies.

## 2. Map cellular roles without using subscriber data

Draw user equipment, the radio access network, the core network, the subscriber authentication function, and the packet-data path. The exact function names and interfaces depend on the architecture generation and release. A SIM or eSIM participates in subscription identity and authentication; it is not the same thing as the handset's equipment identity or a messaging application's account.

Use three fictional labels: subscription `SUB-A`, device `DEV-7`, and application account `APP-MIRA`. Write a scenario in which the same subscription moves to a replacement device. The application might need a separate sign-in. Then write a scenario in which one device changes subscriptions. These exercises prevent conflating identifiers that have different lifecycles and privacy properties.

Study registration, authentication, session establishment, mobility, and release as state transitions. For each transition record the initiating entity, expected response, trust decision, and failure state. Permanent identifiers and temporary identifiers serve different purposes; temporary identifiers can reduce exposure while still allowing session continuity. Key material is derived and scoped within the relevant architecture, so “encryption enabled” is not enough to describe which parties and interfaces are protected.

Roaming introduces relationships between a home network and a visited network. Signaling that establishes service differs from user traffic carrying application data. List which organization authenticates a subscription, provides local access, routes traffic, and handles operational coordination in your selected official specification. Do not assume every interface has identical protections because a deployment has a modern marketing label.

For continued study, select one release in the [official 3GPP specification portal](https://www.3gpp.org/specifications-technologies/specifications-by-series) and record it in the worksheet. This chapter deliberately avoids deployment-specific claims that would require an actual carrier architecture and authorized evidence.

## 3. Understand a VoIP call as a distributed application

A SIP user agent initiates or answers signaling. A registrar associates an identity with a contact location. A proxy routes requests. A transaction concerns an individual request and responses; a dialog represents a longer peer relationship. Session descriptions communicate proposed media parameters. SIP's foundational specification describes establishment, modification, and termination of sessions; later updates and deployment profiles must also be considered. [RFC 3261](https://www.rfc-editor.org/rfc/rfc3261)

RTP carries timed media information using fields such as sequence numbers and timestamps. Its base protocol supplies media transport mechanisms, not a complete identity and confidentiality policy. Media protection, signaling transport protection, signaling authentication, and permission to call a destination are distinct controls. [RFC 3550](https://www.rfc-editor.org/rfc/rfc3550)

Use this simplified successful trace as data, not as packets to send:

| Time in ms | Source → destination | Event | Meaning |
|---|---|---|---|
| 0 | Alice → local service | INVITE Bob | Request the permitted local session |
| 20 | service → Alice | 100 Trying | Request processing has begun |
| 40 | Bob → Alice via service | 180 Ringing | Fictional recipient is being alerted |
| 150 | Bob → Alice | 200 OK with media description | Session accepted |
| 170 | Alice → Bob | ACK | Acknowledge the successful invitation |
| 190–990 | Alice ↔ Bob | Generated media records | Separate media flow |
| 1000 | Alice → Bob | BYE | End session |
| 1020 | Bob → Alice | 200 OK | Teardown acknowledged |

Annotate the call identifier, transaction identifiers, fictional identities, and media addresses in a fuller fixture. Authentication can involve a challenge followed by an authenticated retry; the initial challenge is not necessarily a failed attack. A disabled account should remain denied even if its stored training credential is correct.

Network address translation and session border controllers can affect signaling and media differently. Codecs define media encoding; packetization determines how much media is carried per packet. Jitter buffers trade delay against tolerance for irregular arrival. A call can ring correctly while audio fails because the media path, codec agreement, address advertisement, or clock behavior is wrong.

Caller display text is a claim whose trust depends on the environment and verification policy. Do not treat the displayed name as proof of authorization. The lesson uses only Alice and Bob in synthetic records.

## 4. Measure delay without mislabeling it

Create a media fixture with sequence numbers 1–5, sender times `0,20,40,60,80` milliseconds, and arrival times `30,50,90,80,110`. Sequence 4 arrives before sequence 3. Compute each transit difference: `30,30,50,20,30`. These differences are a simple teaching measure, not an implementation of every RTP reporting formula.

Now remove sequence 3 entirely. Record loss separately from reordering and delay variation. Authentication evidence has not changed. A report saying “account login failed because audio stuttered” confuses layers. Likewise, duplicate capture records may look like retransmissions when the same packet was collected twice; investigate collection topology before inferring protocol behavior.

Build a failure worksheet:

| Fixture | Evidence | Appropriate first hypothesis |
|---|---|---|
| Wrong fictional credential | Authentication denied, no session | Identity validation |
| Disabled account | Policy denied despite valid credential | Account lifecycle |
| Unknown local destination | Authorized user, route absent | Routing or provisioning |
| Successful signaling, no media records | Session accepted, media missing | Media path or incomplete capture |
| Media arrives irregularly | Valid session, timing variation | Network and playout behavior |

Repair one fixture at a time. Correct the account configuration, local route, media description, or time reference as indicated. Rerun the permitted case and the denied case. A correction that makes every account work has broken policy even if the demonstration call succeeds.

## 5. Create a privacy-aware evidence package

Inventory subscription and device identifiers, location-related records, call metadata, messages, media recordings, diagnostic logs, and administrative records. For each, state purpose, authorized readers, retention, and deletion. Generated tones or silence are enough for the media exercise. No real phone numbers or subscriber records are needed.

Pseudonymization is not automatic anonymity. Repeated event times and stable identifiers can link records even after names are removed. Store only fields needed to answer the learning question. Keep originals intact, hash them, analyze working copies, and record the transformation script or manual steps. State the timestamp reference and clock uncertainty.

Emergency-service dependencies and carrier availability make uncontrolled experiments especially consequential. Maintenance windows, vendor interoperability, roaming coordination, and shared infrastructure are part of a real test arrangement. A shielded laboratory is an engineering arrangement to be verified, not a phrase that substitutes for authorization. No transmission procedure is required for this curriculum exercise.

Encrypted traffic changes what a collection point can observe. You may still see selected timing, sizes, and endpoint metadata while lacking content. A dissector's label is also an interpretation: unusual ports, missing headers, or incomplete captures can cause misidentification. Separate decoded fields, inferred meaning, and unknowns in the final report.

## Questions with answer guidance

1. **Why can two frequencies produce identical recorded samples?** Aliasing can make them indistinguishable at the selected sampling rate; metadata and filtering determine what conclusions remain possible.
2. **Does successful SIP signaling prove media protection?** No. Signaling and media use distinct paths and controls that require separate evidence.
3. **Is a changing radio identifier proof of a new subscriber?** No. Temporary identity changes and mobility may preserve the logical session.
4. **What would justify a security finding from a malformed trace?** Reproducible evidence, verified provenance, the expected protocol state, and elimination of collection, timing, and parsing explanations.

Deliver the sample-generation code, aliasing observation, cellular identity map, message sequence table, media timing worksheet, corrected local fixtures, and a retention statement. State what was simulated, what was inferred, and which carrier, RF, and privacy behaviors were not assessed. This demonstrates analytical competence without claiming that a toy call represents a public telecommunications network.
