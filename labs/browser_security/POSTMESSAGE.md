# postMessage sender authorization and safe rendering

Run `python labs/browser_security/run_lab.py` from the repository root, open the printed main URL (normally `http://127.0.0.1:8766/`), and select **postMessage security**. Both launcher processes must be running. Setup instructions are in [the lab README](README.md).

This lesson sends real `window.postMessage` calls between local browser frames. It does not fabricate `MessageEvent.origin` or `MessageEvent.source`. Every input is a predefined fixture; there is no arbitrary HTML, JavaScript, origin, or message editor.

## The browser arrangement

The dashboard runs on the main origin. It embeds two receiver frames on the peer origin, normally `http://127.0.0.1:8767`. Each receiver creates a trusted sender iframe on the main origin. The wrong-origin fixture places that expected sender window on the peer origin instead. The wrong-source fixture sends from a second main-origin iframe.

The sender first announces readiness. The receiver asks the selected child to send its fixed message, using an exact `targetOrigin`. The receiver then compares the **browser-supplied** origin and source against its configured main origin and authorized iframe's `contentWindow`.

Origin is the scheme, host, and port. Another window can have the same origin without being the specific window this receiver authorized. A frame can also keep its window reference while its document has a different origin. Checking one property does not substitute for checking the other. MDN documents the meaning of [message origin, source, and exact targetOrigin](https://developer.mozilla.org/en-US/docs/Web/API/Window/postMessage).

## Walkthrough

1. Start with **Trusted sender and plain text**. Both receivers accept the greeting. The fixed result must show the main origin, matching window, valid schema, and no executed HTML marker.
2. Select **Expected window, wrong origin**. The observed origin changes to the peer origin while the window still matches. The vulnerable receiver renders `WRONG_ORIGIN_MARKER`; the fixed receiver rejects it.
3. Select **Trusted origin, wrong window**. The actual sender origin is correct, but the source is a second frame. The fixed receiver rejects it. Origin validation alone would have allowed this case.
4. Select **Trusted sender, invalid message shape**. Origin and source match, but `text` is an array and the message contains an extra key. The vulnerable receiver coerces it to text; the fixed receiver rejects the schema.
5. Select **Trusted sender, harmless HTML marker**. Both authorize the message. The vulnerable receiver assigns its text to `innerHTML`; a deliberately invalid data image fires an error handler that only sets `window.__messageMarker = true`. The fixed receiver uses `textContent` and displays the markup literally, with no image element or executed marker.

Expand **Inspect the isolated receiver** to see the actual output document. The dashboard separately displays the receiver's text content as escaped text; it never renders reported HTML.

| Fixture | Actual origin | Authorized window | Valid schema | Vulnerable | Fixed |
|---|---|---|---|---|---|
| Plain text | Main | Yes | Yes | Accepts greeting | Accepts greeting |
| Wrong origin | Peer | Yes | Yes | Accepts marker | Rejects origin |
| Wrong source | Main | No | Yes | Accepts marker | Rejects window |
| Wrong shape | Main | Yes | No | Coerces and renders | Rejects schema |
| Markup | Main | Yes | Yes | Runs harmless local marker | Displays literal text |

## The repair

The vulnerable receiver filters the lesson channel and run identifier, then uses `innerHTML`. A channel string and run identifier correlate the demonstration; they do not authenticate the sender.

The fixed receiver requires all of the following before accepting a message:

- `event.origin` exactly equals the configured main origin.
- `event.source` equals the authorized iframe's `contentWindow`.
- The object has exactly `channel`, `runId`, `type`, and `text`; the first three match the expected values and `text` is a string no longer than 512 characters.
- Accepted text goes to `textContent`, so markup is not interpreted.

All message sends use an explicit destination origin. Sending restrictions and receiving checks are separate controls. Validate message content even after authenticating its sender; OWASP recommends [origin validation, data validation, and safe DOM assignment for Web Messaging](https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html#web-messaging).

## Containment and limits

Receiver pages use a CSP sandbox with scripts and origin identity enabled. Preserving origin identity is necessary to demonstrate real origin checks; this is not an opaque-origin sandbox lesson. The receiver is on a different origin from the dashboard, and its sandbox is also supplied as an HTTP response policy. It cannot remove that policy by editing an iframe attribute.

Its resource policy denies connections, forms, objects, and arbitrary frames. Only the two configured local origins may host sender frames. Data images and inline handlers are deliberately permitted in the receiver to demonstrate the single fixed marker; these settings are not a recommended application CSP. Sender documents execute only fixed external scripts, do not render message data, and do not read cookies or storage. No external service or real account is involved.

The dashboard accepts result telemetry only from the configured peer origin, the current receiver window, the current run, fixture, and mode, with bounded result fields. Old runs and messages from the wrong window cannot replace displayed evidence. Changing tabs removes the frames, listener, pending timer, and request.

These are local HTTP origins separated by port. They remain the same site, and cookies are not isolated by port. The companion server therefore exposes only a narrow set of fixed lesson document routes; it blocks the application's data APIs. This lesson does not demonstrate navigation races, opaque origins, transferred MessagePorts, popup lifecycles, hostile arbitrary scripts, or a complete production messaging protocol. Cross-origin framing and sandbox controls contain the fixture; origin/source/schema checks and safe rendering are the demonstrated repair.

## Files and verification

- [Backend documents and fixed scripts](backend/securitylab/message_lab.py)
- [Vue comparison](frontend/src/MessageLab.vue)
- [HTTP tests](backend/securitylab/test_message_lab.py)
- [Real-browser tests](frontend/tests/message.spec.js)

From `labs/browser_security`, run `.venv/Scripts/python.exe backend/manage.py test securitylab.test_message_lab`. For Chrome browser verification, stop the interactive lab, set `LAB_BROWSER_CHANNEL=chrome`, and run `npm run test:e2e -- tests/message.spec.js` from `frontend`. The test configuration starts its own local servers. The browser tests cover all five fixtures, actual source/origin evidence, safe rendering, peer API restrictions, and stale or wrong-window telemetry.
