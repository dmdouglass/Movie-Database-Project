from sqlalchemy import create_engine
import psycopg2
import plotly.plotly as py
import plotly
from plotly.graph_objs import *
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.image import NonUniformImage
from matplotlib import cm
import matplotlib
import seaborn as sns

plotly.tools.set_credentials_file(username='DanielDouglass', api_key='4m3kqfrwh5')

params = {
    'database': 'daniel_douglass_moviedb',
    'user': "daniel.douglass",
    'password': "MYPASSWORD",#password to postgresql database
    'host':'127.0.0.1',
    'port':5432
}
conn = psycopg2.connect(**params)
curs = conn.cursor()

print("database connected")

curs.execute('''select avg(rating) as rate, state
  from
	ratings
  left join
  	(select userId, state
       from users, location
      where users.zipcode = location.zipcode) as a
  on
  	ratings.userId = a.userId
  group by state order by rate desc;''')
d = curs.fetchall()
df = pd.DataFrame(d)
df.columns = ['Ratings','State']

scl = [[0.0, 'rgb(242,240,247)'], [0.2, 'rgb(218,218,235)'], [0.4, 'rgb(188,189,220)'],
       [0.6, 'rgb(158,154,200)'], [0.8, 'rgb(117,107,177)'], [1.0, 'rgb(84,39,143)']]

data = [dict(
    type='choropleth',
    autocolorscale=True,
    locations=df['State'],
    z=df['Ratings'],
    locationmode='USA-states',
    marker=dict(
        line=dict(
            color='rgb(255,255,255)',
            width=2
        )),
    colorbar=dict(
        title="Rating 1-5")
)]

layout = dict(
    title='State and Average Movie Rating',
    geo=dict(
        scope='usa',
        projection=dict(type='albers usa'),
        showlakes=True,
        lakecolor='rgb(255, 255, 255)'),
)

fig = dict( data=data, layout=layout )
py.iplot( fig, filename='d3-cloropleth-map')


curs.execute('''select rate, genre, c.state
	from (
	select avg(rating) as rate, genre, a.state
	  from
		ratings
	  left join
	  	(select userId, state
	       from users, location
	      where users.zipcode = location.zipcode) as a
	  on
	  	ratings.userId = a.userId
	  left join
	  	genres
	  on
	  	genres.movieId = ratings.movieId
		WHERE
		genres.genre IS NOT NULL
		and state IS NOT NULL
	  group by state, genre) as f
  inner join
	  (select max(rate) as mrate, b.state
		from (
	select avg(rating) as rate, genre, d.state
	  from
		ratings
	  left join
	  	(select userId, state
	       from users, location
	      where users.zipcode = location.zipcode) as d
	  on
	  	ratings.userId = d.userId
	  left join
	  	genres
	  on
	  	genres.movieId = ratings.movieId
		WHERE
		genres.genre IS NOT NULL
		and state IS NOT NULL
	  group by state, genre) as b
	  group by b.state) as c
  on c.state = f.state
  and c.mrate =f.rate ;''')


d = curs.fetchall()
df2 = pd.DataFrame(d)
df2.columns = ['Ratings','genre','State']

traceList = [];
i = 1
for genreType in df2['genre'].unique():
    i = i+1
    traceList.append(
        Choropleth(
            z = np.ones(len(df2[df2['genre']==genreType])),
            autocolorscale = False,
            colorscale = [[0, 'rgb(255, 255, 255)'], [1, 'rgb(187, {0}, {1})'.format(i*31%255,i*130%255)]],
            hoverinfo = 'text',
            locationmode = 'USA-states',
            locations = genreType + df2[df2['genre']==genreType]['State'],
            name = genreType,
            showscale=False,
            text = df2[df2['genre']==genreType]['State'],
        )
    )
data = Data(traceList)
layout = Layout(
    autosize=False,
    showlegend = True,
    legend=dict(
        traceorder='reversed'
    ),
    geo=dict(
        countrycolor='rgb(102, 102, 102)',
        countrywidth=0.1,
        lakecolor='rgb(255, 255, 255)',
        landcolor='rgba(237, 247, 138, 0.28)',
        lonaxis=dict(
            gridwidth=1.5999999999999999,
            range=[-180, -50],
            showgrid=False
        ),
        projection=dict(
            type='albers usa'
        ),
        scope='usa',
        showland=True,
        showrivers=False,
        showsubunits=True,
        subunitcolor='rgb(102, 102, 102)',
        subunitwidth=0.5
    )

    )


fig = dict( data=data,layout=layout)
#py.iplot( fig, filename='d3-cloropleth-map' )

curs.execute('''select age, income, avg(rating)
  from
	ratings
  left join
  	users
  on
  	ratings.userId = users.userId
  join
	occupation
  on
	occupation.occupationId = users.occupationId
  group by age,income;
''')


d = curs.fetchall()
df = pd.DataFrame(d)
df.columns = ['age','income','Rating']
ratings = df.pivot_table('Rating', 'age', 'income')
ratings.fillna(3.5,inplace=True)



fig = plt.figure()
interp = 'bilinear'
ax = fig.add_subplot(221)
norm = matplotlib.colors.Normalize(vmin=3.0, vmax=4.0, clip=False)
im = NonUniformImage(ax, norm=norm, interpolation=interp, extent=(0, 170000, 0, 60),
                     cmap=cm.hsv)

im.set_data(df['income'].unique(), df['age'].unique(), ratings)
ax.images.append(im)
ax.set(xlabel='Income',ylabel = 'Age', title='Heat Map of Average Rating vs. Age and Income')
ax.set_xlim(0, 150000)
ax.set_ylim(0, 56)

cbar = fig.colorbar(im, ticks=[3, 3.5, 4,4.5])
plt.show()


curs.execute(''' select avg(runtime) as runtime, genre
   from genres
  left join
    movies
  on genres.movieId = movies.movieId
  group by genre order by runtime;
''')


d = curs.fetchall()
df = pd.DataFrame(d)
df.columns = ['Average Runtime','Genre']
ax = sns.barplot(x = df['Genre'],y = df['Average Runtime'], linewidth=1)
ax.set(xlabel='Genre',ylabel = 'Average Runtime in Minutes', title='Genre Type vs. Average Runtime')
sns.plt.show()

curs.execute(''' select avg(rating) as rating, genre
   from ratings
  left join
    movies
  on ratings.movieId = movies.movieId
  left join
  genres
  on
    genres.movieId = movies.movieId
  group by genre order by rating;
''')


d = curs.fetchall()
dfA = pd.DataFrame(d)
dfA.columns = ['Average Rating','Genre']
ax = sns.barplot(x = dfA['Genre'],y = dfA['Average Rating'], linewidth=1)
ax.set(xlabel='Genre',ylabel = 'Average Rating', title='Genre Type vs. Average Rating')
sns.plt.show()



curs.execute(''' select avg(rating) as rating, gender, genre
   from ratings
  left join
        users
    on
    users.userId = ratings.userId
  left join
    movies
  on ratings.movieId = movies.movieId
  left join
  genres
  on
    genres.movieId = movies.movieId
  group by genre, gender order by rating;
''')
d = curs.fetchall()
dfMF = pd.DataFrame(d)
dfMF.columns = ['Average Rating', 'Gender','Genre']

ax = sns.barplot(x = dfMF['Genre'],y = dfMF['Average Rating'],hue=dfMF['Gender'], linewidth=1)
ax.set(xlabel='Genre',ylabel = 'Average Rating', title='Genre vs. Average Rating by Gender')
sns.plt.show()


curs.execute(''' select movies.movieId, runtime,revenue,budget, a.numberOfRatings, avg(rating)
   from ratings
  left join
  (select movieId, count(*) as numberOfRatings from ratings
  group by movieId) as a
  on
  a.movieId = ratings.movieId
  left join
    movies
  on
  ratings.movieId = movies.movieId
  where
  runtime>0
  and budget >1000
  and numberOfRatings>1000
  group by movies.movieId, a.numberOfRatings;
''')

d = curs.fetchall()
df = pd.DataFrame(d)
df.columns = ['MovieId','Runtime','revenue','budget','numberOfRatings','Average Rating']
df.drop('MovieId',inplace=True,axis=1)
ax = sns.pairplot(df)
sns.plt.show()


conn = psycopg2.connect(**params)
curs = conn.cursor()


curs.execute('''select rat.*,100.0*cast(rat.numUsers as float)/cast(totalUsers.total as float)  from
(select count(distinct ratings.userId) as numUsers, gender, occupationName
   from ratings
  left join
        users
    on
    users.userId = ratings.userId
  join
    occupation
    on
    users.occupationId = occupation.occupationId
  left join
    movies
  on ratings.movieId = movies.movieId
    where rating = 5
    group by gender, occupationName) as rat
    join
   (select count(distinct users.userId) as total, gender, occupationName
   from users
   left join
   occupation
    on
   occupation.occupationId = users.OccupationId
   group by gender, occupationName) as totalUsers
   on
        rat.gender = totalUsers.gender
   and  rat.occupationName = totalUsers.occupationName
''')

d = curs.fetchall()
df = pd.DataFrame(d)
df.columns = ['numberOfPeople','gender','occupationName','ratioOfUsers']
ax = sns.barplot(x=df['ratioOfUsers'],y = df['occupationName'],hue = df['gender'])
ax.set(xlabel='Percentage of Users who rated a movie star',ylabel='Occupation', title='Users who rated a Movie 5 stars')
#ax.set_style("ticks")
plt.legend()
sns.plt.show()
