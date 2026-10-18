"""Real SAX parsing of fixed XML fixtures, with no filesystem or network resolver."""
import io
import json
from xml.sax import SAXException, SAXParseException
from xml.sax.expatreader import ExpatParser
from xml.sax.handler import (
    ContentHandler, EntityResolver, LexicalHandler, feature_external_ges,
    feature_external_pes, property_lexical_handler,
)
from xml.sax.xmlreader import InputSource

from django.http import JsonResponse

MARKER_URI = "urn:lab:private-marker"
MARKER = "PRIVATE_XML_SENTINEL_ONLY_FOR_LAB"
MAX_XML_BYTES = 2048
MAX_TEXT = 1024
MAX_DEPTH = 8
MAX_RESOLUTIONS = 1
FIXTURES = {
    "normal": {"label": "Control: ordinary XML text", "xml": "<message>Hello from the XML fixture.</message>"},
    "builtin": {"label": "Control: built-in XML entities", "xml": "<message>Tea &amp; biscuits &lt;served&gt;</message>"},
    "external": {"label": "External entity reads the in-memory marker", "xml": '<!DOCTYPE message [<!ENTITY sample SYSTEM "urn:lab:private-marker">]>\n<message>&sample;</message>'},
    "unknown": {"label": "Unknown resource is blocked by the lab boundary", "xml": '<!DOCTYPE message [<!ENTITY sample SYSTEM "urn:lab:unknown">]>\n<message>&sample;</message>'},
    "malformed": {"label": "Control: malformed XML is rejected", "xml": "<message>Incomplete fixture</different>"},
}
XML_METADATA = {
    "fixtures": [{"id": key, **value} for key, value in FIXTURES.items()],
    "markerUri": MARKER_URI,
    "inputLimit": MAX_XML_BYTES,
    "textLimit": MAX_TEXT,
    "depthLimit": MAX_DEPTH,
    "resolutionLimit": MAX_RESOLUTIONS,
}


class LabBlocked(SAXException):
    """A parser callback stopped a fixture at an explicit policy boundary."""


class MarkerResolver(EntityResolver):
    """Never delegate to SAX's default resource loader, even on unknown URIs."""

    def __init__(self):
        self.calls = []
        self.streams = []

    def resolveEntity(self, publicId, systemId):
        entry = {"systemId": systemId, "outcome": "blocked"}
        self.calls.append(entry)
        if len(self.calls) > MAX_RESOLUTIONS:
            raise LabBlocked("The one-resolution fixture budget was exceeded.")
        if publicId is not None or systemId != MARKER_URI:
            raise LabBlocked("The lab resolver rejects every resource except its exact in-memory marker URI.")
        source = InputSource(MARKER_URI)
        stream = io.StringIO(MARKER)
        self.streams.append(stream)
        source.setCharacterStream(stream)
        entry["outcome"] = "in_memory_marker"
        return source

    def close(self):
        for stream in self.streams:
            stream.close()


class FixtureEvents(ContentHandler, LexicalHandler):
    def __init__(self, fixed):
        super().__init__()
        self.fixed = fixed
        self.parts = []
        self.text_size = 0
        self.depth = 0

    def startDTD(self, name, public_id, system_id):
        if self.fixed:
            raise LabBlocked("DOCTYPE declarations are rejected before any external entity is resolved.")
        # Fixtures have an internal declaration only. Never load external DTDs.
        if public_id is not None or system_id is not None:
            raise LabBlocked("External DTD resources are outside this lesson.")

    def startElement(self, name, attrs):
        self.depth += 1
        if self.depth > MAX_DEPTH:
            raise LabBlocked("The element-depth fixture budget was exceeded.")

    def endElement(self, name):
        self.depth -= 1

    def characters(self, content):
        self.text_size += len(content)
        if self.text_size > MAX_TEXT:
            raise LabBlocked("The parsed-text fixture budget was exceeded.")
        self.parts.append(content)


def parse_fixture(fixture_id, mode):
    """Only identifiers select source XML; this function has no free-text XML input."""
    if mode not in {"vulnerable", "fixed"}:
        raise ValueError("Unknown parser mode")
    source_xml = FIXTURES[fixture_id]["xml"]
    result = {"mode": mode, "outcome": "blocked", "text": "", "reason": "", "resolverCalls": []}
    if len(source_xml.encode("utf-8")) > MAX_XML_BYTES:
        result["reason"] = "The XML fixture exceeds its byte budget."
        return result
    events = FixtureEvents(fixed=mode == "fixed")
    resolver = MarkerResolver()
    # Explicit implementation selection avoids environment-selected SAX drivers.
    parser = ExpatParser()
    parser.setContentHandler(events)
    parser.setEntityResolver(resolver)
    parser.setProperty(property_lexical_handler, events)
    parser.setFeature(feature_external_pes, False)
    parser.setFeature(feature_external_ges, mode == "vulnerable")
    source = InputSource()
    source.setCharacterStream(io.StringIO(source_xml))
    try:
        parser.parse(source)
        result.update(outcome="parsed", text="".join(events.parts), reason=(
            "XML parsed with DOCTYPE forbidden and external general entities disabled."
            if mode == "fixed" else
            "XML parsed with external general entities enabled and the lab's in-memory-only resolver."
        ))
    except LabBlocked as exc:
        result["reason"] = str(exc)
    except SAXParseException as exc:
        result.update(outcome="parse_error", reason=f"XML parser error at line {exc.getLineNumber()}, column {exc.getColumnNumber()}: {exc.getMessage()[:160]}")
    finally:
        source.getCharacterStream().close()
        resolver.close()
    # Never return partially parsed application data after rejection or failure.
    result["resolverCalls"] = resolver.calls
    return result


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON field")
        result[key] = value
    return result


def xml_compare(request):
    """Both comparisons are protected by Django's normal CSRF middleware."""
    def invalid(reason, status=400):
        return JsonResponse({"error": reason}, status=status)

    if request.method != "POST":
        response = invalid("Use POST with an application/json body.", 405)
        response["Allow"] = "POST"
        return response
    if request.GET or request.content_type != "application/json":
        return invalid("Use an application/json body without query parameters.")
    if len(request.body) > 256:
        return invalid("The fixture selector exceeds its request budget.")
    try:
        data = json.loads(request.body, object_pairs_hook=unique_object)
    except (ValueError, UnicodeDecodeError):
        return invalid("Invalid JSON or duplicate fields.")
    if not isinstance(data, dict) or set(data) != {"fixture"}:
        return invalid("Provide exactly fixture; custom XML, paths, and URLs are not accepted.")
    fixture_id = data["fixture"]
    if not isinstance(fixture_id, str) or fixture_id not in FIXTURES:
        return invalid("Choose a listed XML fixture.")
    return JsonResponse({
        "fixture": fixture_id,
        "xml": FIXTURES[fixture_id]["xml"],
        "results": {mode: parse_fixture(fixture_id, mode) for mode in ("vulnerable", "fixed")},
    })
