import aiohttp
import logging
from bs4 import BeautifulSoup
from .const import URL_LOGIN, URL_DASHBOARD, HEADERS

_LOGGER = logging.getLogger(__name__)

class AquatimAPI:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.session = None

    async def _get_session(self):
        """Creează o sesiune dacă nu există."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(headers=HEADERS, cookie_jar=aiohttp.CookieJar())
        return self.session

    async def login(self):
        """Efectuează autentificarea."""
        session = await self._get_session()
        payload = {"user": self.email, "pass": self.password}
        try:
            async with session.post(URL_LOGIN, data=payload) as resp:
                return resp.status == 200 and "login.jsp" not in str(resp.url)
        except Exception as e:
            _LOGGER.error("Eroare la login: %s", e)
            return False

    async def get_balance(self):
        """Extrage soldul din dashboard."""
        if await self.login():
            session = await self._get_session()
            async with session.get(URL_DASHBOARD) as resp:
                html = await resp.text()
                soup = BeautifulSoup(html, 'html.parser')
                element = soup.find("a", {"id": "__link0"})
                if element:
                    # Extrage cifra din "Sold : 12.50"
                    return element.get_text().replace("Sold :", "").strip()
        return None

    async def send_index(self, value):
        """Trimite indexul nou."""
        if await self.login():
            session = await self._get_session()
            # Aici pui URL-ul și câmpul corect pentru index
            payload = {"index_nou": value, "submit": "Trimite"}
            async with session.post("URL_PENTRU_SUBMIT", data=payload) as resp:
                return resp.status == 200
        return False