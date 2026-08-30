import pytest

from server.kernel_interface import KernelInterface, LocalMap, LocalMapQuery, create_kernel


def _kernel(tmp_path) -> KernelInterface:
    return create_kernel(tmp_path / "kernel.db", tmp_path / "artifacts")


def _project(kernel: KernelInterface):
    return kernel.create_project(
        "Orbit study", "Why do planetary orbits remain stable?"
    )


def _project_and_session(kernel: KernelInterface):
    project = _project(kernel)
    return project, kernel.create_session(project.id)


def test_project_is_persisted_through_the_kernel_interface(tmp_path):
    kernel = _kernel(tmp_path)

    project = _project(kernel)
    reopened = _kernel(tmp_path)

    assert reopened.get_project(project.id) == project
    assert reopened.list_projects() == [project]


def test_project_names_are_unique_at_the_kernel_interface(tmp_path):
    kernel = _kernel(tmp_path)
    _project(kernel)

    with pytest.raises(ValueError, match="project name already exists"):
        kernel.create_project("Orbit study", "A different question")


def test_session_can_be_created_listed_and_read_for_a_project(tmp_path):
    kernel = _kernel(tmp_path)
    project = _project(kernel)
    session = kernel.create_session(project.id, "Orbit notes")
    reopened = _kernel(tmp_path)

    assert session.project_id == project.id
    assert session.messages == ()
    assert reopened.get_session(project.id, session.id) == session
    assert reopened.list_sessions(project.id) == [session]


def test_user_message_is_persisted_with_a_stable_id(tmp_path):
    kernel = _kernel(tmp_path)
    project, session = _project_and_session(kernel)

    message = kernel.append_user_message(project.id, session.id, "Check the evidence")
    reopened = _kernel(tmp_path)

    assert message.id.startswith("message:")
    assert reopened.get_session(project.id, session.id).messages == (message,)
    assert reopened.list_sessions(project.id)[0].messages == (message,)


def test_repeated_message_persistence_reuses_the_same_association(tmp_path):
    kernel = _kernel(tmp_path)
    project, session = _project_and_session(kernel)

    first = kernel.append_user_message(
        project.id, session.id, "Check the evidence", message_id="message:retry"
    )
    repeated = kernel.append_user_message(
        project.id, session.id, "Check the evidence", message_id="message:retry"
    )

    assert repeated == first
    assert kernel.get_session(project.id, session.id).messages == (first,)
    with pytest.raises(ValueError, match="already belongs"):
        kernel.append_user_message(
            project.id, session.id, "Changed", message_id="message:retry"
        )


def test_assistant_response_is_projected_onto_its_user_message(tmp_path):
    kernel = _kernel(tmp_path)
    project, session = _project_and_session(kernel)
    message = kernel.append_user_message(project.id, session.id, "Check the evidence")

    projected = kernel.project_assistant_response(
        project.id, session.id, message.id, "The evidence is persisted."
    )

    assert projected.assistant_response == "The evidence is persisted."
    assert kernel.get_session(project.id, session.id).messages == (projected,)


def test_artifact_is_captured_and_read_through_the_kernel_interface(tmp_path):
    kernel = _kernel(tmp_path)
    project = _project(kernel)

    artifact = kernel.capture_artifact(project.id, b"result", "text/plain")

    assert artifact.id == f"artifact:{artifact.sha256}"
    assert kernel.get_artifact(project.id, artifact.id) == artifact
    reopened = _kernel(tmp_path)
    assert reopened.read_artifact(project.id, artifact.id) == b"result"


def test_artifact_is_project_scoped_and_immutable(tmp_path):
    kernel = _kernel(tmp_path)
    project = _project(kernel)
    other = kernel.create_project("Other study", "Why do stars shine?")

    artifact = kernel.capture_artifact(project.id, b"result", "text/plain")

    with pytest.raises(KeyError):
        kernel.get_artifact(other.id, artifact.id)
    same_content = kernel.capture_artifact(other.id, b"result", "text/plain")

    assert same_content.id == artifact.id
    assert same_content.project_id == other.id
    with pytest.raises(ValueError):
        kernel.capture_artifact(project.id, b"result", "application/json")


def test_session_is_not_readable_from_another_project(tmp_path):
    kernel = _kernel(tmp_path)
    project, session = _project_and_session(kernel)
    other = kernel.create_project("Other study", "Why do stars shine?")

    assert kernel.list_sessions(other.id) == []
    with pytest.raises(PermissionError, match="another project"):
        kernel.get_session(other.id, session.id)


def test_reprojecting_the_same_answer_is_idempotent_and_cannot_overwrite(tmp_path):
    kernel = _kernel(tmp_path)
    project, session = _project_and_session(kernel)
    message = kernel.append_user_message(project.id, session.id, "Check the evidence")

    first = kernel.project_assistant_response(
        project.id, session.id, message.id, "Saved"
    )
    repeated = kernel.project_assistant_response(
        project.id, session.id, message.id, "Saved"
    )

    assert repeated == first
    with pytest.raises(ValueError, match="already projected"):
        kernel.project_assistant_response(project.id, session.id, message.id, "Changed")


def test_response_completion_order_does_not_reorder_session_messages(tmp_path):
    kernel = _kernel(tmp_path)
    project, session = _project_and_session(kernel)
    first = kernel.append_user_message(project.id, session.id, "First")
    second = kernel.append_user_message(project.id, session.id, "Second")

    second = kernel.project_assistant_response(
        project.id, session.id, second.id, "Answer two"
    )
    first = kernel.project_assistant_response(
        project.id, session.id, first.id, "Answer one"
    )

    assert kernel.get_session(project.id, session.id).messages == (first, second)


def test_record_is_immediately_readable_through_the_kernel_interface(tmp_path):
    kernel = _kernel(tmp_path)
    project = _project(kernel)

    record = kernel.record(
        project.id,
        "direction",
        {"text": "Orbital resonance prevents close encounters."},
    )
    reopened = _kernel(tmp_path)

    assert reopened.get_record(project.id, record.id) == record
    assert reopened.list_records(project.id) == [record]


def test_existing_records_can_be_connected_through_the_kernel_interface(tmp_path):
    kernel = _kernel(tmp_path)
    project = _project(kernel)
    source = kernel.record(project.id, "source", {"title": "Resonance study"})
    direction = kernel.record(project.id, "direction", {"text": "Candidate"})

    relation = kernel.connect(project.id, source.id, direction.id, "supports")
    reopened = _kernel(tmp_path)

    assert reopened.get_relation(project.id, relation.id) == relation
    assert reopened.list_relations(project.id) == [relation]


def test_duplicate_connect_is_a_domain_error(tmp_path):
    kernel = _kernel(tmp_path)
    project = _project(kernel)
    source = kernel.record(project.id, "source", {"title": "Study"})
    direction = kernel.record(project.id, "direction", {"text": "Candidate"})
    relation = kernel.connect(project.id, source.id, direction.id, "supports")

    with pytest.raises(ValueError, match="relation already exists"):
        kernel.connect(project.id, source.id, direction.id, "supports")

    assert kernel.list_relations(project.id) == [relation]


def test_connect_rejects_invalid_relation_types_and_cross_project_records(tmp_path):
    kernel = _kernel(tmp_path)
    project = _project(kernel)
    other = kernel.create_project("Other study", "Why do stars shine?")
    source = kernel.record(project.id, "source", {"title": "Study"})
    direction = kernel.record(project.id, "direction", {"text": "Candidate"})
    foreign = kernel.record(other.id, "direction", {"text": "Foreign"})

    with pytest.raises(ValueError, match="invalid relation type"):
        kernel.connect(project.id, source.id, direction.id, "reviews")
    with pytest.raises(PermissionError, match="another project"):
        kernel.connect(project.id, source.id, foreign.id, "supports")


def test_remove_relation_preserves_both_records(tmp_path):
    kernel = _kernel(tmp_path)
    project = _project(kernel)
    source = kernel.record(project.id, "source", {"title": "Study"})
    direction = kernel.record(project.id, "direction", {"text": "Candidate"})
    relation = kernel.connect(project.id, source.id, direction.id, "supports")

    kernel.remove_relation(project.id, relation.id)

    assert kernel.list_relations(project.id) == []
    assert kernel.get_record(project.id, source.id) == source
    assert kernel.get_record(project.id, direction.id) == direction


def _connected_records(kernel, project):
    artifact = kernel.capture_artifact(project.id, b"evidence", "text/plain")
    source = kernel.record(
        project.id, "source", {"title": "Study"}
    )
    direction = kernel.record(
        project.id, "direction", {"text": "Candidate"}, (artifact.id,)
    )
    experiment = kernel.record(project.id, "experiment", {"title": "Trial"})
    kernel.connect(project.id, source.id, direction.id, "supports")
    kernel.connect(project.id, experiment.id, direction.id, "refutes")
    remaining = kernel.connect(project.id, source.id, experiment.id, "depends_on")
    return artifact, source, direction, experiment, remaining


def test_remove_record_cascades_direct_relations_and_preserves_artifact(tmp_path):
    kernel = _kernel(tmp_path)
    project = _project(kernel)
    values = _connected_records(kernel, project)
    artifact, source, direction, experiment, remaining = values

    kernel.remove_record(project.id, direction.id)

    assert kernel.list_records(project.id) == [source, experiment]
    assert kernel.list_relations(project.id) == [remaining]
    assert kernel.read_artifact(project.id, artifact.id) == b"evidence"
    with pytest.raises(KeyError):
        kernel.get_record(project.id, direction.id)


def test_local_map_text_query_returns_bounded_matching_records(tmp_path):
    kernel = _kernel(tmp_path)
    project = _project(kernel)
    first = kernel.record(project.id, "source", {"title": "Orbital resonance"})
    kernel.record(project.id, "direction", {"text": "Orbital stability"})
    kernel.record(project.id, "experiment", {"title": "Unrelated trial"})

    result = kernel.local_map(
        project.id, LocalMapQuery(text="orbital", limit=1)
    )

    assert result.records == (first,)


def test_local_map_node_reference_returns_relations_and_artifacts(tmp_path):
    kernel = _kernel(tmp_path)
    project = _project(kernel)
    artifact = kernel.capture_artifact(project.id, b"evidence", "text/plain")
    source = kernel.record(project.id, "source", {"title": "Study"})
    direction = kernel.record(
        project.id, "direction", {"text": "Candidate"}, (artifact.id,)
    )
    relation = kernel.connect(project.id, source.id, direction.id, "supports")

    result = kernel.local_map(
        project.id, LocalMapQuery(record_id=direction.id, limit=5)
    )

    assert result == LocalMap((direction,), (relation,), (artifact,))


@pytest.mark.parametrize(
    ("invalid_field", "invalid_value"), (("text", 123), ("record_id", 123))
)
def test_local_map_rejects_wrong_query_field_types(tmp_path, invalid_field, invalid_value):
    kernel = _kernel(tmp_path)
    project = _project(kernel)
    record = kernel.record(project.id, "source", {"title": "Orbit"})
    values = {"text": "orbit", "record_id": record.id}
    values[invalid_field] = invalid_value

    with pytest.raises(ValueError, match="local map query"):
        kernel.local_map(project.id, LocalMapQuery(**values, limit=5))


@pytest.mark.parametrize(
    ("invalid_field", "invalid_value"),
    (("text", ""), ("text", "  "), ("record_id", ""), ("record_id", "  ")),
)
def test_local_map_rejects_empty_query_fields(tmp_path, invalid_field, invalid_value):
    kernel = _kernel(tmp_path)
    project = _project(kernel)
    record = kernel.record(project.id, "source", {"title": "Orbit"})
    values = {"text": "orbit", "record_id": record.id}
    values[invalid_field] = invalid_value

    with pytest.raises(ValueError, match="local map query"):
        kernel.local_map(project.id, LocalMapQuery(**values, limit=5))


def test_local_map_text_query_matches_content_values_only(tmp_path):
    kernel = _kernel(tmp_path)
    project = _project(kernel)
    record = kernel.record(project.id, "source", {"title": "Study"})

    result = kernel.local_map(project.id, LocalMapQuery(text="  study  ", limit=5))

    assert result.records == (record,)


def test_local_map_text_query_does_not_match_content_field_names(tmp_path):
    kernel = _kernel(tmp_path)
    project = _project(kernel)
    kernel.record(project.id, "source", {"title": "Study"})

    result = kernel.local_map(project.id, LocalMapQuery(text="title", limit=5))

    assert result.records == ()


def test_local_map_preserves_duplicates_and_project_scope(tmp_path):
    kernel = _kernel(tmp_path)
    project = _project(kernel)
    other = kernel.create_project("Other study", "Why do stars shine?")
    first = kernel.record(project.id, "source", {"text": "shared finding"})
    second = kernel.record(project.id, "direction", {"text": "shared finding"})
    kernel.record(other.id, "source", {"text": "shared finding"})

    result = kernel.local_map(project.id, LocalMapQuery(text="shared", limit=5))

    assert result.records == (first, second)


def test_local_map_updates_after_relation_and_record_removal(tmp_path):
    kernel = _kernel(tmp_path)
    project = _project(kernel)
    source = kernel.record(project.id, "source", {"title": "Orbit study"})
    direction = kernel.record(project.id, "direction", {"text": "Orbit route"})
    relation = kernel.connect(project.id, source.id, direction.id, "supports")
    query = LocalMapQuery(text="orbit", limit=5)

    assert kernel.local_map(project.id, query).relations == (relation,)
    kernel.remove_relation(project.id, relation.id)
    assert kernel.local_map(project.id, query).relations == ()
    kernel.remove_record(project.id, direction.id)
    assert kernel.local_map(project.id, query).records == (source,)
