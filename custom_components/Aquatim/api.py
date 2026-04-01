import aiohttp
import logging
import asyncio
from bs4 import BeautifulSoup
from .const import URL_LOGIN, HEADERS

_LOGGER = logging.getLogger(__name__)

# URL-uri extrase din Component.js și Component-preload.js
URL_BASE_REST = "https://portal.aquatim.ro/self_utilities/rest/self/"
URL_INFO_SESSION = f"{URL_BASE_REST}infoSession"
URL_LISTA_CONTRACTE = f"{URL_BASE_REST}admcl/getListaContracte"

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
            # 1. Inițializăm sesiunea (InfoSession POST - conform onInit din JS)
            # Chiar dacă nu suntem logați, acest apel creează contextul de securitate
            await session.post(URL_INFO_SESSION, json={}, timeout=10)

            # 2. Preluăm token-urile din pagina de login
            async with session.get(URL_LOGIN, timeout=10) as resp:
                html = await resp.text()
                soup = BeautifulSoup(html, 'html.parser')
                form_data = {
                    tag.get("name"): tag.get("value", "")
                    for tag in soup.find_all("input", type="hidden")
                    if tag.get("name")
                }

            # 3. Executăm Autentificarea
            payload = {
                **form_data,
                "user": self.email,
                "pass": self.password,
                "login": "Autentificare"
            }
            
            login_headers = {
                **HEADERS,
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": URL_LOGIN,
                "Origin": "https://portal.aquatim.ro"
            }

            async with session.post(URL_LOGIN, data=payload, headers=login_headers, allow_redirects=True) as resp:
                final_url = str(resp.url)
                if "login.jsp" in final_url:
                    _LOGGER.error("Aquatim a respins autentificarea. Verificați email-ul și parola.")
                    return False

            # 4. PASUL CRITIC: Validăm sesiunea de date (Re-apelăm infoSession după login)
            # Aceasta este metoda prin care interfața UI5 își confirmă drepturile de acces
            _LOGGER.debug("Validare sesiune post-login...")
            async with session.post(URL_INFO_SESSION, json={}, headers={"X-Requested-With": "XMLHttpRequest"}) as resp:
                if resp.status == 200:
                    _LOGGER.info("Sesiune Aquatim validată cu succes.")
                    return True
                
            return False

        except Exception as e:
            _LOGGER.error("Eroare în fluxul de autentificare Aquatim: %s", e)
            return False

    async def get_data(self):
        if not await self.login():
            return None

        # Pauză scurtă pentru procesarea serverului
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
                            "cod_client": str(c.get("codClient")),
                            "nr_contract": str(c.get("nrContract")),
                            "nume": c.get("denClient"),
                            "adresa": c.get("adrClient"),
                            "stare": c.get("stareContract"),
                            "sold": 0
                        }
                _LOGGER.warning("Status neașteptat la preluare contracte: %s", resp.status)
                return None
        except Exception as e:
            _LOGGER.error("Eroare la preluarea datelor: %s", e)
            return None