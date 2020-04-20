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
        geojson=counties,
        locations=locations, 
        z=z, 
        text=text,
        colorscale=colorscale,
        zmin=zmin,
        zmax=zmax,
        marker_opacity=0.8, 
        marker_line_width=0.5, 
        colorbar_title=colorbar_title, 
        hoverinfo='text'
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

def choropleth_mapbox_layered_plot (counties, html_filename,
    locations_0, z_0, text_0, colorscale_0, zmin_0, zmax_0, title_0, colorbar_title_0,
    locations_1, z_1, text_1, colorscale_1, zmin_1, zmax_1, title_1, colorbar_title_1,
    locations_2, z_2, text_2, colorscale_2, zmin_2, zmax_2, title_2, colorbar_title_2,
    locations_3, z_3, text_3, colorscale_3, zmin_3, zmax_3, title_3, colorbar_title_3,
    ):
    
    fig = go.Figure()
    
    # First trace
    fig = fig.add_trace(go.Choroplethmapbox(
        geojson=counties,
        locations=locations_0, 
        z=z_0, 
        text=text_0,
        colorscale=colorscale_0,
        zmin=zmin_0,
        zmax=zmax_0,
        marker_opacity=0.8, 
        marker_line_width=0.5, 
        colorbar_title=colorbar_title_0, 
        hoverinfo='text',
        visible=True
        ))
    
    # Second trace
    fig = fig.add_trace(go.Choroplethmapbox(
        geojson=counties,
        locations=locations_1, 
        z=z_1, 
        text=text_1,
        colorscale=colorscale_1,
        zmin=zmin_1,
        zmax=zmax_1,
        marker_opacity=0.8, 
        marker_line_width=0.5, 
        colorbar_title=colorbar_title_1, 
        hoverinfo='text',
        visible=False
        ))
    
    # Third trace
    fig = fig.add_trace(go.Choroplethmapbox(
        geojson=counties,
        locations=locations_2, 
        z=z_2, 
        text=text_2,
        colorscale=colorscale_2,
        zmin=zmin_2,
        zmax=zmax_2,
        marker_opacity=0.8, 
        marker_line_width=0.5, 
        colorbar_title=colorbar_title_2, 
        hoverinfo='text',
        visible=False
        ))
    
    # Fourth trace
    fig = fig.add_trace(go.Choroplethmapbox(
        geojson=counties,
        locations=locations_3, 
        z=z_3, 
        text=text_3,
        colorscale=colorscale_3,
        zmin=zmin_3,
        zmax=zmax_3,
        marker_opacity=0.8, 
        marker_line_width=0.5, 
        colorbar_title=colorbar_title_3, 
        hoverinfo='text',
        visible=False
        ))
    

    # Create button list
    buttons_list=list([
        dict(label='PPE Requests', method="update",
             args=[{"visible": ([True,False,False,False])},
                   {"title": title_0}]),
        dict(label='COVID19 Cases', method="update",
             args=[{"visible": ([False,True,False,False])},
                   {"title": title_1}]),
        dict(label='COVID19 Cases Per PPE Request', method="update",
             args=[{"visible": ([False,False,True,False])},
                   {"title": title_2}]),
        dict(label='COVID19 Cases Per Hospital Bed', method="update",
             args=[{"visible": ([False,False,False,True])},
                   {"title": title_3}]),
        
    
        ])
    
    # Add buttons
    fig.update_layout(
        updatemenus=list([
            dict(
                type = "buttons",
                active=0,
                showactive=True,
                direction="right",
                pad={"l":75,"t": -40},
                yanchor="top",
                xanchor="left",
                buttons=buttons_list,
            )])
    )
    
    # Center on US
    fig.update_layout(
        title='GetUsPPE.org - 04/18/2020',
        mapbox_style="carto-positron",
        mapbox_zoom=3.5, 
        mapbox_center = {"lat": 37.0902, "lon": -95.7129},
        margin={"r":100,"t":100,"l":30,"b":0},
    )
    
    # Download the figure From Sunny Mui
    go.Figure.write_html(fig, file=html_filename, config={'responsive': True}, include_plotlyjs='cdn')

