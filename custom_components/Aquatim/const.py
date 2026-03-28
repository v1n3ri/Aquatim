DOMAIN = "Aquatim"
CONF_EMAIL = "email"
CONF_PASSWORD = "password"

URL_LOGIN = "https://portal.aquatim.ro/self_utilities/login.jsp"
URL_DASHBOARD = "https://portal.aquatim.ro/self_utilities/index.jsp"
URL_POST_INDEX = "https://portal.aquatim.ro/self_utilities/oui/cl/index.html#/transmitere"

# User-Agent-ul ajută portalul să creadă că suntem un browser real, nu un bot
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}