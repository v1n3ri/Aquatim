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
                cookie_jar=aiohttp.CookieJar(unsafe=True)
            )
        return self.session

    async def login(self):
        session = await self._get_session()
        
        try:
            # PASUL 1: Accesăm pagina de login pentru a obține cookie-urile inițiale
            async with session.get(URL_LOGIN, timeout=10) as resp:
                await resp.text()
            
            # PASUL 2: Trimitem datele de logare
            payload = {
                "user": self.email,
                "pass": self.password,
                "login": "Autentificare"
            }
            
            # Adăugăm headers extra pentru a simula un formular real
            extra_headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "https://portal.aquatim.ro",
                "Referer": "https://portal.aquatim.ro/self_utilities/login.jsp"
            }

            async with session.post(URL_LOGIN, data=payload, headers=extra_headers, timeout=15, allow_redirects=True) as resp:
                final_url = str(resp.url)
                text_raspuns = await resp.text()

                # Dacă URL-ul s-a schimbat din login.jsp în index.jsp sau altceva, e succes
                if resp.status == 200 and "login.jsp" not in final_url:
                    _LOGGER.info("Autentificare reușită la Aquatim.")
                    return True
                
                _LOGGER.error("Eșec la autentificare. URL final: %s. Verificați dacă email/parola sunt corecte.", final_url)
                return False

        except Exception as e:
            _LOGGER.error("Eroare în timpul procesului de login: %s", e)
            return False

    async def get_data(self):
        if not await self.login():
            return None

        await asyncio.sleep(1)
        session = await self._get_session()
        
        try:
            async with session.get(URL_LISTA_CONTRACTE, timeout=10) as resp:
                if resp.status != 200:
                    _LOGGER.error("Portalul a returnat status %s la cererea de date", resp.status)
                    return None
                
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
                return None
        except Exception as e:
            _LOGGER.error("Eroare la preluarea datelor finale: %s", e)
            return None