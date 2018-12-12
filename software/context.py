STORAGE_FILE = "software/data/memory.conf"
READ = "r"
WRITE = "w"

class Context:
    DENSITY = 0.4
    CoF = 0.4
    
    @staticmethod
    def save():
        with open(STORAGE_FILE, WRITE) as data:
            data.write(str(Context.DENSITY) + "\n")
            data.write(str(Context.CoF) + "\n")
        
        print("Context Saved.")
        print("\tDensity:", Context.DENSITY, "g/cm^3")
        print("\tCoF:", Context.CoF)

    @staticmethod
    def load():
        with open(STORAGE_FILE, READ) as data:
            Context.DENSITY = float(data.readline())
            Context.CoF = float(data.readline())

        print("Context Loaded.")
        print("\tDensity:", Context.DENSITY, "g/cm^3")
        print("\tCoF:", Context.CoF)
    
    @staticmethod
    def reset():
        with open(STORAGE_FILE, WRITE) as data:
            data.write(str(0.3) + "\n")
            data.write(str(0.4) + "\n")

if __name__ == "__main__":
    Context.save()
    Context.load()
    print(Context.DENSITY)
    Context.reset()

