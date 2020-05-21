import streamlit as st
import pandas as pd
from datetime import date
from math import pi

from bokeh.plotting import figure
from bokeh.palettes import Spectral10 as palette
from bokeh.models.formatters import DatetimeTickFormatter
from bokeh.models import (
    ColumnDataSource,
    Panel,
    Span,
    CrosshairTool,
    HoverTool,
    ResetTool,
    PanTool,
    WheelZoomTool,
)


def makePlot(coronaData, plotColumn, plotCountries):
    """
    Returns a figure object with the drawn graphs of the corona data.

    Args:
        coronaData (pd.DataFrame): Pandas dataframe with the raw coronadata
        plotColumn (str): Name of the column in the coronaData to plot
        plotCountries (list of str): A list of countries the should be plotted.
                                     List cant be more than 10 long, because of plotting coloring index

    Returns:
        Bokeh figure object.
    """

    fig = figure(
        plot_height=800,
        plot_width=800,
        x_axis_type="datetime",
        x_axis_label="Date",
        tools="wheel_zoom, pan, reset",
    )
    fig.add_tools(
        HoverTool(
            tooltips=[("Date", "@date{%F}"), ("Country", "$name"), ("Value", "$y{0}")],
            formatters={"@date": "datetime"},
        )
    )

    # Go through each country and draw a graph for it.
    for idx, country in enumerate(plotCountries):
        countryData = coronaData.query(f"location=='{country}'")

        # Make an interpolated upsampling of the data. Now we get values for each hour instead of each day.
        # Data are smoothed out by a second polynomial function
        upsampled = countryData[plotColumn].resample("H")
        interpolated = upsampled.interpolate(method="polynomial", order=2)

        # Construct the graph
        line = fig.line(
            x="date",
            y=plotColumn,
            color=palette[idx],
            legend_label=country,
            line_width=2,
            source=pd.DataFrame(interpolated),
            name=country,
        )

    # Place the legend
    fig.legend.click_policy = "hide"
    fig.legend.location = "top_left"

    # Format x-axis labels
    fig.xaxis.formatter = DatetimeTickFormatter(days=["%d/%m"], months=["%d/%m"])
    fig.xaxis.ticker.desired_num_ticks = 30
    fig.xaxis.major_label_orientation = pi / 4

    return fig


@st.cache(suppress_st_warning=True)  # Use streamlit cache decorater to optimize speed
def getData(dateNow):
    """
    Gets the corona data online

    Args:
        dateNow (date): You should pass todays date to this function. 
                        Every time the date changes the streamlit cache will have a miss. 
                        This forces it to fetch new data online insted of just returning cached data

    Returns:
        coronaData (pd.DataFrame): Pandas dataframe with the coronadata
    """
    st.write("Fetching fresh data... wait a sec...")
    coronaData = pd.read_csv(
        "https://github.com/owid/covid-19-data/raw/master/public/data/owid-covid-data.csv"
    )
    coronaData["date"] = pd.to_datetime(coronaData.date)
    coronaData.set_index(("date"), inplace=True)

    return coronaData


if __name__ == "__main__":
    """
    # Corona stats by Alex Jensen
    Get your fresh customized statistics here...
    Raw data fetched from: https://github.com/owid/covid-19-data/tree/master/public/data

    Built with python and streamlit

    Source code here: https://github.com/x821938/corona-stat/blob/master/corona_stat.py
    """

    statList = {  # Lookuptable to give column names a more human touch
        "Total deaths": "total_deaths",
        "Total deaths per 1.000.000": "total_deaths_per_million",
        "New deaths today": "new_deaths",
        "New deaths today per 1.000.000": "new_deaths_per_million",
        "New cases today": "new_cases",
        "New cases today per 1.000.000": "new_cases_per_million",
        "Total tests": "total_tests",
        "Total test per 1.000": "total_tests_per_thousand",
    }

    coronaData = getData(date.today())  # Make cache miss when we have new date
    countryList = coronaData.location.unique().tolist()  # Get all countries that have corona data

    # Get streamlit input from user
    drawCountries = st.multiselect("Select your countries", countryList, ["Denmark", "Peru"])
    statChoice = st.selectbox("Choose your statistics", list(statList.keys()))

    if len(drawCountries) <= 10:  # Plotting function can only handle 10 countries
        stat = statList[statChoice]
        fig = makePlot(coronaData, stat, drawCountries)
        st.bokeh_chart(fig)
    else:
        st.write("Please no more than 10 countries")
