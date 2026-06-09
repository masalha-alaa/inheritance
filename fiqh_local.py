from fractions import Fraction
from io import StringIO
from pathlib import Path

import pandas as pd
import yaml
from bs4 import BeautifulSoup as bs
from pandas import read_html

from heirs import Heirs
from my_utils import F, HeirsOrderInHtml, display_fraction_in_unicode


class Fiqh:
    def __init__(self):
        self.br = None
        self.relative_details = None

    def initialize(self):
        config_filename = Path(__file__).with_name("fiqh_config.yml")
        config = yaml.safe_load(config_filename.read_text())
        self.relative_details = config["relative_details"]

    def run(self, heirs: Heirs, estate=24):
        dummy = self._dummy_results()
        if not self._has_supported_input(heirs):
            return dummy, False

        shares, awl_applied = self._calculate_shares(heirs)
        df = self._shares_to_fiqh_fields(shares, heirs)
        try:
            final_results = self.fiqh_fields_to_dict(df, heirs, estate=estate)
        except ValueError:
            final_results = dummy
        return final_results if final_results else dummy, awl_applied

    def heirs_to_input_fields(self, heirs: Heirs):
        return {
            "husband": int(heirs.husband),
            "wives": int(heirs.wife),
            "sons": heirs.son,
            "daughters": heirs.daughter,
            "father": int(heirs.father),
            "mother": int(heirs.mother),
            "full_brothers": heirs.brother,
            "full_sisters": heirs.sister,
            "full_cousins": heirs.relatives,
        }

    def inflate(self, combination_d, relative_details):
        inflated = {}
        for k, v in combination_d.items():
            inflated[relative_details[k]["id"]] = str(v)
        return inflated

    def send_request(self, br, form_fields_dict):
        heirs = self._form_fields_to_heirs(form_fields_dict)
        if not self._has_supported_input(heirs):
            return bs("<html><body>No relatives entered.</body></html>", features="lxml")

        shares, awl_applied = self._calculate_shares(heirs)
        return self._shares_to_response(shares, heirs, awl_applied)

    def parse_response(self, response):
        shares_table = response.find("table", id="dgSharesCtg")
        df = read_html(StringIO(str(shares_table)))[0]
        df.columns = df.iloc[0]
        df.drop(0, inplace=True)
        df.reset_index(drop=True, inplace=True)
        df["Share Percentage"] = df["Share Percentage"].apply(self._eval_percentage)
        return df

    def _eval_percentage(self, percentage):
        return round(float(percentage.replace("%", "")) / 100, 4)

    def fiqh_fields_to_dict(self, fiqh_fields: pd.DataFrame, heirs: Heirs, estate):
        def get_share_per_capital(heirs_num, total_share_for_heirs):
            if heirs_num:
                return float(total_share_for_heirs * estate) / heirs_num
            return 0

        fiqh_fields.set_index("Relative Category", inplace=True)
        shares_d = self._zero_shares()
        if "Husband" in fiqh_fields.index:
            shares_d["husband"] = F(fiqh_fields.loc["Husband", "Share Fraction"])
        if "Wife" in fiqh_fields.index:
            shares_d["wife"] = F(fiqh_fields.loc["Wife", "Share Fraction"])
        if "Son" in fiqh_fields.index:
            shares_d["son"] = F(fiqh_fields.loc["Son", "Share Fraction"])
        if "Daughter" in fiqh_fields.index:
            shares_d["daughter"] = F(fiqh_fields.loc["Daughter", "Share Fraction"])
        if "Father" in fiqh_fields.index:
            shares_d["father"] = F(fiqh_fields.loc["Father", "Share Fraction"])
        if "Mother" in fiqh_fields.index:
            shares_d["mother"] = F(fiqh_fields.loc["Mother", "Share Fraction"])
        if "FullBrother" in fiqh_fields.index:
            shares_d["brother"] = F(fiqh_fields.loc["FullBrother", "Share Fraction"])
        if "FullSister" in fiqh_fields.index:
            shares_d["sister"] = F(fiqh_fields.loc["FullSister", "Share Fraction"])
        if "FullCousin" in fiqh_fields.index:
            shares_d["relatives"] = F(fiqh_fields.loc["FullCousin", "Share Fraction"])

        for k, v in shares_d.items():
            shares_d[k] = f"{display_fraction_in_unicode(v)}: {int(heirs[k])} x {get_share_per_capital(int(heirs[k]), v):.2f}"
        return shares_d

    def _calculate_shares(self, heirs: Heirs):
        shares = self._zero_shares()
        fixed = self._fixed_shares(heirs)
        shares.update(fixed)

        fixed_total = sum(fixed.values(), Fraction(0, 1))
        if fixed_total > 1:
            return self._apply_awl(shares, fixed_total), True

        remaining = Fraction(1, 1) - fixed_total
        if remaining > 0:
            self._apply_residue_or_radd(shares, heirs, remaining)
        return shares, False

    def _fixed_shares(self, heirs: Heirs):
        fixed = {}
        has_children = self._has_children(heirs)

        if heirs.husband:
            fixed["husband"] = Fraction(1, 4) if has_children else Fraction(1, 2)
        if heirs.wife:
            fixed["wife"] = Fraction(1, 8) if has_children else Fraction(1, 4)
        if heirs.mother:
            fixed["mother"] = self._mother_fixed_share(heirs, fixed)
        if heirs.father and has_children:
            fixed["father"] = Fraction(1, 6)
        if heirs.daughter and not heirs.son:
            fixed["daughter"] = Fraction(1, 2) if heirs.daughter == 1 else Fraction(2, 3)
        if self._sisters_have_fixed_share(heirs):
            fixed["sister"] = Fraction(1, 2) if heirs.sister == 1 else Fraction(2, 3)

        return fixed

    def _mother_fixed_share(self, heirs: Heirs, fixed):
        if self._has_children(heirs) or self._has_multiple_siblings(heirs):
            return Fraction(1, 6)
        if heirs.father and self._has_spouse(heirs) and heirs.siblings == 0:
            return (Fraction(1, 1) - fixed[self._spouse_key(heirs)]) * Fraction(1, 3)
        return Fraction(1, 3)

    def _sisters_have_fixed_share(self, heirs: Heirs):
        return (
            heirs.sister > 0
            and heirs.brother == 0
            and heirs.daughter == 0
            and not heirs.son
            and not heirs.father
        )

    def _apply_awl(self, shares, fixed_total):
        return {key: share / fixed_total for key, share in shares.items()}

    def _apply_residue_or_radd(self, shares, heirs: Heirs, remaining):
        if heirs.father and not heirs.son:
            shares["father"] += remaining
        elif heirs.son:
            self._divide_male_female_residue(shares, "son", heirs.son, "daughter", heirs.daughter, remaining)
        elif heirs.brother:
            self._divide_male_female_residue(shares, "brother", heirs.brother, "sister", heirs.sister, remaining)
        elif heirs.sister and heirs.daughter:
            shares["sister"] += remaining
        elif heirs.relatives:
            shares["relatives"] += remaining
        else:
            self._apply_radd(shares, remaining)

    def _divide_male_female_residue(self, shares, male_key, male_count, female_key, female_count, remaining):
        units = male_count * 2 + female_count
        if units == 0:
            return
        shares[male_key] += remaining * Fraction(male_count * 2, units)
        shares[female_key] += remaining * Fraction(female_count, units)

    def _apply_radd(self, shares, remaining):
        radd_keys = [key for key in self._non_spouse_keys() if shares[key] > 0]
        if radd_keys:
            radd_base = sum((shares[key] for key in radd_keys), Fraction(0, 1))
            for key in radd_keys:
                shares[key] += remaining * shares[key] / radd_base
            return

        spouse_keys = [key for key in ("husband", "wife") if shares[key] > 0]
        for key in spouse_keys:
            shares[key] += remaining / len(spouse_keys)

    def _shares_to_fiqh_fields(self, shares, heirs: Heirs):
        rows = []
        for key in self._output_keys():
            if int(heirs[key]) or shares[key]:
                rows.append(
                    {
                        "Relative Category": self._relative_category(key),
                        "Share Fraction": self._fraction_to_str(shares[key]),
                        "Share Percentage": round(float(shares[key]), 4),
                    }
                )
        return pd.DataFrame(rows, columns=["Relative Category", "Share Fraction", "Share Percentage"])

    def _shares_to_response(self, shares, heirs: Heirs, awl_applied):
        rows = [
            "<tr><td>Relative Category</td><td>Share Fraction</td><td>Share Percentage</td></tr>"
        ]
        for key in self._output_keys():
            if int(heirs[key]) or shares[key]:
                rows.append(
                    "<tr>"
                    f"<td>{self._relative_category(key)}</td>"
                    f"<td>{self._fraction_to_str(shares[key])}</td>"
                    f"<td>{float(shares[key]) * 100:.2f}%</td>"
                    "</tr>"
                )
        awl_text = "shares have exceeded 100%" if awl_applied else ""
        return bs(f"<html><body>{awl_text}<table id='dgSharesCtg'>{''.join(rows)}</table></body></html>", features="lxml")

    def _form_fields_to_heirs(self, form_fields_dict):
        if self.relative_details is None:
            self.initialize()
        reverse_details = {details["id"]: name for name, details in self.relative_details.items()}
        heirs_kwargs = {
            "husband": 0,
            "wife": 0,
            "son": 0,
            "daughter": 0,
            "father": 0,
            "mother": 0,
            "brother": 0,
            "sister": 0,
            "relatives": 0,
        }
        field_to_heir = {
            "husband": "husband",
            "wives": "wife",
            "sons": "son",
            "daughters": "daughter",
            "father": "father",
            "mother": "mother",
            "full_brothers": "brother",
            "full_sisters": "sister",
            "full_cousins": "relatives",
        }
        for field_id, value in form_fields_dict.items():
            field_name = reverse_details.get(field_id)
            heir_name = field_to_heir.get(field_name)
            if heir_name:
                heirs_kwargs[heir_name] = int(value)
        return Heirs(**heirs_kwargs)

    def _has_supported_input(self, heirs: Heirs):
        if not self._has_any_heirs(heirs):
            return False
        one_or_zero_fields = ("husband", "wife", "father", "mother", "relatives")
        if any(int(heirs[field]) not in (0, 1) for field in one_or_zero_fields):
            return False
        if any(int(heirs[field]) < 0 for field in self._output_keys()):
            return False
        return not (heirs.husband and heirs.wife)

    def _has_any_heirs(self, heirs: Heirs):
        return any(int(heirs[key]) > 0 for key in self._output_keys())

    def _has_children(self, heirs: Heirs):
        return heirs.son > 0 or heirs.daughter > 0

    def _has_multiple_siblings(self, heirs: Heirs):
        return heirs.siblings >= 2

    def _has_spouse(self, heirs: Heirs):
        return bool(heirs.husband or heirs.wife)

    def _spouse_key(self, heirs: Heirs):
        return "husband" if heirs.husband else "wife"

    def _dummy_results(self):
        return {h: f"{display_fraction_in_unicode(F(0, 1))} ≡ 0" for h in HeirsOrderInHtml}

    def _zero_shares(self):
        return {key: Fraction(0, 1) for key in self._output_keys()}

    def _output_keys(self):
        return ("husband", "wife", "son", "daughter", "father", "mother", "brother", "sister", "relatives")

    def _non_spouse_keys(self):
        return ("son", "daughter", "father", "mother", "brother", "sister", "relatives")

    def _relative_category(self, key):
        return {
            "husband": "Husband",
            "wife": "Wife",
            "son": "Son",
            "daughter": "Daughter",
            "father": "Father",
            "mother": "Mother",
            "brother": "FullBrother",
            "sister": "FullSister",
            "relatives": "FullCousin",
        }[key]

    def _fraction_to_str(self, fraction):
        return f"{fraction.numerator}/{fraction.denominator}"


if __name__ == "__main__":
    from pprint import pprint

    fiqh = Fiqh()
    fiqh.initialize()
    heirs = Heirs(mother=True, brother=1)
    shares, awl_applied = fiqh.run(heirs)
    pprint(shares, sort_dicts=False)
    print(f"{awl_applied = }")
