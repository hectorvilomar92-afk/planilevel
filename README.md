# PLANI PRESENTACION LEVEL

Aplicación Streamlit para generar presentaciones educativas. Las cuentas se
gestionan con Supabase Auth. No hay registro público: el administrador crea
las cuentas de los clientes y ellos inician sesión con sus credenciales.

## Configuración de Supabase

1. Crea un proyecto en [Supabase](https://supabase.com/) o usa uno existente.
2. En el panel del proyecto, habilita el proveedor de autenticación **Email**.
3. Copia la **Project URL** y la clave pública **anon** (o **publishable**).
   No uses la `service_role` ni una clave secreta en la aplicación.
4. En Streamlit Community Cloud, abre la aplicación, entra a **Settings >
   Secrets** y agrega:

   ```toml
   SUPABASE_URL = "https://TU-PROYECTO.supabase.co"
   SUPABASE_ANON_KEY = "TU-CLAVE-PUBLICA"
   ```

5. Guarda los cambios y reinicia la aplicación. Para desarrollo local, coloca
   esas mismas variables en `.streamlit/secrets.toml`; ese archivo está
   excluido de Git.
6. En la pantalla de acceso, compara **Proyecto Supabase conectado** con el
   dominio de la **Project URL** que copiaste. Ambos deben pertenecer al mismo
   proyecto donde están las cuentas, por ejemplo
   `abcdefgh.supabase.co`. Si no coinciden, corrige `SUPABASE_URL` y
   `SUPABASE_ANON_KEY` en Secrets y reinicia la aplicación.

Si se actualizó el código y una pestaña todavía aparece autenticada, ciérrala
y abre la aplicación nuevamente. La versión actual invalida sesiones de acceso
guardadas por versiones anteriores y exige autenticar otra vez contra Supabase.

## Crear cuentas de clientes sin enviar correos

En **Authentication > Users**, crea cada usuario directamente desde el panel
de Supabase y establece su contraseña. Confirma la dirección del correo al
crear la cuenta (`email_confirm = true` si utilizas la Admin API). La creación
directa con `create_user` no envía correo de confirmación ni invitación.
Comparte las credenciales con el cliente de forma privada.

La aplicación solo permite iniciar sesión. Nunca configures la clave
`service_role` en Streamlit Secrets ni en el código de la aplicación.

## Si una cuenta nueva no puede iniciar sesión

- Confirma que estás creando el usuario en el mismo proyecto que aparece en
  **Proyecto Supabase conectado** dentro de la app.
- En **Authentication > Users**, verifica que el correo esté confirmado y que
  la contraseña sea la que estás probando. Restablece la contraseña desde el
  panel si no estás seguro.
- En **Authentication > Providers > Email**, confirma que Email esté activo.
- En Streamlit Cloud, comprueba que el **Main file path** apunte a este
  `app.py`, que la rama seleccionada tenga este código y que los Secrets
  correspondan al mismo proyecto. Guarda y vuelve a desplegar la aplicación.
- La app no permite crear cuentas ni consulta `usuarios.db`; las credenciales
  válidas son exclusivamente las administradas por Supabase Auth.
