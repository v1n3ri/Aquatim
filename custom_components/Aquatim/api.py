import aiohttp
import logging
import asyncio
from bs4 import BeautifulSoup
from .const import URL_LOGIN, HEADERS

_LOGGER = logging.getLogger(__name__)

URL_PRELOAD = "https://portal.aquatim.ro/self_utilities/oui/cl/index.html?_infosession=preload"
URL_LISTA_CONTRACTE = "https://portal.aquatim.ro/self_utilities/rest/self/admcl/getListaContracte"

class AquatimAPI:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.session = None

    async def _get_session(self):
        if self.session is None or self.session.closed:
            # Important: unsafe=True permite cookie-uri de pe domenii care par diferite dar sunt sub-resurse
            self.session = aiohttp.ClientSession(
                headers=HEADERS,
                cookie_jar=aiohttp.CookieJar(unsafe=True)
            )
        return self.session

    async def login(self):
        session = await self._get_session()
        
        try:
            # PASUL 1: Request-ul de PRELOAD pe care l-ai găsit
            # Acesta setează cookie-urile de infrastructură SAP (JSESSIONID etc.)
            _LOGGER.debug("Inițializare sesiune SAP (Preload)...")
            async with session.get(URL_PRELOAD, timeout=15) as resp:
                await resp.text()

            # PASUL 2: Încărcăm pagina de login vizuală
            async with session.get(URL_LOGIN, timeout=15) as resp:
                html = await resp.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extragem orice token ascuns care ar putea exista în formular
                form_data = {}
                for hidden_input in soup.find_all("input", type="hidden"):
                    if hidden_input.get("name"):
                        form_data[hidden_input.get("name")] = hidden_input.get("value", "")

            # PASUL 3: Executăm Post-ul de login
            payload = {
                **form_data,
                "user": self.email,
                "pass": self.password,
                "login": "Autentificare"
            }
            
            # Adăugăm headers specifice pentru a simula un browser complet
            login_headers = {
                **HEADERS,
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": "https://portal.aquatim.ro/self_utilities/login.jsp",
                "Origin": "https://portal.aquatim.ro",
                "Upgrade-Insecure-Requests": "1"
            }

            async with session.post(URL_LOGIN, data=payload, headers=login_headers, timeout=15, allow_redirects=True) as resp:
                final_url = str(resp.url)
                
                # Verificăm dacă am scăpat de pagina de login
                if resp.status == 200 and "login.jsp" not in final_url:
                    _LOGGER.info("Autentificare reușită pe infrastructura SAP Aquatim.")
                    return True
                
                _LOGGER.error("Autentificare eșuată. Serverul a refuzat accesul la %s", final_url)
                return False

        except Exception as e:
            _LOGGER.error("Eroare la procesul de login SAP: %s", e)
            return False

    async def get_data(self):
        if not await self.login():
            return None

        # Aplicațiile SAP au nevoie de o secundă să proceseze sesiunea în spate
        await asyncio.sleep(2)
        session = await self._get_session()
        
        # Headers pentru API-ul de date (foarte important Accept-ul JSON)
        data_headers = {
            **HEADERS,
            "Accept": "application/json, text/plain, */*",
            "X-Requested-With": "XMLHttpRequest"
        }

        try:
            async with session.get(URL_LISTA_CONTRACTE, headers=data_headers, timeout=15) as resp:
                if resp.status != 200:
                    _LOGGER.error("Eroare preluare date. Status: %s", resp.status)
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
            _LOGGER.error("Eroare la parsarea datelor JSON: %s", e)
            return None