import aiohttp
import logging
import asyncio
import json

_LOGGER = logging.getLogger(__name__)

URL_BASE = "https://portal.aquatim.ro/self_utilities/"
URL_REST_LOGIN = f"{URL_BASE}rest/admcl/login"
URL_INFO_SESSION = f"{URL_BASE}rest/self/infoSession"
URL_LISTA_CONTRACTE = f"{URL_BASE}rest/self/admcl/getListaContracte"

class AquatimAPI:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.session = None
        self.gsid = None

    async def _get_session(self):
        if self.session is None or self.session.closed:
            # Folosim headerele de bază din browser-ul tău
            self.session = aiohttp.ClientSession(
                cookie_jar=aiohttp.CookieJar(unsafe=True),
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
                    "Accept-Language": "en-US,en;q=0.9,ro-RO;q=0.8,ro;q=0.7",
                    "X-Requested-With": "XMLHttpRequest"
                }
            )
        return self.session

    async def login(self):
        session = await self._get_session()
        try:
            # 1. Login (folosind password, nu pass)
            login_data = {"user": self.email, "password": self.password}
            async with session.post(URL_REST_LOGIN, data=login_data, headers={"Referer": f"{URL_BASE}login.jsp"}) as resp:
                res_data = await resp.json()
                if res_data.get("authSuccessfull") is True:
                    # GSID este cheia succesului (self_gsid în browser)
                    self.gsid = res_data.get("sessionId")
                    _LOGGER.warning("Autentificare reușită. GSID generat.")
                    
                    # 2. Activare sesiune
                    await session.post(URL_INFO_SESSION, json={}, headers={"Referer": f"{URL_BASE}oui/cl/index.html"})
                    return True
                return False
        except Exception as e:
            _LOGGER.error("Eroare la login: %s", e)
            return False

    async def get_data(self):
        if not await self.login():
            return None

        await asyncio.sleep(1)
        session = await self._get_session()
        
        try:
            # Implementăm exact headerele găsite de tine în Chrome
            data_headers = {
                "accept": "*/*",
                "oui_req": "true", # Header-ul magic identificat
                "self_gsid": str(self.gsid), # ID-ul de sesiune cu numele corect
                "referer": f"{URL_BASE}oui/cl/index.html",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin"
            }

            async with session.get(URL_LISTA_CONTRACTE, headers=data_headers, timeout=15) as resp:
                raw_text = await resp.text()
                _LOGGER.warning("Status: %s | Răspuns: %s", resp.status, raw_text)

                if resp.status == 200 and raw_text:
                    data = json.loads(raw_text)
                    contracte = data if isinstance(data, list) else data.get("listaContracte", [])
                    
                    if contracte and len(contracte) > 0:
                        c = contracte[0]
                        return {
                            "cod_client": str(c.get("codClient", "N/A")),
                            "nr_contract": str(c.get("nrContract", "N/A")),
                            "nume": c.get("denClient", "N/A"),
                            "adresa": c.get("adrClient", "N/A"),
                            "stare": c.get("stareContract", "N/A")
                        }
                return None

        except Exception as e:
            _LOGGER.error("Eroare la preluarea datelor: %s", e)
            return None