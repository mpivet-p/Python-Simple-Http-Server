from Thermos import Thermos, HttpResponse
import time

app = Thermos(__name__)

@app.route("/test")
def test() -> HttpResponse:
    for i in range(500000000):
        pass
    return HttpResponse(201, "OK", {}, ".")

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