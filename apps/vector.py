import streamlit as st
import leafmap.foliumap as leafmap
import geemap
import geopandas as gpd
import ee
import geemap.colormaps as cm
import datetime
ee.Initialize()


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
    st.title("Example")
    row1_col1, row1_col2 = st.columns([2, 1])
    width, height = 950, 600
    with row1_col2:
        # -- Basemaps --#
        keys = list(geemap.basemaps.keys())[1:]
        basemap = st.selectbox("Selecciona un basemap", keys)
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
        # -- Palette --#
        geemap.save_colorbar(vis_params={'min': -1, "max": 1,
                                         'palette': cm.get_palette("jet")},
                             tick_size=12,
                             label="NDVI")
    with row1_col1:
        # -- Centroid --#
        lon, lat = leafmap.gdf_centroid(gdf.query("shapeName==@deparment"))
        # -- Geemap --#
        m = geemap.Map(center=[lat, lon], zoom=7)
        vis_params = {'min': -1, 'max': 1, 'palette': cm.palettes.jet}
        m.add_colorbar(vis_params, label='NDVI Modis 500 m.')
        m.add_basemap(basemap)
        # -- add Feature --#
        fc = geemap.geopandas_to_ee(gdf.query("shapeName==@deparment"))
        m.addLayer(fc, {'color': 'gray',
                        'colorOpacity': 0.25,
                        'width': 1,
                        'lineType': 'solid',
                        'fillColorOpacity': 0.26,
                        }, deparment)
        # -- NDVI --#
        myclass = indicesGEE(aoieFeature=fc)
        #sinitDate, sendDate = stdate.strftime('%Y-%m-%d'), eddate.strftime('%Y-%m-%d')
        myclass.getcollection(initDate=stdate.strftime('%Y-%m-%d'),
                              endDate=eddate.strftime('%Y-%m-%d'))
        # -- Plot NDVI --#
        vis_params = {'min': -1, 'max': 1, 'palette': cm.palettes.jet}
        m.addLayer(myclass.imgCollection, vis_params, 'NDVI Modis 500 m.')
        m.add_colorbar(vis_params, label='NDVI Modis 500 m.')
        m.add_legend(legend_title="NLCD Land Cover Classification",
                     builtin_legend="NLCD")
        # -- To Streamlit --#
        m.to_streamlit(width=width, height=height)
