# Proyecto de Lenguajes Formales y Autómatas — Fase 2

Programa de consola en Python para crear, cargar, validar y analizar AFD y
AFND. También convierte un AFND en un AFD equivalente mediante el algoritmo
de construcción de subconjuntos implementado en el proyecto.

## Ejecución

```bash
python3 ProyectoNo1_LFA/ProyectoNo1_LFA.py
```

## Formato de archivo AFD

```text
NOMBRE=AFD_EJEMPLO
ESTADOS=q0,q1
ALFABETO=a,b
INICIAL=q0
FINALES=q1
TRANSICIONES:
q0,a,q1
q0,b,q0
q1,a,q1
q1,b,q0
```

## Formato de archivo AFND

```text
NOMBRE=AFND_EJEMPLO
TIPO=AFND
ESTADOS=q0,q1
ALFABETO=a,b
INICIAL=q0
FINALES=q1
TRANSICIONES:
q0,a,q0|q1
q0,b,∅
q1,a,q1
q1,b,∅
```

`|` separa varios destinos y `∅` representa ausencia de destinos. El alcance
del proyecto no incluye transiciones epsilon.

La simulación recorre las cadenas carácter por carácter. Por ello, aunque el
formato no restringe expresamente la longitud de los símbolos, para evaluar
cadenas sin ambigüedad se recomienda usar símbolos de un solo carácter.

## Menú

1. Crear AFD manualmente.
2. Cargar AFD desde archivo.
3. Crear AFND manualmente.
4. Cargar AFND desde archivo.
5. Mostrar definición formal y tabla.
6. Validar estructura y completar AFD incompleto con TRAMPA.
7. Convertir AFND a AFD.
8. Mostrar tabla de equivalencias.
9. Mostrar tabla del AFD generado.
10. Evaluar cadena.
11. Evaluar archivo de cadenas.
12. Consultar historial.
13. Realizar análisis estructural.
14. Limpiar la sesión.
15. Salir.

## Archivos de prueba

Los archivos están en `ProyectoNo1_LFA/`. Entre ellos se incluyen AFD válido,
AFD incompleto, errores sintácticos y semánticos, AFND con múltiples destinos,
conversión con varios macroestados y conversión que alcanza `∅`.

Los resultados comprobados se documentan en
`ProyectoNo1_LFA/CASOS_PRUEBA_FASE2.md`.
