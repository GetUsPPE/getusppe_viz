import plotly.graph_objects as go
from plotly.offline import plot

def choropleth_mapbox_usa_plot (counties, locations, z, text,
                                colorscale = "RdBu_r", zmin=-1, zmax=10, 
                                title='choropleth_mapbox_usa_plot',
                                colorbar_title = 'count',
                                html_filename='plot.html'):
    
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
        margin={"r":300,"t":30,"l":30,"b":0},
    )
    
    # Show the figure
    fig.show()
    
    # Download the figure
    plot(fig, filename=html_filename)