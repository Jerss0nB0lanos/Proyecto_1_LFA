# Casos de prueba — Fase 2

Resultados obtenidos ejecutando el código de `ProyectoNo1_LFA.py` en la rama
`Samuel_fase2_reparacion`.

| # | Archivo utilizado | Qué se prueba | Resultado esperado | Resultado obtenido |
|---|---|---|---|---|
| 1 | `afd_valido.txt` | AFD válido y completo | Cero errores de validación | Cero errores |
| 2 | `afd_incompleto.txt` | Completar AFD incompleto | Crear `TRAMPA` y obtener un AFD completo | Se creó `TRAMPA`; validación sin errores |
| 3 | `afnd_prueba.txt` | AFND con múltiples destinos | `(q0,a)` debe producir `{q0,q1}` | Se obtuvo `{q0,q1}` |
| 4 | `afnd_prueba.txt` | Conversión con al menos tres macroestados | Tres o más subconjuntos alcanzables | Se obtuvieron 4: `A={q0}`, `B={q0,q1}`, `C={q0,q2}`, `D={q0,q1,q2}` |
| 5 | `afnd_vacio_prueba.txt` | Conversión que alcanza `∅` | Crear un macroestado para el vacío con ciclos propios | `C=∅`; `(C,a)=C` y `(C,b)=C`; AFD válido y completo |
| 6 | `afnd_prueba.txt` | Macroestado final mixto | Marcar como final todo subconjunto que contenga `q2` | `C={q0,q2}` y `D={q0,q1,q2}` quedaron finales |
| 7 | `afnd_prueba.txt` | Cadena aceptada | AFND y AFD aceptan `ab` | Ambos aceptaron `ab` |
| 8 | `afnd_prueba.txt` | Cadena rechazada | AFND y AFD rechazan `a` | Ambos rechazaron `a` |
| 9 | `afnd_prueba.txt` | Cadena vacía | Ambos obtienen el mismo resultado | Ambos rechazaron `ε` y permanecieron en sus estados iniciales equivalentes |
| 10 | `afnd_prueba.txt` | Símbolo fuera del alfabeto | Rechazar `c` | Error: el símbolo `c` no pertenece al alfabeto |
| 11 | `sintaxis_invalida.txt` | Error sintáctico | Informar línea incorrecta | `SyntaxError` en línea 1 |
| 12 | `origen_invalido.txt` | Estado inexistente | Rechazar origen no declarado | Error en línea 7: `q9` no pertenece a `Q` |
| 13 | `afnd_prueba.txt` | Comparación AFND original contra AFD generado | Mismo veredicto para todas las cadenas | Coincidieron en 9 de 9 cadenas |

## Comparación AFND contra AFD generado

La comprobación interna del AFND mantuvo un conjunto de estados actuales. Para
cada símbolo calculó la unión de destinos y aceptó cuando el conjunto final
intersectó `F`. Esta simulación se usó únicamente durante las pruebas y no se
agregó al menú.

| Cadena | AFND original | AFD generado |
|---|---|---|
| `ε` | Rechazada | Rechazada |
| `a` | Rechazada | Rechazada |
| `b` | Rechazada | Rechazada |
| `ab` | Aceptada | Aceptada |
| `aa` | Rechazada | Rechazada |
| `ba` | Rechazada | Rechazada |
| `bb` | Rechazada | Rechazada |
| `aab` | Aceptada | Aceptada |
| `abb` | Aceptada | Aceptada |

También se comprobó que el AFD generado tiene exactamente una transición para
cada combinación de macroestado y símbolo, que el historial registra las
evaluaciones, que el análisis estructural funciona y que la opción 14 limpia
AFD, AFND, tabla de equivalencias e historial de la sesión.
