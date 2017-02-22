class enlaces:
    id=0
    episode=0
    type=0
    link=""
    
    
    def __repr__(self):
        return "<Test id:%d episoide:%d type:%d link:%s>" % (self.id,  self.episode, self.type, self.link)

    def __str__(self):
        return "From str method of Test:id:%d, episoide:%d, title:%s, status:%r"  % (self.id, self.episode, self.type, self.link)
