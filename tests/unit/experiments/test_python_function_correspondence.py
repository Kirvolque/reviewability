from reviewability.domain.models import Hunk
from reviewability.experiments.python_function_correspondence import match_python_functions


def test_matches_renamed_function_with_shared_identifiers():
    source = Hunk(
        file_path="legacy.py",
        raw_removed_lines=[
            "def calculate_fee(order):\n",
            "    return order.total\n",
        ],
    )
    target = Hunk(
        file_path="pricing.py",
        raw_added_lines=[
            "def calculate_order_fee(order):\n",
            "    return order.total\n",
        ],
    )

    matches = match_python_functions([source, target])

    assert len(matches) == 1
    assert matches[0].source is source
    assert matches[0].target is target


def test_rejects_unrelated_functions_with_only_boilerplate_in_common():
    source = Hunk(
        file_path="invoices.py",
        raw_removed_lines=[
            "def archive_invoice(invoice):\n",
            "    if not invoice.is_final:\n",
            "        return False\n",
            "    return True\n",
        ],
    )
    target = Hunk(
        file_path="sessions.py",
        raw_added_lines=[
            "def refresh_session(session):\n",
            "    if not session.is_active:\n",
            "        return False\n",
            "    return True\n",
        ],
    )

    assert match_python_functions([source, target]) == []
