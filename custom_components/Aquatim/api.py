import aiohttp
import logging
import asyncio
from .const import URL_LOGIN, HEADERS

_LOGGER = logging.getLogger(__name__)

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
                cookie_jar=aiohttp.CookieJar()
            )
        return self.session

    async def login(self):
        session = await self._get_session()
        payload = {
            "user": self.email,
            "pass": self.password,
            "login": "Autentificare"
        }
        try:
            async with session.post(URL_LOGIN, data=payload, timeout=15) as resp:
                # Verificăm dacă am fost redirecționați (semn de login reușit)
                if resp.status == 200 and "login.jsp" not in str(resp.url):
                    _LOGGER.info("Autentificare Aquatim reușită")
                    return True
                _LOGGER.error("Autentificare eșuată - verificați datele de acces")
                return False
        except Exception as e:
            _LOGGER.error("Eroare la conectare login: %s", e)
            return False

    async def get_data(self):
        if not await self.login():
            return None

        # Așteptăm o secundă pentru ca sesiunea să fie propagată pe server
        await asyncio.sleep(1)
        
        session = await self._get_session()
        # Adăugăm Referer pentru a simula navigarea din portal
        custom_headers = {**HEADERS, "Referer": "https://portal.aquatim.ro/self_utilities/index.jsp"}
        
        try:
            async with session.get(URL_LISTA_CONTRACTE, headers=custom_headers, timeout=15) as resp:
                if resp.status != 200:
                    _LOGGER.error("Eroare API Contracte: Status %s", resp.status)
                    return None
                
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
            _LOGGER.error("Eroare la citirea listei de contracte: %s", e)
            return None