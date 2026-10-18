from django.urls import path
from securitylab import views
from securitylab.traversal import traversal
from securitylab import cross_origin
from securitylab.sql_lab import sql_compare
from securitylab.access_lab import access_state, access_identity, access_record
from securitylab.auth_lab import auth_compare
from securitylab.ssrf_lab import ssrf_compare
from securitylab.logic_lab import logic_compare
from securitylab.template_lab import template_compare
from securitylab.command_lab import command_compare
from securitylab.xml_lab import xml_compare
from securitylab.write_lab import write_compare
from securitylab.jwt_lab import jwt_compare
from securitylab.webhook_lab import webhook_compare
from securitylab.sanitizer_lab import sanitizer_save, sanitizer_state, sanitizer_frame
from securitylab.message_lab import message_prepare, message_receiver, message_receiver_script, message_sender, message_sender_script
from securitylab.archive_lab import archive_compare

urlpatterns = [
    path("", views.index),
    path("assets/<path:asset>", views.asset),
    path("api/health", views.health),
    path("api/bootstrap", views.bootstrap),
    path("api/traversal/", traversal),
    path("api/sql/", sql_compare),
    path("api/access/state/", access_state),
    path("api/access/identity/", access_identity),
    path("api/access/record/", access_record),
    path("api/auth/compare/", auth_compare),
    path("api/ssrf/compare/", ssrf_compare),
    path("api/logic/compare/", logic_compare),
    path("api/template/compare/", template_compare),
    path("api/command/compare/", command_compare),
    path("api/xml/compare/", xml_compare),
    path("api/write/compare/", write_compare),
    path("api/jwt/compare/", jwt_compare),
    path("api/webhook/compare/", webhook_compare),
    path("api/sanitizer/save/", sanitizer_save),
    path("api/sanitizer/state/", sanitizer_state),
    path("lab/sanitizer/frame/", sanitizer_frame),
    path("api/message/prepare/", message_prepare),
    path("peer/message/", message_receiver),
    path("peer/message/receiver.js", message_receiver_script),
    path("lab/message/sender/", message_sender),
    path("lab/message/sender.js", message_sender_script),
    path("api/archive/compare/", archive_compare),
    path("api/cross-origin/prepare/", cross_origin.prepare),
    path("api/cross-origin/state/", cross_origin.state),
    path("api/cross-origin/change/vulnerable/", cross_origin.csrf_vulnerable),
    path("api/cross-origin/change/fixed/", cross_origin.csrf_fixed),
    path("api/cross-origin/data/<str:mode>/", cross_origin.cors_data),
    path("peer/", cross_origin.peer_page),
    path("peer/boot.js", cross_origin.peer_script),
    path("api/stored/", views.stored),
    path("api/uploads/", views.uploads),
    path("api/uploads/<uuid:upload_id>/", views.delete_upload),
    path("api/fixtures/<str:name>", views.fixture),
    path("lab/frame/", views.frame),
    path("lab/boot.js", views.script, {"name": "boot"}),
    path("lab/probe.js", views.script, {"name": "probe"}),
    path("lab/parser.js", views.script, {"name": "parser"}),
    path("lab/jsonp.js", views.jsonp),
    path("lab/ping", views.ping),
    path("lab/uploads/<uuid:upload_id>/download/", views.download),
    path("lab/uploads/<uuid:upload_id>/preview/", views.preview),
]
handler400 = "securitylab.views.bad_request"
handler403 = "securitylab.views.forbidden"
handler404 = "securitylab.views.not_found"
handler500 = "securitylab.views.server_error"
