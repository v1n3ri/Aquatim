import aiohttp
import logging
import asyncio
from bs4 import BeautifulSoup
from .const import URL_LOGIN, HEADERS

_LOGGER = logging.getLogger(__name__)

# Endpoint-uri descoperite în component_preload.js
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
            # PASUL 1: Inițializăm sesiunea (InfoSession - găsit în JS)
            # SAP are nevoie de acest apel POST pentru a genera token-ul de securitate
            async with session.post(URL_INFO_SESSION, json={}, timeout=10) as resp:
                await resp.text()

            # PASUL 2: Luăm formularul de login
            async with session.get(URL_LOGIN, timeout=10) as resp:
                html = await resp.text()
                soup = BeautifulSoup(html, 'html.parser')
                form_data = {
                    tag.get("name"): tag.get("value", "")
                    for tag in soup.find_all("input", type="hidden")
                    if tag.get("name")
                }

            # PASUL 3: Login propriu-zis
            payload = {
                **form_data,
                "user": self.email,
                "pass": self.password,
                "login": "Autentificare"
            }
            
            login_headers = {
                **HEADERS,
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": URL_LOGIN
            }

            async with session.post(URL_LOGIN, data=payload, headers=login_headers, allow_redirects=True) as resp:
                # Verificăm dacă am fost redirecționați departe de login.jsp
                if "login.jsp" not in str(resp.url):
                    _LOGGER.info("Autentificare reușită conform fluxului SAP descoperit.")
                    return True
                
                _LOGGER.error("Autentificare eșuată. Serverul a rămas pe pagina de login.")
                return False

        except Exception as e:
            _LOGGER.error("Eroare la procesul de login (SAP UI5 Logic): %s", e)
            return False

    async def get_data(self):
        if not await self.login():
            return None

        await asyncio.sleep(1)
        session = await self._get_session()
        
        # Header-ul X-Requested-With este OBLIGATORIU în SAP UI5 (văzut în codul JS)
        data_headers = {
            **HEADERS,
            "Accept": "application/json, text/plain, */*",
            "X-Requested-With": "XMLHttpRequest"
        }

        try:
            async with session.get(URL_LISTA_CONTRACTE, headers=data_headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        c = data[0]
                        return {
                            "cod_client": str(c.get("codClient")),
                            "nr_contract": str(c.get("nrContract")),
                            "nume": c.get("denClient"),
                            "adresa": c.get("adrClient"),
                            "stare": c.get("stareContract")
                        }
                return None
        except Exception as e:
            _LOGGER.error("Eroare la preluarea contractelor: %s", e)
            return None