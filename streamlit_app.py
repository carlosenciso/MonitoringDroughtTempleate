import streamlit as st
from streamlit_option_menu import option_menu
from apps import home, heatmap, upload  # import your app modules here

st.set_page_config(page_title="Streamlit Geospatial", layout="wide")

# A dictionary of apps in the format of {"App title": "App icon"}
# More icons can be found here: https://icons.getbootstrap.com

apps = [
    {"func": home.app, "title": "Home", "icon": "house"},
    {"func": heatmap.app, "title": "Heatmap", "icon": "map"},
    {"func": upload.app, "title": "Upload", "icon": "cloud-upload"},
]

titles = [app["title"] for app in apps]
titles_lower = [title.lower() for title in titles]
icons = [app["icon"] for app in apps]

params = st.experimental_get_query_params()

if "page" in params:
    default_index = int(titles_lower.index(params["page"][0].lower()))
else:
    default_index = 0

with st.sidebar:
    selected = option_menu(
        "Menu Principal",
        options=titles,
        icons=icons,
        menu_icon="cast",
        default_index=default_index,
    )

    st.sidebar.title("About")
    st.sidebar.info(
        """
        Este repositorio web [app](https://carlosenciso-monitoringdroughttempleate-streamlit-app-huiz8l.streamlit.app/) es gestionado 
        por [Carlos Enciso Ojeda](https://github.com/carlosenciso). Puede seguir mas publicaciones:
        [GitHub](https://github.com/carlosenciso) | [Twitter](https://mobile.twitter.com/ojeda_enciso_o) | [Gitlab](https://gitlab.com/cenciso) | [LinkedIn](https://www.linkedin.com/in/carlos-enciso-ojeda-63449998/).
        
        More menu icons: <https://icons.getbootstrap.com>
    """
    )

for app in apps:
    if app["title"] == selected:
        app["func"]()
        break
