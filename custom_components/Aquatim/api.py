import aiohttp
import logging
from .const import URL_LOGIN, URL_LISTA_CONTRACTE, URL_API_SOLD, HEADERS

_LOGGER = logging.getLogger(__name__)

class AquatimAPI:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.session = None

    async def _get_session(self):
        """Gestionează sesiunea HTTP și cookie-urile."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers=HEADERS, 
                cookie_jar=aiohttp.CookieJar()
            )
        return self.session

    async def login(self):
        """Efectuează autentificarea pe portal."""
        session = await self._get_session()
        payload = {
            "user": self.email,
            "pass": self.password,
            "login": "Autentificare"
        }
        try:
            async with session.post(URL_LOGIN, data=payload, timeout=10) as resp:
                # Succes dacă statusul e 200 și nu am fost trimiși înapoi la login
                if resp.status == 200 and "login.jsp" not in str(resp.url):
                    _LOGGER.debug("Autentificare reușită pentru %s", self.email)
                    return True
                _LOGGER.error("Autentificare eșuată. Verificați email-ul și parola.")
                return False
        except Exception as e:
            _LOGGER.error("Eroare de conexiune la login: %s", e)
            return False

async def get_data(self):
        """Obține toate datele despre contract și sold."""
        if not await self.login():
            return None

        session = await self._get_session()
        try:
            # 1. Date Contract
            async with session.get(URL_LISTA_CONTRACTE) as resp:
                contracte = await resp.json()
                if not contracte: return None
                c = contracte[0]

            # 2. Date Sold
            params = {"codClient": c["codClient"], "nrContract": c["nrContract"]}
            async with session.get(URL_API_SOLD, params=params) as resp:
                sold = await resp.json()

            # Returnăm un pachet complet de date
            return {
                "sold": sold if isinstance(sold, (int, float)) else sold.get("sold", 0),
                "cod_client": c.get("codClient"),
                "nr_contract": c.get("nrContract"),
                "nume": c.get("denClient"),
                "adresa": c.get("adrClient"),
                "stare": c.get("stareContract")
            }
        except Exception as e:
            _LOGGER.error("Eroare la preluarea datelor: %s", e)
            return None

    async def close(self):
        """Închide sesiunea aiohttp."""
        if self.session:
            await self.session.close()