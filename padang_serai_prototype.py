import streamlit as st
import pandas as pd
import numpy as np
import branca
import streamlit_folium
import shapely.geometry
from branca.colormap import linear
from streamlit_folium import st_folium
import folium
import json
import random
from shapely.geometry import shape, Point

st.title("GE15 Election Analytics")

col1 , col2 = st.columns(2)

with col1:
    option = st.selectbox(
        "Select State",
        ("Kedah", "Lain-Lain (Coming Soon)"),
    )

with col2:
    lang_option = st.selectbox(
        "Select Language",
        ("English", "Bahasa Malaysia (Coming Soon)", "中文 (Coming Soon)", "தமிழ் (Coming Soon)"),
    )

# st.write("You selected:", option)

overview_df = pd.DataFrame({
    "Party": ["PH", "BN", "PN", "GTA", "Lain-lain"],
    "Seats Won": [3, 0, 33, 0, 0]
})

total_seats = 36
bn, ph, pn, gta, oth = 0, 3, 33, 0, 0
bn_color = "#000081"
ph_color = "#d8232b"
pn_color = "#002d51"
gta_color = "#000000"
oth_color = "#7C6C78"

# HEADER
# st.markdown("""
# <h2 style="text-align:center; font-weight:700; margin-top: 15px; ">Kedah GE15 Election Analytics</h2>
# <hr style="margin-top: 15px; margin-bottom: 15px;">
# """, unsafe_allow_html=True)

st.markdown("""
<hr style="margin-top: 15px; margin-bottom: 15px;">
""", unsafe_allow_html=True)

# PROGRESS BAR
party_colors = [ph_color, pn_color, bn_color, gta_color, oth_color]
party_counts = [ph, pn, bn, gta, oth]
party_widths = [count/total_seats*100 for count in party_counts]

bar_html = f"""
<div style="width:100%; background: none; border-radius:16px; overflow:hidden; margin-top:15px; position: relative;">
  <div style="display: flex; height:50px; font-size:2rem;">
    {''.join([f'<div style="background:{color}; width:{width}%;"></div>' 
        for color, width in zip(party_colors, party_widths) if width > 0])}
  </div>
  <div style="
      width:100%; height:50px; position: absolute; left:0; top:0;
      display: flex; align-items:center; justify-content:center;">
      <span style="color: #fff; font-size:2.2rem; font-weight:700; text-shadow:1px 1px 6px #888;">
        {sum(party_counts)} OF {total_seats} SEATS
      </span>
  </div>
"""
st.markdown(bar_html, unsafe_allow_html=True)

# PARTY COUNTS
row_html = f"""
<div style="text-align:center; margin-top:15px; font-size:3rem; letter-spacing:0.03em;">
  <span style="color:{bn_color}; font-weight:700; margin-right:15px;"><span style="font-size:1.5rem;">BN</span> {bn}</span>
  <span style="color:{ph_color}; font-weight:700; margin-right:15px;"><span style="font-size:1.5rem;">PH</span> {ph}</span>
  <span style="color:{pn_color}; font-weight:700; margin-right:15px;"><span style="font-size:1.5rem;">PN</span> {pn}</span>
  <span style="color:{gta_color}; font-weight:700; margin-right:15px;"><span style="font-size:1.5rem;">GTA</span> {gta}</span>
  <span style="color:{oth_color}; font-weight:700;"><span style="font-size:1.0rem;">OTHER</span> {oth}</span>
</div>
</div>
<hr style="margin-top: 15px; margin-bottom: 15px;">
"""
st.markdown(row_html, unsafe_allow_html=True)

candidate_df = pd.read_csv("kedah_state_election_prototype_data - Sheet1.csv")

# Standardize koddun in CSV (assume col is numeric or string)
candidate_df["koddun"] = candidate_df["koddun"].apply(lambda x: str(int(x)).zfill(2))

candidates_by_koddun = {}
for _, row in candidate_df.iterrows():
    koddun = row["koddun"]
    # candidates_by_koddun[koddun].append(row)
    candidates_by_koddun.setdefault(str(koddun), []).append(row)

# Popup HTML formatter (Initial Ugly Design)
# def make_popup_text(koddun, dun_name):
#     rows = candidates_by_koddun.get(str(koddun), [])
#     popup = f"<b>{dun_name}</b><br><table style='width:100%'><tr><th>Candidates</th><th>Votes</th></tr>"
#     party_colors = {"PH": "#d8232b", "PN": "#002d51", "BN": "#000081", "GTA": "#000000", "IND": "#7C6C78"}
#     for row in rows:
#         color = party_colors.get(row['main_party'], '#444')
#         popup += f"<tr><td style='color:{color}'>{row['candidate']} ({row['party']})</td><td>{row['votes_received']}</td></tr>"
#     popup += "</table>"
#     return popup

def make_popup_text(koddun, dun_name):
    rows = candidates_by_koddun.get(str(koddun), [])
    if not rows:
        return f"<b>{dun_name}</b><br><i>No candidate data</i>"

    # Find the row with maximum votes (the winner)
    # Make sure to convert 'votes_received' to int for comparison
    winner_row = max(rows, key=lambda r: int(r['votes_received']))

    party_colors = {
        "PH": "#d8232b",      # red
        "PN": "#002d51",      # blue
        "BN": "#000081",      # navy
        "GTA": "#000000",     # black
        "IND": "#7C6C78"      # gray
    }

    popup = f"""
    <div style='margin:7px 3px 3px 3px;'>
        <div style="font-size:1.3em; font-weight:bold; margin-bottom:5px;">{dun_name}</div>
        <table style='width:100%; border-collapse:collapse; font-size:1em; margin-top:9px;'>
            <tr>
                <th style='text-align:left; padding:6px 8px; border-bottom:2px solid #eee; font-size:1em;'>Candidates</th>
                <th style='text-align:right; padding:6px 8px; border-bottom:2px solid #eee; font-size:1em;'>Votes</th>
            </tr>
    """

    # Identify the winner via unique column(s), e.g. candidate name or (candidate, party)
    winner_candidate = winner_row['candidate']
    winner_party = winner_row['party']

    for row in rows:
        color = party_colors.get(row['main_party'], '#444')
        is_winner = (row['candidate'] == winner_candidate) and (row['party'] == winner_party)
        bg_style = "background:#f9f6e3; box-shadow:0px 1px 6px #d3cbb1;" if is_winner else ""
        bold = "font-weight:700;" if is_winner else ""
        trophy = " 🏆" if is_winner else ""
        popup += (
            f"<tr style='{bg_style}'>"
            f"<td style='color:{color}; padding:4px 8px; {bold}'>"
            f"{row['candidate']} ({row['party']}){trophy}</td>"
            f"<td style='text-align:right; padding:4px 8px; {bold}'>{row['votes_received']}</td>"
            f"</tr>"
        )
    
    popup += "</table></div>"
    return popup

m = folium.Map(
    max_bounds = True,
    location = (5.8,100.35),
    zoom_start = 9.25,
    tiles = "cartodb positron",
    # tiles = None
    # min_lat = 5.5,
    # max_lat = 6.5,
    # min_lon = 99,
    # max_lon = 103
    )


kedah_filepath = r"Tindak_Malaysia_Kedah_DUN_2015.geojson"
ge15_ph_wins_koddun = ("13", "28", "29")
padang_serai_koddun = ("33", "34")

with open(kedah_filepath, "r", encoding="utf-8") as f:
    geojson_data = json.load(f)

for feature in geojson_data['features']:
    koddun = feature['properties']['KodDun']
    dun_name = feature['properties']['DUN']

    # # Debugging code
    # if not candidates_by_koddun.get(koddun):
    #     print(f"No candidate info found for KodDun={koddun}, DUN={dun_name}")

    popup_html = make_popup_text(koddun, dun_name)

    folium.GeoJson(
        feature,
        style_function = lambda feat : {
            "fillColor": ph_color
                if any(code in feat["properties"]["KodDun"] for code in ge15_ph_wins_koddun)
                else pn_color,
            "color": "black",
            "weight": 0.5,
            "dashArray": "5, 5",
        },
        highlight_function = lambda feat : {
            "fillColor": "yellow"
        },
        tooltip = folium.GeoJsonTooltip(fields=["DUN"], aliases=["DUN"], labels=True, sticky=True),
        popup = folium.Popup(popup_html, max_width=500),
        # popup_keep_highlighted = True, # not needed here
    ).add_to(m)


# popup = folium.GeoJsonPopup(fields = ["DUN"])
# folium.GeoJson(
#     data = kedah_filepath,
#     style_function = lambda feature : {
#         # "fillColor": "#FB2C36" # red
#         "fillColor": ph_color
#         if any(code in feature["properties"]["KodDun"] for code in ge15_ph_wins_koddun)
#         # else "#E12AFB" if any(code in feature["properties"]["KodDun"] for code in padang_serai_koddun) # purple
#         else "#3BB8DB", # blue
#         # else bn_color, # PN colour
#         "color": "black",
#         "weight": 0.5,
#         "dashArray": "5, 5",
#     },
#     highlight_function = lambda feature :{
#         "fillColor": "yellow"
#     },
#     popup = popup,
#     popup_keep_highlighted = True
# ).add_to(m)


# folium.GeoJson(
#     data = kedah_filepath,
#     highlight_function = lambda feature :{
#         "fillColor": "green"
#     },
#     popup = popup,
#     popup_keep_highlighted = True
# ).add_to(m)


# folium.Marker(
#     location = [5.6, 100.5],
#     tooltip = "Lokasi A",
#     popup = "PH Menang! \n\n PH:5 \n\n PN:1",
#     icon = folium.Icon(icon = "cloud", color = "red"),
# ).add_to(m)


# # folium.Marker(
#     location = [6, 100.5],
#     tooltip = "Lokasi B",
#     popup = "PN Menang! \n\n PH:1 \n\n PN:5",
#     icon = folium.Icon(icon = "cloud", color = "blue"),
# ).add_to(m)


st_data = st_folium(
    m,
    width = 700,
    height = 700
)

test_data = {
    "PARTIES": [
    "PH - PKR", "PH - DAP", "PH - AMANAH",
    "PN - PAS", "PN - BERSATU", "PN - GERAKAN",
    "BN - UMNO", "BN - MCA",
    "GTA",
    "IND (Lain-lain)"],
    "CONTESTING": [10, 2, 9, 21, 12, 3, 15, 0, 0, 10],
    "WON": [2, 1, 0, 21, 11, 0, 0, 0, 0, 0],
}

test_df = pd.DataFrame(test_data)

st.subheader("Details")
st.dataframe(test_df, hide_index=True, column_config={'alignment': 'center'})

st.subheader("View Details By DUN [Simulated Data Only]")
option = st.selectbox(
    "Select DUN",
    ("DUN 29: Sidam / DUN 33 & 34: Padang Serai", "Lain-Lain (Coming Soon)"),
)

# n = folium.Map(
#     max_bounds = True,
#     location = (5.5, 100.65),
#     zoom_start = 11.2,
#     tiles = "cartodb positron",
#     # tiles = None
#     min_lat = 5,
#     max_lat = 7,
#     min_lon = 99,
#     max_lon = 103
#     )

# target_duns = ('29', '33', '34')

# # Extract geometries for target DUNs
# dun_geoms = {}
# for feat in geojson_data['features']:
#     if feat['properties']['KodDun'] in target_duns:
#         dun_geoms[feat['properties']['KodDun']] = shape(feat['geometry'])

# # Cause looping issue
# # def random_points_in_polygon(polygon, n):
# #     minx, miny, maxx, maxy = polygon.bounds
# #     points = []
# #     count = 0

# #     while count < n:
# #         rand_point = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
# #         if polygon.contains(rand_point):
# #             points.append((rand_point.y, rand_point.x)) # folium expects (lat, lon)
# #             count += 1
# #     return points


# @st.cache_data
# def generate_random_points(dun_geoms, n_per_dun=10, seed=42):
#     import random
#     random.seed(seed)
#     points_dict = {}
#     for koddun, poly in dun_geoms.items():
#         points = []
#         attempts = 0
#         max_points = n_per_dun
#         minx, miny, maxx, maxy = poly.bounds
#         while len(points) < max_points and attempts < 1000:
#             pt = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
#             if poly.contains(pt):
#                 points.append((pt.y, pt.x))
#             attempts += 1
#         points_dict[koddun] = points
#     return points_dict

# random_points = generate_random_points(dun_geoms)

# # For each DUN, generate and plot random points
# for koddun, poly in dun_geoms.items():
#     points = random_points_in_polygon(poly, 10)
#     for i, pt in enumerate(pointlist):
#         folium.CircleMarker(
#             location = pt,
#             radius = 5,
#             color = 'red' if koddun == '29' else 'blue',
#             fill = True,
#             fill_color = 'red' if koddun == '29' else 'blue',
#             fill_opacity = 0.7,
#             popup = f"Random Point {i+1} in DUN {koddun}"
#         ).add_to(n)
        

#     # Optionally, add the DUN boundary too
#     folium.GeoJson(poly, name=f"DUN {koddun}", style_function=lambda x: {
#         'fillColor': '#00000000', 'weight': 2, 'color': 'blue'
#     }).add_to(n)

# folium.GeoJson(
#     data = kedah_filepath,
#     style_function = lambda feature : {
#         # "fillColor": "#FB2C36" # red
#         "fillColor": ph_color
#         if any(code in feature["properties"]["KodDun"] for code in ge15_ph_wins_koddun)
#         # else "#E12AFB" if any(code in feature["properties"]["KodDun"] for code in padang_serai_koddun) # purple
#         else pn_color
#         if any(code in feature["properties"]["KodDun"] for code in padang_serai_koddun)
#         else "#808080", # grey
#         # else bn_color, # PN colour
#         "color": "black",
#         "weight": 0.5,
#         "dashArray": "5, 5",
#     },
#     # highlight_function = lambda feature :{
#     #     "fillColor": "yellow"
#     # },
# ).add_to(n) 

# st_folium(n, width = 1000, height = 700)

n = folium.Map(
    max_bounds = True,
    location = (5.5, 100.55),
    zoom_start = 11.2,
    tiles = "cartodb positron",
    min_lat = 5,
    max_lat = 7,
    min_lon = 99,
    max_lon = 103
)

target_duns = ('29', '33', '34')

# Extract geometries for target DUNs as shapely objects
dun_geoms = {}
for feat in geojson_data['features']:
    if feat['properties']['KodDun'] in target_duns:
        dun_geoms[feat['properties']['KodDun']] = shape(feat['geometry'])

@st.cache_data
def generate_random_points(_dun_geoms, n_per_dun=10, seed=42):
    random.seed(seed)
    points_dict = {}
    for koddun, poly in dun_geoms.items():
        points = []
        attempts = 0
        max_points = n_per_dun
        minx, miny, maxx, maxy = poly.bounds
        while len(points) < max_points and attempts < 1000:
            pt = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
            if poly.contains(pt):
                points.append((pt.y, pt.x))
            attempts += 1
        points_dict[koddun] = points
    return points_dict

random_points = generate_random_points(dun_geoms)

@st.cache_data
def generate_simulation_data(random_points_dict, parties, seed=42):
    import random
    random.seed(seed)
    # random_points_dict: dict of DUN -> list of (lat, lon)
    # Create a dict of DUN -> list of dicts {party: votes ...} for each poll
    votes_dict = {}
    for koddun, points in random_points_dict.items():
        dun_votes = []
        for pt in points:
            simulated_votes = {party: random.randint(100, 500) for party in parties}
            dun_votes.append(simulated_votes)
        votes_dict[koddun] = dun_votes
    return votes_dict

detail_party_colors = {"PH": "#d8232b", "PN": "#002d51", "BN": "#000081"}
detail_parties = list(detail_party_colors.keys())
votes_dict = generate_simulation_data(random_points, detail_parties)

# Plot the points from the cached dictionary!
for koddun, pointlist in random_points.items():
    for i, pt in enumerate(pointlist):

        # Simulate vote counts for demonstration
        # simulated_votes = {party: random.randint(100, 500) for party in detail_parties}
        simulated_votes = votes_dict[koddun][i]
        # Optional: highlight the winner (max votes)
        winner = max(simulated_votes, key=simulated_votes.get)

        # Build HTML table
        detail_popup_html = f"""
        <div style='min-width:150px;'>
            <b>Voting Poll {i+1}</b><br>
            <table style='width:100%; border-collapse:collapse; margin-top:7px;font-size:1em;'>
                <tr>
                    <th style='text-align:left;padding:4px;border-bottom:1px solid #ccc;'>Party</th>
                    <th style='text-align:right;padding:4px;border-bottom:1px solid #ccc;'>Votes</th>
                </tr>
        """

        for dp in detail_parties:
            bold = "font-weight:700;" if dp == winner else ""
            bg = "background:#f9f6e3;" if dp == winner else ""
            color = detail_party_colors[dp]
            detail_popup_html += (
                f"<tr style='{bg}'>"
                f"<td style='color:{color};padding:4px;{bold}'>{dp}</td>"
                f"<td style='text-align:right;padding:4px;{bold}'>{simulated_votes[dp]}</td>"
                f"</tr>"
            )
        
        detail_popup_html += "</table></div>"

        folium.Marker(
            location=pt,
            icon=folium.Icon(color='red' if koddun == '29' else 'blue', icon="info-sign"),
            # popup=f"Voting Poll {i+1}"
            popup=detail_popup_html
        ).add_to(n)

    # Optionally, add the DUN boundary too
    folium.GeoJson(
        data=dun_geoms[koddun].__geo_interface__,
        name=f"DUN {koddun}",
        style_function=lambda x: {
            'fillColor': '#00000000', 'weight': 2, 'color': 'green'
        }
    ).add_to(n)

# Add whole state layer if you wish
folium.GeoJson(
    data=kedah_filepath,
    style_function=lambda feature: {
        "fillColor": ph_color
        if any(code in feature["properties"]["KodDun"] for code in ge15_ph_wins_koddun)
        else pn_color
        if any(code in feature["properties"]["KodDun"] for code in padang_serai_koddun)
        else "#808080",
        "color": "black",
        "weight": 0.5,
        "dashArray": "5, 5",
    },
).add_to(n)

st_folium(n, width=700, height=700)

st.subheader("Statistics, Predictions, Choropleth and Heatmaps (Coming Soon)")
candidate_df['koddun'] = candidate_df['koddun'].apply(lambda x: str(int(x)).zfill(2))
candidate_df['votes_received'] = candidate_df['votes_received'].astype(int)


winners = (
    candidate_df.groupby('koddun')
    .apply(lambda g: g.loc[g['votes_received'].idxmax()])
    .reset_index(drop=True)
    .set_index('koddun')
)


ph_votes = candidate_df[candidate_df['main_party'] == 'PH'].set_index('koddun')['votes_received']
summary = winners[['candidate', 'party', 'votes_received']].rename(columns={
    'party': 'winner_party',
    'votes_received': 'winner_votes'
}).copy()
summary['ph_votes'] = ph_votes
summary['ph_votes'] = summary['ph_votes'].fillna(0)
summary['ph_diff'] = summary['ph_votes'] - summary['winner_votes']
phdiff_dict = summary['ph_diff'].to_dict()  # koddun: diff

max_abs = max(abs(summary['ph_diff'].max()), abs(summary['ph_diff'].min()))
ph_color_scale = linear.RdYlBu_11.scale(-35000, 0)#.to_step(8)
# ph_color_scale = linear.RdYlGn_11.to_step(8)

np = folium.Map(
    max_bounds=True,
    location=(5.8, 100.35),
    zoom_start=9,
    tiles="cartodb positron"
)

def dun_style(feat):
    koddun = str(feat['properties']['KodDun']).zfill(2)
    value = phdiff_dict.get(koddun, 0)
    color = ph_color_scale(value)
    return {
        'fillColor': color,
        'color': 'black',
        'weight': 1.5,
        'fillOpacity': 0.7,
    }

folium.GeoJson(
    data=geojson_data,
    style_function=dun_style,
    tooltip=folium.GeoJsonTooltip(fields=["DUN", "KodDun"]),
    popup=folium.GeoJsonPopup(fields=["DUN", "KodDun"])
).add_to(np)
ph_color_scale.caption = "Vote Difference Between Pakatan Harapan vs Winner"
ph_color_scale.add_to(np)

st.subheader("PH Vote Difference vs Winner")
st_folium(np, width=700)

# st.subheader("PH – Winner Vote Differences (Sorted)")

# # Prepare table sorted by ph_diff, from smallest (most negative) to largest (least negative or positive)
# sorted_summary = summary.copy()
# sorted_summary['DUN'] = sorted_summary.index.map(lambda k: geojson_data['features'][int(k)-1]['properties']['DUN'] if int(k)-1 < len(geojson_data['features']) else k)
# display_cols = ['DUN', 'winner_party', 'winner_votes', 'ph_votes', 'ph_diff']

# st.dataframe(
#     sorted_summary[display_cols].sort_values('ph_diff', ascending=True).style.format({'winner_votes': '{:,}', 'ph_votes': '{:,}', 'ph_diff': '{:,}'}),
#     hide_index=True,
#     use_container_width=True,
# )

st.subheader("PH – Winner Vote Differences (Sorted)")

# Get the winning candidate per DUN (already in summary)
# Now get PH candidate per DUN (will be NaN if PH did not contest)
ph_candidates = (
    candidate_df[candidate_df['main_party'] == 'PH']
    .set_index('koddun')['candidate']
)
summary['ph_candidate'] = ph_candidates
summary['ph_candidate'] = summary['ph_candidate'].fillna("NA")

# (Optional) Add DUN name if you want
# If your geojson_data list of features matches your sorted DUNs:
dun_names = {str(f['properties']['KodDun']).zfill(2): f['properties']['DUN'] for f in geojson_data['features']}
summary['DUN'] = summary.index.map(lambda k: dun_names.get(k, k))

# Select columns for display and sort
display_cols = [
    'DUN',
    # 'candidate',        # Winner's candidate name
    'winner_party',
    'winner_votes',
    'ph_candidate',     # PH candidate name
    'ph_votes',
    'ph_diff'
]

show_df = summary[display_cols].sort_values('ph_diff', ascending=True)
show_df = show_df.rename(columns={
    # 'candidate': "Winner Candidate",
    'winner_party': "Winner Party",
    'winner_votes': "Winner Votes",
    'ph_candidate': "PH Candidate",
    'ph_votes': "PH Votes",
    'ph_diff': "Vote Diff (PH - Winner)"
})
st.dataframe(
    show_df.reset_index(drop=True),
    hide_index=True,
    use_container_width=True,
    height = 1300,
    # width = 2000
    )