from typing import Iterable

from corptools.models import CorpAsset  # from allianceauth-corptools
# You may need to adjust import path depending on version.


# Placeholder: you’ll replace this with real capital type IDs.
CAPITAL_TYPE_IDS = [
    # e.g. 23919, 3764, ...
]


def get_capital_assets_for_corps(corp_ids: Iterable[int]):
    """Return CorpTools assets that are capital ships for given corps."""
    return CorpAsset.objects.filter(
        corporation_id__in=corp_ids,
        type_id__in=CAPITAL_TYPE_IDS,
    )