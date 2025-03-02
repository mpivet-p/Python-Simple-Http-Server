class HttpResponse:
    def __init__(self, status_code: int, message: str, headers: dict = {}, body: str = None) -> None:
        self._status_code = status_code
        self._message = message
        self._headers = headers
        if body:
            self.body = body
        else:
            self._body = ""

    def add_header(self, key: str, value: str):
        self._headers[key] = value

    def _get_headers(self) -> str:
        result = ""
        for key in self._headers:
            result += f"{key}: {self._headers[key]}\r\n"
        return result

    @property
    def body(self) -> str:
        return self._body
    
    @body.setter
    def body(self, body: str) -> None:
        self._body = body
        self._headers["Content-Length"] = str(len(self._body))

    def __repr__(self) -> str:
        return f"HTTP/1.1 {self._status_code} {self._message}\r\n{self._get_headers()}\r\n{self._body}"

    # If content is not None, need to add Content-Length header
    def to_bytes(self) -> bytes:
        return bytes(f"HTTP/1.1 {self._status_code} {self._message}\r\n{self._get_headers()}\r\n{self._body}", "utf-8")