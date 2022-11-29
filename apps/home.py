import streamlit as st
import leafmap.foliumap as leafmap
import ee
import geemap.foliumap as geemap
import geopandas as gpd
import datetime
import geemap.colormaps as cm
ee.Initizalize()


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

    # -- NDVI --#
    def getNDVI(self, initDate=None, endDate=None):
        self.ndvi = ee.ImageCollection('MODIS/MOD09GA_006_NDVI')\
                      .filterDate(initDate, endDate)\
                      .filterBounds(self.aoieFeature.geometry())\
                      .select('NDVI')\
                      .map(lambda img: img.clip(self.aoieFeature))
    # -- Compute VCI --#

    def getVCI(self, initDate=None, endDate=None):
        """
            For Compute the Vegetation Condition Index (VCI) (Kogan et al., 2003)
            VCI = (NDVIi-NDVImin)/(NDVImax-NDVImin)*100
        """
        ndviCollect = ee.ImageCollection('MODIS/MOD09GA_006_NDVI')\
                        .filterBounds(self.aoieFeature.geometry())\
                        .filter(ee.Filter.date('2000-03-01', endDate))\
                        .select('NDVI')\
                        .map(lambda img: img.clip(self.aoieFeature))
        ndvi = ee.ImageCollection('MODIS/MOD09GA_006_NDVI')\
            .filterBounds(self.aoieFeature.geometry())\
            .filter(ee.Filter.date(initDate, endDate))\
            .select('NDVI')\
            .map(lambda img: img.clip(self.aoieFeature))
        # -- Retrieve all dates --#
        arr = ndvi.aggregate_array('system:time_start')
        dates = arr.map(lambda x: ee.Date(x).format('YYYY-MM-dd'))
        eeDates = [ee.Date(x) for x in dates.getInfo()]
        # -- Compute VCI --#
        self.vci = ee.ImageCollection([
            ndvi.filter(ee.Filter.calendarRange(
                x.get('year'), x.get('year'), 'year'))
            .filter(ee.Filter.calendarRange(x.get('month'), x.get('month'), 'month'))
            .filter(ee.Filter.calendarRange(x.get('day'), x.get('day'), 'day_of_month')).median()
            .subtract(ndviCollect.filter(ee.Filter.calendarRange(x.get('month'), x.get('month'), 'month')).min())
            .divide(ndviCollect.filter(ee.Filter.calendarRange(x.get('month'), x.get('month'), 'month')).max()
                    .subtract(ndviCollect.filter(ee.Filter.calendarRange(x.get('month'), x.get('month'), 'month')).min())).multiply(1e2)
            .set({"system:time_start": ee.Date.fromYMD(x.get('year'), x.get('month'), x.get('day'))})
            for x in eeDates]).median().rename('VCI')
    # -- Compute TCI --#

    def getTCI(self, initDate=None, endDate=None):
        """
            For Compute the Temperature Condition Index (TCI) (Kogan et al., 2003)
            TCI = (LSTmax-LSTi)/(LSTmax-LSTmin)*100
        """
        lstCollect = ee.ImageCollection('MODIS/061/MOD11A1')\
            .filterBounds(self.aoieFeature.geometry())\
            .filter(ee.Filter.date('2000-03-01', endDate))\
            .select('LST_Day_1km')\
            .map(lambda img: img.clip(self.aoieFeature))
        lst = ee.ImageCollection('MODIS/061/MOD11A1')\
            .filterBounds(self.aoieFeature.geometry())\
            .filter(ee.Filter.date(initDate, endDate))\
            .select('LST_Day_1km')\
            .map(lambda img: img.clip(self.aoieFeature))
        # -- Retrieve all dates --#
        arr = lst.aggregate_array('system:time_start')
        dates = arr.map(lambda x: ee.Date(x).format('YYYY-MM-dd'))
        eeDates = [ee.Date(x) for x in dates.getInfo()]
        # -- Compute VCI --#
        self.tci = ee.ImageCollection([
            lst.filter(ee.Filter.calendarRange(
                x.get('year'), x.get('year'), 'year'))
            .filter(ee.Filter.calendarRange(x.get('month'), x.get('month'), 'month'))
            .filter(ee.Filter.calendarRange(x.get('day'), x.get('day'), 'day_of_month')).median()
            .subtract(lstCollect.filter(ee.Filter.calendarRange(x.get('month'), x.get('month'), 'month')).min())
            .divide(lstCollect.filter(ee.Filter.calendarRange(x.get('month'), x.get('month'), 'month')).max()
                    .subtract(lstCollect.filter(ee.Filter.calendarRange(x.get('month'), x.get('month'), 'month')).min())).multiply(1e2)
            .set({"system:time_start": ee.Date.fromYMD(x.get('year'), x.get('month'), x.get('day'))})
            for x in eeDates]).median().rename('TCI')
    # -- Compute VHI --#

    def getVHI(self):
        """
            For Compute the Vegetation Health Index (VHI) (Kogan et al., 1998)
            VHI = a*VCI + (1-a)*TCI
        """
        self.vhi = self.vci.multiply(0.5).add(
            self.tci.multiply(0.5)).rename('VHI')


def app():
    st.title("Sequias Agrometeorológicas")

    st.markdown(
        """
    El monitoreo de indices mediante [GEE](https://developers.google.com/earth-engine/datasets/catalog) nos permite la observación temporal y territorial mediante la utilización 
    de la versión [Pre-Construida](https://carlosenciso-monitoringdroughttempleate-streamlit-app-huiz8l.streamlit.app/). 

    """
    )
    row1_col1, row1_col2 = st.columns([2, 1])
    width, height = 950, 700
    with row1_col2:
        # -- Indices --#
        indice = st.selectbox(
            "Selecciona un Indice", ['NDVI', 'VCI', 'TCI', 'VHI'], index=0
        )
        # -- Reading GJson --#
        depGjson = 'https://raw.githubusercontent.com/wmgeolab/geoBoundaries/d46566667e443b7a2e8e1ce6aa23cb15f26ff9dd/releaseData/gbOpen/PER/ADM1/geoBoundaries-PER-ADM1.geojson'
        gdf = gpd.read_file(depGjson)
        gjsonObj = sorted(list(gpd.read_file(depGjson)['shapeName'].unique()))
        deparment = st.selectbox(
            "Selecciona un departamento", gjsonObj, index=20
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
        if indice == 'NDVI':
            myclass.getNDVI(initDate=stdate.strftime('%Y-%m-%d'),
                            endDate=eddate.strftime('%Y-%m-%d'))
            vis_params = {
                'min': -1,
                'max': 1,
                'palette': cm.palettes.jet,
            }
            m.addLayer(myclass.ndvi, vis_params, 'NDVI Modis 500 m.')
            colors = vis_params['palette']
            vmin = vis_params['min']
            vmax = vis_params['max']
            m.add_colorbar(vis_params, label='NDVI')
            m.addLayerControl()
        elif indice == 'VCI':
            myclass.getVCI(initDate=stdate.strftime('%Y-%m-%d'),
                           endDate=eddate.strftime('%Y-%m-%d'))
            vis_params = {
                'min': 0,
                'max': 100,
                'palette': cm.palettes.jet,
            }
            m.addLayer(myclass.vci, vis_params, 'VCI Modis 500 m.')
            colors = vis_params['palette']
            vmin = vis_params['min']
            vmax = vis_params['max']
            m.add_colorbar(vis_params, label='VCI')
            m.addLayerControl()
        elif indice == 'TCI':
            myclass.getTCI(initDate=stdate.strftime('%Y-%m-%d'),
                           endDate=eddate.strftime('%Y-%m-%d'))
            vis_params = {
                'min': 0,
                'max': 100,
                'palette': cm.palettes.jet,
            }
            m.addLayer(myclass.tci, vis_params, 'TCI Modis 1 km.')
            colors = vis_params['palette']
            vmin = vis_params['min']
            vmax = vis_params['max']
            m.add_colorbar(vis_params, label='TCI')
            m.addLayerControl()
        elif indice == 'VHI':
            myclass.getVCI(initDate=stdate.strftime('%Y-%m-%d'),
                           endDate=eddate.strftime('%Y-%m-%d'))
            myclass.getTCI(initDate=stdate.strftime('%Y-%m-%d'),
                           endDate=eddate.strftime('%Y-%m-%d'))
            myclass.getVHI()
            # -- Classification for ranges --#
            droughtsRanges = [ee.Image(1).mask(myclass.vhi.lt(10)).toInt(),
                              ee.Image(2).mask(myclass.vhi.lt(20).And(
                                  myclass.vhi.gte(10))).toInt(),
                              ee.Image(3).mask(myclass.vhi.lt(30).And(
                                  myclass.vhi.gte(20))).toInt(),
                              ee.Image(4).mask(myclass.vhi.lte(40).And(
                                  myclass.vhi.gte(30))).toInt(),
                              ee.Image(5).mask(myclass.vhi.gt(40)).toInt()
                              ]
            myclass.vhiClassify = ee.ImageCollection(
                droughtsRanges).reduce(ee.Reducer.max())
            # -- Legend Categorical render --#
            labels = ['Sequía Extrema', 'Sequía Severa',
                      'Sequía Moderada', 'Sequía Leve', 'Sin Sequía']
            colors = ['#CD1414', '#F3BB0F', '#F3F00F', '#06B4F5', '#0F892C']
            m.addLayer(myclass.vhiClassify, {
                       'min': 1, 'max': 5, 'palette': colors}, 'VHI Categorical Modis 1000 m.')
            m.add_legend(title='Vegetation Heath Index (VHI)',
                         labels=labels, colors=colors)
            m.addLayerControl()
        m.to_streamlit(height=700)
