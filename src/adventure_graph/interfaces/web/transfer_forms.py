"""Bounded upload forms for portable adventure and playthrough documents."""

from __future__ import annotations

from dataclasses import dataclass
from wsgiref.types import WSGIEnvironment

from adventure_graph.application.document_limits import (
    MAX_CANONICAL_JSON_BYTES as MAX_PORTABLE_DOCUMENT_BYTES,
)
from adventure_graph.interfaces.web.form_parsing import (
    one_form_value,
    one_uploaded_file,
    parse_multipart_form,
    require_allowed_upload_fields,
    require_revision_value,
)


@dataclass(frozen=True, slots=True)
class ImportDocumentValues:
    """One uploaded portable JSON document and its expected revision."""

    expected_revision: str
    content: bytes


def parse_import_document_form(
    environ: WSGIEnvironment,
    *,
    file_field: str,
) -> tuple[ImportDocumentValues, str]:
    """Parse one canonical JSON upload with CSRF and revision fields."""
    fields, files = parse_multipart_form(
        environ,
        max_num_fields=3,
        max_file_bytes=MAX_PORTABLE_DOCUMENT_BYTES,
    )
    require_allowed_upload_fields(
        fields,
        files,
        allowed_fields={"csrf_token", "expected_revision"},
        allowed_files={file_field},
    )
    token = one_form_value(fields, "csrf_token")
    revision = one_form_value(fields, "expected_revision")
    require_revision_value(revision)
    uploaded = one_uploaded_file(files, file_field)
    return ImportDocumentValues(revision, uploaded.content), token
