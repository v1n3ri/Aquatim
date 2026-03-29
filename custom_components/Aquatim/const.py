DOMAIN = "aquatim" # Asigură-te că e cu "a" mic!
CONF_EMAIL = "email"
CONF_PASSWORD = "password"

URL_LOGIN = "https://portal.aquatim.ro/self_utilities/login.jsp"
# Noul URL pentru date brute
URL_API_SOLD = "https://portal.aquatim.ro/self_utilities/rest/self/facturi/getSoldClient"
URL_POST_INDEX = "https://portal.aquatim.ro/self_utilities/rest/self/index/saveIndex" # Probabil acesta e și pentru index

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*"
}