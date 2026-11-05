#!/usr/bin/env python3
import requests
import json

# Variables de configuracion del Simulador API Local (Lab 4.5.5) y API HTTPS
APIHOST = "http://library.demo.local"
LOGIN = "cisco"
PASSWORD = "Cisco123!"
HTTPS_API_URL = "https://api.github.com/users/cisco"

# 1. Funcion para obtener el token de autenticacion (Estilo Lab 4.5.5)
def getAuthToken():
    authCreds = (LOGIN, PASSWORD)
    try:
        r = requests.post(
            f"{APIHOST}/api/v1/loginViaBasic",
            auth=authCreds,
            timeout=5
        )
        if r.status_code == 200:
            print("[OK] Autenticacion exitosa. Token generado correctamente.")
            return r.json()["token"]
        elif r.status_code == 401:
            raise Exception(f"Error 401 No Autorizado: Credenciales invalidas ({r.text}).")
        else:
            raise Exception(f"Codigo de estado {r.status_code} y texto {r.text}, mientras intenta Auth.")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR DE CONEXION] No se pudo conectar al simulador local: {e}")
        return None

# 2. Funcion para verificar conectividad y auditoria mediante REST API sobre HTTPS
def checkHttpsService():
    print("\n--- Verificando Servicio Externo sobre HTTPS ---")
    headers = {
        "Accept": "application/json",
        "User-Agent": "DevNet-Inventory-Script-JPerez"
    }
    try:
        r = requests.get(HTTPS_API_URL, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            print(f"[HTTPS 200 OK] Conexion segura establecida con: {data.get('html_url')}")
            print(f"Organizacion verificada: {data.get('name')} | Repositorios publicos: {data.get('public_repos')}")
            return True
        elif r.status_code == 404:
            print("[HTTPS 404] Recurso no encontrado en el servidor remoto.")
            return False
        elif r.status_code >= 500:
            print(f"[HTTPS {r.status_code}] Error interno en el servidor remoto (5xx).")
            return False
        else:
            print(f"[HTTPS {r.status_code}] Respuesta inesperada: {r.text}")
            return False
    except requests.exceptions.SSLError:
        print("[ERROR SSL] Fallo en la verificacion del certificado HTTPS.")
        return False
    except requests.exceptions.RequestException as e:
        print(f"[ERROR HTTPS] Fallo de red al consultar el endpoint seguro: {e}")
        return False

# 3. Funcion para registrar manual de configuracion del dispositivo en la API (Lab 4.5.5)
def registerDeviceRecord(record, apiKey):
    headers = {
        "Content-type": "application/json",
        "X-API-Key": apiKey
    }
    r = requests.post(
        f"{APIHOST}/api/v1/books",
        headers=headers,
        data=json.dumps(record)
    )
    if r.status_code == 200:
        print(f"[API POST 200] Registro sincronizado en API: {record}")
    elif r.status_code == 401:
        raise Exception("Error 401: Clave X-API-Key invalida o expirada.")
    else:
        print(f"[AVISO API] Codigo {r.status_code} ({r.text}) al registrar ID {record['id']}.")

# 4. Modulo interactivo para agregar nuevos equipos y validar VLAN / ACL (Estilo Lab 1.3.3)
def addDevicesToFile():
    print("\n--- Registro Interactivo de Dispositivos de Red ---")
    file = open("devices.txt", "a")
    while True:
        newItem = input("Ingrese el nombre del nuevo dispositivo (o 'exit' para terminar): ")
        if newItem == "exit" or newItem == "q" or newItem == "quit":
            print("¡Carga de dispositivos finalizada!")
            break
        file.write(newItem + "\n")
        print(f"Dispositivo '{newItem}' guardado en devices.txt.")
    file.close()

    # Validacion de ACL IPv4 y VLAN (Estilo if-acl.py e if-vlan.py del Lab 1.3.3)
    aclNum = int(input("\nIngrese el numero de ACL IPv4 de seguridad aplicada (ej. 10 o 110): "))
    if aclNum >= 1 and aclNum <= 99:
        tipoAcl = "ACL IPv4 estandar"
    elif aclNum >= 100 and aclNum <= 199:
        tipoAcl = "ACL IPv4 extendida"
    else:
        tipoAcl = "ACL fuera de rango estandar/extendido"
    print("Clasificacion de politica:", tipoAcl)

    nativeVLAN = 1
    dataVLAN = int(input("Ingrese el ID de la VLAN de datos del segmento (ej. 100): "))
    if nativeVLAN == dataVLAN:
        estadoVlan = "Alerta: VLAN nativa y VLAN de datos son iguales"
    else:
        estadoVlan = f"Optimo: VLAN nativa ({nativeVLAN}) y VLAN de datos ({dataVLAN}) separadas"
    print("Estado de segmentacion:", estadoVlan)
    return tipoAcl, estadoVlan

# 5. Lectura de TXT, transformacion y exportacion a multiples formatos: JSON y CSV
def processAndExportInventory(tipoAcl, estadoVlan, apiKey):
    devices = []
    file = open("devices.txt", "r")
    for item in file:
        item = item.strip()
        if item != "":
            devices.append(item)
    file.close()

    routers = []
    switches = []
    otros = []
    inventario_estructurado = []

    # Clasificacion con bucle for e if (Estilo Lab 1.3.3)
    id_counter = 200
    for item in devices:
        if "Router" in item:
            categoria = "Enrutamiento"
            routers.append(item)
        elif "Switch" in item:
            categoria = "Conmutacion"
            switches.append(item)
        else:
            categoria = "Seguridad/Appliance"
            otros.append(item)

        equipo_dict = {
            "id": id_counter,
            "dispositivo": item,
            "categoria": categoria,
            "politica_acl": tipoAcl,
            "segmentacion_vlan": estadoVlan,
            "responsable": "Jeysson Perez - NetAdmin"
        }
        inventario_estructurado.append(equipo_dict)

        # Si tenemos apiKey del simulador, sincronizamos via POST
        if apiKey is not None:
            book_payload = {
                "id": id_counter,
                "title": f"Config: {item} ({categoria})",
                "author": "Jeysson Perez",
                "isbn": f"978-000-{id_counter}"
            }
            registerDeviceRecord(book_payload, apiKey)

        id_counter = id_counter + 1

    # Exportar a formato JSON
    json_file = open("reporte_inventario.json", "w")
    json_file.write(json.dumps(inventario_estructurado, indent=4))
    json_file.close()

    # Exportar a formato CSV
    csv_file = open("reporte_inventario.csv", "w")
    csv_file.write("ID,Dispositivo,Categoria,Politica_ACL,Segmentacion_VLAN,Responsable\n")
    for eq in inventario_estructurado:
        linea_csv = f"{eq['id']},{eq['dispositivo']},{eq['categoria']},{eq['politica_acl']},{eq['segmentacion_vlan']},{eq['responsable']}\n"
        csv_file.write(linea_csv)
    csv_file.close()

    print("\n--- Resumen del Inventario Procesado ---")
    print(f"Total de equipos: {len(devices)} | Routers: {len(routers)} | Switches: {len(switches)} | Otros: {len(otros)}")
    print("Archivos generados exitosamente: 'reporte_inventario.json' y 'reporte_inventario.csv'")

# Ejecucion principal
if __name__ == "__main__":
    print("=== SISTEMA DE AUTOMATIZACION DE INVENTARIO DE RED ===")
    checkHttpsService()
    tipoAcl, estadoVlan = addDevicesToFile()
    apiKey = getAuthToken()
    processAndExportInventory(tipoAcl, estadoVlan, apiKey)