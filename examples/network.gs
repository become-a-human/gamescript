# --header
@load "curl"

class HTTP(System):
    def fetch(self, url: str):
        self.response = http_get(url)
