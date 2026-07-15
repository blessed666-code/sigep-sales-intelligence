# Methodology — segmentación y preparación

## Principio (cargos)

No filtrar con un simple `contains("secretario")`. Se usan:

1. **Lista de inclusión** (roles de interés)
2. **Lista de exclusión** (ruido / no decisores)
3. **Límites de palabra** (`\b`) y normalización Unicode
4. **Overrides** cuando un término negativo aparece junto a mando alto  
   (ej. `DIRECTOR SECCIONAL DE FISCALIAS` se conserva; `FISCAL DELEGADO` no)

Campo primario: `Cargo_Detallado` (perfil individual).

## Inclusión (resumen)

- Ejecutivo territorial: alcalde, gobernador, …
- Dirección / gerencia: director(a), subdirector(a), gerente, subgerente
- Secretaría: todos los `SECRETARIO*`; `SECRETARIA` solo general / despacho / cartera
- Jefatura, coordinación, asesoría, liderazgo (criterio comercial)
- Control / representación: personero, contralor, procurador, registrador, concejal, …
- Perfiles TI explícitos: director TIC, arquitecto TI/empresarial, CIO

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

## Correo (`email_ready`)

Se descartan: vacío, `No reportado`, sin `@`, formato inválido.

## Tipografía y unificación (`normalize_contacts` + `text_format`)

- Encoding **UTF-8 con BOM** (`utf-8-sig`) para compatibilidad Excel / importadores
- Title case español con partículas (`de`, `del`, `la`, …)
- Glosario de tildes institucionales y apellidos frecuentes (sin inventar cargos)
- Correo en minúsculas
- Un solo archivo nacional; columnas: Departamento, Nombre, Cargo, Correo, Entidad_Asignada
- **1 fila por email** (omite buzones compartidos / duplicados SIGEP)
- Pulido visual de cargos: quita guiones decorativos; cortes SIGEP se marcan con punto (`Operac.` / `Fin.`) sin completar la palabra

## BillionMail (`billionmail_export`)

- Header exacto: `email,attributes`
- JSON en `attributes` con: `department`, `name`, `position`, `assigned_entity`
- Escapado CSV estándar (`""` dentro del campo)
- Ver sample sintético: `sample/sample_billionmail.csv`

## Por qué esta metodología

- Escala (~400k filas) sin clasificar fila a fila con LLM
- Criterios auditables en código
- Separación de canales: limpio completo (LinkedIn) vs email-ready vs import ESP

## Limitaciones

- Calidad heterogénea de textos en SIGEP (typos, códigos, truncados)
- El HTML del portal puede cambiar y romper el scraper
- Un cargo ambiguo puede colarse o quedar fuera; la taxonomía se itera con negocio
