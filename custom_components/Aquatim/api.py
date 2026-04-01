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
            # Folosim un CookieJar care stochează automat cookie-urile de sesiune
            self.session = aiohttp.ClientSession(
                headers=HEADERS,
                cookie_jar=aiohttp.CookieJar(unsafe=True)
            )
        return self.session

    async def login(self):
        session = await self._get_session()
        
        # Datele de login exact cum pleacă din formularul HTML al site-ului
        payload = {
            "user": self.email,
            "pass": self.password,
            "login": "Autentificare"
        }
        
        # Header special pentru a simula trimiterea unui formular web
        login_headers = {
            **HEADERS,
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": "https://portal.aquatim.ro/self_utilities/login.jsp",
            "Origin": "https://portal.aquatim.ro"
        }

        try:
            _LOGGER.debug("Se încearcă login pentru: %s", self.email)
            async with session.post(URL_LOGIN, data=payload, headers=login_headers, timeout=15, allow_redirects=True) as resp:
                text = await resp.text()
                
                # Verificăm dacă suntem încă pe pagina de login (semn de eșec)
                # Sau dacă în răspuns apare ceva de genul "Eroare autentificare"
                if resp.status == 200 and "login.jsp" not in str(resp.url):
                    _LOGGER.info("Autentificare Aquatim reușită!")
                    return True
                
                _LOGGER.error("Autentificare eșuată. Serverul a returnat pagina de login sau eroare.")
                return False
        except Exception as e:
            _LOGGER.error("Eroare critică la login: %s", e)
            return False

    async def get_data(self):
        # Încercăm login
        if not await self.login():
            return None

        # O mică pauză să fim siguri că sesiunea e activă
        await asyncio.sleep(1)
        
        session = await self._get_session()
        # Header pentru cererea de date (JSON)
        data_headers = {
            **HEADERS,
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://portal.aquatim.ro/self_utilities/index.jsp"
        }

        try:
            async with session.get(URL_LISTA_CONTRACTE, headers=data_headers, timeout=15) as resp:
                if resp.status != 200:
                    _LOGGER.error("Eroare API la preluare contracte: %s", resp.status)
                    return None
                
                data = await resp.json()
                _LOGGER.debug("Date primite: %s", data)

                if isinstance(data, list) and len(data) > 0:
                    c = data[0]
                    return {
                        "cod_client": str(c.get("codClient", "N/A")),
                        "nr_contract": str(c.get("nrContract", "N/A")),
                        "nume": c.get("denClient", "N/A"),
                        "adresa": c.get("adrClient", "N/A"),
                        "stare": c.get("stareContract", "N/A"),
                        "sold": 0 # Vom adăuga logica de sold după ce vedem că merge asta
                    }
                _LOGGER.warning("Lista de contracte este goală.")
                return None
        except Exception as e:
            _LOGGER.error("Eroare la get_data: %s", e)
            return None