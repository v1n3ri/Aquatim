import aiohttp
import logging
import asyncio
from bs4 import BeautifulSoup
from .const import URL_LOGIN, HEADERS

_LOGGER = logging.getLogger(__name__)

URL_PRELOAD = "https://portal.aquatim.ro/self_utilities/oui/cl/index.html?_infosession=preload"
URL_ACTIVATE_DP = "https://portal.aquatim.ro/self_utilities/oui/cl/index.html?action=dp"
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
            # 1. Pasul Preload (Pre-autentificare SAP)
            async with session.get(URL_PRELOAD, timeout=15) as resp:
                await resp.text()

            # 2. Obținem pagina de login și extragem input-urile ascunse
            async with session.get(URL_LOGIN, timeout=15) as resp:
                html = await resp.text()
                soup = BeautifulSoup(html, 'html.parser')
                form_data = {
                    tag.get("name"): tag.get("value", "")
                    for tag in soup.find_all("input", type="hidden")
                    if tag.get("name")
                }

            # 3. Trimitem datele de login
            payload = {**form_data, "user": self.email, "pass": self.password, "login": "Autentificare"}
            
            # Forțăm headers-ul să arate ca un browser care a dat click pe buton
            login_headers = {
                **HEADERS,
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": URL_LOGIN,
                "Origin": "https://portal.aquatim.ro"
            }

            async with session.post(URL_LOGIN, data=payload, headers=login_headers, allow_redirects=True) as resp:
                url_dupa_login = str(resp.url)
                _LOGGER.debug("URL după POST login: %s", url_dupa_login)

                if "login.jsp" in url_dupa_login:
                    _LOGGER.error("Autentificare eșuată - Date incorecte sau sesiune respinsă.")
                    return False

            # 4. Simulăm încărcarea Component-preload.js (așteptăm 1.5 secunde)
            # Acest delay este critic pentru ca serverul SAP să proceseze sesiunea
            await asyncio.sleep(1.5)

            # 5. Activăm Data Provider (Pasul esențial găsit de tine)
            _LOGGER.debug("Activare Data Provider (action=dp)...")
            async with session.get(URL_ACTIVATE_DP, timeout=15) as resp:
                text_dp = await resp.text()
                # Dacă primim un JSON cu "err: false", e perfect
                _LOGGER.debug("Răspuns DP: %s", text_dp[:100])

            return True

        except Exception as e:
            _LOGGER.error("Eroare la pașii de autentificare: %s", e)
            return False

    async def get_data(self):
        # Încercăm login-ul complet
        if not await self.login():
            return None

        session = await self._get_session()
        # Headers specifice pentru cererea REST de date
        data_headers = {
            "Accept": "application/json, text/plain, */*",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://portal.aquatim.ro/self_utilities/index.jsp",
            "User-Agent": HEADERS["User-Agent"]
        }

        try:
            async with session.get(URL_LISTA_CONTRACTE, headers=data_headers, timeout=15) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        c = data[0]
                        _LOGGER.info("Date primite pentru contract: %s", c.get("nrContract"))
                        return {
                            "cod_client": str(c.get("codClient")),
                            "nr_contract": str(c.get("nrContract")),
                            "nume": c.get("denClient"),
                            "adresa": c.get("adrClient"),
                            "stare": c.get("stareContract"),
                            "sold": 0 # Vom popula asta într-un pas viitor
                        }
                _LOGGER.warning("Status server date: %s. Nu s-au găsit contracte.", resp.status)
                return None
        except Exception as e:
            _LOGGER.error("Eroare la preluarea listei de contracte: %s", e)
            return None