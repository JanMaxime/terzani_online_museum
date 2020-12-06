class Terzani_Photo(object):
    def __init__(self, iiif, country):
        self.iiif = iiif
        self.country = country

    def get_photo_link(self):
        return self.iiif["images"][0]["resource"]["@id"]
