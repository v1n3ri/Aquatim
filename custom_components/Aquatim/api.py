import aiohttp
import logging
import asyncio
from .const import HEADERS

_LOGGER = logging.getLogger(__name__)

# URL-ul de login REST identificat de tine
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
            self.session = aiohttp.ClientSession(
                headers=HEADERS,
                cookie_jar=aiohttp.CookieJar(unsafe=True)
            )
        return self.session

    async def login(self):
        session = await self._get_session()
        
        try:
            # PASUL 1: Login folosind exact numele câmpurilor din browser
            # Trimitem ca Form Data (data=...), nu ca JSON (json=...)
            login_data = {
                "user": self.email,
                "password": self.password  # Am schimbat din 'pass' în 'password'
            }
            
            _LOGGER.debug("Trimitere login REST (Form Data) către %s", URL_REST_LOGIN)
            
            headers = {
                **HEADERS,
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": "https://portal.aquatim.ro/self_utilities/login.jsp"
            }

            async with session.post(URL_REST_LOGIN, data=login_data, headers=headers) as resp:
                if resp.status != 200:
                    _LOGGER.error("Serverul a returnat status %s la login REST", resp.status)
                    return False
                
                # Citim răspunsul (probabil un JSON de confirmare)
                res_text = await resp.text()
                _LOGGER.debug("Răspuns login: %s", res_text)

            # PASUL 2: Activare sesiune (infoSession) - POST conform JS
            async with session.post(URL_INFO_SESSION, json={}, headers={"X-Requested-With": "XMLHttpRequest"}) as resp:
                if resp.status == 200:
                    _LOGGER.info("Sesiune Aquatim activată cu succes.")
                    return True
                
            return False

        except Exception as e:
            _LOGGER.error("Eroare la autentificarea REST: %s", e)
            return False

    async def get_data(self):
        if not await self.login():
            return None

        await asyncio.sleep(1)
        session = await self._get_session()
        
        headers = {
            "Accept": "application/json, text/plain, */*",
            "X-Requested-With": "XMLHttpRequest"
        }

        try:
            async with session.get(URL_LISTA_CONTRACTE, headers=headers) as resp:
                if resp.status == 200:
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
            _LOGGER.error("Eroare la preluarea datelor: %s", e)
            return None