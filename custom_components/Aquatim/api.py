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

    async def _get_session(self):
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
        session = await self._get_session()
        try:
            login_data = {"user": self.email, "password": self.password}
            async with session.post(URL_REST_LOGIN, data=login_data, headers={"Referer": f"{URL_BASE}login.jsp"}) as resp:
                res_data = await resp.json()
                if res_data.get("authSuccessfull") is True:
                    self.gsid = res_data.get("sessionId")
                    _LOGGER.warning("Login Aquatim OK.")
                    await session.post(URL_INFO_SESSION, json={}, headers={"Referer": f"{URL_BASE}oui/cl/index.html"})
                    return True
                return False
        except Exception as e:
            _LOGGER.error("Eroare login: %s", e)
            return False

    async def get_data(self):
        if not await self.login():
            return None

        await asyncio.sleep(1)
        session = await self._get_session()
        
        try:
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
                    return None
                c = contracte[0]
                cod_client = str(c.get("codClient"))
                nr_contract = str(c.get("nrContract"))

            # 2. Preluăm Soldul
            sold_final = 0.0
            async with session.get(URL_SOLD, params={"codClient": cod_client, "nrContract": nr_contract}, headers=data_headers) as s_resp:
                raw_sold = await s_resp.text()
                try:
                    sold_final = float(raw_sold.strip())
                except:
                    sold_final = 0.0

            # 3. Verificăm perioada de transmitere index
            mesaj_index = "Informație indisponibilă"
            async with session.get(URL_VERIFICA_PERIOADA, params={"codClient": cod_client}, headers=data_headers) as p_resp:
                try:
                    p_data = await p_resp.json()
                    _LOGGER.warning("Date perioadă index: %s", p_data)
                    # Extragem câmpul 'response' care conține textul complet
                    mesaj_index = p_data.get("response", "Perioada nu a putut fi determinată")
                except Exception:
                    # Fallback în cazul în care serverul trimite text simplu în loc de JSON
                    raw_p = await p_resp.text()
                    mesaj_index = raw_p.strip() if raw_p else mesaj_index

            return {
                "cod_client": cod_client,
                "nr_contract": nr_contract,
                "nume": c.get("denClient", "N/A"),
                "adresa": c.get("adrClient", "N/A"),
                "stare": c.get("stareContract", "N/A"),
                "sold": sold_final,
                "perioada_index": mesaj_index
            }

        except Exception as e:
            _LOGGER.error("Eroare la procesarea datelor finale: %s", e)
            return None