# XML external entities: a bounded parser comparison

Open the [Vue + Django lab](README.md), select **XML external entities**, and compare the same document with two fresh SAX/Expat parsers. The page displays actual parser text, resolver calls, and failures. The browser sends a fixture identifier; the backend chooses the corresponding fixed XML document.

An external entity declaration can cause a parser to ask a resolver for additional content. This lesson deliberately enables that feature only in the vulnerable comparison. Python documents both the external-general-entity feature and the resolver callback in its [SAX handler reference](https://docs.python.org/3/library/xml.sax.handler.html).

## Run the lesson

From `labs/browser_security`, use the existing launcher:

```powershell
python run_lab.py
```

Open `http://127.0.0.1:8766/` and choose **XML external entities**. First-time dependency setup is covered in the [lab README](README.md). This lesson adds no dependencies and does not need the companion origin to perform its comparisons.

| Fixture | External entities enabled | DOCTYPE rejected |
| --- | --- | --- |
| Ordinary XML text | Returns `Hello from the XML fixture.` | Same text; no resolver calls |
| Built-in entities | Returns `Tea & biscuits <served>` | Same text; no resolver calls |
| External entity | Returns `PRIVATE_XML_SENTINEL_ONLY_FOR_LAB`; one resolver call | Blocks the DOCTYPE before resolution; no application text |
| Unknown resource | Resolver rejects `urn:lab:unknown`; no application text | Blocks the DOCTYPE; no resolver call |
| Malformed XML | Reports a real parser error | Reports a real parser error |

The external-entity fixture is:

```xml
<!DOCTYPE message [<!ENTITY sample SYSTEM "urn:lab:private-marker">]>
<message>&sample;</message>
```

Compare it, then select the built-in-entities control. The private marker should disappear, and both parsers should accept ordinary XML escaping. The displayed `<served>` remains text in Vue; it does not create a DOM element.

## What changes between the parsers

The vulnerable parser enables external general entities. Its custom resolver returns a `StringIO` stream containing the synthetic marker for the exact identifier `urn:lab:private-marker`. SAX then parses that stream and delivers its text through the normal content-handler callback. This is an actual entity expansion, not a predicted result keyed to the fixture name. Streams are closed after success or failure. Python describes stream-backed parser inputs in the [InputSource reference](https://docs.python.org/3/library/xml.sax.reader.html).

The fixed parser disables external general entities and rejects every DOCTYPE in its `LexicalHandler.startDTD` callback. This happens at XML parsing time, before a resolver can supply entity content. Built-in entities such as `&amp;` require no DTD and continue to work. Rejecting unnecessary DTDs and external entities follows the approach described in the [OWASP XXE prevention guidance](https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html). Applications that require DTDs need a policy designed for that requirement; this lesson does not implement one.

## The experiment boundary

Both comparisons use the same outer restrictions. Only five server-defined documents are selectable; custom XML, file paths, URLs, and extra fields are rejected. The resolver never delegates to the default resource loader. It rejects unknown identifiers, public identifiers, and more than one resolution. External DTD resources are rejected before loading; external parameter entities are disabled. No fixture uses recursive entity expansion.

Each parse allows at most 2,048 source bytes, 1,024 returned text characters, eight nested elements, and one external resolution. Parser state is recreated per mode and request. Rejected or malformed documents return no partial application text. These limits bound the fixed experiment; they are not a general XML sandbox or a demonstration of denial-of-service payload handling.

The resolver restriction keeps the intentionally vulnerable comparison harmless. It is separate from the fixed parser's demonstrated defense. The word "private" refers to a synthetic marker in this Python module, not to a real file or credential. For actual path-handling comparisons, use the separate [path traversal lesson](PATH_TRAVERSAL.md).

## Request and implementation

`POST /api/xml/compare/` requires the ordinary same-origin Django CSRF token and an `application/json` body containing exactly:

```json
{"fixture":"external"}
```

A valid comparison returns HTTP 200 with the selected source and `results.vulnerable` / `results.fixed`. Each result contains `outcome`, `text`, `reason`, and `resolverCalls`. Outcomes are `parsed`, `blocked`, or `parse_error`; invalid selectors return HTTP 400 without parsing.

- [Backend parsers and in-memory resolver](backend/securitylab/xml_lab.py)
- [Vue comparison and escaped output](frontend/src/XmlLab.vue)
- [Backend tests](backend/securitylab/test_xml_lab.py)
- [Browser tests](frontend/tests/xml.spec.js)

From the lab directory, run the focused backend checks with:

```powershell
.\.venv\Scripts\python.exe backend\manage.py test securitylab.test_xml_lab
```

They check actual entity resolution, legitimate controls, DTD rejection, malformed input, parser budgets, stream closure, and rejection of attempted file/network loading. They also verify selector validation and CSRF protection. Browser checks compare visible parser outcomes, inert text rendering, and clearing of earlier results. See the [README test instructions](README.md) for the browser command and required free ports.
