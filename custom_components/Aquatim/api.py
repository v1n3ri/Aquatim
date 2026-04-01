import aiohttp
import logging
import asyncio
import json

_LOGGER = logging.getLogger(__name__)

URL_BASE = "https://portal.aquatim.ro/self_utilities/"
URL_REST_LOGIN = f"{URL_BASE}rest/admcl/login"
URL_INFO_SESSION = f"{URL_BASE}rest/self/infoSession"
URL_LISTA_CONTRACTE = f"{URL_BASE}rest/self/admcl/getListaContracte"
URL_SOLD = f"{URL_BASE}rest/self/facturi/getSoldClient"
URL_VERIFICA_PERIOADA = f"{URL_BASE}rest/self/transmitere/verificaPerioada"

class AquatimAPI:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.session = None
        self.gsid = None
        self.last_data = {}

    async def _get_session(self):
        """Creează sau returnează sesiunea HTTP curentă."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                cookie_jar=aiohttp.CookieJar(unsafe=True),
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
                    "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
                    "X-Requested-With": "XMLHttpRequest"
                }
            )
        return self.session

    async def login(self):
        """Efectuează logarea și activează sesiunea OUI."""
        session = await self._get_session()
        try:
            login_data = {"user": self.email, "password": self.password}
            _LOGGER.warning("Încercare autentificare Aquatim pentru: %s", self.email)
            
            async with session.post(URL_REST_LOGIN, data=login_data, headers={"Referer": f"{URL_BASE}login.jsp"}) as resp:
                res_data = await resp.json()
                if res_data.get("authSuccessfull") is True:
                    self.gsid = res_data.get("sessionId")
                    _LOGGER.warning("Autentificare reușită! GSID: %s", self.gsid)
                    
                    # Activare context sesiune (foarte important pentru a evita 403 ulterior)
                    await session.post(URL_INFO_SESSION, json={}, headers={"Referer": f"{URL_BASE}oui/cl/index.html"})
                    return True
                
                _LOGGER.error("Eroare la login: %s", res_data.get("errMessage", "Date incorecte"))
                return False
        except Exception as e:
            _LOGGER.error("Excepție la procesul de login: %s", e)
            return False

    async def get_data(self):
        """Prelucrează toate datele necesare senzorilor."""
        if not await self.login():
            return None

        await asyncio.sleep(1) # Mică pauză pentru backend-ul SAP
        session = await self._get_session()
        
        try:
            # Headere obligatorii extrase din Network Tab (Chrome)
            data_headers = {
                "accept": "*/*",
                "oui_req": "true",
                "self_gsid": str(self.gsid),
                "referer": f"{URL_BASE}oui/cl/index.html"
            }

            # 1. Preluăm lista de contracte
            async with session.get(URL_LISTA_CONTRACTE, headers=data_headers) as resp:
                contracte = await resp.json()
                if not isinstance(contracte, list) or len(contracte) == 0:
                    _LOGGER.warning("Nu s-au găsit contracte în cont.")
                    return None
                
                c = contracte[0]
                cod_client = str(c.get("codClient"))
                nr_contract = str(c.get("nrContract"))

            # 2. Preluăm Soldul Clientului
            sold_final = 0.0
            params_sold = {"codClient": cod_client, "nrContract": nr_contract}
            async with session.get(URL_SOLD, params=params_sold, headers=data_headers) as s_resp:
                raw_sold = await s_resp.text()
                _LOGGER.warning("Date brute sold primite: %s", raw_sold)
                try:
                    sold_final = float(raw_sold.strip())
                except:
                    sold_final = 0.0

            # 3. Verificăm Perioada de Transmitere Index
            mesaj_index = "Informație indisponibilă"
            start_perioada = "N/A"
            sfarsit_perioada = "N/A"
            
            async with session.get(URL_VERIFICA_PERIOADA, params={"codClient": cod_client}, headers=data_headers) as p_resp:
                try:
                    p_data = await p_resp.json()
                    _LOGGER.warning("Date brute perioadă index: %s", p_data)
                    
                    mesaj_index = p_data.get("response", "N/A")
                    start_perioada = p_data.get("start", "N/A")
                    sfarsit_perioada = p_data.get("end", "N/A")
                except Exception:
                    # Fallback dacă serverul returnează text în loc de JSON
                    mesaj_index = await p_resp.text()

            # Construim dicționarul final
            result = {
                "cod_client": cod_client,
                "nr_contract": nr_contract,
                "nume": c.get("denClient", "N/A"),
                "adresa": c.get("adrClient", "N/A"),
                "stare": c.get("stareContract", "N/A"),
                "sold": sold_final,
                "perioada_index": mesaj_index,
                "start_citire": start_perioada,
                "sfarsit_citire": sfarsit_perioada
            }

            # Salvăm pentru a fi accesibil din sensor.py
            self.last_data = result
            return result

        except Exception as e:
            _LOGGER.error("Eroare la preluarea datelor finale Aquatim: %s", e)
            return None