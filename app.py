from Thermos import Thermos

app = Thermos(__name__)

@app.route("/ping")
def pong():
    return "Pong!"

@app.route("/")
def home() -> str:
    print("This is the home function")
    return "Hello World!"

def main() -> None:
    app.run("0.0.0.0", 5001)

if __name__ == "__main__":
    main()