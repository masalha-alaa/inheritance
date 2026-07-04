from __future__ import annotations

from fractions import Fraction

from heirs import Heirs
from my_utils import F, HeirsOrderInHtml, display_fraction_in_unicode


class Fiqh:
    def run(self, heirs: Heirs, estate=24):
        dummy = self._dummy_results()
        if not self._has_supported_input(heirs):
            return dummy, False

        shares, awl_applied = self._calculate_shares(heirs)
        fiqh_fields = self._shares_to_fiqh_fields(shares, heirs)
        try:
            final_results = self.fiqh_fields_to_dict(fiqh_fields, heirs, estate=estate)
        except ValueError:
            final_results = dummy
        return final_results if final_results else dummy, awl_applied

    def fiqh_fields_to_dict(self, fiqh_fields, heirs: Heirs, estate):
        def get_share_per_capital(heirs_num, total_share_for_heirs):
            if heirs_num:
                return float(total_share_for_heirs * estate) / heirs_num
            return 0

        fiqh_fields = self._fiqh_fields_by_category(fiqh_fields)
        shares_d = self._zero_shares()
        if "Husband" in fiqh_fields:
            shares_d["husband"] = F(fiqh_fields["Husband"]["Share Fraction"])
        if "Wife" in fiqh_fields:
            shares_d["wife"] = F(fiqh_fields["Wife"]["Share Fraction"])
        if "Son" in fiqh_fields:
            shares_d["son"] = F(fiqh_fields["Son"]["Share Fraction"])
        if "Daughter" in fiqh_fields:
            shares_d["daughter"] = F(fiqh_fields["Daughter"]["Share Fraction"])
        if "Father" in fiqh_fields:
            shares_d["father"] = F(fiqh_fields["Father"]["Share Fraction"])
        if "Mother" in fiqh_fields:
            shares_d["mother"] = F(fiqh_fields["Mother"]["Share Fraction"])
        if "FullBrother" in fiqh_fields:
            shares_d["brother"] = F(fiqh_fields["FullBrother"]["Share Fraction"])
        if "FullSister" in fiqh_fields:
            shares_d["sister"] = F(fiqh_fields["FullSister"]["Share Fraction"])
        if "FullCousin" in fiqh_fields:
            shares_d["relatives"] = F(fiqh_fields["FullCousin"]["Share Fraction"])

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
        return rows

    def _fiqh_fields_by_category(self, fiqh_fields):
        return {row["Relative Category"]: row for row in fiqh_fields}

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
    heirs = Heirs(mother=True, brother=1)
    shares, awl_applied = fiqh.run(heirs)
    pprint(shares, sort_dicts=False)
    print(f"{awl_applied = }")
