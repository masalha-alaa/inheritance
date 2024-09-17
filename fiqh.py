import mechanize
import pandas as pd
from bs4 import BeautifulSoup as bs
from pandas import read_html
from io import StringIO
import yaml
from heirs import Heirs
from my_utils import display_fraction_in_unicode, F, HeirsOrderInHtml


class Fiqh:
    def __init__(self):
        self.br = None
        self.relative_details = None

    def initialize(self):
        url = "http://inheritance.ilmsummit.org//projects/inheritance/home.aspx"
        br = mechanize.Browser()
        # Set the user-agent as Mozilla - if the page knows we're Mechanize, it won't return all fields
        br.addheaders = [('User-agent',
                          'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
        # br.addheaders = [('User-agent',
        #                   'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36')]
        br.open(url)
        self.br = br

        config_filename = "fiqh_config.yml"
        config = yaml.safe_load(open(config_filename))
        self.relative_details = config['relative_details']

    def run(self, heirs: Heirs, estate=24):
        dummy = {h: f"{display_fraction_in_unicode(F(0, 1))} ≡ 0" for h in HeirsOrderInHtml}
        input_fields = self.heirs_to_input_fields(heirs)
        form_fields = self.inflate(input_fields, self.relative_details)
        response = self.send_request(self.br, form_fields)
        self.br.back()
        if response is None:
            return dict(), False
        awl_applied = "shares have exceeded 100%" in response.text.lower()
        try:
            df = self.parse_response(response)
            final_results = self.fiqh_fields_to_dict(df, estate=estate)
        except ValueError:
            final_results = dummy
        return final_results if final_results else dummy, awl_applied

    def heirs_to_input_fields(self, heirs: Heirs):
        return {'husband': int(heirs.husband), 'wives': int(heirs.wife), 'sons': heirs.son, 'daughters': heirs.daughter, 'father': int(heirs.father), 'mother': int(heirs.mother), 'full_brothers': heirs.brother, 'full_sisters': heirs.sister, 'full_cousins': heirs.relatives}

    def inflate(self, combination_d, relative_details):
        inflated = {}
        for k, v in combination_d.items():
            inflated[relative_details[k]['id']] = str(v)
        return inflated

    def send_request(self, br, form_fields_dict):
        br.select_form(name='form1')
        br.form.set_all_readonly(False)
        # set the relevant ASP.NET fields, as required in the page's onSubmit function
        # Your .aspx page may not have these
        # Luckily we can ignore the __VIEWSTATE variable: mechanize handles this for us.
        try:
            for k, v in form_fields_dict.items():
                br[k] = v
        except mechanize.ControlNotFoundError as e:
            print(f"ControlNotFoundError: {e}")
            return None
        br.submit()
        response = bs(br.response().read(), features="lxml")
        return response

    def parse_response(self, response):
        shares_table = response.find("table", id="dgSharesCtg")
        df = read_html(StringIO(str(shares_table)))[0]
        df.columns = df.iloc[0]
        df.drop(0, inplace=True)
        df.reset_index(drop=True, inplace=True)
        df['Share Percentage'] = df['Share Percentage'].apply(self._eval_percentage)
        return df

    def _eval_percentage(self, percentage):
        return round(float(percentage.replace("%", "")) / 100, 4)

    def fiqh_fields_to_dict(self, fiqh_fields: pd.DataFrame, estate):
        fiqh_fields.set_index("Relative Category", inplace=True)
        shares_d = dict()
        shares_d['husband'] = F(0, 1)
        shares_d['wife'] = F(0, 1)
        shares_d['son'] = F(0, 1)
        shares_d['daughter'] = F(0, 1)
        shares_d['father'] = F(0, 1)
        shares_d['mother'] = F(0, 1)
        shares_d['brother'] = F(0, 1)
        shares_d['sister'] = F(0, 1)
        shares_d['relatives'] = F(0, 1)
        if 'Husband' in fiqh_fields.index:
            shares_d['husband'] = F(fiqh_fields.loc['Husband', 'Share Fraction'])
        if 'Wife' in fiqh_fields.index:
            shares_d['wife'] = F(fiqh_fields.loc['Wife', 'Share Fraction'])
        if 'Son' in fiqh_fields.index:
            shares_d['son'] = F(fiqh_fields.loc['Son', 'Share Fraction'])
        if 'Daughter' in fiqh_fields.index:
            shares_d['daughter'] = F(fiqh_fields.loc['Daughter', 'Share Fraction'])
        if 'Father' in fiqh_fields.index:
            shares_d['father'] = F(fiqh_fields.loc['Father', 'Share Fraction'])
        if 'Mother' in fiqh_fields.index:
            shares_d['mother'] = F(fiqh_fields.loc['Mother', 'Share Fraction'])
        if 'FullBrother' in fiqh_fields.index:
            shares_d['brother'] = F(fiqh_fields.loc['FullBrother', 'Share Fraction'])
        if 'FullSister' in fiqh_fields.index:
            shares_d['sister'] = F(fiqh_fields.loc['FullSister', 'Share Fraction'])
        if 'FullCousin' in fiqh_fields.index:
            shares_d['relatives'] = F(fiqh_fields.loc['FullCousin', 'Share Fraction'])

        shares_d = {k: f"{display_fraction_in_unicode(v)} ≡ {float(v * estate):.2f}"
                    for k, v in shares_d.items()}
        return shares_d


if __name__ == '__main__':
    from pprint import pprint
    fiqh = Fiqh()
    fiqh.initialize()
    # heirs = Heirs(wife=True, son=1, daughter=1, brother=1, sister=1, father=True, mother=True, relatives=1)
    heirs = Heirs(wife=True, daughter=2, father=True, mother=True)
    # heirs = Heirs(husband=True, son=2)
    shares, awl_applied = fiqh.run(heirs)
    pprint(shares, sort_dicts=False)
    print(f"{awl_applied = }")
