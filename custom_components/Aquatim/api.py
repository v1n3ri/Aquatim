import aiohttp
import logging
from bs4 import BeautifulSoup
from .const import URL_LOGIN, URL_DASHBOARD, URL_POST_INDEX, HEADERS

_LOGGER = logging.getLogger(__name__)

class AquatimAPI:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.session = None

    async def _get_session(self):
        """Creează sau returnează sesiunea activă cu suport pentru cookies."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers=HEADERS, 
                cookie_jar=aiohttp.CookieJar()
            )
        return self.session

    async def login(self):
        """Efectuează autentificarea pe portal."""
        session = await self._get_session()
        # Folosim id-urile 'user' și 'pass' identificate de tine în HTML
        payload = {
            "user": self.email,
            "pass": self.password,
            "login": "Autentificare"
        }
        try:
            async with session.post(URL_LOGIN, data=payload, timeout=10) as resp:
                # Verificăm dacă am fost redirecționați de la pagina de login (semn de succes)
                if resp.status == 200 and "login.jsp" not in str(resp.url):
                    _LOGGER.debug("Autentificare reușită pentru %s", self.email)
                    return True
                _LOGGER.error("Autentificare eșuată. Verificați credențialele.")
                return False
        except Exception as e:
            _LOGGER.error("Eroare la conectarea cu portalul Aquatim: %s", e)
            return False

    async def get_balance(self):
        """Extrage soldul curent prin web scraping."""
        if not await self.login():
            return None

        session = await self._get_session()
        try:
            async with session.get(URL_DASHBOARD, timeout=10) as resp:
                if resp.status != 200:
                    return None
                
                html = await resp.text()
                soup = BeautifulSoup(html, 'html.parser')
                # Căutăm link-ul cu id-ul specific identificat anterior
                element = soup.find("a", {"id": "__link0"})
                
                if element:
                    raw_text = element.get_text() # Exemplu: "Sold : 12.50"
                    # Curățăm textul pentru a rămâne doar cu valoarea numerică
                    clean_value = raw_text.replace("Sold :", "").strip()
                    _LOGGER.debug("Sold extras: %s", clean_value)
                    return clean_value
                
                _LOGGER.warning("Elementul de sold nu a fost găsit în pagină.")
                return None
        except Exception as e:
            _LOGGER.error("Eroare la extragerea soldului: %s", e)
            return None

    async def send_index(self, value):
        """Trimite indexul nou către Aquatim."""
        if not await self.login():
            return False

        session = await self._get_session()
        payload = {
            "index_nou": value,
            "submit": "Trimite"
        }
        try:
            async with session.post(URL_POST_INDEX, data=payload, timeout=10) as resp:
                return resp.status == 200
        except Exception as e:
            _LOGGER.error("Eroare la trimiterea indexului: %s", e)
            return False