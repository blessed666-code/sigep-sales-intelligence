# Methodology — segmentación de cargos

## Principio

No filtrar con un simple `contains("secretario")`. Se usan:

1. **Lista de inclusión** (roles de interés)
2. **Lista de exclusión** (ruido / no decisores)
3. **Límites de palabra** (`\b`) y normalización Unicode (sin tildes, mayúsculas)
4. **Overrides** cuando un término negativo aparece junto a mando alto  
   (ej. `DIRECTOR SECCIONAL DE FISCALIAS` se conserva; `FISCAL DELEGADO` no)

Campo primario: `Cargo_Detallado` (perfil individual).

## Inclusión (resumen)

- Ejecutivo territorial: alcalde, gobernador, …
- Dirección / gerencia: director(a), subdirector(a), gerente, subgerente
- Secretaría: todos los `SECRETARIO*`; `SECRETARIA` solo general / despacho / cartera
- Jefatura, coordinación, asesoría, liderazgo (según criterio comercial del proyecto)
- Control / representación: personero, contralor, procurador, registrador, concejal, …
- Perfiles TI explícitos: director TIC, arquitecto TI/empresarial, CIO (pocos en SIGEP)

## Exclusión (resumen)

- Planta operativa: auxiliar, técnico (salvo mando), docente, dragoneante, …
- Profesional universitario / especializado
- Contador, tesorero (salvo combo con secretario/director/gerente)
- Abogados / litigantes
- Defensor de familia, enfermería “jefe”, asesor comercial
- Fiscal / magistrado operativos (no dirección)

## Vigencia

`Fecha_Fin_Cargo`:

| Valor | Acción |
|-------|--------|
| `Actual` | Conservar |
| Fecha ≥ hoy | Conservar |
| Fecha pasada / `No especificada` | Descartar |

## Correo (email_ready)

Se descartan: vacío, `No reportado`, sin `@`, formato inválido.  
Se conservan correos con patrón básico `local@dominio.tld`.

## Por qué esta metodología

- Escala (~400k filas) sin clasificar fila a fila con LLM
- Criterios auditables y versionables en código
- Separación de canales: set completo limpio (LinkedIn) vs set con email (campañas)

## Limitaciones

- Calidad y homogeneidad de textos en SIGEP (typos, códigos, ruido)
- El HTML del portal puede cambiar y romper selectores del scraper
- Un cargo ambiguo puede colarse o quedar fuera; la taxonomía se itera con negocio
