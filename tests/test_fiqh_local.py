import os
import unittest

from heirs import Heirs
from fiqh_local import Fiqh
from my_utils import F, HeirsOrderInHtml, display_fraction_in_unicode


OUTPUT_KEYS = ("husband", "wife", "son", "daughter", "father", "mother", "brother", "sister", "relatives")


WEBSITE_DERIVED_CASES = (
    ("husband_alone_spouse_radd", {"husband": 1}, {"husband": "1"}),
    ("wife_alone_spouse_radd", {"wife": 1}, {"wife": "1"}),
    ("son_alone_residue", {"son": 1}, {"son": "1"}),
    ("daughter_alone_radd", {"daughter": 1}, {"daughter": "1"}),
    ("daughters_alone_radd", {"daughter": 2}, {"daughter": "1"}),
    ("father_alone_residue", {"father": 1}, {"father": "1"}),
    ("mother_alone_radd", {"mother": 1}, {"mother": "1"}),
    ("brother_alone_residue", {"brother": 1}, {"brother": "1"}),
    ("sister_alone_radd", {"sister": 1}, {"sister": "1"}),
    ("sisters_alone_radd", {"sister": 2}, {"sister": "1"}),
    ("cousin_alone_residue", {"relatives": 1}, {"relatives": "1"}),
    ("son_daughter_residue", {"son": 1, "daughter": 1}, {"son": "2/3", "daughter": "1/3"}),
    ("husband_son", {"husband": 1, "son": 1}, {"husband": "1/4", "son": "3/4"}),
    ("wife_son", {"wife": 1, "son": 1}, {"wife": "1/8", "son": "7/8"}),
    (
        "father_son_mother",
        {"father": 1, "mother": 1, "son": 1},
        {"son": "2/3", "father": "1/6", "mother": "1/6"},
    ),
    (
        "father_son_daughter_mother",
        {"father": 1, "mother": 1, "son": 1, "daughter": 1},
        {"son": "4/9", "daughter": "2/9", "father": "1/6", "mother": "1/6"},
    ),
    ("daughter_father", {"daughter": 1, "father": 1}, {"daughter": "1/2", "father": "1/2"}),
    ("daughters_father", {"daughter": 2, "father": 1}, {"daughter": "2/3", "father": "1/3"}),
    ("daughter_mother_radd", {"daughter": 1, "mother": 1}, {"daughter": "3/4", "mother": "1/4"}),
    (
        "husband_daughter_mother_radd",
        {"husband": 1, "daughter": 1, "mother": 1},
        {"husband": "1/4", "daughter": "9/16", "mother": "3/16"},
    ),
    (
        "wife_daughter_mother_radd",
        {"wife": 1, "daughter": 1, "mother": 1},
        {"wife": "1/8", "daughter": "21/32", "mother": "7/32"},
    ),
    (
        "wife_daughters_mother_radd",
        {"wife": 1, "daughter": 2, "mother": 1},
        {"wife": "1/8", "daughter": "7/10", "mother": "7/40"},
    ),
    (
        "husband_daughters_mother_awl",
        {"husband": 1, "daughter": 2, "mother": 1},
        {"husband": "3/13", "daughter": "8/13", "mother": "2/13"},
        True,
    ),
    ("parents_no_spouse", {"father": 1, "mother": 1}, {"father": "2/3", "mother": "1/3"}),
    (
        "husband_parents_umariyat",
        {"husband": 1, "father": 1, "mother": 1},
        {"husband": "1/2", "father": "1/3", "mother": "1/6"},
    ),
    (
        "wife_parents_umariyat",
        {"wife": 1, "father": 1, "mother": 1},
        {"wife": "1/4", "father": "1/2", "mother": "1/4"},
    ),
    (
        "husband_parents_one_sibling",
        {"husband": 1, "father": 1, "mother": 1, "brother": 1},
        {"husband": "1/2", "father": "1/6", "mother": "1/3", "brother": "0"},
    ),
    (
        "husband_parents_multiple_siblings",
        {"husband": 1, "father": 1, "mother": 1, "brother": 2},
        {"husband": "1/2", "father": "1/3", "mother": "1/6", "brother": "0"},
    ),
    ("mother_brother", {"mother": 1, "brother": 1}, {"mother": "1/3", "brother": "2/3"}),
    ("mother_brothers", {"mother": 1, "brother": 2}, {"mother": "1/6", "brother": "5/6"}),
    (
        "mother_brother_sister",
        {"mother": 1, "brother": 1, "sister": 1},
        {"mother": "1/6", "brother": "5/9", "sister": "5/18"},
    ),
    ("husband_sister", {"husband": 1, "sister": 1}, {"husband": "1/2", "sister": "1/2"}),
    (
        "husband_sisters_awl",
        {"husband": 1, "sister": 2},
        {"husband": "3/7", "sister": "4/7"},
        True,
    ),
    ("wife_sister_radd", {"wife": 1, "sister": 1}, {"wife": "1/4", "sister": "3/4"}),
    (
        "wife_sister_cousin",
        {"wife": 1, "sister": 1, "relatives": 1},
        {"wife": "1/4", "sister": "1/2", "relatives": "1/4"},
    ),
    ("mother_sister_radd", {"mother": 1, "sister": 1}, {"mother": "2/5", "sister": "3/5"}),
    (
        "mother_sister_cousin",
        {"mother": 1, "sister": 1, "relatives": 1},
        {"mother": "1/3", "sister": "1/2", "relatives": "1/6"},
    ),
    (
        "wife_mother_sister_awl",
        {"wife": 1, "mother": 1, "sister": 1},
        {"wife": "3/13", "mother": "4/13", "sister": "6/13"},
        True,
    ),
    ("daughter_sister_asabah", {"daughter": 1, "sister": 1}, {"daughter": "1/2", "sister": "1/2"}),
    ("daughters_sister_asabah", {"daughter": 2, "sister": 1}, {"daughter": "2/3", "sister": "1/3"}),
    (
        "daughter_brother_sister_asabah",
        {"daughter": 1, "brother": 1, "sister": 1},
        {"daughter": "1/2", "brother": "1/3", "sister": "1/6"},
    ),
    (
        "wife_daughters_brother_sister",
        {"wife": 1, "daughter": 2, "brother": 1, "sister": 1},
        {"wife": "1/8", "daughter": "2/3", "brother": "5/36", "sister": "5/72"},
    ),
    ("father_blocks_brother", {"father": 1, "brother": 1}, {"father": "1", "brother": "0"}),
    (
        "son_blocks_brother_and_cousin",
        {"son": 1, "brother": 1, "relatives": 1},
        {"son": "1", "brother": "0", "relatives": "0"},
    ),
    ("brother_blocks_cousin", {"brother": 1, "relatives": 1}, {"brother": "1", "relatives": "0"}),
    ("daughter_cousin", {"daughter": 1, "relatives": 1}, {"daughter": "1/2", "relatives": "1/2"}),
    (
        "daughter_sister_blocks_cousin",
        {"daughter": 1, "sister": 1, "relatives": 1},
        {"daughter": "1/2", "sister": "1/2", "relatives": "0"},
    ),
    (
        "husband_sisters_cousin_awl",
        {"husband": 1, "sister": 2, "relatives": 1},
        {"husband": "3/7", "sister": "4/7", "relatives": "0"},
        True,
    ),
    (
        "wife_mother_sister_cousin_awl",
        {"wife": 1, "mother": 1, "sister": 1, "relatives": 1},
        {"wife": "3/13", "mother": "4/13", "sister": "6/13", "relatives": "0"},
        True,
    ),
    (
        "husband_father_daughter_mother_awl",
        {"husband": 1, "father": 1, "daughter": 1, "mother": 1},
        {"husband": "3/13", "daughter": "6/13", "father": "2/13", "mother": "2/13"},
        True,
    ),
    (
        "wife_father_daughter_mother_no_awl",
        {"wife": 1, "father": 1, "daughter": 1, "mother": 1},
        {"wife": "1/8", "daughter": "1/2", "father": "5/24", "mother": "1/6"},
    ),
)


def expected_result(heirs, expected_shares, estate=24):
    result = {}
    for key in OUTPUT_KEYS:
        share = F(expected_shares.get(key, 0))
        count = int(heirs[key])
        amount = float(share * estate) / count if count else 0
        result[key] = f"{display_fraction_in_unicode(share)}: {count} x {amount:.2f}"
    return result


class FiqhLocalTest(unittest.TestCase):
    def setUp(self):
        self.fiqh = Fiqh()
        self.fiqh.initialize()

    def test_website_derived_calculation_paths(self):
        for case_data in WEBSITE_DERIVED_CASES:
            name, heirs_kwargs, expected_shares, *optional_awl = case_data
            expected_awl = optional_awl[0] if optional_awl else False
            heirs = Heirs(**heirs_kwargs)

            with self.subTest(name=name):
                result, awl_applied = self.fiqh.run(heirs)

                self.assertEqual(expected_awl, awl_applied)
                self.assertEqual(expected_result(heirs, expected_shares), result)

    def test_no_relatives_matches_legacy_dummy_result(self):
        result, awl_applied = self.fiqh.run(Heirs())

        self.assertFalse(awl_applied)
        self.assertEqual({h: f"{display_fraction_in_unicode(F(0, 1))} ≡ 0" for h in HeirsOrderInHtml}, result)

    def test_public_compatibility_helpers(self):
        heirs = Heirs(wife=1, son=2, daughter=1, father=1, mother=1, brother=3, sister=4, relatives=1)
        fields = self.fiqh.heirs_to_input_fields(heirs)
        inflated = self.fiqh.inflate(fields, self.fiqh.relative_details)

        self.assertEqual(
            {
                "husband": 0,
                "wives": 1,
                "sons": 2,
                "daughters": 1,
                "father": 1,
                "mother": 1,
                "full_brothers": 3,
                "full_sisters": 4,
                "full_cousins": 1,
            },
            fields,
        )
        self.assertEqual(
            {"tb1": "0", "tb2": "1", "tb3": "2", "tb4": "1", "tb7": "1", "tb8": "1", "tb12": "3", "tb13": "4", "tb24": "1"},
            inflated,
        )

    def test_send_request_and_parse_response_compatibility(self):
        heirs = Heirs(husband=1, sister=2)
        fields = self.fiqh.inflate(self.fiqh.heirs_to_input_fields(heirs), self.fiqh.relative_details)
        response = self.fiqh.send_request(None, fields)
        parsed = self.fiqh.parse_response(response)
        result = self.fiqh.fiqh_fields_to_dict(parsed, heirs, estate=24)

        self.assertIn("shares have exceeded 100%", response.text)
        self.assertEqual(expected_result(heirs, {"husband": "3/7", "sister": "4/7"}), result)

    @unittest.skipUnless(os.environ.get("FIQH_LIVE_WEBSITE_TESTS") == "1", "set FIQH_LIVE_WEBSITE_TESTS=1 to compare against the live website")
    def test_live_website_parity_for_all_snapshot_cases(self):
        from fiqh import Fiqh as WebsiteFiqh

        website_fiqh = WebsiteFiqh()
        website_fiqh.initialize()

        for case_data in WEBSITE_DERIVED_CASES:
            name, heirs_kwargs, _expected_shares, *_optional_awl = case_data
            heirs = Heirs(**heirs_kwargs)

            with self.subTest(name=name):
                self.assertEqual(website_fiqh.run(heirs), self.fiqh.run(heirs))


if __name__ == "__main__":
    unittest.main()
