"""## Heirs"""


class Heirs:
    def __init__(self, husband:bool=False, wife:bool=False, son:int=0, daughter:int=0, brother:int=0, sister:int=0, father:bool=False, mother:bool=False, relatives:int=0):
        self.husband = husband
        self.wife = wife
        self.son = son
        self.daughter = daughter
        self.brother = brother
        self.sister = sister
        self.father = father
        self.mother = mother
        self.relatives = relatives
        assert not (husband and wife), "Husband and wife cannot co-exist"

    @property
    def siblings(self):
        return self.brother + self.sister

    def is_multi_siblings(self):
        # TODO: i think (siblings > 2) is wrong, and should be (brother > 0 and sister > 0)
        # TODO: Also why > 1 and not > 0?
        return self.sister > 1 or self.brother > 1 or (self.siblings > 2)

    @property
    def children(self):
        return self.son + self.daughter

    @property
    def spouse(self) -> bool:
        return self.husband or self.wife

    @property
    def adults(self):
        return self.husband + self.wife + self.father + self.mother

    @property
    def parents(self) -> bool:
        return self.father or self.mother

    def __repr__(self):
        return f"husband: {self.husband}, wife: {self.wife}, son: {self.son}, daughter: {self.daughter}, brother: {self.brother}, sister: {self.sister}, father: {self.father}, mother: {self.mother}, relatives: {self.relatives}"