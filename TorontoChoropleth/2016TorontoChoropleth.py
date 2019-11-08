import json
import numpy as np
import pandas as pd
import geopandas as gpd

from bokeh.io import show
from bokeh.plotting import figure, curdoc
from bokeh.models import GeoJSONDataSource, LinearColorMapper, ColorBar, HoverTool
from bokeh.palettes import brewer
from bokeh.models.widgets import Select
from bokeh.layouts import widgetbox, column

###

## To make sure all of our data is here

# read in our dataframe
Merged_df_2016 = pd.read_csv("Merged_df_2016.csv")

# Read shapefile using Geopandas
shapefile = "./Neighbourhoods/Neighbourhoods.shp"

gdf_neighbourhoods = gpd.read_file(shapefile)[["FIELD_5", "FIELD_7", "geometry"]]

# Rename Columns
gdf_neighbourhoods.columns = ["Neighbourhood#", "Neighbourhood", "geometry"]

###

def update_data(selectedOrigin):
    """
    This function updates our data source to be only the data from our selected origin.
    """
    # Gather the data about the selected origin we want
    df = Merged_df_2016[Merged_df_2016["ReportedOrigin"] == selectedOrigin].copy()
    # Combine the population data from all the CTs into neighbourhoods
    df["TotalPopulation"] = df.groupby("Neighbourhood#")["Population"].transform("sum")
    # Grab the first instance in our dataframe for each neighbourhood (removing duplicate information)
    df = df.groupby("Neighbourhood#").first().reset_index()
    # Combining our shapefile data with our dataframe
    df = gdf_neighbourhoods.merge(df, how = "left", on = "Neighbourhood#")
    # Restructuring our dataframe
    df = df[["Neighbourhood", "geometry", "ReportedOrigin", "TotalPopulation"]]
    return df

def data_to_json(df):
    """
    We use this to convert our data to `.json` so that we can graph in bokeh
    This step is seperate to acces data from the dataframe.
    """
    # Convert dataframe to a json string
    tojson = df.to_json()

    return tojson

def origindata(attr, old, new):
    """
    This function updates our plot with our new origin selection
    """
    # To get the index of our value selected in the menu
    choice = menu.index(select.value)

    # To change the user facing category to the dataframe recognized category
    selectedOrigin = menulist[choice]

    # Changing our title to represent the data being shown
    if select.value == "Total Immigrant Population":
        p.title.text = "Total Immigrant Population Who Reported Their Origin by Neighbourhood"
    else:
        p.title.text = f"Population of Immigrants Who Reported {select.value} As Their Origin by Neighbourhood"

    # Update our dataframe to our selected data
    df_to_use = update_data(selectedOrigin)

    # Change the tick labels on our colorbar
    color_map.high = df_to_use.iloc[:,3].max()
    color_map.low = df_to_use.iloc[:,3].min()

    # Convert our data to be used.
    new_data = data_to_json(df_to_use)
    geosource.geojson = new_data
    return

# Our intial starting point
selectedOrigin = "Total_Immigrant_Population"

#Getting our data into a starting position
df_to_use = update_data(selectedOrigin)
geosource = GeoJSONDataSource(geojson = data_to_json(df_to_use))

# Choosing our colorblind friendly colours
palette = brewer['YlGn'][7]

# Making the darker areas represent the higher population
palette = palette[::-1]

# Map our colours from the palette to our data. High and low set the ticks.
color_map = LinearColorMapper(palette = palette, high = df_to_use.iloc[:,3].max(), low = df_to_use.iloc[:,3].min())

# Add hover tool with defined information
hover = HoverTool(tooltips = [("Neighbourhood","@Neighbourhood"),("Population", "@TotalPopulation")])

# Create color bar.
color_bar = ColorBar(color_mapper=color_map, label_standoff= 8, width = 20, height = 500,
                     border_line_color=None, location = (0,0), orientation = "vertical")

# Our plot!
p = figure(title = "Total Immigrant Population Who Reported Their Origin by Neighbourhood", plot_height = 600 , plot_width = 950, tools = [hover])

# For aesthetic reasons, getting rid of excess lines and borders
p.axis.visible = False
p.grid.visible = False
p.outline_line_color = None

# Add patch renderer to figure.
p.patches("xs", "ys", source = geosource, fill_color = {"field" : "TotalPopulation", "transform" : color_map},
              line_color = "black", line_width = 0.25, fill_alpha = 1)

# Put the colorbar on the left.
p.add_layout(color_bar, "left")


### Create our widget, and what is in it.

# Take a list of categories
menulist = list(Merged_df_2016["ReportedOrigin"].unique())
# Sort the list alphabetically, but put the total population as choice one.
menulist[1:] = sorted(menulist[1:])

# Repeat process above, but make the categories more user/reader friendly
menu = list(map(lambda x : x.replace("_", " "), menulist))
menu[1:] = sorted(menu[1:])
menu[31] = "Korea, South"
menu[51] = 'South Africa, Republic of'

# This is our Select widget.
select = Select(title="Reported Origin:", options=menu)
select.on_change("value", origindata)

###

# To layout our graph
layout = column(p, widgetbox(select))
curdoc().add_root(layout)

#Display figure.
show(layout)
