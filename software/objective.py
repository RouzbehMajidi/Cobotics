import uuid
from context import Context

GRAVITY = 9.81

class Objective:
    def __init__(self, x_width, y_width, z_width):
        self.id = "objective-" + str(uuid.uuid4())[:6]
        self.x_width = x_width
        self.y_width = y_width
        self.z_width = z_width
        self.DENSITY = Context.DENSITY
        self.is_heavier = False
        self.COF = Context.CoF
        self.print_info()

    def get_volume(self):
        return self.x_width*self.y_width*self.z_width
        
    def get_weight(self):
        return self.get_volume() * self.DENSITY
    
    def get_force_required(self):
        return self.get_weight()/1000 * GRAVITY * self.COF

    def print_info(self):
            print(self.id)
            print("\t Dimensions:", self.x_width, "cm x", self.y_width, "cm x", self.z_width, "cm")
            print("\t Volume:", self.get_volume(), "cm³")
            print("\t Density:", self.DENSITY, "g/cm²")
            print("\t Coefficient of Friction:", self.COF)
            print("\t Weight:", self.get_weight(), "g")
            print("\t Push force required:", self.get_force_required(), "N")

if __name__ == "__main__":
    Context.load()
    small_objective = Objective(6,6,6)
    medium_objective = Objective(12,12,12)
    large2_objective = Objective(12.7,12.7,12.7)
    Context.DENSITY = 0.5
    large_objective = Objective(12,12,12)

