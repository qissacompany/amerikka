#app.py very beta
import streamlit as st
import boto3
import geocoder

import open_utils, client_utils

# --------- CLIENT CONFIGS ---------------
client_name = "Lorem Ipsum Ltd."
client_app_name = ":violet[Urban Data Lab]"
client_bucket_url = st.secrets['client_bucket']['BUCKET_url']
bucket_name = st.secrets["client_bucket"]['BUCKET_name']
client_logo_url = "https://" + client_bucket_url + "/" + bucket_name + '/media/logo_holder.png'
default_lang = "FIN"

# random image from client collection
client_bg_image_url = open_utils.get_random_image_url_from_collection(bucket_folder="appbackgrounds")

#page configs
st.set_page_config(page_title=client_name, layout="wide", initial_sidebar_state='collapsed',
                page_icon="✨",
                menu_items={"Get help":None,
                            "Report a bug":None,
                            "About": "Sanely Simple Urban Metrics By https://qissa.fi"})
# custom feature configs
st.markdown("""
<style>
div.stButton > button:first-child {
    background-color: #fab43a;
    color:#ffffff;
}
div.stButton > button:hover {
    background-color: #e75d35; 
    color:#ffffff;
    }
[data-testid="stMetricDelta"] svg {
        display: none;}
.stProgress .st-bo {
    background-color: green;
}
</style>
""", unsafe_allow_html=True)

#background
def add_bg_image(bg_image_url=None):
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: url({bg_image_url});
            background-size: cover
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

add_bg_image(client_bg_image_url)


#LOCAT
qissa_footer_badge_text = ["Kaupunkiarkkitehtuurin_analytiikkaa",
                      "Urban_architecture_analytics"]
signin_text = ['Kirjaudu sisään!','Sign in!']
datasource_expander = ['Datalähteet','Datasource']
address_input_title = ['Kohdeosoite','Case address']
mode_title = ['Tarkastelun mittakaava','Travel scale of analysis']
basemap_title = ['Pohjakartta','Basemap']
datasource_title = ['Datalähde','Datasource']
source_warning = ['Tulossa 2024!','Coming up 2024!']

tab_titles = [['Saavutettavuus','Palveluprofiili','Väestöprofiili'],
              ['Reach','Service profile','Residential profile']]

map_gen_status = ["Laatii karttaa...","Generating map..."]
add_coverage_warning = ['Osoite tulee olla Suomessa','Coverage only in Finland']
profile_autogen_toggle = ['Koosta palveluprofiili automaattisesti','Autogenerate profile']
profile_gen_status = ['Koostaa profiilia...','Generating profile...']
profile_coverage_warning = ['Palveluprofiili saatavissa vain kävelyetäisyydeltä','Profile available only in walkable scale']

not_available_warning = ['Tilaa lisää analytiikka osoitteesta office@qissa.fi','For more analytics contact office@qissa.fi']

# ------- HEADER -----------
st.image(client_logo_url,width=150)
st.header(client_name,divider="orange")
st.subheader(client_app_name)

#lang toggle if needed
if default_lang == "FIN":
    lang = st.toggle('In English')
    if lang:
        lin = 1
    else:
        lin = 0
else:
    lang = st.toggle('Suomeksi')
    if lang:
        lin = 0
    else:
        lin = 1

st.markdown('###')
st.markdown("###")
st.subheader(signin_text[lin])




# ------- CLIENT CONTENT -----------

auth_check = open_utils.check_password(lin=lin)
if auth_check:

    with st.expander(datasource_expander[lin], expanded=True):
        from faker import Faker
        fake = Faker("fi_FI")
        if "add" not in st.session_state:
            input_value = fake.city()
        else:
            input_value = st.session_state.add

        # UI for reach based analytics
        c1,c2,c3 = st.columns(3)
        add = c1.text_input(address_input_title[lin],key="add",value=input_value)
        moodit = [['Kävely','Pyöräily','Joukkoliikenne'],
                    ['Walking','Biking','Public transit']
                    ]
        modes = {moodit[lin][0]:'walk',
                    moodit[lin][1]:'bicycle',
                    moodit[lin][2]: 'approximated_transit'
                    }
        moodi =  c2.radio(mode_title[lin],moodit[lin],horizontal=True)
        source = c3.radio(datasource_title[lin],['OSM', 'Overturemaps'], horizontal=True)
        if source != 'OSM':
            st.success(source_warning[lin])
            st.stop()

        loc = geocoder.osm(add)



    # ------ TABS --------
    tab1,tab2,tab3 = st.tabs(tab_titles[lin])

    with tab1:
        tab_holder1 = st.empty()
    with tab2:
        tab_holder2 = st.empty()
    with tab3:
        tab_holder3 = st.empty()

    if add:
        with tab_holder1:
            with st.status(map_gen_status[lin], expanded=True):
                loc = geocoder.osm(add)
                if loc.country == "Suomi / Finland":
                    latlng = loc.latlng
                    times = [10,15,20,25]

                    # cached isolines
                    if moodi == moodit[lin][0]: #walk
                        reso = 10
                        zoom = 13
                        @st.cache_data(show_spinner=False)
                        def isolines_walk(times,mode,reso,latlng):
                            h3_isolines = client_utils.reach_h3(latlng=latlng,mode=mode,
                                                        reso=reso,times=times,reid_list=None)
                            return h3_isolines
                        h3_isolines = isolines_walk(times,modes[moodi],reso,latlng)

                    elif moodi == moodit[lin][1]: #bike
                        reso = 9
                        zoom = 12
                        @st.cache_data(show_spinner=False)
                        def isolines_bike(times,mode,reso,latlng):
                            h3_isolines = client_utils.reach_h3(latlng=latlng,mode=mode,
                                                        reso=reso,times=times,reid_list=None)
                            return h3_isolines
                        h3_isolines = isolines_bike(times,modes[moodi],reso,latlng)

                    elif moodi == moodit[lin][2]: #public trans
                        reso = 9
                        zoom = 11
                        @st.cache_data(show_spinner=False)
                        def isolines_pub(times,mode,reso,latlng):
                            h3_isolines = client_utils.reach_h3(latlng=latlng,mode=mode,
                                                        reso=reso,times=times,reid_list=None)
                            return h3_isolines
                        h3_isolines = isolines_pub(times,modes[moodi],reso,latlng)
                    else:
                        h3_isolines = None
                        st.stop()
                    
                    if h3_isolines is not None:
                        reach_fig = client_utils.reach_map_plot(h3_isolines,latlng=latlng,zoom=zoom)
                        st.plotly_chart(reach_fig, use_container_width=True, config = {'displayModeBar': False})
                else:
                    st.warning(add_coverage_warning[lin])

        with tab_holder2:
            if moodi == moodit[lin][0]:
                gdf = h3_isolines.copy()
                categories = client_utils.get_classificator_json()
                autorun_tab2 = st.toggle(profile_autogen_toggle[lin])
                
                if autorun_tab2:
                    with st.status(profile_gen_status[lin], expanded=True):
                        gdf['time'] = gdf['time'].astype(float).astype(int)
                        ##aggregate to h9..
                        h3_isolines_09 = gdf[['time']].h3.h3_to_parent_aggregate(9, operation='mean', return_geometry=False)
                        h3_isoline_query = h3_isolines_09.reset_index() 
                        h3_isoline_query.rename(columns={'h3_09':'h3_id'}, inplace=True)
                        h3_isoline_query.set_index('h3_id', inplace=True)
                        
                        def round_to_five(n):
                            return round(n / 5) * 5
                        h3_isoline_query['time'] = h3_isoline_query['time'].apply(round_to_five)

                        grouped_sums, pois_gdf = client_utils.osm_pois_for_h3(_h3_df=h3_isoline_query,categories_json=categories,lin=lin)
                        
                        #plot
                        profile_scat = client_utils.plot_amenity_profile(grouped_sums,lin=lin)
                        st.plotly_chart(profile_scat, use_container_width=True, config = {'displayModeBar': False})
            else:
                st.warning(profile_coverage_warning[lin])

        with tab_holder3:
            st.success(not_available_warning[lin])

#footer
st.markdown('###')
st.markdown('---')
license = f'[![Custom badge](https://img.shields.io/badge/{qissa_footer_badge_text[lin]}-Qissa-fab43a)](https://qissa.fi)'
st.markdown(license)