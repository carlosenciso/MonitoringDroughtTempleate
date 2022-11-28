import streamlit as st
import leafmap.foliumap as leafmap
import ee
import geemap.foliumap as geemap
import geopandas as gpd
import datetime
import geemap.colormaps as cm


class indicesGEE:
    def __init__(self, collect='MODIS/MOD09GA_006_NDVI',
                 bands='NDVI', aoieFeature=None):
        self.collect = collect
        self.bands = bands
        self.aoieFeature = aoieFeature

    def getcollection(self, initDate=None, endDate=None):
        self.imgCollection = ee.ImageCollection(self.collect)\
            .filterDate(initDate, endDate)\
            .filterBounds(self.aoieFeature.geometry())\
            .select(self.bands)\
            .median()\
            .clip(self.aoieFeature)


def app():
    st.title("Sequias Agrometeorológicas")

    st.markdown(
        """
    A [streamlit](https://streamlit.io) app template for geospatial applications based on [streamlit-option-menu](https://github.com/victoryhb/streamlit-option-menu). 
    To create a direct link to a pre-selected menu, add `?page=<app name>` to the URL, e.g., `?page=upload`.
    https://share.streamlit.io/giswqs/streamlit-template?page=upload

    """
    )
    row1_col1, row1_col2 = st.columns([2, 1])
    width, height = 950, 700
    with row1_col2:
        # -- Reading GJson --#
        depGjson = 'https://raw.githubusercontent.com/wmgeolab/geoBoundaries/d46566667e443b7a2e8e1ce6aa23cb15f26ff9dd/releaseData/gbOpen/PER/ADM1/geoBoundaries-PER-ADM1.geojson'
        gdf = gpd.read_file(depGjson)
        gjsonObj = list(gpd.read_file(depGjson)['shapeName'].unique())
        deparment = st.selectbox(
            "Selecciona un departamento", gjsonObj, index=6
        )
        # -- Dates --#
        stdate = st.date_input("Fecha Inicial", datetime.date(2022, 11, 20))
        eddate = st.date_input("Fecha Final", datetime.date(2022, 11, 22))
        st.write('La colleción de indice es de ', stdate, ' hasta ', eddate)
        #st.write('Fecha Inicial:', stdate)
        #st.write('Fecha Final:', eddate)
        # -- Threshold --#
        threshold = st.number_input('Umbral?')
        st.write("Se aplicara el umbral:", threshold)

    with row1_col1:
        # -- Centroid --#
        lon, lat = leafmap.gdf_centroid(gdf.query("shapeName==@deparment"))
        # -- Geemap --#
        m = geemap.Map(center=[lat, lon], zoom=7)
        vis_params = {
            'min': -1,
            'max': 1,
            'palette': cm.palettes.jet,
        }
        # -- add Feature --#
        fc = geemap.geopandas_to_ee(gdf.query("shapeName==@deparment"))
        m.addLayer(fc, {'color': 'gray',
                        'colorOpacity': 0.25,
                        'width': 1,
                        'lineType': 'solid',
                        'fillColorOpacity': 0.26,
                        }, deparment)

        # -- My Class --#
        myclass = indicesGEE(aoieFeature=fc)
        myclass.getcollection(initDate=stdate.strftime('%Y-%m-%d'),
                              endDate=eddate.strftime('%Y-%m-%d'))
        m.addLayer(myclass.imgCollection, vis_params, 'NDVI Modis 500 m.')
        colors = vis_params['palette']
        vmin = vis_params['min']
        vmax = vis_params['max']
        m.add_colorbar(vis_params, label='Elevation (m)')
        m.addLayerControl()
        m.to_streamlit(height=700)
