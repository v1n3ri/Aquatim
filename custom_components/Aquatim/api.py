import aiohttp
import logging
import asyncio
import json
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
        self.session_id = None

    async def _get_session(self):
        if self.session is None or self.session.closed:
            browser_headers = {
                "authority": "portal.aquatim.ro",
                "accept": "application/json, text/plain, */*",
                "accept-language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
                "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                "origin": "https://portal.aquatim.ro",
                "referer": "https://portal.aquatim.ro/self_utilities/login.jsp",
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
            await session.get("https://portal.aquatim.ro/self_utilities/login.jsp", timeout=10)
            login_data = {"user": self.email, "password": self.password}
            
            async with session.post(URL_REST_LOGIN, data=login_data, timeout=10) as resp:
                res_data = await resp.json()
                if res_data.get("authSuccessfull") is True:
                    self.session_id = res_data.get("sessionId")
                    _LOGGER.warning("Autentificare reușită! Sesiune: %s", self.session_id)
                    # Activăm sesiunea fără a aștepta un body specific
                    await session.post(URL_INFO_SESSION, json={}, timeout=10)
                    return True
                return False
        except Exception as e:
            _LOGGER.error("Eroare login: %s", e)
            return False

    async def get_data(self):
        if not await self.login():
            return None

        await asyncio.sleep(1)
        session = await self._get_session()
        
        try:
            # IMPORTANT: Nu mai folosim resp.json() direct pentru a evita crash-ul la linia 75
            async with session.get(URL_LISTA_CONTRACTE, timeout=10) as resp:
                raw_text = await resp.text()
                _LOGGER.warning("Răspuns brut server (Status %s): %s", resp.status, raw_text)

                if not raw_text or resp.status != 200:
                    return None

                try:
                    data = json.loads(raw_text)
                except Exception as json_err:
                    _LOGGER.error("Serverul nu a trimis JSON valid: %s", json_err)
                    return None
                
                contracte = data if isinstance(data, list) else data.get("lista", [])

                if contracte and len(contracte) > 0:
                    c = contracte[0]
                    return {
                        "cod_client": str(c.get("codClient", "N/A")),
                        "nr_contract": str(c.get("nr_contract", c.get("nrContract", "N/A"))),
                        "nume": c.get("denClient", "N/A"),
                        "adresa": c.get("adrClient", "N/A"),
                        "stare": c.get("stareContract", "N/A"),
                        "sold": 0
                    }
                
                _LOGGER.warning("Lista de contracte este goală în JSON.")
                return None

        except Exception as e:
            _LOGGER.error("Eroare critică în get_data: %s", e)
            return None