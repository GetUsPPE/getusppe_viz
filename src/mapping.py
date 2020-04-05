import plotly.graph_objects as go
from plotly.offline import plot
import plotly.express as px

def choropleth_mapbox_usa_plot (counties, locations, z, text,
                                colorscale = "RdBu_r", zmin=-1, zmax=10, 
                                title='choropleth_mapbox_usa_plot',
                                colorbar_title = 'count',
                                html_filename='plot.html',
                                show_fig=True):
    
    # Choropleth graph. For reference: https://plotly.com/python/mapbox-county-choropleth/
    fig = go.Figure(go.Choroplethmapbox(
        geojson=counties, locations=locations, z=z, text=text,
        colorscale=colorscale,zmin=zmin,zmax=zmax,marker_opacity=0.8, 
        marker_line_width=0.5, colorbar_title=colorbar_title, hoverinfo='text'
        ))
    
    # Center on US
    fig.update_layout(
        title=title,
        mapbox_style="carto-positron",
        mapbox_zoom=3.5, 
        mapbox_center = {"lat": 37.0902, "lon": -95.7129},
        margin={"r":100,"t":30,"l":30,"b":0},
    )
    
    # Show the figure
    if show_fig:
        fig.show()
    
    # Download the figure From Sunny Mui
    go.Figure.write_html(fig, file=html_filename, config={'responsive': True}, include_plotlyjs='cdn')


def viz_correlation_ppe_request_covid19_cases(merged_covid_ppe_hosp_df):
    # select counties that have had at least 1 ppe request
    counties_with_ppe_requests_and_covid_cases = merged_covid_ppe_hosp_df[
        merged_covid_ppe_hosp_df.PPE_requests != 0]

    # sort by highest normalized_covid_patients_per_bed
    counties_with_ppe_requests_and_covid_cases.sort_values(by=['PPE_requests','cases'], ascending=False, inplace=True)
    counties_with_ppe_requests_and_covid_cases.head(5)

    fig = px.scatter(
        counties_with_ppe_requests_and_covid_cases,
        x=counties_with_ppe_requests_and_covid_cases.cases, 
        y=counties_with_ppe_requests_and_covid_cases.PPE_requests,
        color='Covid_cases_per_bed',
        log_x=True,
        #log_y=True,
        labels={
            'Covid_cases_per_bed':'Covid19 cases per hospital bed',
            'x':'Covid19 Cases Per County',
            'y':'PPE Requests Per County',
            'text':'County'
            },
        hover_name=counties_with_ppe_requests_and_covid_cases.county,
        range_color=(0,1),
        range_x=(1,30000)
        )

    fig.update_layout(
        title = "Correlation of PPE request per county with COVID19 cases",
        #hoverlabel={'text'},
        )
    
    fig.show()


