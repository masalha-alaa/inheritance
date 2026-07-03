import json
from importlib import import_module

from heirs import Heirs
from inheritance import get_results
from my_utils import HeirsOrderInHtml as HOIH
from settings import FIQH_ENGINE


_fiqh = None


def _get_fiqh():
    global _fiqh
    if _fiqh is None:
        fiqh_module = import_module(FIQH_ENGINE)
        _fiqh = fiqh_module.Fiqh()
        _fiqh.initialize()
    return _fiqh


def _problem_from_heirs(heirs):
    return Heirs(
        husband=heirs[HOIH.HUSBAND.value],
        wife=heirs[HOIH.WIFE.value],
        son=heirs[HOIH.SON.value],
        daughter=heirs[HOIH.DAUGHTER.value],
        father=heirs[HOIH.FATHER.value],
        mother=heirs[HOIH.MOTHER.value],
        brother=heirs[HOIH.BROTHER.value],
        sister=heirs[HOIH.SISTER.value],
        relatives=heirs[HOIH.RELATIVES.value],
    )


def calculate(payload_json):
    data = json.loads(payload_json)
    heirs = data.get("heirs") or [0] * 9
    estate = float(data.get("estate") or 24)
    problem = _problem_from_heirs(heirs)

    the_case, _, _, study_result = get_results(problem, estate)
    fiqh_result, awl_applied = _get_fiqh().run(problem, estate)

    return json.dumps(
        {
            "study": list(study_result.values()),
            "study_error": len(study_result) == 0,
            "case": the_case.name,
            "fiqh": list(fiqh_result.values()),
            "fiqh_error": len(fiqh_result) == 0,
            "awl": awl_applied,
        }
    )
