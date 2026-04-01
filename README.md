# 💧 Aquatim Home Assistant Custom Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
![GitHub All Releases](https://img.shields.io/github/downloads/v1n3ri/Aquatim/total?color=blue&logo=github&style=for-the-badge)
![GitHub Release Date](https://img.shields.io/github/release-date/v1n3ri/Aquatim?style=for-the-badge)
![version](https://img.shields.io/badge/version-v1.0.0-blue.svg)

Această integrare neoficială permite utilizatorilor **Aquatim Timișoara** să vizualizeze soldul curent, perioada de citire și să transmită indexul de apă direct din interfața Home Assistant.

## ✨ Funcționalități

- **Senzor de Sold:** Monitorizează suma datorată (în RON) extrasă automat din portalul Aquatim.
- **Perioadă Transmitere:** Afișează fereastra activă pentru autocitire (ziua de start și sfârșit).
- **Serviciu Transmitere Index:** Permite trimiterea citirii apometrului prin intermediul serviciului `aquatim.send_water_index`.
- **Actualizare Inteligentă:** Datele sunt reîmprospătate la fiecare 4 ore pentru a menține sincronizarea cu portalul fără a agresa serverele.

---

## 🚀 Instalare

### Metoda 1: HACS (Recomandat)
1. Asigură-te că ai [HACS](https://hacs.xyz/) instalat.
2. Mergi la **HACS** -> **Integrations**.
3. Click pe cele trei puncte din dreapta sus și alege **Custom repositories**.
4. Adaugă URL-ul acestui repository: `https://github.com/v1n3ri/Aquatim`
5. La categorie alege **Integration**.
6. Click pe **Add**, apoi instalează "Aquatim Portal".
7. **Restart Home Assistant.**

### Metoda 2: Manual
1. Descarcă arhiva acestui repository.
2. Copiază folderul `custom_components/Aquatim` în folderul `config/custom_components/` al instanței tale de Home Assistant.
3. **Restart Home Assistant.**

---

## ⚙️ Configurare

1. După restart, mergi la **Settings** -> **Devices & Services**.
2. Click pe **Add Integration** (jos în dreapta).
3. Caută **"Aquatim Portal"**.
4. Introdu adresa de **E-mail** și **Parola** folosite pe [portalul Aquatim](https://portal.aquatim.ro).

---

## 🛠️ Utilizare Serviciu (Transmitere Index)

Poți crea un card în Dashboard sau o automatizare folosind serviciul creat de integrare:

```yaml
service: aquatim.send_water_index
data:
  value: "123" # Introduceți valoarea indexului aici