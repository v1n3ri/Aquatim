import aiohttp
import logging
import asyncio
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
            # Folosim un CookieJar care păstrează strict ordinea setată de server
            self.session = aiohttp.ClientSession(
                headers=HEADERS,
                cookie_jar=aiohttp.CookieJar(unsafe=True)
            )
        return self.session

    async def login(self):
        session = await self._get_session()
        
        try:
            # 1. Obținem pagina de login pentru a genera JSESSIONID
            async with session.get(URL_LOGIN, timeout=10) as resp:
                html = await resp.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extragem orice camp ascuns care ar putea fi necesar
                payload = {}
                for tag in soup.find_all("input", type="hidden"):
                    if tag.get("name"):
                        payload[tag.get("name")] = tag.get("value", "")
                
                # Adăugăm datele de login
                payload.update({
                    "user": self.email,
                    "pass": self.password,
                    "login": "Autentificare"
                })

            # 2. Trimitem POST-ul de login cu referer-ul setat (Critic pentru SAP)
            login_headers = {
                **HEADERS,
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": URL_LOGIN,
                "Origin": "https://portal.aquatim.ro"
            }

            _LOGGER.debug("Încercare login standard cu headere de browser...")
            async with session.post(URL_LOGIN, data=payload, headers=login_headers, allow_redirects=True) as resp:
                final_url = str(resp.url)
                
                # Dacă URL-ul s-a schimbat, înseamnă că am trecut de login
                if "login.jsp" not in final_url:
                    _LOGGER.info("Autentificare reușită prin redirecționare.")
                    
                    # 3. Validăm imediat sesiunea prin infoSession (POST)
                    # Acest pas transformă sesiunea anonimă în sesiune de utilizator
                    async with session.post(URL_INFO_SESSION, json={}, headers={"X-Requested-With": "XMLHttpRequest"}) as info_resp:
                        if info_resp.status == 200:
                            return True
                
                _LOGGER.error("Serverul a respins logarea. URL curent: %s", final_url)
                return False

        except Exception as e:
            _LOGGER.error("Eroare la logare: %s", e)
            return False

    async def get_data(self):
        if not await self.login():
            return None

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
                _LOGGER.warning("Serverul a returnat status %s la cererea de date.", resp.status)
                return None
        except Exception as e:
            _LOGGER.error("Eroare la preluarea contractelor: %s", e)
            return None