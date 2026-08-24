import json

import respx
from httpx import Response

from helpers import MODEL_URL, completion, create_session, run_turn


def test_restart_keeps_history_and_continues(make_client):
    with respx.mock(assert_all_called=False) as router:
        route = router.post(MODEL_URL).mock(side_effect=[
            Response(200, json=completion("first answer")),
            Response(200, json=completion("second answer"))])
        client1 = make_client()
        s = create_session(client1, role_prompt="be terse")
        t1 = run_turn(client1, s["id"], prompt="q1")
        assert t1["status"] == "completed"
        # simulate process restart: brand-new Store/app on the same db
        client2 = make_client()
        detail = client2.get(f"/sessions/{s['id']}").json()
        assert detail["message_count"] == 2
        assert detail["role_prompt"] == "be terse"
        t2 = run_turn(client2, s["id"], prompt="q2")
        assert t2["status"] == "completed"
        assert t2["result_text"] == "second answer"
        detail = client2.get(f"/sessions/{s['id']}").json()
        assert detail["message_count"] == 4
        second = json.loads(route.calls[1].request.content)
        assert [m["role"] for m in second["messages"]] == [
            "system", "user", "assistant", "user"]
        assert second["messages"][2]["content"] == "first answer"
