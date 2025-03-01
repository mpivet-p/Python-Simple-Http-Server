SUPPORTED_HTTP = ["HTTP/1.0", "HTTP/1.1"]
SUPPORTED_METHODS = ["GET"]

class HttpRequest:

    def __init__(self, request_content: bytes):
        content_str = request_content.decode()

        self._start_line = content_str.split('\n')[0]
        self._method, self._path, self._version = self._start_line.split(' ')
        self._headers = self._extract_headers(content_str)
        self._body = content_str.split('\r\n\r\n')[1].strip()
    
    def _extract_headers(self, content_str: str) -> dict:
        headers = {}
        for line in content_str.split('\n')[1:]:
            if line.strip() == '':
                break
            header_name, header_value = line.split(': ', 1)
            headers[header_name.lower()] = header_value.strip()
        return headers
    
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

    @staticmethod
    def is_version_supported(data: bytes) -> bool:
        try:
            str_content = data.decode()
            request_line = str_content.split("\r\n", 1)[0]
            http_vers = request_line.split(" ")[2]

            return http_vers in SUPPORTED_HTTP
        except AttributeError:
            return False
        except UnicodeDecodeError:
            return False

    @staticmethod
    def is_http_request_complete(data: bytes) -> bool:
        header_end: int = data.find(b"\r\n\r\n")
        return header_end != -1
        
    @staticmethod
    def is_tls_handshake(data: bytes) -> bool:
        return data[0] == 22