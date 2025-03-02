from Thermos import Thermos

app = Thermos(__name__)

@app.route("/")
def home():
    print("This is the home function")


def main() -> None:
    app.run("0.0.0.0", 5001)

if __name__ == "__main__":
    main()