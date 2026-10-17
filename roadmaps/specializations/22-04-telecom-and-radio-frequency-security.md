# 22.4 Telecom and radio-frequency security

[All topic roadmaps](../README.md) | [Specialization overview](../22-advanced-specialization-map.md)

<!-- TOPIC-TOC:START -->

## Contents

- [Detailed learning sequence](#detailed-learning-sequence)
  - [Stage 1: Build the signal and protocol foundations](#stage-1-build-the-signal-and-protocol-foundations)
  - [Stage 2: Map cellular identities and architecture](#stage-2-map-cellular-identities-and-architecture)
  - [Stage 3: Learn VoIP as a distributed application](#stage-3-learn-voip-as-a-distributed-application)
  - [Stage 4: Evaluate privacy and operational constraints](#stage-4-evaluate-privacy-and-operational-constraints)
  - [Stage 5: Develop an evidence-based analysis method](#stage-5-develop-an-evidence-based-analysis-method)
- [Worked lab: simulated signaling and media](#worked-lab-simulated-signaling-and-media)
- [Debugging blind spots and pass criteria](#debugging-blind-spots-and-pass-criteria)

<!-- TOPIC-TOC:END -->



**Prerequisites:** Networking, authentication, signal basics, and the applicable authorization rules for your location.

- [ ] Learn cellular architecture, SIM/eSIM identity, roaming, signaling trust, VoIP/SIP/RTP, software-defined radio concepts, modulation, and spectrum boundaries.
- [ ] Study protocol threat models, privacy implications, lawful test arrangements, and emergency-service dependencies.

**Project:** Analyze supplied recordings or a fully simulated protocol exchange; any radio transmission requires the appropriate approved environment. **Pass:** Explain trust boundaries and monitoring controls without interacting with public carrier infrastructure or third-party communications.

## Detailed learning sequence

### Stage 1: Build the signal and protocol foundations

Study frequency, wavelength, bandwidth, amplitude, phase, noise, power ratios, decibels, sampling, aliasing, filtering, and modulation. Use generated numerical signals before connecting hardware. Learn how a signal becomes samples, symbols, frames, protocol messages, and application behavior. Keep RF performance questions separate from identity and authorization questions.

- [ ] Explain sampling rate, center frequency, complex I/Q samples, and the information a recording preserves.
- [ ] Describe how clipping, frequency offset, gain, filtering, and synchronization affect decoding.
- [ ] Distinguish a spectrum plot from a decoded message and a decoded message from authenticated meaning.
- [ ] Generate a simple simulated signal, add known noise, and compare the expected and observed result.
- [ ] Document whether a learning exercise uses generated data, a supplied authorized recording, or an approved shielded laboratory.
- [ ] Treat reception, recording, decoding, retention, and transmission as separate activities requiring an appropriate lawful basis.

### Stage 2: Map cellular identities and architecture

Study the user equipment, radio access network, core network, subscriber identity, authentication service, and packet data path. Learn SIM and eSIM provisioning concepts, permanent versus temporary identifiers, subscription state, roaming relationships, and identity privacy goals. Distinguish a subscriber identity from a device identity and from an application account.

Follow registration, authentication, session establishment, mobility, and release through a specification or instructor-provided trace. Identify which entity trusts which other entity and how key material is derived and scoped at a conceptual level. Compare architectural generations without assuming a modern marketing label proves every deployed interface has equivalent protections.

Study roaming and interconnection as trust relationships between organizations. Identify home-network and visited-network responsibilities, signaling versus user traffic, and service dependencies. Use diagrams and supplied traces for this stage; public carrier systems and real subscriber records are outside a self-directed training lab.

### Stage 3: Learn VoIP as a distributed application

Build understanding of SIP user agents, registrars, proxies, dialogs, transactions, session descriptions, and RTP media. Trace call setup, ringing, answering, media exchange, and teardown. Separate signaling authentication, signaling transport protection, media protection, and authorization for calling a destination.

Study address translation, session border controllers, codecs, packetization, jitter buffers, loss, and clock behavior. Examine why signaling can succeed while media fails and why media can flow through a different path. Review account lifecycle, provisioning, administrative roles, logging, and recording retention using fictional users.

Treat caller display information as a claim whose trust depends on the environment. Study verification and policy controls conceptually. Avoid learning exercises involving unsolicited calls, impersonating real callers, emergency numbers, or paid routing.

### Stage 4: Evaluate privacy and operational constraints

Create a data inventory for identifiers, location-related records, call metadata, messages, recordings, and diagnostic traces. Record who needs each data type, how access is controlled, and how long the training evidence is retained. Pseudonymized identifiers may still permit linking events; replacing a name alone does not make a dataset anonymous.

Study emergency-service dependencies, service availability, network maintenance, roaming coordination, and vendor interoperability. Explain why a radio or signaling experiment can affect systems beyond the intended test device. Before any physical RF work, obtain the exact applicable authorization and engineering controls from qualified local specialists; do not infer permission from low power, a short range, or ownership of one endpoint.

### Stage 5: Develop an evidence-based analysis method

For each trace, record origin, collection authorization, timestamp reference, sample format, channel assumptions, processing steps, and known omissions. Separate decoded fields from inferred meaning. Retain the original recording or packet trace unchanged and perform analysis on a working copy. Compare results against known generated inputs wherever possible.

Build a worksheet linking each protocol state to expected messages, identities, protection properties, and error handling. When decoding fails, investigate signal processing and framing before proposing a security defect. When a message is unexpected, consider retransmission, reordering, duplicate captures, clock skew, and incomplete collection.

## Worked lab: simulated signaling and media

**Setup:** Run a local software-only VoIP training environment with two fictional clients and a local signaling service. Disable external calling and public network registration. Use generated audio tones or silence. Alternatively, use an instructor-provided packet trace with documented synthetic identities. Keep the environment on a private virtual network.

**Actions:** Place a permitted call between the two local clients, observe setup and teardown, and correlate signaling with media flows. Test an incorrect training credential and a disabled fictional account. Introduce controlled packet delay in the simulator or analyze a supplied impaired-media fixture. Examine the difference between failed authentication, failed routing, and degraded media.

**Expected behavior:** Only permitted local identities establish the allowed session; denied cases are logged; media paths match the declared session; delay changes media quality without being misreported as an authentication failure.

**Evidence:** Produce a message sequence diagram, identity and trust map, sanitized trace excerpts, timing measurements, and explanations of observed failures. Record whether transport and media protection were enabled and what was visible at the chosen collection point.

**Correction:** Fix the local account policy, route configuration, time reference, or protection setting. Re-run both the authorized call and the denied case. Avoid claiming that the corrected toy environment represents an entire carrier network.

## Debugging blind spots and pass criteria

An undecodable recording may lack sufficient bandwidth or metadata. A radio identifier can change while the same logical session continues. A media flow can bypass the signaling server. Encrypted traffic limits content inspection but still exposes selected metadata. A protocol dissector can mislabel traffic when ports or framing assumptions are wrong.

- [ ] Explain a generated signal from samples to protocol meaning.
- [ ] Draw cellular and VoIP trust boundaries without conflating subscriber, device, and application identities.
- [ ] Analyze one supplied or local trace with explicit provenance and uncertainty.
- [ ] Distinguish authentication failures, protocol-state errors, network reachability problems, and media-quality problems.
- [ ] Produce a privacy-aware evidence package containing no real subscriber information.
- [ ] State the authorization and containment questions that must be answered before any transmission-based research.

**Primary resources:** Read [RFC 3261 for SIP](https://www.rfc-editor.org/rfc/rfc3261) and [RFC 3550 for RTP](https://www.rfc-editor.org/rfc/rfc3550) as foundational protocol references, noting that later extensions may apply to a particular deployment. Use the [GNU Radio manual](https://www.gnuradio.org/doc/doxygen/) for software signal-processing concepts and the appropriate official telecom specification for the architecture being studied.

