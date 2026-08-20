import json

from httpx import Response

from helpers import completion, create_session, run_turn


def test_prompt_segments_append_to_system_prompt(client, model_route):
    model_route.mock(return_value=Response(200, json=completion("done")))
    session = create_session(client, role_prompt="你是构思助手",
                             prompt_segments=["能力段一", "能力段二"])
    turn = run_turn(client, session["id"])
    assert turn["status"] == "completed"
    request = json.loads(model_route.calls[0].request.content)
    assert request["messages"][0] == {"role": "system",
                                      "content": "你是构思助手\n\n能力段一\n\n能力段二"}
    detail = client.get(f"/sessions/{session['id']}").json()
    assert detail["role_prompt"] == "你是构思助手\n\n能力段一\n\n能力段二"


def test_prompt_segments_without_role_prompt(client, model_route):
    model_route.mock(return_value=Response(200, json=completion("done")))
    session = create_session(client, prompt_segments=["能力段"])
    run_turn(client, session["id"])
    request = json.loads(model_route.calls[0].request.content)
    assert request["messages"][0] == {"role": "system", "content": "能力段"}
