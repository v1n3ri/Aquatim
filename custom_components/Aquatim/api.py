import aiohttp
import logging
import asyncio
from .const import HEADERS

_LOGGER = logging.getLogger(__name__)

# Endpoint-urile confirmate din payload-ul de browser și Component-preload.js
URL_REST_LOGIN = "https://portal.aquatim.ro/self_utilities/rest/admcl/login"
URL_INFO_SESSION = "https://portal.aquatim.ro/self_utilities/rest/self/infoSession"
URL_LISTA_CONTRACTE = "https://portal.aquatim.ro/self_utilities/rest/self/admcl/getListaContracte"

class AquatimAPI:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.session = None
        self.session_id = None

    async def _get_session(self):
        if self.session is None or self.session.closed:
            # Headerele care imită exact browserul tău pentru a trece de Cloudflare
            browser_headers = {
                "authority": "portal.aquatim.ro",
                "accept": "application/json, text/javascript, */*; q=0.01",
                "accept-language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
                "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                "origin": "https://portal.aquatim.ro",
                "referer": "https://portal.aquatim.ro/self_utilities/login.jsp",
                "sec-ch-ua-platform": '"Windows"',
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
                "x-requested-with": "XMLHttpRequest",
            }
            self.session = aiohttp.ClientSession(
                headers=browser_headers,
                cookie_jar=aiohttp.CookieJar(unsafe=True)
            )
        return self.session

    async def login(self):
        session = await self._get_session()
        try:
            # Pasul 1: Login (folosind exact payload-ul văzut de tine în browser)
            login_data = {
                "user": self.email,
                "password": self.password 
            }
            
            async with session.post(URL_REST_LOGIN, data=login_data) as resp:
                if resp.status != 200:
                    _LOGGER.error("Eroare server la login: %s", resp.status)
                    return False
                    
                res_data = await resp.json()
                if res_data.get("authSuccessfull") is True:
                    self.session_id = res_data.get("sessionId")
                    _LOGGER.warning("Autentificare reușită! Sesiune: %s", self.session_id)
                    
                    # Pasul 2: Activare context sesiune (POST infoSession conform JS)
                    await session.post(URL_INFO_SESSION, json={})
                    return True
                
                _LOGGER.error("Login respins: %s", res_data.get("errMessage"))
                return False

        except Exception as e:
            _LOGGER.error("Eroare la procesul de login: %s", e)
            return False

    async def get_data(self):
        if not await self.login():
            return None

        # Mică pauză pentru ca serverul să proceseze sesiunea
        await asyncio