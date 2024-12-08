class FraudulentId:
    def __init__(self, id):
        self.id = id
    
    def __str__(self):
        return f"F{self.id}"
    
    def __add__(self, other):
        return self.id + other
    
    def __iadd__(self, other):
        self.id += other
        return self