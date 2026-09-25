# -*- coding: utf-8 -*-
"""
Proyecto No. 2 - Lenguajes Formales y Autómatas
Motor de AFD, AFND, Conversión por Subconjuntos y Simulación
Todo en un solo archivo para evitar problemas de importación.
"""

import re

# ========================== CLASE AFD ==========================
class AFD:
    """
    Representa un Autómata Finito Determinista (AFD).
    """
    def __init__(self, nombre=""):
        self.nombre = nombre
        self.Q = set()          # estados
        self.Sigma = set()      # alfabeto
        self.delta = {}         # transiciones: (estado, simbolo) -> estado
        self.q0 = None          # estado inicial
        self.F = set()          # estados finales
        # Atributos para análisis estructural
        self.estados_alcanzables = set()
        self.estados_inaccesibles = set()
        self.finales_alcanzables = set()
        self.lenguaje_vacio = False
        self.historial = []     # evaluaciones

    def agregar_transicion(self, origen, simbolo, destino):
        """
        Agrega una transición. Lanza excepción si ya existe (AFND).
        """
        clave = (origen, simbolo)
        if clave in self.delta:
            raise ValueError(f"Transición duplicada para ({origen}, {simbolo}). No es determinista.")
        self.delta[clave] = destino

    def __str__(self):
        return (f"AFD: {self.nombre}\nQ = {self.Q}\nΣ = {self.Sigma}\n"
                f"δ = {self.delta}\nq0 = {self.q0}\nF = {self.F}")

    def tabla_transiciones(self):
        """
        Devuelve encabezado y filas para mostrar la tabla de transiciones.
        """
        estados = sorted(self.Q)
        simbolos = sorted(self.Sigma)
        header = ["Estado"] + simbolos
        filas = []
        for estado in estados:
            fila = [estado]
            for sim in simbolos:
                fila.append(self.delta.get((estado, sim), "-"))
            filas.append(fila)
        return header, filas


class AFND:
    """Representa un AFND como M = (Q, Sigma, delta, q0, F)."""
    def __init__(self, nombre=""):
        self.nombre = nombre
        self.Q = set()
        self.Sigma = set()
        self.delta = {}  # (estado, simbolo) -> set de destinos
        self.q0 = None
        self.F = set()

    def agregar_transicion(self, origen, simbolo, destinos):
        """Guarda cero, uno o varios destinos para un mismo par."""
        clave = (origen, simbolo)
        if clave not in self.delta:
            self.delta[clave] = set()
        self.delta[clave].update(destinos)

    def obtener_destinos(self, estado, simbolo):
        return self.delta.get((estado, simbolo), set())

    def __str__(self):
        transiciones = {}
        for clave, destinos in self.delta.items():
            transiciones[clave] = set(destinos)
        return (f"AFND: {self.nombre}\nQ = {self.Q}\nΣ = {self.Sigma}\n"
                f"δ = {transiciones}\nq0 = {self.q0}\nF = {self.F}")

    def tabla_transiciones(self):
        header = ["Estado"] + sorted(self.Sigma)
        filas = []
        for estado in sorted(self.Q):
            fila = [estado]
            for simbolo in sorted(self.Sigma):
                destinos = self.obtener_destinos(estado, simbolo)
                if destinos:
                    fila.append("{" + ",".join(sorted(destinos)) + "}")
                else:
                    fila.append("∅")
            filas.append(fila)
        return header, filas


def es_epsilon(valor):
    """Reconoce las formas prohibidas de epsilon sin importar mayúsculas."""
    return valor.strip().casefold() in {"ε", "epsilon"}


def generar_nombre_macroestado(indice):
    """Genera A, B, ..., Z, AA, AB... para identificar macroestados."""
    letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    indice += 1
    nombre = ""
    while indice > 0:
        indice, residuo = divmod(indice - 1, 26)
        nombre = letras[residuo] + nombre
    return nombre


# ========================== CARGA MANUAL Y DESDE ARCHIVO ==========================
def cargar_manual():
    """
    Solicita al usuario los componentes del AFD por consola.
    Retorna un objeto AFD.
    """
    print("\n--- CREACIÓN MANUAL DE AFD ---")
    nombre = input("Nombre o identificador del autómata: ").strip()
    afd = AFD(nombre)

    # Estados: se revisan duplicados antes de convertir la lista a set.
    while True:
        estados_str = input("Ingrese los estados (separados por comas): ").strip()
        estados = [e.strip() for e in estados_str.split(",") if e.strip()]
        duplicados = {e for e in estados if estados.count(e) > 1}
        if not estados:
            print("Debe ingresar al menos un estado.")
        elif duplicados:
            print(f"Error: estados duplicados: {sorted(duplicados)}. Intente de nuevo.")
        else:
            afd.Q = set(estados)
            break

    # Alfabeto: también se revisan duplicados antes de usar set.
    while True:
        sigma_str = input("Ingrese el alfabeto (símbolos separados por comas): ").strip()
        sigma = [s.strip() for s in sigma_str.split(",") if s.strip()]
        duplicados = {s for s in sigma if sigma.count(s) > 1}
        if not sigma:
            print("Debe ingresar al menos un símbolo.")
        elif duplicados:
            print(f"Error: símbolos duplicados: {sorted(duplicados)}. Intente de nuevo.")
        # Epsilon no forma parte del alfabeto porque no consume un símbolo de entrada.
        elif any(s.casefold() in {"ε", "epsilon"} for s in sigma):
            print("Error: ε no puede formar parte del alfabeto de un AFD.")
        else:
            afd.Sigma = set(sigma)
            break

    # Estado inicial
    while True:
        q0 = input("Ingrese el estado inicial: ").strip()
        if q0 in afd.Q:
            afd.q0 = q0
            break
        else:
            print(f"Error: '{q0}' no está en el conjunto de estados. Intente de nuevo.")

    # F puede ser vacío: el AFD es válido, aunque no aceptará cadenas.
    while True:
        finales_str = input("Ingrese los estados finales (separados por comas): ").strip()
        if not finales_str:
            afd.F = set()
            break
        finales = [f.strip() for f in finales_str.split(",") if f.strip()]
        # Se buscan duplicados antes de usar set para no ocultarlos.
        duplicados = {f for f in finales if finales.count(f) > 1}
        if duplicados:
            print(
                f"Error: estados finales duplicados: {sorted(duplicados)}. "
                "Intente de nuevo."
            )
        elif all(f in afd.Q for f in finales):
            afd.F = set(finales)
            break
        else:
            print("Error: uno o más estados finales no pertenecen a Q. Intente de nuevo.")

    # Transiciones
    print("\nIngrese las transiciones una por una.")
    print("Formato: estado_origen, símbolo, estado_destino")
    print("Escriba 'fin' para terminar.")
    # Regex exige exactamente tres elementos y permite espacios junto a las comas.
    patron_transicion_manual = re.compile(
        r"([^,\s]+)\s*,\s*([^,\s]+)\s*,\s*([^,\s]+)"
    )
    while True:
        linea = input("Transición: ").strip()
        if linea.lower() == "fin":
            break
        coincidencia = patron_transicion_manual.fullmatch(linea)
        if not coincidencia:
            print("Formato incorrecto. Debe ser: origen, símbolo, destino")
            continue
        origen, simbolo, destino = coincidencia.groups()
        if origen not in afd.Q:
            print(f"Error: '{origen}' no está en Q.")
            continue
        # Un AFD consume símbolos; no puede cambiar de estado usando epsilon.
        if simbolo.casefold() in {"ε", "epsilon"}:
            print("Error: un AFD no permite transiciones ε.")
            continue
        if simbolo not in afd.Sigma:
            print(f"Error: '{simbolo}' no está en Σ.")
            continue
        if destino not in afd.Q:
            print(f"Error: '{destino}' no está en Q.")
            continue
        try:
            afd.agregar_transicion(origen, simbolo, destino)
            print("Transición agregada.")
        except ValueError as e:
            print(f"Error: {e}")

    return afd


def cargar_desde_archivo(ruta_archivo):
    """
    Lee un archivo de texto con el formato especificado y retorna un objeto AFD.
    Las expresiones regulares validan la sintaxis completa de cada línea.
    """
    afd = AFD()
    modo_transiciones = False

    # Un elemento no puede estar vacío ni contener comas o espacios.
    elemento = r"[^,\s]+"
    lista = rf"({elemento}(?:\s*,\s*{elemento})*)"

    # fullmatch exige que toda la línea, de principio a fin, cumpla el patrón.
    patrones_secciones = {
        "NOMBRE": re.compile(r"NOMBRE\s*=\s*(\S+)\s*", re.IGNORECASE),
        "ESTADOS": re.compile(rf"ESTADOS\s*=\s*{lista}\s*", re.IGNORECASE),
        "ALFABETO": re.compile(rf"ALFABETO\s*=\s*{lista}\s*", re.IGNORECASE),
        "INICIAL": re.compile(rf"INICIAL\s*=\s*({elemento})\s*", re.IGNORECASE),
        # El grupo opcional permite escribir FINALES= para representar F vacío.
        "FINALES": re.compile(
            rf"FINALES\s*=\s*({elemento}(?:\s*,\s*{elemento})*)?\s*",
            re.IGNORECASE
        ),
        "TRANSICIONES": re.compile(r"TRANSICIONES\s*:\s*", re.IGNORECASE)
    }
    # Tres elementos separados por comas: origen, símbolo y destino.
    patron_transicion = re.compile(
        rf"({elemento})\s*,\s*({elemento})\s*,\s*({elemento})"
    )
    secciones_encontradas = set()
    secciones_esperadas = set(patrones_secciones)
    valores_secciones = {}
    transiciones_temporales = []

    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
    except FileNotFoundError:
        raise FileNotFoundError(f"No se encontró el archivo: {ruta_archivo}")
    except Exception as e:
        raise Exception(f"Error al leer el archivo: {e}")

    # ETAPA 1: reconocer la sintaxis y guardar los datos temporalmente.
    for num_linea, linea_raw in enumerate(lineas, start=1):
        linea = linea_raw.strip()
        if not linea:
            continue

        # Primero se comprueba si la línea es una sección principal.
        seccion_actual = None
        coincidencia = None
        for nombre_seccion, patron in patrones_secciones.items():
            resultado = patron.fullmatch(linea)
            if resultado:
                seccion_actual = nombre_seccion
                coincidencia = resultado
                break

        if seccion_actual:
            if seccion_actual in secciones_encontradas:
                raise SyntaxError(
                    f"Error de sintaxis en línea {num_linea}: "
                    f"la sección {seccion_actual} está repetida."
                )
            if modo_transiciones:
                raise SyntaxError(
                    f"Error de sintaxis en línea {num_linea}: no se permiten "
                    f"secciones después de TRANSICIONES: '{linea}'"
                )

            secciones_encontradas.add(seccion_actual)
            if seccion_actual == "TRANSICIONES":
                modo_transiciones = True
            else:
                valores_secciones[seccion_actual] = (
                    coincidencia.group(1), num_linea
                )
            continue

        if modo_transiciones:
            coincidencia = patron_transicion.fullmatch(linea)
            if not coincidencia:
                raise SyntaxError(
                    f"Error de sintaxis en línea {num_linea}: '{linea}'"
                )
            transiciones_temporales.append((num_linea,) + coincidencia.groups())
            continue

        raise SyntaxError(f"Error de sintaxis en línea {num_linea}: '{linea}'")

    faltantes = secciones_esperadas - secciones_encontradas
    if faltantes:
        raise ValueError(
            f"Faltan las siguientes secciones: {', '.join(sorted(faltantes))}."
        )

    # ETAPA 2: construir el AFD y validar relaciones entre sus componentes.
    afd.nombre = valores_secciones["NOMBRE"][0]

    estados_str, linea_estados = valores_secciones["ESTADOS"]
    estados = [e.strip() for e in estados_str.split(",")]
    duplicados = {e for e in estados if estados.count(e) > 1}
    if duplicados:
        raise ValueError(
            f"Línea {linea_estados}: estados duplicados: {sorted(duplicados)}."
        )
    afd.Q = set(estados)

    sigma_str, linea_sigma = valores_secciones["ALFABETO"]
    sigma = [s.strip() for s in sigma_str.split(",")]
    duplicados = {s for s in sigma if sigma.count(s) > 1}
    if duplicados:
        raise ValueError(
            f"Línea {linea_sigma}: símbolos duplicados: {sorted(duplicados)}."
        )
    if any(s.casefold() in {"ε", "epsilon"} for s in sigma):
        raise ValueError(
            f"Línea {linea_sigma}: ε no puede formar parte del alfabeto de un AFD."
        )
    afd.Sigma = set(sigma)

    q0, linea_inicial = valores_secciones["INICIAL"]
    if q0 not in afd.Q:
        raise ValueError(
            f"Línea {linea_inicial}: el estado inicial '{q0}' no pertenece a Q."
        )
    afd.q0 = q0

    finales_str, linea_finales = valores_secciones["FINALES"]
    finales = []
    if finales_str:
        finales = [f.strip() for f in finales_str.split(",")]
    duplicados = {f for f in finales if finales.count(f) > 1}
    if duplicados:
        raise ValueError(
            f"Línea {linea_finales}: estados finales duplicados: "
            f"{sorted(duplicados)}."
        )
    finales_invalidos = sorted(f for f in finales if f not in afd.Q)
    if len(finales_invalidos) == 1:
        raise ValueError(
            f"Línea {linea_finales}: el estado final "
            f"'{finales_invalidos[0]}' no pertenece a Q."
        )
    if len(finales_invalidos) > 1:
        raise ValueError(
            f"Línea {linea_finales}: los estados finales "
            f"{finales_invalidos} no pertenecen a Q."
        )
    afd.F = set(finales)

    for num_linea, origen, simbolo, destino in transiciones_temporales:
        if origen not in afd.Q:
            raise ValueError(
                f"Línea {num_linea}: el estado origen '{origen}' no pertenece a Q."
            )
        if simbolo.casefold() in {"ε", "epsilon"}:
            raise ValueError(
                f"Línea {num_linea}: un AFD no permite transiciones ε."
            )
        if simbolo not in afd.Sigma:
            raise ValueError(
                f"Línea {num_linea}: el símbolo '{simbolo}' no pertenece al alfabeto."
            )
        if destino not in afd.Q:
            raise ValueError(
                f"Línea {num_linea}: el estado destino '{destino}' no pertenece a Q."
            )
        try:
            afd.agregar_transicion(origen, simbolo, destino)
        except ValueError as e:
            raise ValueError(
                f"Línea {num_linea}: la transición ({origen}, {simbolo}) "
                f"tiene más de un destino; corresponde a un AFND y no a un AFD."
            ) from e

    # Validaciones básicas después de la construcción.
    if not afd.Q:
        raise ValueError("No se definieron estados (Q).")
    if not afd.Sigma:
        raise ValueError("No se definió el alfabeto (Σ).")
    if afd.q0 is None:
        raise ValueError("No se definió el estado inicial (q0).")

    return afd


def cargar_manual_afnd():
    """Solicita por consola los cinco componentes y transiciones de un AFND."""
    print("\n--- CREACIÓN MANUAL DE AFND ---")
    afnd = AFND(input("Nombre o identificador del autómata: ").strip())

    while True:
        texto = input("Ingrese los estados (separados por comas): ").strip()
        estados = [e.strip() for e in texto.split(",") if e.strip()]
        duplicados = {e for e in estados if estados.count(e) > 1}
        if not estados:
            print("Debe ingresar al menos un estado.")
        elif duplicados:
            print(f"Error: estados duplicados: {sorted(duplicados)}. Intente de nuevo.")
        else:
            afnd.Q = set(estados)
            break

    while True:
        texto = input("Ingrese el alfabeto (símbolos separados por comas): ").strip()
        simbolos = [s.strip() for s in texto.split(",") if s.strip()]
        duplicados = {s for s in simbolos if simbolos.count(s) > 1}
        if not simbolos:
            print("Debe ingresar al menos un símbolo.")
        elif duplicados:
            print(f"Error: símbolos duplicados: {sorted(duplicados)}. Intente de nuevo.")
        elif any(es_epsilon(s) for s in simbolos):
            print("Error: ε no puede formar parte del alfabeto de un AFND.")
        else:
            afnd.Sigma = set(simbolos)
            break

    while True:
        q0 = input("Ingrese el estado inicial: ").strip()
        if q0 in afnd.Q:
            afnd.q0 = q0
            break
        print(f"Error: '{q0}' no está en el conjunto de estados. Intente de nuevo.")

    while True:
        texto = input("Ingrese los estados finales (separados por comas): ").strip()
        if not texto:
            afnd.F = set()
            break
        finales = [f.strip() for f in texto.split(",") if f.strip()]
        duplicados = {f for f in finales if finales.count(f) > 1}
        if duplicados:
            print(f"Error: estados finales duplicados: {sorted(duplicados)}. Intente de nuevo.")
        elif not set(finales).issubset(afnd.Q):
            print("Error: uno o más estados finales no pertenecen a Q. Intente de nuevo.")
        else:
            afnd.F = set(finales)
            break

    patron = re.compile(r"([^,\s]+)\s*,\s*([^,\s]+)\s*,\s*([^,\s]+(?:\s*\|\s*[^,\s]+)*)")
    print("\nIngrese transiciones: origen, símbolo, destino1|destino2")
    print("Use ∅ para indicar ausencia de destinos y 'fin' para terminar.")
    while True:
        linea = input("Transición: ").strip()
        if linea.lower() == "fin":
            break
        coincidencia = patron.fullmatch(linea)
        if not coincidencia:
            print("Formato incorrecto. Debe ser: origen, símbolo, destino(s)")
            continue
        origen, simbolo, destinos_str = coincidencia.groups()
        if origen not in afnd.Q:
            print(f"Error: '{origen}' no está en Q.")
            continue
        if es_epsilon(simbolo) or es_epsilon(destinos_str):
            print("Error: las transiciones ε no están permitidas.")
            continue
        if simbolo not in afnd.Sigma:
            print(f"Error: '{simbolo}' no está en Σ.")
            continue
        if destinos_str == "∅":
            destinos = set()
        else:
            lista_destinos = [d.strip() for d in destinos_str.split("|")]
            if any(es_epsilon(d) for d in lista_destinos):
                print("Error: las transiciones ε no están permitidas.")
                continue
            destinos = set(lista_destinos)
            invalidos = destinos - afnd.Q
            if invalidos:
                print(f"Error: destinos no declarados en Q: {sorted(invalidos)}")
                continue
        afnd.agregar_transicion(origen, simbolo, destinos)
        print("Transición agregada.")

    return afnd


def cargar_desde_archivo_afnd(ruta_archivo):
    """Carga un AFND con regex, primero sintaxis y luego semántica."""
    elemento = r"[^,\s|]+"
    lista = rf"({elemento}(?:\s*,\s*{elemento})*)"
    patrones = {
        "NOMBRE": re.compile(r"NOMBRE\s*=\s*(\S+)\s*", re.IGNORECASE),
        "TIPO": re.compile(r"TIPO\s*=\s*(AFND)\s*", re.IGNORECASE),
        "ESTADOS": re.compile(rf"ESTADOS\s*=\s*{lista}\s*", re.IGNORECASE),
        "ALFABETO": re.compile(rf"ALFABETO\s*=\s*{lista}\s*", re.IGNORECASE),
        "INICIAL": re.compile(rf"INICIAL\s*=\s*({elemento})\s*", re.IGNORECASE),
        "FINALES": re.compile(
            rf"FINALES\s*=\s*({elemento}(?:\s*,\s*{elemento})*)?\s*",
            re.IGNORECASE
        ),
        "TRANSICIONES": re.compile(r"TRANSICIONES\s*:\s*", re.IGNORECASE)
    }
    patron_transicion = re.compile(
        rf"({elemento})\s*,\s*({elemento})\s*,\s*(∅|{elemento}(?:\s*\|\s*{elemento})*)"
    )
    encontrados = set()
    valores = {}
    transiciones = []
    modo_transiciones = False

    try:
        with open(ruta_archivo, "r", encoding="utf-8") as archivo:
            lineas = archivo.readlines()
    except FileNotFoundError:
        raise FileNotFoundError(f"No se encontró el archivo: {ruta_archivo}")
    except Exception as e:
        raise Exception(f"Error al leer el archivo: {e}")

    # Primera etapa: reconocer líneas completas y guardar datos temporales.
    for num_linea, linea_raw in enumerate(lineas, start=1):
        linea = linea_raw.strip()
        if not linea:
            continue
        seccion = None
        coincidencia = None
        for nombre, patron in patrones.items():
            resultado = patron.fullmatch(linea)
            if resultado:
                seccion = nombre
                coincidencia = resultado
                break
        if seccion:
            if seccion in encontrados:
                raise SyntaxError(
                    f"Error de sintaxis en línea {num_linea}: la sección {seccion} está repetida."
                )
            if modo_transiciones:
                raise SyntaxError(
                    f"Error de sintaxis en línea {num_linea}: no se permiten secciones "
                    "después de TRANSICIONES."
                )
            encontrados.add(seccion)
            if seccion == "TRANSICIONES":
                modo_transiciones = True
            else:
                valores[seccion] = (coincidencia.group(1), num_linea)
            continue
        if modo_transiciones:
            coincidencia = patron_transicion.fullmatch(linea)
            if not coincidencia:
                raise SyntaxError(f"Error de sintaxis en línea {num_linea}: '{linea}'")
            transiciones.append((num_linea,) + coincidencia.groups())
            continue
        raise SyntaxError(f"Error de sintaxis en línea {num_linea}: '{linea}'")

    faltantes = set(patrones) - encontrados
    if faltantes:
        raise ValueError(f"Faltan las siguientes secciones: {', '.join(sorted(faltantes))}.")

    # Segunda etapa: construir conjuntos y comprobar relaciones semánticas.
    afnd = AFND(valores["NOMBRE"][0])
    estados_str, linea_estados = valores["ESTADOS"]
    estados = [e.strip() for e in estados_str.split(",")]
    duplicados = {e for e in estados if estados.count(e) > 1}
    if duplicados:
        raise ValueError(f"Línea {linea_estados}: estados duplicados: {sorted(duplicados)}.")
    afnd.Q = set(estados)

    sigma_str, linea_sigma = valores["ALFABETO"]
    sigma = [s.strip() for s in sigma_str.split(",")]
    duplicados = {s for s in sigma if sigma.count(s) > 1}
    if duplicados:
        raise ValueError(f"Línea {linea_sigma}: símbolos duplicados: {sorted(duplicados)}.")
    if any(es_epsilon(s) for s in sigma):
        raise ValueError(f"Línea {linea_sigma}: ε no puede formar parte del alfabeto de un AFND.")
    afnd.Sigma = set(sigma)

    q0, linea_inicial = valores["INICIAL"]
    if q0 not in afnd.Q:
        raise ValueError(f"Línea {linea_inicial}: el estado inicial '{q0}' no pertenece a Q.")
    afnd.q0 = q0

    finales_str, linea_finales = valores["FINALES"]
    finales = [] if not finales_str else [f.strip() for f in finales_str.split(",")]
    duplicados = {f for f in finales if finales.count(f) > 1}
    if duplicados:
        raise ValueError(
            f"Línea {linea_finales}: estados finales duplicados: {sorted(duplicados)}."
        )
    invalidos = sorted(set(finales) - afnd.Q)
    if invalidos:
        raise ValueError(
            f"Línea {linea_finales}: estados finales que no pertenecen a Q: {invalidos}."
        )
    afnd.F = set(finales)

    for num_linea, origen, simbolo, destinos_str in transiciones:
        if origen not in afnd.Q:
            raise ValueError(f"Línea {num_linea}: el estado origen '{origen}' no pertenece a Q.")
        if es_epsilon(simbolo) or es_epsilon(destinos_str):
            raise ValueError(f"Línea {num_linea}: las transiciones ε no están permitidas.")
        if simbolo not in afnd.Sigma:
            raise ValueError(f"Línea {num_linea}: el símbolo '{simbolo}' no pertenece al alfabeto.")
        if destinos_str == "∅":
            destinos = set()
        else:
            lista_destinos = [d.strip() for d in destinos_str.split("|")]
            if any(es_epsilon(d) for d in lista_destinos):
                raise ValueError(
                    f"Línea {num_linea}: las transiciones ε no están permitidas."
                )
            destinos = set(lista_destinos)
            invalidos = sorted(destinos - afnd.Q)
            if invalidos:
                raise ValueError(
                    f"Línea {num_linea}: estados destino que no pertenecen a Q: {invalidos}."
                )
        afnd.agregar_transicion(origen, simbolo, destinos)

    return afnd


# ========================== VALIDACIÓN Y ANÁLISIS ESTRUCTURAL ==========================
def validar_afd(afd):
    """
    Verifica la integridad del AFD:
    - q0 ∈ Q
    - F ⊆ Q
    - Transiciones consistentes
    - Determinismo: exactamente una transición por par (estado, símbolo)
    Retorna una lista de errores (vacía si todo es correcto).
    """
    errores = []

    if afd.q0 not in afd.Q:
        errores.append(f"El estado inicial '{afd.q0}' no pertenece a Q.")

    if not afd.F.issubset(afd.Q):
        no_pertenecen = afd.F - afd.Q
        errores.append(f"Los siguientes estados finales no pertenecen a Q: {no_pertenecen}")

    for (origen, simbolo), destino in afd.delta.items():
        # Epsilon convertiría la transición en una característica de un AFND-ε.
        if simbolo.casefold() in {"ε", "epsilon"}:
            errores.append("Un AFD no permite transiciones ε.")
        if origen not in afd.Q:
            errores.append(f"En transición ({origen}, {simbolo}) -> {destino}: origen no está en Q.")
        if simbolo not in afd.Sigma:
            errores.append(f"En transición ({origen}, {simbolo}) -> {destino}: símbolo no está en Σ.")
        if destino not in afd.Q:
            errores.append(f"En transición ({origen}, {simbolo}) -> {destino}: destino no está en Q.")

    # Determinismo: verificar que exista transición para cada par
    for estado in afd.Q:
        for simbolo in afd.Sigma:
            if (estado, simbolo) not in afd.delta:
                errores.append(f"Falta transición para el par ({estado}, {simbolo}).")

    return errores


def validar_afnd(afnd):
    """Valida la integridad de un AFND sin exigir una transición por cada par."""
    errores = []
    if afnd.q0 not in afnd.Q:
        errores.append(f"El estado inicial '{afnd.q0}' no pertenece a Q.")
    if not afnd.F.issubset(afnd.Q):
        errores.append(f"Estados finales fuera de Q: {sorted(afnd.F - afnd.Q)}.")
    if any(es_epsilon(s) for s in afnd.Sigma):
        errores.append("ε no puede formar parte del alfabeto de un AFND.")
    for (origen, simbolo), destinos in afnd.delta.items():
        if origen not in afnd.Q:
            errores.append(f"En ({origen}, {simbolo}): el origen no pertenece a Q.")
        if es_epsilon(simbolo):
            errores.append("Las transiciones ε no están permitidas.")
        elif simbolo not in afnd.Sigma:
            errores.append(f"En ({origen}, {simbolo}): el símbolo no pertenece a Σ.")
        invalidos = destinos - afnd.Q
        if invalidos:
            errores.append(
                f"En ({origen}, {simbolo}): destinos fuera de Q: {sorted(invalidos)}."
            )
    return errores


def convertir_afnd_a_afd(afnd):
    """Convierte un AFND a AFD mediante construcción manual de subconjuntos."""
    errores = validar_afnd(afnd)
    if errores:
        raise ValueError("No se puede convertir un AFND inválido.")

    subconjunto_inicial = frozenset({afnd.q0})
    nombres = {}
    pendientes = []
    procesados = set()

    def registrar(subconjunto):
        if subconjunto not in nombres:
            nombres[subconjunto] = generar_nombre_macroestado(len(nombres))
            pendientes.append(subconjunto)
        return nombres[subconjunto]

    registrar(subconjunto_inicial)
    afd = AFD(f"{afnd.nombre}_AFD")
    afd.Sigma = set(afnd.Sigma)

    while pendientes:
        macroestado = pendientes.pop(0)
        if macroestado in procesados:
            continue
        procesados.add(macroestado)
        nombre_origen = nombres[macroestado]
        afd.Q.add(nombre_origen)

        for simbolo in sorted(afnd.Sigma):
            union_destinos = set()
            for estado in macroestado:
                union_destinos.update(afnd.obtener_destinos(estado, simbolo))
            destino = frozenset(union_destinos)
            nombre_destino = registrar(destino)
            afd.delta[(nombre_origen, simbolo)] = nombre_destino

    afd.q0 = nombres[subconjunto_inicial]
    for subconjunto, nombre in nombres.items():
        afd.Q.add(nombre)
        if subconjunto.intersection(afnd.F):
            afd.F.add(nombre)

    equivalencias = {
        nombre: subconjunto for subconjunto, nombre in nombres.items()
    }
    return afd, equivalencias


def imprimir_tabla_equivalencias(equivalencias):
    """Muestra la relación entre nombres del AFD y subconjuntos del AFND."""
    print("\n--- TABLA DE EQUIVALENCIAS ---")
    print("Macroestado AFD | Estados AFND")
    print("-" * 42)
    for nombre in sorted(equivalencias):
        estados = equivalencias[nombre]
        representacion = "∅" if not estados else "{" + ",".join(sorted(estados)) + "}"
        print(f"{nombre:<15} | {representacion}")


def completar_con_estado_trampa(afd, transiciones_faltantes):
    """Completa un AFD enviando las transiciones faltantes a un estado de trampa."""
    nombre_trampa = "TRAMPA"
    numero = 1
    while nombre_trampa in afd.Q:
        nombre_trampa = f"TRAMPA_{numero}"
        numero += 1

    afd.Q.add(nombre_trampa)

    # Cada transición faltante dirige al estado de trampa.
    for estado, simbolo in transiciones_faltantes:
        afd.delta[(estado, simbolo)] = nombre_trampa

    # Una vez en el estado de trampa, cualquier símbolo permanece en él.
    for simbolo in afd.Sigma:
        afd.delta[(nombre_trampa, simbolo)] = nombre_trampa

    return nombre_trampa


def analizar_estructura(afd):
    """
    Calcula estados alcanzables, inaccesibles, finales alcanzables y si el lenguaje es vacío.
    Actualiza los atributos del objeto AFD.
    """
    if afd.q0 not in afd.Q:
        afd.estados_alcanzables = set()
        afd.estados_inaccesibles = afd.Q.copy()
        afd.finales_alcanzables = set()
        afd.lenguaje_vacio = True
        return {
            "alcanzables": set(),
            "inaccesibles": afd.Q.copy(),
            "finales_alcanzables": set(),
            "lenguaje_vacio": True
        }

    # BFS con lista (sin usar collections.deque)
    alcanzables = set()
    cola = [afd.q0]
    alcanzables.add(afd.q0)
    idx = 0
    while idx < len(cola):
        estado = cola[idx]
        idx += 1
        for simbolo in afd.Sigma:
            destino = afd.delta.get((estado, simbolo))
            if destino is not None and destino not in alcanzables:
                alcanzables.add(destino)
                cola.append(destino)

    inaccesibles = afd.Q - alcanzables
    finales_alcanzables = afd.F.intersection(alcanzables)
    lenguaje_vacio = (len(finales_alcanzables) == 0)

    afd.estados_alcanzables = alcanzables
    afd.estados_inaccesibles = inaccesibles
    afd.finales_alcanzables = finales_alcanzables
    afd.lenguaje_vacio = lenguaje_vacio

    return {
        "alcanzables": alcanzables,
        "inaccesibles": inaccesibles,
        "finales_alcanzables": finales_alcanzables,
        "lenguaje_vacio": lenguaje_vacio
    }


# ========================== SIMULACIÓN ==========================
def simular(afd, cadena):
    """
    Simula el AFD con la cadena de entrada.
    Retorna un diccionario con:
        - aceptada: bool
        - traza: lista de pasos (cada paso: estado, simbolo, destino)
        - estado_final: str
    """
    # Validar símbolos
    for simbolo in cadena:
        if simbolo not in afd.Sigma:
            raise ValueError(f"El símbolo '{simbolo}' no pertenece al alfabeto {afd.Sigma}")

    estado_actual = afd.q0
    traza = []
    for simbolo in cadena:
        destino = afd.delta.get((estado_actual, simbolo))
        if destino is None:
            raise ValueError(f"No hay transición definida para ({estado_actual}, {simbolo})")
        traza.append({
            "estado": estado_actual,
            "simbolo": simbolo,
            "destino": destino
        })
        estado_actual = destino

    aceptada = estado_actual in afd.F
    return {
        "aceptada": aceptada,
        "traza": traza,
        "estado_final": estado_actual
    }


def imprimir_traza(resultado, cadena):
    """
    Imprime en consola la traza de la simulación.
    """
    print("\n--- TRAZA DE EJECUCIÓN ---")
    cadena_mostrada = "ε" if cadena == "" else f"'{cadena}'"
    print(f"Cadena evaluada: {cadena_mostrada}")
    for i, paso in enumerate(resultado["traza"], start=1):
        print(f"Paso {i}: Estado actual: {paso['estado']}, "
              f"Símbolo: '{paso['simbolo']}', Siguiente estado: {paso['destino']}")
    print(f"Estado final: {resultado['estado_final']}")
    if resultado["aceptada"]:
        print("VEREDICTO: ACEPTADA ✅")
    else:
        print("VEREDICTO: RECHAZADA ❌")
    print("-" * 30)


# ========================== HISTORIAL ==========================
def agregar_historial(afd, cadena, resultado):
    """
    Agrega una entrada al historial del AFD.
    """
    entrada = {
        "cadena": cadena,
        "aceptada": resultado["aceptada"],
        "estado_final": resultado["estado_final"],
        "traza": resultado["traza"]
    }
    afd.historial.append(entrada)


def mostrar_historial(afd):
    """
    Muestra el historial de evaluaciones.
    """
    if not afd.historial:
        print("\nNo hay evaluaciones en el historial.")
        return
    print("\n--- HISTORIAL DE EVALUACIONES ---")
    for i, entrada in enumerate(afd.historial, start=1):
        estado = "ACEPTADA ✅" if entrada["aceptada"] else "RECHAZADA ❌"
        cadena_mostrada = "ε" if entrada["cadena"] == "" else f"'{entrada['cadena']}'"
        print(f"{i}. Cadena: {cadena_mostrada} -> {estado} "
              f"(Estado final: {entrada['estado_final']})")
    print("-" * 30)


# ========================== MENÚ PRINCIPAL ==========================
class EstadoSesion:
    """Mantiene separados el autómata original y el resultado convertido."""
    def __init__(self):
        self.reiniciar()

    def reiniciar(self):
        self.afd_directo = None
        self.afnd = None
        self.afd_generado = None
        self.equivalencias = None

    def afd_activo(self):
        if self.afd_generado is not None:
            return self.afd_generado
        return self.afd_directo


def imprimir_tabla(header, filas, titulo):
    print(f"\n--- {titulo} ---")
    print(" | ".join(header))
    print("-" * (len(header) * 8))
    for fila in filas:
        print(" | ".join(str(valor) for valor in fila))


def mostrar_menu():
    """Muestra el menú principal."""
    print("\n" + "=" * 62)
    print("   MOTOR DE AFD, AFND Y CONVERSIÓN POR SUBCONJUNTOS")
    print("=" * 62)
    print("1. Crear AFD manualmente")
    print("2. Cargar AFD desde archivo .txt")
    print("3. Crear AFND manualmente")
    print("4. Cargar AFND desde archivo .txt")
    print("5. Mostrar definición formal y tabla del autómata cargado")
    print("6. Validar estructura")
    print("7. Convertir AFND a AFD")
    print("8. Mostrar tabla de equivalencias")
    print("9. Mostrar tabla del AFD generado")
    print("10. Evaluar cadena")
    print("11. Evaluar archivo de cadenas")
    print("12. Historial")
    print("13. Análisis estructural")
    print("14. Cargar o crear otro autómata")
    print("15. Salir")
    print("-" * 62)


def menu_principal():
    """Bucle principal del menú."""
    sesion = EstadoSesion()

    while True:
        mostrar_menu()
        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            nuevo = cargar_manual()
            sesion.reiniciar()
            sesion.afd_directo = nuevo
            print("\nAFD creado exitosamente.")
            input("Presione Enter para continuar...")

        elif opcion == "2":
            ruta = input("Ingrese la ruta del archivo .txt: ").strip()
            try:
                nuevo = cargar_desde_archivo(ruta)
                sesion.reiniciar()
                sesion.afd_directo = nuevo
                print(f"\nAFD cargado exitosamente desde '{ruta}'.")
            except Exception as e:
                print(f"\nError: {e}")
            input("Presione Enter para continuar...")

        elif opcion == "3":
            nuevo = cargar_manual_afnd()
            sesion.reiniciar()
            sesion.afnd = nuevo
            print("\nAFND creado exitosamente.")
            input("Presione Enter para continuar...")

        elif opcion == "4":
            ruta = input("Ingrese la ruta del archivo .txt: ").strip()
            try:
                nuevo = cargar_desde_archivo_afnd(ruta)
                sesion.reiniciar()
                sesion.afnd = nuevo
                print(f"\nAFND cargado exitosamente desde '{ruta}'.")
            except Exception as e:
                print(f"\nError: {e}")
            input("Presione Enter para continuar...")

        elif opcion == "5":
            if sesion.afnd is None and sesion.afd_activo() is None:
                print("\nPrimero debe crear o cargar un autómata.")
            if sesion.afnd is not None:
                print("\n--- DEFINICIÓN FORMAL DEL AFND ORIGINAL ---")
                print(sesion.afnd)
                imprimir_tabla(*sesion.afnd.tabla_transiciones(), "TABLA DEL AFND")
            afd = sesion.afd_activo()
            if afd is not None:
                titulo = "AFD GENERADO" if sesion.afd_generado else "AFD CARGADO"
                print(f"\n--- DEFINICIÓN FORMAL DEL {titulo} ---")
                print(afd)
                imprimir_tabla(*afd.tabla_transiciones(), f"TABLA DEL {titulo}")
            input("Presione Enter para continuar...")

        elif opcion == "6":
            if sesion.afnd is None and sesion.afd_activo() is None:
                print("\nPrimero debe crear o cargar un autómata.")
            if sesion.afnd is not None:
                errores = validar_afnd(sesion.afnd)
                if errores:
                    print("\nEl AFND es inválido:")
                    for error in errores:
                        print(f"  - {error}")
                else:
                    print("\n✅ El AFND es formalmente válido.")
            afd = sesion.afd_activo()
            if afd is not None:
                errores = validar_afd(afd)
                faltantes = [(q, s) for q in afd.Q for s in afd.Sigma
                             if (q, s) not in afd.delta]
                otros_errores = [e for e in errores if not e.startswith("Falta transición")]
                if otros_errores:
                    print("\nEl AFD es inválido:")
                    for error in errores:
                        print(f"  - {error}")
                elif faltantes:
                    print("\nEl AFD es determinista, pero está incompleto:")
                    for error in errores:
                        print(f"  - {error}")
                    respuesta = input(
                        "¿Desea completar el AFD utilizando un estado de trampa? (S/N): "
                    ).strip().upper()
                    if respuesta == "S":
                        nombre = completar_con_estado_trampa(afd, faltantes)
                        print(f"Se creó el estado de trampa '{nombre}'.")
                        if not validar_afd(afd):
                            print("✅ El AFD ahora es válido, completo y determinista.")
                else:
                    print("\n✅ El AFD es válido, completo y determinista.")
            input("Presione Enter para continuar...")

        elif opcion == "7":
            if sesion.afnd is None:
                print("\nNo hay un AFND cargado para convertir.")
            else:
                errores = validar_afnd(sesion.afnd)
                if errores:
                    print("\nEl AFND es inválido y no puede convertirse:")
                    for error in errores:
                        print(f"  - {error}")
                else:
                    sesion.afd_generado, sesion.equivalencias = convertir_afnd_a_afd(
                        sesion.afnd
                    )
                    print("\nConversión realizada correctamente.")
                    imprimir_tabla_equivalencias(sesion.equivalencias)
            input("Presione Enter para continuar...")

        elif opcion == "8":
            if sesion.equivalencias is None:
                print("\nPrimero debe convertir un AFND.")
            else:
                imprimir_tabla_equivalencias(sesion.equivalencias)
            input("Presione Enter para continuar...")

        elif opcion == "9":
            if sesion.afd_generado is None:
                print("\nPrimero debe convertir un AFND.")
            else:
                imprimir_tabla(
                    *sesion.afd_generado.tabla_transiciones(),
                    "TABLA DE TRANSICIÓN DEL AFD GENERADO"
                )
            input("Presione Enter para continuar...")

        elif opcion == "10":
            afd = sesion.afd_activo()
            if afd is None:
                print("\nNo hay un AFD disponible. Convierta primero el AFND.")
            elif validar_afd(afd):
                print("\nEl AFD no está completo y válido. Use la opción 6.")
            else:
                cadena = input("Ingrese la cadena a evaluar: ").strip()
                try:
                    resultado = simular(afd, cadena)
                    imprimir_traza(resultado, cadena)
                    agregar_historial(afd, cadena, resultado)
                except Exception as e:
                    print(f"Error: {e}")
            input("Presione Enter para continuar...")

        elif opcion == "11":
            afd = sesion.afd_activo()
            if afd is None:
                print("\nNo hay un AFD disponible. Convierta primero el AFND.")
            elif validar_afd(afd):
                print("\nEl AFD no está completo y válido. Use la opción 6.")
            else:
                ruta = input("Ingrese la ruta del archivo con cadenas: ").strip()
                try:
                    with open(ruta, "r", encoding="utf-8") as archivo:
                        cadenas = []
                        for linea in archivo:
                            cadena = linea.strip()
                            if not cadena:
                                continue
                            if cadena.casefold() in {"ε", "epsilon"}:
                                cadena = ""
                            cadenas.append(cadena)
                    if not cadenas:
                        print("El archivo no contiene cadenas.")
                    for cadena in cadenas:
                        try:
                            resultado = simular(afd, cadena)
                            imprimir_traza(resultado, cadena)
                            agregar_historial(afd, cadena, resultado)
                        except Exception as e:
                            print(f"Error al evaluar '{cadena}': {e}")
                except Exception as e:
                    print(f"Error al leer el archivo: {e}")
            input("Presione Enter para continuar...")

        elif opcion == "12":
            afd = sesion.afd_activo()
            if afd is None:
                print("\nNo hay un AFD disponible. Convierta primero el AFND.")
            else:
                mostrar_historial(afd)
            input("Presione Enter para continuar...")

        elif opcion == "13":
            afd = sesion.afd_activo()
            if afd is None:
                print("\nNo hay un AFD disponible. Convierta primero el AFND.")
            elif validar_afd(afd):
                print("\nEl AFD no está completo y válido. Use la opción 6.")
            else:
                analisis = analizar_estructura(afd)
                print("\n--- ANÁLISIS ESTRUCTURAL ---")
                print(f"Estados alcanzables: {analisis['alcanzables']}")
                print(f"Estados inaccesibles: {analisis['inaccesibles']}")
                print(f"Finales alcanzables: {analisis['finales_alcanzables']}")
                print(f"Lenguaje vacío: {analisis['lenguaje_vacio']}")
            input("Presione Enter para continuar...")

        elif opcion == "14":
            sesion.reiniciar()
            print("\nAutómatas, equivalencias e historiales anteriores descartados.")
            input("Presione Enter para continuar...")

        elif opcion == "15":
            print("\nSaliendo del programa. ¡Hasta luego!")
            break

        else:
            print("\nOpción no válida. Intente de nuevo.")
            input("Presione Enter para continuar...")


# ========================== PUNTO DE ENTRADA ==========================
if __name__ == "__main__":
    menu_principal()
