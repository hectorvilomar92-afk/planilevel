import os
import requests
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError
from duckduckgo_search import DDGS
from pptx import Presentation
from pptx.util import Inches, Pt
from urllib.parse import urlparse

# Configuración de la interfaz web
st.set_page_config(
    page_title="Generador de Presentaciones Educativas",
    page_icon="🎓",
    layout="centered",
)

# --- INICIO DE SESIÓN ---
class ErrorAutenticacion(Exception):
  pass


def obtener_configuracion_supabase():
  try:
    url = st.secrets.get("SUPABASE_URL", "")
    clave = st.secrets.get("SUPABASE_ANON_KEY", "")
  except StreamlitSecretNotFoundError:
    url = ""
    clave = ""
  url = url or os.environ.get("SUPABASE_URL", "")
  clave = clave or os.environ.get("SUPABASE_ANON_KEY", "")
  return url.rstrip("/"), clave


def solicitar_autenticacion_supabase(endpoint, datos):
  url, clave = obtener_configuracion_supabase()
  respuesta = requests.post(
      f"{url}/auth/v1/{endpoint}",
      headers={"apikey": clave, "Content-Type": "application/json"},
      json=datos,
      timeout=20,
  )

  try:
    resultado = respuesta.json()
  except requests.exceptions.JSONDecodeError as error:
    raise ErrorAutenticacion(
        "El servicio de autenticación devolvió una respuesta no válida."
    ) from error

  if not respuesta.ok:
    mensaje = (
        resultado.get("msg")
        or resultado.get("message")
        or resultado.get("error_description")
        or resultado.get("error")
        or f"Error del servicio de autenticación (HTTP {respuesta.status_code})."
    )
    raise ErrorAutenticacion(str(mensaje))

  return resultado


def obtener_nombre_usuario(resultado, correo):
  usuario = resultado.get("user") or resultado
  metadatos = usuario.get("user_metadata") or {}
  return metadatos.get("full_name") or correo.split("@", maxsplit=1)[0]


SUPABASE_URL, SUPABASE_ANON_KEY = obtener_configuracion_supabase()
if not SUPABASE_URL or not SUPABASE_ANON_KEY:
  st.error(
      "Falta configurar Supabase. Añade SUPABASE_URL y SUPABASE_ANON_KEY "
      "en Secrets de Streamlit Cloud. Consulta README.md."
  )
  st.stop()

# Invalidate sessions created by older app versions that bypassed Supabase.
if st.session_state.get("version_autenticacion") != 1:
  st.session_state.pop("autenticado", None)
  st.session_state.pop("usuario", None)
  st.session_state.version_autenticacion = 1

if "autenticado" not in st.session_state:
  st.session_state.autenticado = False

if not st.session_state.autenticado:
  st.title("🔐 Acceso a la Plataforma Educativa")
  st.caption(
      f"Proyecto Supabase conectado: {urlparse(SUPABASE_URL).hostname}"
  )
  st.write(
      "Ingresa con el correo y la contraseña que te proporcionó el administrador."
  )

  with st.form("login_form"):
    correo_ingreso = st.text_input("Correo electrónico")
    contrasena_ingreso = st.text_input("Contraseña", type="password")
    entrar = st.form_submit_button("Ingresar")

    if entrar:
      try:
        resultado = solicitar_autenticacion_supabase(
            "token?grant_type=password",
            {
                "email": correo_ingreso.strip().lower(),
                "password": contrasena_ingreso,
            },
        )
        if not resultado.get("access_token") or not resultado.get("user"):
          raise ErrorAutenticacion(
              "Supabase no confirmó el inicio de sesión. Verifica el proyecto "
              "y vuelve a intentarlo."
          )
        st.session_state.autenticado = True
        st.session_state.usuario = obtener_nombre_usuario(
            resultado, correo_ingreso.strip()
        )
        st.rerun()
      except ErrorAutenticacion as error:
        mensaje = str(error)
        if "invalid login credentials" in mensaje.lower():
          mensaje = "Correo electrónico o contraseña incorrectos."
        elif "email not confirmed" in mensaje.lower():
          mensaje = (
              "La cuenta aún no está confirmada. Contacta al administrador."
          )
        st.error(mensaje)
      except requests.RequestException:
        st.error(
            "No se pudo conectar con el servicio de autenticación. "
            "Inténtalo de nuevo más tarde."
        )

  st.stop()

# --- APLICACIÓN PRINCIPAL ---
st.sidebar.success(f"Conectado como: **{st.session_state.usuario}**")
if st.sidebar.button("Cerrar Sesión"):
  st.session_state.pop("autenticado", None)
  st.session_state.pop("usuario", None)
  st.rerun()

st.title("🎓 Generador de Presentaciones con Enlaces de YouTube")
st.write(
    "Crea presentaciones automáticas con investigación web y links de videos de"
    " YouTube listos para exponer."
)

with st.form("form_presentacion"):
  tema = st.text_input(
      "¿Sobre qué tema o asignatura deseas la presentación?",
      "La Célula y sus Partes",
  )
  col1, col2 = st.columns(2)
  with col1:
    num_slides = st.slider(
        "Número de diapositivas", min_value=3, max_value=8, value=4
    )
  with col2:
    incluir_yt = st.checkbox(
        "Incluir enlaces de videos de YouTube", value=True
    )

  generar_btn = st.form_submit_button("🚀 Generar y Descargar Presentación")


# Función para buscar información y videos en la web
@st.cache_data(show_spinner=False)
def buscar_contenido_y_videos(query):
  texto_info = ""
  videos_encontrados = []
  try:
    with DDGS() as ddgs:
      res_texto = [r["body"] for r in ddgs.text(query, max_results=5)]
      if res_texto:
        texto_info = " ".join(res_texto)

      res_yt = [
          r
          for r in ddgs.text(
              f"site:youtube.com watch?v {query}", max_results=3
          )
      ]
      for v in res_yt:
        titulo_v = v.get("title", "Video educativo")
        url_v = v.get("href", "#")
        videos_encontrados.append({"titulo": titulo_v, "url": url_v})
  except Exception:
    pass

  return (
      texto_info
      or f"Contenido académico e investigativo de referencia sobre {query}.",
      videos_encontrados,
  )


if generar_btn:
  if not tema.strip():
    st.warning("Por favor, escribe un tema válido.")
  else:
    barra = st.progress(0)
    estado = st.empty()

    try:
      estado.text(
          "🌐 Investigando contenido y buscando videos en YouTube en tiempo"
          " real..."
      )
      barra.progress(30)
      informacion, lista_videos = buscar_contenido_y_videos(tema)

      estado.text("📝 Estructurando las diapositivas...")
      barra.progress(60)

      prs = Presentation()

      # Generar diapositivas de contenido
      for i in range(num_slides):
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        slide.shapes.title.text = f"Sección {i+1}: {tema}"
        slide.placeholders[1].text = (
            f"Desarrollo teórico y análisis del tema.\n\nInformación clave:"
            f" {informacion[:250]}..."
        )

      # Diapositiva final con los links de YouTube
      if incluir_yt and lista_videos:
        slide_yt = prs.slides.add_slide(prs.slide_layouts[1])
        slide_yt.shapes.title.text = "🎥 Enlaces de Videos en YouTube"
        detalle_yt = (
            "Recursos audiovisuales recomendados para complementar la"
            " clase:\n\n"
        )
        for v in lista_videos:
          detalle_yt += f"• {v['titulo']}\n  🔗 {v['url']}\n\n"
        slide_yt.placeholders[1].text = detalle_yt

      barra.progress(90)
      estado.text("📊 Compilando archivo PowerPoint...")

      # Guardar temporalmente en el entorno de ejecución para descarga inmediata
      archivo_salida = f"presentacion_{os.getpid()}.pptx"
      prs.save(archivo_salida)

      barra.progress(100)
      estado.text("¡Completado con éxito!")

      with open(archivo_salida, "rb") as f:
        st.success("🎉 ¡Tu presentación está lista para descargar!")
        st.download_button(
            label="📥 Descargar Presentación (.pptx)",
            data=f,
            file_name=f"{tema.replace(' ', '_')}.pptx",
            mime=(
                "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            ),
        )

      # Eliminar archivo del servidor inmediatamente después de habilitar la descarga
      if os.path.exists(archivo_salida):
        os.remove(archivo_salida)

    except Exception as err:
      st.error(f"Ocurrió un error: {err}")