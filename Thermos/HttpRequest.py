class HttpRequest:

    def __init__(self, request_content: bytes):
        content_str = request_content.decode()

        self._start_line = content_str.split('\n')[0]
        self._method, self._query, self._version = self._start_line.split(' ')

        self._extract_params_path()

        self._headers = self._extract_headers(content_str)
        self._body = content_str.split('\r\n\r\n')[1].strip()

    def _extract_params_path(self) -> None:
        query_split = self._query.split("?")
        self._path = query_split[0]
        self._params = {}

        if len(query_split) != 2:
            return

        for pair in query_split[1].split("&"):
            key_value = pair.split("=")
            if len(key_value) == 2:
                self._params[key_value[0]] = key_value[1]
    
    def _extract_headers(self, content_str: str) -> dict:
        headers = {}
        for line in content_str.split('\n')[1:]:
            if line.strip() == '':
                break
            header_name, header_value = line.split(': ', 1)
            headers[header_name.lower()] = header_value.strip()
        return headers
    
    def __repr__(self):
        headers = "\n".join((f"{key}: {self._headers[key]}" for key in self._headers))
        return f"{self._start_line}\n{headers}\n{self.body}"
    
    @property
    def params(self) -> dict:
        return self._params

    @property
    def path(self) -> str:
        return self._path

    @property
    def headers(self) -> dict:
        return self._headers
    
    @property
    def body(self) -> str:
        return self._body
    
    @property
    def method(self) -> str:
        return self._method