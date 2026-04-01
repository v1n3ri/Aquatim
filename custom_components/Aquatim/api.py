import aiohttp
import logging
import asyncio
import urllib.parse
from bs4 import BeautifulSoup
from .const import URL_LOGIN, HEADERS

_LOGGER = logging.getLogger(__name__)

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
            # PASUL 1: Preluăm pagina de login pentru cookie-uri inițiale și campuri hidden
            async with session.get(URL_LOGIN, timeout=10) as resp:
                html = await resp.text()
                soup = BeautifulSoup(html, 'html.parser')
                form_data = {
                    tag.get("name"): tag.get("value", "")
                    for tag in soup.find_all("input", type="hidden")
                    if tag.get("name")
                }

            # PASUL 2: POST Login
            payload = {
                **form_data,
                "user": self.email,
                "pass": self.password,
                "login": "Autentificare"
            }
            
            # Folosim encoding manual pentru a fi siguri că caracterele speciale din parolă ajung corect
            encoded_payload = urllib.parse.urlencode(payload)
            
            login_headers = {
                **HEADERS,
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": URL_LOGIN
            }

            async with session.post(URL_LOGIN, data=encoded_payload, headers=login_headers, allow_redirects=True) as resp:
                if "login.jsp" in str(resp.url):
                    _LOGGER.error("Autentificare respinsă (URL-ul a rămas login.jsp)")
                    return False

            # PASUL 3: ACTIVARE SESIUNE (Request-ul descoperit de tine!)
            # Fără acest POST, deși suntem logați, API-ul de date va returna eroare sau listă goală
            _LOGGER.debug("Activare sesiune via infoSession...")
            async with session.post(URL_INFO_SESSION, json={}, headers={"X-Requested-With": "XMLHttpRequest"}) as resp:
                if resp.status == 200:
                    _LOGGER.info("Sesiune Aquatim activată cu succes.")
                    return True
                
                _LOGGER.error("Eroare la activarea sesiunii infoSession: %s", resp.status)
                return False

        except Exception as e:
            _LOGGER.error("Eroare în procesul de login: %s", e)
            return False

    async def get_data(self):
        # Ne asigurăm că suntem logați și sesiunea e activată
        if not await self.login():
            return None

        # O mică pauză pentru ca backend-ul să proceseze activarea
        await asyncio.sleep(1)
        session = await self._get_session()
        
        data_headers = {
            **HEADERS,
            "Accept": "application/json, text/plain, */*",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://portal.aquatim.ro/self_utilities/index.jsp"
        }

        try:
            async with session.get(URL_LISTA_CONTRACTE, headers=data_headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        c = data[0]
                        return {
                            "cod_client": str(c.get("codClient", "N/A")),
                            "nr_contract": str(c.get("nrContract", "N/A")),
                            "nume": c.get("denClient", "N/A"),
                            "adresa": c.get("adrClient", "N/A"),
                            "stare": c.get("stareContract", "N/A"),
                            "sold": 0
                        }
                _LOGGER.warning("Nu s-au putut prelua contractele. Status: %s", resp.status)
                return None
        except Exception as e:
            _LOGGER.error("Eroare la preluarea datelor finale: %s", e)
            return None