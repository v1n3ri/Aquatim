import aiohttp
import logging
import asyncio
from .const import URL_LOGIN, HEADERS

_LOGGER = logging.getLogger(__name__)

# Endpoint-uri derivate din structura SAP observată
URL_AUTH = "https://portal.aquatim.ro/self_utilities/j_security_check"
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
            # 1. Pas obligatoriu pentru a genera JSESSIONID
            async with session.get("https://portal.aquatim.ro/self_utilities/login.jsp") as resp:
                await resp.text()

            # 2. Trimitem datele către j_security_check (Standard Java/SAP Auth)
            # Aceasta este ceea ce funcția loginPage() face probabil în spate
            auth_data = {
                "j_username": self.email,
                "j_password": self.password
            }
            
            _LOGGER.debug("Încercare autentificare securizată...")
            async with session.post(URL_AUTH, data=auth_data, allow_redirects=True) as resp:
                # Dacă login-ul prin j_security_check reușește, ne trimite la index
                if resp.status == 200 and "login.jsp" not in str(resp.url):
                    _LOGGER.info("Autentificare reușită prin Security Check.")
                else:
                    # Dacă metoda de mai sus nu merge, încercăm metoda clasică dar cu parametrii extra
                    payload = {
                        "user": self.email,
                        "pass": self.password,
                        "login": "Autentificare"
                    }
                    async with session.post(URL_LOGIN, data=payload, allow_redirects=True) as resp2:
                        if "login.jsp" in str(resp2.url):
                            _LOGGER.error("Toate metodele de autentificare au eșuat.")
                            return False

            # 3. Validăm sesiunea (InfoSession) - Acest pas "leagă" userul de API-ul de date
            async with session.post(URL_INFO_SESSION, json={}) as resp:
                res_text = await resp.text()
                if resp.status == 200:
                    _LOGGER.info("Sesiune activată pentru API.")
                    return True
            
            return False

        except Exception as e:
            _LOGGER.error("Eroare critică: %s", e)
            return False

    async def get_data(self):
        if not await self.login():
            return None

        await asyncio.sleep(1)
        session = await self._get_session()
        
        headers = {
            **HEADERS,
            "Accept": "application/json",
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
            _LOGGER.error("Eroare la preluare date: %s", e)
            return None