"""Download-only copies of the ten harmless upload controls in the Markdown."""
import json
import struct
import zlib

HTML_MARKER = b'''<!doctype html>
<html lang="en"><meta charset="utf-8"><title>Upload marker</title>
<body><p id="marker">UPLOAD_HTML_STATIC</p>
<script>
console.log('UPLOAD_HTML_TEST_24');
document.getElementById('marker').textContent = 'UPLOAD_HTML_TEST_24';
</script></body></html>
'''
SVG_MARKER = b'''<svg xmlns="http://www.w3.org/2000/svg" width="320" height="50">
<rect width="320" height="50" fill="white"/>
<text id="marker" x="8" y="30" fill="black">UPLOAD_SVG_STATIC</text>
<script>
console.log('UPLOAD_SVG_TEST_25');
document.getElementById('marker').textContent = 'UPLOAD_SVG_TEST_25';
</script></svg>
'''


def _chunk(kind, data):
    return (struct.pack(">I", len(data)) + kind + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff))


PNG = (b"\x89PNG\r\n\x1a\n"
       + _chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
       + _chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00\xff"))
       + _chunk(b"IEND", b""))
FIXTURES = {
    "marker.txt": (b"UPLOAD_TEXT_TEST_27\n", "Plain UTF-8 text control"),
    "marker.html": (HTML_MARKER, "HTML with one console and visible marker"),
    "marker.svg": (SVG_MARKER, "SVG with one console and visible marker"),
    "marker.js": (b"console.log('UPLOAD_JS_TEST_26');\n", "JavaScript marker; previews remain plain text"),
    "marker.json": (json.dumps({"marker": "UPLOAD_JSON_DATA_ONLY"}).encode(), "JSON data control"),
    "pixel.png": (PNG, "Valid one-pixel PNG"),
    "pixel-upper.PNG": (PNG, "Valid PNG with uppercase extension"),
    "marker.html.txt": (HTML_MARKER, "HTML bytes with final .txt extension"),
    "marker.txt.html": (HTML_MARKER, "HTML bytes with final .html extension"),
    "html-as-image.png": (HTML_MARKER, "HTML bytes falsely named .png"),
}
