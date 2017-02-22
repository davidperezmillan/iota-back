
class temporadas:
    id=0
    serie=''
    season=0
    episode=0
    title = ''
    status=False
    
    
    
    def __repr__(self):
        return "<Test id:%d serie:%s season:%d episoide:%d title:%s status:%r>" % (self.id, self.serie, self.season, self.episode, self.title, self.status)

    def __str__(self):
        return "From str method of Test:id:%d serie:%s, season:%d, episoide:%d, title:%s, status:%r" % (self.id, self.serie, self.season, self.episode, self.title, self.status)
    
    
