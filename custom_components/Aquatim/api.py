import aiohttp
import logging
import asyncio
from .const import HEADERS

_LOGGER = logging.getLogger(__name__)

URL_REST_LOGIN = "https://portal.aquatim.ro/self_utilities/rest/admcl/login"
URL_INFO_SESSION = "https://portal.aquatim.ro/self_utilities/rest/self/infoSession"
URL_LISTA_CONTRACTE = "https://portal.aquatim.ro/self_utilities/rest/self/admcl/getListaContracte"

class AquatimAPI:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.session = None

    async def _get_session(self):
        if self.session is None or self.session.closed:
            # Recreăm setul de headere exact cum l-ai trimis tu din browser
            browser_headers = {
                "authority": "portal.aquatim.ro",
                "accept": "application/json, text/javascript, */*; q=0.01",
                "accept-language": "en-US,en;q=0.9,ro-RO;q=0.8,ro;q=0.7",
                "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                "origin": "https://portal.aquatim.ro",
                "referer": "https://portal.aquatim.ro/self_utilities/login.jsp",
                "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
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
            # Cloudflare are nevoie de o vizită inițială pentru a seta cookie-urile de bază
            async with session.get("https://portal.aquatim.ro/self_utilities/login.jsp") as resp:
                await resp.text()

            login_data = {
                "user": self.email,
                "password": self.password 
            }
            
            _LOGGER.warning("Trimitere Login către Cloudflare/Aquatim...")
            
            async with session.post(URL_REST_LOGIN, data=login_data) as resp:
                res_text = await resp.text()
                _LOGGER.warning("Răspuns Login (Status %s): %s", resp.status, res_text)
                
                # Cloudflare poate returna 403 dacă ne detectează
                if resp.status == 403:
                    _LOGGER.error("Acces blocat de Cloudflare. Integrarea nu poate trece de protecție.")
                    return False
                
                if resp.status != 200:
                    return False

            # Pasul 2: InfoSession
            async with session.post(URL_INFO_SESSION, json={}) as resp:
                return resp.status == 200

        except Exception as e:
            _LOGGER.error("Eroare la autentificare: %s", e)
            return False

    async def get_data(self):
        if not await self.login():
            return None

        await asyncio.sleep(1)
        session = await self._get_session()
        
        try:
            async with session.get(URL_LISTA_CONTRACTE) as resp:
                data = await resp.json()
                if isinstance(data, list) and len(data) > 0:
                    c = data[0]
                    return {
                        "cod_client": str(c.get("codClient", "N/A")),
                        "nr_contract": str(c.get("nrContract", "N/A")),
                        "nume": c.get("denClient", "N/A"),
                        "adresa": c.get("adrClient", "N/A"),
                        "stare": c.get("stareContract", "N/A")
                    }
            return None
        except Exception as e:
            _LOGGER.error("Eroare preluare date: %s", e)
            return None