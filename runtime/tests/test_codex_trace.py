from runtime.trace import TraceStore, inspect_trace


def test_public_trace_redacts_embedded_credentials_and_paths():
    view = inspect_trace([_event(_attack_payload())])
    rendered = str(view)
    assert "hunter2" not in rendered and "Bearer token" not in rendered
    assert "alice" not in rendered and "C:\\Users" not in rendered


def test_trace_redacts_secrets_and_paths_before_private_persistence(tmp_path):
    store, payload = TraceStore(tmp_path), _private_attack_payload()
    store.create("s", payload)
    raw, view = store.path("s").read_text(), inspect_trace(store.read("s"))
    for value in _private_values():
        assert value not in raw and value not in str(view)


def test_public_trace_keeps_token_accounting():
    event = _event(_projection_boundary_payload())
    session = inspect_trace([event])["session"]
    assert session["token_budget"] == 10
    assert session["usage"] == {"input_tokens": 3, "output_tokens": 2}
    assert all(session[key] == "<redacted>" for key in _projection_boundary_payload() if key not in {"token_budget", "usage"})


def _projection_boundary_payload():
    hidden = {key: "secret" for key in ["credentials", "tokens", "access_token", "refresh_token", "id_token", "bearer_token", "session_token", "base_url", "endpoint"]}
    return {**hidden, "token_budget": 10, "usage": {"input_tokens": 3, "output_tokens": 2}}


def test_public_trace_redacts_generic_uris_and_encoded_queries():
    event = _event({"command": "curl ftp://u:p@host/a?x%2Dapi%2Dkey=secret"})
    rendered = str(inspect_trace([event]))
    assert "u:p" not in rendered and "secret" not in rendered


def test_public_trace_redacts_malformed_uri_ports():
    rendered = str(inspect_trace([_event({"uri": "https://u:p@host:bad/a?token=secret"})]))
    assert "u:p" not in rendered and "secret" not in rendered


def test_public_trace_redacts_credential_label_variants():
    labels = "api-key=a apikey:b client_secret=c secret=d token=e password=f credential=g"
    rendered = str(inspect_trace([_event({"output": labels})]))
    assert all(value not in rendered for value in ["api-key=a", "apikey:b", "client_secret=c", "secret=d", "token=e", "password=f", "credential=g"])


def _event(data):
    return {"type": "session_meta", "seq": 0, "time": "now", "session_id": "s", "data": data}


def _attack_payload():
    return {"command": "curl https://alice:hunter2@example.test/a?x-api-key=hunter2 /srv/private", "authorization": "Bearer token", "nested": {"items": [{"url": "ssh://u:p@host/x?secret=one", "path": "C:\\Users\\a\\x"}]}}


def _private_attack_payload():
    return {"provider_item": {"raw": "Authorization: Bearer auth-secret; Set-Cookie: sid=cookie-secret; ./private/file", "Database_URL": "postgres://db:dsn-secret@host/db", "nested": [{"URL": "https://user:url-secret@host/a?token=query-secret", "path": "relative/private", "COOKIE": "cookie-secret"}]}}


def _private_values():
    return ["auth-secret", "cookie-secret", "dsn-secret", "url-secret", "query-secret", "./private/file", "relative/private"]
