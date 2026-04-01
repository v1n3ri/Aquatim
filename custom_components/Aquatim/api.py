import aiohttp
import logging
from .const import URL_LOGIN, URL_LISTA_CONTRACTE, HEADERS

_LOGGER = logging.getLogger(__name__)

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
            async with session.post(URL_LOGIN, data=payload, timeout=10) as resp:
                if resp.status == 200 and "login.jsp" not in str(resp.url):
                    return True
                return False
        except Exception as e:
            _LOGGER.error("Eroare login: %s", e)
            return False

    async def get_data(self):
        """Obține doar lista de contracte."""
        if not await self.login():
            return None

        session = await self._get_session()
        try:
            async with session.get(URL_LISTA_CONTRACTE) as resp:
                contracte = await resp.json()
                if not contracte or not isinstance(contracte, list):
                    return None
                
                # Luăm primul contract din listă
                c = contracte[0]
                return {
                    "cod_client": c.get("codClient"),
                    "nr_contract": c.get("nrContract"),
                    "nume": c.get("denClient"),
                    "adresa": c.get("adrClient"),
                    "stare": c.get("stareContract")
                }
        except Exception as e:
            _LOGGER.error("Eroare la preluarea listei de contracte: %s", e)
            return None