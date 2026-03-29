import aiohttp
import logging
from .const import URL_LOGIN, URL_LISTA_CONTRACTE, URL_API_SOLD, HEADERS

_LOGGER = logging.getLogger(__name__)

class AquatimAPI:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.session = None

    async def _get_session(self):
        """Gestionează sesiunea HTTP."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers=HEADERS, 
                cookie_jar=aiohttp.CookieJar()
            )
        return self.session

    async def login(self):
        """Autentificare pe portal."""
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
        """Obține toate datele despre contract și sold."""
        if not await self.login():
            return None

        session = await self._get_session()
        try:
            # 1. Obținem Contractul
            async with session.get(URL_LISTA_CONTRACTE) as resp:
                contracte = await resp.json()
                if not contracte:
                    return None
                c = contracte[0]

            # 2. Obținem Soldul
            params = {"codClient": c["codClient"], "nrContract": c["nrContract"]}
            async with session.get(URL_API_SOLD, params=params) as resp:
                sold_data = await resp.json()

            # Extragem soldul (gestionăm dacă e număr sau obiect)
            sold = sold_data if isinstance(sold_data, (int, float)) else sold_data.get("sold", 0)
            
            return {
                "sold": sold,
                "cod_client": c.get("codClient"),
                "nr_contract": c.get("nrContract"),
                "nume": c.get("denClient"),
                "adresa": c.get("adrClient"),
                "stare": c.get("stareContract"),
                "data_scadenta": sold_data.get("dataScadenta") if isinstance(sold_data, dict) else None
            }
        except Exception as e:
            _LOGGER.error("Eroare la preluarea datelor: %s", e)
            return None

    async def close(self):
        """Închide sesiunea aiohttp."""
        if self.session:
            await self.session.close()