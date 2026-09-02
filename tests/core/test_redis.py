from unittest.mock import MagicMock

from app.core.redis import clear_balance_cache


def test_clear_balance_cache_removes_only_balance_keys():
    client = MagicMock()
    client.scan_iter.side_effect = [
        iter(["user_balances:1", "user_balances:2"]),
        iter(["group_balances:3"]),
    ]
    client.delete.side_effect = [2, 1]

    deleted = clear_balance_cache(client)

    assert deleted == 3
    assert [call.kwargs["match"] for call in client.scan_iter.call_args_list] == [
        "user_balances:*",
        "group_balances:*",
    ]
    client.delete.assert_any_call("user_balances:1", "user_balances:2")
    client.delete.assert_any_call("group_balances:3")
