from werkzeug.routing import BaseConverter

class RegionConverter(BaseConverter):
    regex = r"[A-Z]{2}"

    def to_url(self, value: str) -> str:
        return value.upper()