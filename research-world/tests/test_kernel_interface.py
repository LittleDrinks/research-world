import pytest

from server.kernel_interface import SQLiteKernel


def test_project_is_persisted_through_the_kernel_interface(tmp_path):
    kernel = SQLiteKernel(tmp_path / "kernel.db", tmp_path / "artifacts")

    project = kernel.create_project(
        "Orbit study", "Why do planetary orbits remain stable?"
    )
    reopened = SQLiteKernel(tmp_path / "kernel.db", tmp_path / "artifacts")

    assert reopened.get_project(project.id) == project
    assert reopened.list_projects() == [project]


def test_project_names_are_unique_at_the_kernel_interface(tmp_path):
    kernel = SQLiteKernel(tmp_path / "kernel.db", tmp_path / "artifacts")
    kernel.create_project("Orbit study", "Why do planetary orbits remain stable?")

    with pytest.raises(ValueError, match="project name already exists"):
        kernel.create_project("Orbit study", "A different question")


def test_session_can_be_created_listed_and_read_for_a_project(tmp_path):
    kernel = SQLiteKernel(tmp_path / "kernel.db", tmp_path / "artifacts")
    project = kernel.create_project(
        "Orbit study", "Why do planetary orbits remain stable?"
    )

    session = kernel.create_session(project.id, "Orbit notes")
    reopened = SQLiteKernel(tmp_path / "kernel.db", tmp_path / "artifacts")

    assert session.project_id == project.id
    assert session.messages == ()
    assert reopened.get_session(project.id, session.id) == session
    assert reopened.list_sessions(project.id) == [session]


def test_user_message_is_persisted_with_a_stable_id(tmp_path):
    kernel = SQLiteKernel(tmp_path / "kernel.db", tmp_path / "artifacts")
    project = kernel.create_project(
        "Orbit study", "Why do planetary orbits remain stable?"
    )
    session = kernel.create_session(project.id)

    message = kernel.append_user_message(project.id, session.id, "Check the evidence")
    reopened = SQLiteKernel(tmp_path / "kernel.db", tmp_path / "artifacts")

    assert message.id.startswith("message:")
    assert reopened.get_session(project.id, session.id).messages == (message,)
    assert reopened.list_sessions(project.id)[0].messages == (message,)


def test_repeated_message_persistence_reuses_the_same_association(tmp_path):
    kernel = SQLiteKernel(tmp_path / "kernel.db", tmp_path / "artifacts")
    project = kernel.create_project(
        "Orbit study", "Why do planetary orbits remain stable?"
    )
    session = kernel.create_session(project.id)

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
    kernel = SQLiteKernel(tmp_path / "kernel.db", tmp_path / "artifacts")
    project = kernel.create_project(
        "Orbit study", "Why do planetary orbits remain stable?"
    )
    session = kernel.create_session(project.id)
    message = kernel.append_user_message(project.id, session.id, "Check the evidence")

    projected = kernel.project_assistant_response(
        project.id, session.id, message.id, "The evidence is persisted."
    )

    assert projected.assistant_response == "The evidence is persisted."
    assert kernel.get_session(project.id, session.id).messages == (projected,)


def test_artifact_is_captured_and_read_through_the_kernel_interface(tmp_path):
    kernel = SQLiteKernel(tmp_path / "kernel.db", tmp_path / "artifacts")
    project = kernel.create_project(
        "Orbit study", "Why do planetary orbits remain stable?"
    )

    artifact = kernel.capture_artifact(project.id, b"result", "text/plain")

    assert artifact.id == f"artifact:{artifact.sha256}"
    assert not hasattr(artifact, "path")
    assert kernel.get_artifact(project.id, artifact.id) == artifact
    reopened = SQLiteKernel(tmp_path / "kernel.db", tmp_path / "artifacts")
    assert reopened.read_artifact(project.id, artifact.id) == b"result"


def test_artifact_is_project_scoped_and_immutable(tmp_path):
    kernel = SQLiteKernel(tmp_path / "kernel.db", tmp_path / "artifacts")
    project = kernel.create_project(
        "Orbit study", "Why do planetary orbits remain stable?"
    )
    other = kernel.create_project("Other study", "Why do stars shine?")

    artifact = kernel.capture_artifact(project.id, b"result", "text/plain")

    with pytest.raises(KeyError):
        kernel.get_artifact(other.id, artifact.id)
    same_content = kernel.capture_artifact(other.id, b"result", "text/plain")

    assert same_content.id == artifact.id
    assert same_content.project_id == other.id
    with pytest.raises(ValueError, match="metadata_conflict"):
        kernel.capture_artifact(project.id, b"result", "application/json")


def test_session_is_not_readable_from_another_project(tmp_path):
    kernel = SQLiteKernel(tmp_path / "kernel.db", tmp_path / "artifacts")
    project = kernel.create_project(
        "Orbit study", "Why do planetary orbits remain stable?"
    )
    other = kernel.create_project("Other study", "Why do stars shine?")
    session = kernel.create_session(project.id)

    assert kernel.list_sessions(other.id) == []
    with pytest.raises(PermissionError, match="another project"):
        kernel.get_session(other.id, session.id)


def test_reprojecting_the_same_answer_is_idempotent_and_cannot_overwrite(tmp_path):
    kernel = SQLiteKernel(tmp_path / "kernel.db", tmp_path / "artifacts")
    project = kernel.create_project(
        "Orbit study", "Why do planetary orbits remain stable?"
    )
    session = kernel.create_session(project.id)
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
    kernel = SQLiteKernel(tmp_path / "kernel.db", tmp_path / "artifacts")
    project = kernel.create_project(
        "Orbit study", "Why do planetary orbits remain stable?"
    )
    session = kernel.create_session(project.id)
    first = kernel.append_user_message(project.id, session.id, "First")
    second = kernel.append_user_message(project.id, session.id, "Second")

    second = kernel.project_assistant_response(
        project.id, session.id, second.id, "Answer two"
    )
    first = kernel.project_assistant_response(
        project.id, session.id, first.id, "Answer one"
    )

    assert kernel.get_session(project.id, session.id).messages == (first, second)
