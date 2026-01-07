import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class NessusAPI:
    def __init__(self, url, access_key, secret_key):
        self.url = url.rstrip('/')
        self.headers = {
            'X-ApiKeys': f'accessKey={access_key}; secretKey={secret_key}',
            'Content-Type': 'application/json'
        }

    def get_scans(self):
        try:
            response = requests.get(f"{self.url}/scans", headers=self.headers, verify=False, timeout=5)
            return response.json()
        except Exception as e:
            return {"error": str(e), "scans": []}