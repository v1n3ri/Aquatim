import aiohttp
import logging
import asyncio
import json
from .const import HEADERS

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
        self.session_id = None

    async def _get_session(self):
        if self.session is None or self.session.closed:
            # Folosim un CookieJar care NU ignoră cookie-urile setate pe domenii secundare
            jar = aiohttp.CookieJar(unsafe=True)
            self.session = aiohttp.ClientSession(
                cookie_jar=jar,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
                    "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Connection": "keep-alive"
                }
            )
        return self.session

    async def login(self):
        session = await self._get_session()
        try:
            # 1. Accesăm pagina de login pentru a lua cookie-ul JSESSIONID inițial
            async with session.get(f"{URL_BASE}login.jsp", timeout=10) as resp:
                await resp.text()

            # 2. Login POST
            login_data = {"user": self.email, "password": self.password}
            login_headers = {
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": f"{URL_BASE}login.jsp",
                "Accept": "application/json, text/javascript, */*; q=0.01"
            }
            
            async with session.post(URL_REST_LOGIN, data=login_data, headers=login_headers, timeout=10) as resp:
                res_data = await resp.json()
                if res_data.get("authSuccessfull") is True:
                    self.session_id = res_data.get("sessionId")
                    _LOGGER.warning("Login OK. SessionId preluat.")
                    
                    # 3. ACCESARE INDEX (Pasul critic pentru a evita 403)
                    # Simulăm încărcarea paginii principale după login
                    async with session.get(f"{URL_BASE}index.jsp", headers={"Referer": f"{URL_BASE}login.jsp"}) as idx_resp:
                        await idx_resp.text()

                    # 4. InfoSession pentru activarea contextului REST
                    await session.post(URL_INFO_SESSION, json={}, headers={"X-Requested-With": "XMLHttpRequest", "Referer": f"{URL_BASE}index.jsp"})
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
            # Setăm Referer la index.jsp pentru a părea o cerere legitimă din portal
            data_headers = {
                "Accept": "application/json, text/plain, */*",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": f"{URL_BASE}index.jsp",
                "Session-Id": str(self.session_id)
            }

            async with session.get(URL_LISTA_CONTRACTE, headers=data_headers, timeout=10) as resp:
                raw_text = await resp.text()
                _LOGGER.warning("Răspuns Contracte (Status %s): %s", resp.status, raw_text)

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
            _LOGGER.error("Eroare get_data: %s", e)
            return None