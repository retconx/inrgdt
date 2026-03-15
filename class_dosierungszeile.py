class Dosierungszeile:
    def __init__(self, inr:float, wochentagdosen:list, halbStatt05:bool):
        self.inr = inr # keine Darstellung = -1
        self.wochentagdosen = wochentagdosen # float-Liste
        self.halbStatt05 = halbStatt05

    