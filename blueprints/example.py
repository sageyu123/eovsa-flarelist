import numpy as np
import pandas as pd
from flask import Flask, Blueprint, render_template, request, jsonify, url_for
import plotly.express as px
import plotly.graph_objects as go
import socket
import json
import plotly
import os
import mysql.connector
from astropy.time import Time
import requests


def check_url_exists(url):
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


example = Blueprint('example', __name__, template_folder='templates')


def get_eo_flare_list_MySQL(start_utc, end_utc):
    """
    info from MySQL
    """
    connection = mysql.connector.connect(
        host=os.getenv('FLARE_DB_HOST'),
        database=os.getenv('FLARE_DB_DATABASE'),
        user=os.getenv('FLARE_DB_USER'),
        password=os.getenv('FLARE_DB_PASSWORD')
    )

    cursor = connection.cursor()

    # cursor.execute("SHOW COLUMNS FROM EOVSA_flare_list_wiki_tb")
    # columns = cursor.fetchall()
    # for column in columns:
    #     print(column)

    cursor.execute("SELECT Flare_ID FROM EOVSA_flare_list_wiki_tb")
    flare_id = cursor.fetchall()

    cursor.execute("SELECT Flare_class FROM EOVSA_flare_list_wiki_tb")
    GOES_class = cursor.fetchall()

    cursor.execute("SELECT EO_tstart FROM EOVSA_flare_list_wiki_tb")
    EO_tstart = np.array(cursor.fetchall())  ##in Julian Dates i.e., Time('2019-04-15 19:30:04').jd

    cursor.execute("SELECT EO_tpeak FROM EOVSA_flare_list_wiki_tb")
    EO_tpeak = np.array(cursor.fetchall())  ##in Julian Dates i.e., Time('2019-04-15 19:30:04').jd

    cursor.execute("SELECT EO_tend FROM EOVSA_flare_list_wiki_tb")
    EO_tend = np.array(cursor.fetchall())

    cursor.execute("SELECT depec_file FROM EOVSA_flare_list_wiki_tb")
    depec_file1 = cursor.fetchall()
    depec_file = [item[0] for item in depec_file1]

    cursor.execute("SELECT depec_img FROM EOVSA_flare_list_wiki_tb")
    depec_img1 = cursor.fetchall()
    depec_img = [item[0] for item in depec_img1]

    # cursor.execute("SELECT EO_xcen FROM EOVSA_flare_list_wiki_tb")
    # EO_xcen = cursor.fetchall()

    cursor.execute("SELECT flux_pk_3GHz FROM EOVSA_flare_list_wiki_tb")
    flux_pk_3GHz = cursor.fetchall()

    cursor.execute("SELECT flux_pk_7GHz FROM EOVSA_flare_list_wiki_tb")
    flux_pk_7GHz = cursor.fetchall()

    cursor.execute("SELECT flux_pk_11GHz FROM EOVSA_flare_list_wiki_tb")
    flux_pk_11GHz = cursor.fetchall()

    cursor.execute("SELECT flux_pk_15GHz FROM EOVSA_flare_list_wiki_tb")
    flux_pk_15GHz = cursor.fetchall()

    cursor.close()
    connection.close()

    t_st = Time(start_utc).jd
    t_ed = Time(end_utc).jd

    ind = np.where((EO_tstart <= t_ed) & (t_st <= EO_tend))[0]

    ind_sorted = ind[np.argsort(EO_tstart[ind].flatten())]
    ind = ind_sorted

    result = []
    keys = ['_id', 'start', 'end', 'link']
    keys = ['_id', 'flare_id', 'start', 'peak', 'end', 'GOES_class', 'link_dspec_data', 'link_movie', 'link_fits']
    # keys=['_id','flare_id','start','end','GOES_class','link_dspec','link_dspec_data','link_movie','link_fits']
    ql_symbol_url = url_for('static', filename='images/ql.svg')
    dl_symbol_url = url_for('static', filename='images/dl.svg')

    if ind.size > 0:
        for i, j in enumerate(ind):
            flare_id_str = str(flare_id[j][0])

            link_dspec_str = f'https://www.ovsa.njit.edu/wiki/index.php/File:' + depec_img[j]
            link_dspec_data_str = f'https://ovsa.njit.edu/events/{flare_id_str[0:4]}/' + depec_file[j]
            link_movie_str = f'https://www.ovsa.njit.edu/SynopticImg/eovsamedia/eovsa-browser/{flare_id_str[0:4]}/{flare_id_str[4:6]}/{flare_id_str[6:8]}/eovsa.lev1_mbd_12s.flare_id_{flare_id_str}.mp4'
            link_fits_str = f'https://www.ovsa.njit.edu/fits/flares/{flare_id_str[0:4]}/{flare_id_str[4:6]}/{flare_id_str[6:8]}/{flare_id_str}/'

            link_movie = None  # Default to None
            link_fits = None
            # if EO_xcen[j][0]:  # If link_movie_str is non-empty or meets your criteria
            #     link_movie = f'<a href="{link_movie_str}"><img src="{ql_symbol_url}" alt="QL_Movie" style="width:20px;height:20px;"></a>'
            #     link_fits = '<a href="'+link_fits_str+'"><img src="'+dl_symbol_url+'" alt="FITS" style="width:20px;height:20px;"></a>'

            if check_url_exists(link_movie_str):
                link_movie = f'<div style="text-align: center;"><a href="{link_movie_str}"><img src="{ql_symbol_url}" alt="QL_Movie" style="width:20px;height:20px;"></a></div>'
                link_fits = f'<div style="text-align: center;"><a href="{link_fits_str}"><img src="{dl_symbol_url}" alt="FITS" style="width:20px;height:20px;"></a></div>'

            result.append({'_id': i + 1,
                           'flare_id': int(flare_id[j][0]),
                           'start': Time(EO_tstart[j], format='jd').isot[0].split('.')[0],
                           'peak': Time(EO_tpeak[j], format='jd').isot[0].split('.')[0],
                           'end': Time(EO_tend[j], format='jd').isot[0].split('.')[0],
                           'GOES_class': GOES_class[j][0],
                           'flux_pk_3GHz': f'<div style="text-align: center;">{flux_pk_3GHz[j][0]}</div>',
                           'flux_pk_7GHz': f'<div style="text-align: center;">{flux_pk_7GHz[j][0]}</div>',
                           'flux_pk_11GHz': f'<div style="text-align: center;">{flux_pk_11GHz[j][0]}</div>',
                           'flux_pk_15GHz': f'<div style="text-align: center;">{flux_pk_15GHz[j][0]}</div>',
                           'link_dspec': '<div style="text-align: center;"><a href="' + link_dspec_str + '"><img src="' + ql_symbol_url + '" alt="DSpec" style="width:20px;height:20px;"></a></div>',
                           'link_dspec_data': '<div style="text-align: center;"><a href="' + link_dspec_data_str + '"><img src="' + dl_symbol_url + '" alt="DSpec_Data" style="width:20px;height:20px;"></a></div>',
                           'link_movie': link_movie,
                           'link_fits': link_fits
                           })
    return result


@example.route("/api/flare/query", methods=['POST'])
def get_flare_list_from_database():
    try:
        start = request.form['start']
        end = request.form['end']
        if not start or not end:
            raise ValueError("Start and end times are required.")

        result = get_eo_flare_list_MySQL(start, end)
        return jsonify({"result": result})

    except Exception as e:
        # Log the exception for debugging
        print(f"Error: {e}")
        # Return a JSON response with the error message
        return jsonify({"error": str(e)}), 500


@example.route('/fetch-spectral-data/<flare_id>', methods=['GET'])
# #####=========================click on flare ID and show its corresponding flux curves
def fetch_spectral_data(flare_id):
    #####=========================
    ##Connect to the MySQL database

    connection = mysql.connector.connect(
        host=os.getenv('FLARE_DB_HOST'),
        database=os.getenv('FLARE_LC_DB_DATABASE'),
        user=os.getenv('FLARE_DB_USER'),
        password=os.getenv('FLARE_DB_PASSWORD')
    )

    given_flare_id = int(flare_id)

    cursor = connection.cursor()
    #####=========================
    cursor.execute("SELECT * FROM time_QL WHERE Flare_ID = %s", (given_flare_id,))
    records = cursor.fetchall()
    # jd_times = []  # List to store jd_time values
    # for record in records:
    #     # Assuming jd_time is the third column (index 2) in the table
    #     jd_time = record[2]
    #     jd_times.append(jd_time)
    # time1 = jd_times
    time1 = [record[2] for record in records]

    #####=========================
    cursor.execute("SELECT * FROM freq_QL WHERE Flare_ID = %s", (given_flare_id,))
    records = cursor.fetchall()
    # Extract the values from the fetched records
    fghz = [record[2] for record in records]

    #####=========================
    cursor.execute("SELECT * FROM flux_QL WHERE Flare_ID = %s", (given_flare_id,))
    records = cursor.fetchall()

    spec_QL = []
    # Iterate over the retrieved records and reconstruct the array
    for record in records:
        Flare_ID, Index_f, Index_t, flux = record
        while len(spec_QL) <= Index_f:
            spec_QL.append([])
        while len(spec_QL[Index_f]) <= Index_t:
            spec_QL[Index_f].append(None)
        spec_QL[Index_f][Index_t] = flux

    spec = np.array(spec_QL)

    cursor.close()
    connection.close()

    #####=========================
    from astropy.time import Time
    tim_plt_datetime = pd.to_datetime(Time(time1, format='jd').isot)
    # tim_plt_datetime = ["2021-01-01T00:00:00", "2021-01-01T00:01:00", "2021-01-01T00:02:00"]

    spec_plt_log = spec
    freq_plt = fghz

    # Create the Plotly figure
    fig = go.Figure()

    # Plot the spectral data
    # fig.add_trace(go.Scatter(x=tim_plt_datetime, y=spec_plt_log, mode='lines', name='Spectral Data'))
    fig.add_trace(go.Scatter(x=tim_plt_datetime, y=spec_plt_log[0, :], mode='lines', name=f"{freq_plt[0]:.1f} GHz"))
    fig.add_trace(go.Scatter(x=tim_plt_datetime, y=spec_plt_log[1, :], mode='lines', name=f"{freq_plt[1]:.1f} GHz"))
    fig.add_trace(go.Scatter(x=tim_plt_datetime, y=spec_plt_log[2, :], mode='lines', name=f"{freq_plt[2]:.1f} GHz"))
    fig.add_trace(go.Scatter(x=tim_plt_datetime, y=spec_plt_log[3, :], mode='lines', name=f"{freq_plt[3]:.1f} GHz"))

    # Update layout
    fig.update_layout(
        title=f'Flux Data for Flare ID: {flare_id}',
        xaxis_title="Time [UT]",
        yaxis_title="Flux [sfu]",
        xaxis_tickformat='%H:%M:%S',
        template="plotly"  # or choose another template that fits your web design
    )

    # Convert Plotly figure to HTML
    plot_html_ID = fig.to_html(full_html=False)  # , include_plotlyjs=False
    print(f"Flare ID {flare_id}: fetch-spectral-data success")

    # # Return the plot's HTML for dynamic insertion into the webpage
    plot_data_ID = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return jsonify({"plot_data_ID": plot_data_ID})


# route example
@example.route("/")
def render_example_paper():
    hostname = socket.gethostname()
    return render_template('index.html', result=[], plot_html_ID=None, hostname=hostname)
