import streamlit as st
import nltk
import matplotlib.pyplot as plt
import matplotlib as mpl
from subprocess import check_output
from wordcloud import WordCloud, STOPWORDS
from plotly.offline import plot
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import seaborn as sns
from streamlit import components

st.set_page_config(layout="wide")
service_provider = st.selectbox(
    "Select Diagnostic Service Provider Redcliffe or Comparison",
    ("Comparison", "Redcliffe Labs", "Healthians"

     # , "Lal PathLabs"
     )
)

from st_utils import *


@st.cache(hash_funcs={"MyUnhashableClass": lambda _: None}, allow_output_mutation=True)
def read_data():
    if service_provider == "Redcliffe Labs":
        redcliffe_labs = pd.read_excel('redcliffelabs15k.xlsx', parse_dates=['review_datetime_utc'])

    elif service_provider == 'Lal PathLabs':
        redcliffe_labs = pd.read_excel('lalpathlabs.xlsx', parse_dates=['review_datetime_utc'])
    else:
        redcliffe_labs = pd.read_csv('healthians_1k_recent_new.csv', parse_dates=['review_datetime_utc'])
    redcliffe_labs = redcliffe_labs.dropna()
    redcliffe_labs = redcliffe_labs[['review_text', 'review_rating', 'review_datetime_utc']]
    redcliffe_labs['review_text'] = pd.DataFrame(redcliffe_labs.review_text.apply(lambda x: clean_text(x)))
    # redcliffe_labs["review_text"] = redcliffe_labs.apply(lambda x: lemmatizer(x['review_text']), axis=1)
    redcliffe_labs['review_lemmatize_clean'] = redcliffe_labs['review_text'].str.replace('-PRON-', '')
    redcliffe_labs['polarity'] = redcliffe_labs.review_lemmatize_clean.apply(detect_polarity)
    redcliffe_labs = redcliffe_labs.sort_values(by='review_datetime_utc')
    redcliffe_labs['keywords'] = redcliffe_labs.review_text.apply(search_service)
    return redcliffe_labs


redcliffe_labs = read_data()
if service_provider != 'Comparison':
    st.title(service_provider + ' Google Reviews')

    with st.expander("See/Download Data"):
        st.write(redcliffe_labs.head())
        csv = convert_df(redcliffe_labs)
        st.download_button(
            "Press to Download Complete Data",
            csv,
            "file.csv",
            "text/csv",
            key='download-csv'
        )


    def search_service_(text):
        count = 0
        for i in title.split():
            if re.search(i, text):
                count += 1
                if count == len(title.split()):
                    return title


    with st.form(key='search_form'):
        st.info(
            'Search Keyword to analyze trend over period of months.')
        title = st.text_input('Keyword Search and Analyze', 'Report experience')
        submitted = st.form_submit_button("Submit")
        if submitted:
            st.write('Selected Review Values: ', title)
            redcliffe_labs_ = redcliffe_labs.copy()
            title = title.lower()
            redcliffe_labs_['keyword'] = redcliffe_labs.review_text.apply(search_service_)
            sdf_ = redcliffe_labs_[redcliffe_labs_['keyword'] == title]
            st.write(sdf_[['review_datetime_utc', 'review_text', 'polarity', 'keyword', 'keywords']])
            sdf_ = \
                redcliffe_labs_.groupby(
                    [redcliffe_labs_['review_datetime_utc'].dt.month_name(), redcliffe_labs_['keyword']],
                    sort=False).agg(['count', 'mean'])[
                    ['polarity']].reset_index()
            sdf_.columns = ['month', 'keyword', 'polarity_count', 'polarity_mean']
            sdf_ = sdf_[
                sdf_.month.isin(['January', 'February', 'March', 'April', 'March', 'April', 'May', 'June', 'July'])]
            fig = px.line(sdf_, x="month", y="polarity_mean", color='keyword', markers=True)
            fig.update_layout(
                autosize=False,
                width=1200,
                height=600, )
            st.plotly_chart(fig, use_container_width=True)

            fig = px.bar(sdf_, x='month', y='polarity_count', color='keyword')
            fig.update_layout(barmode='group')
            st.plotly_chart(fig, use_container_width=True)

    my_slider = st.checkbox('Select Reviews with Polarity Values', True)
    if my_slider:
        st.subheader('Select Reviews with Polarity Values')
        with st.form(key='my_form'):
            values = st.slider(
                'Select a range of Review Polarity values',
                -1.0, 1.0, (-1.0, -0.3))
            submitted = st.form_submit_button("Submit")
            if submitted:
                st.write('Selected Polarity Values:', values)
                st.write(redcliffe_labs[['polarity', 'review_text', 'review_rating']][
                             redcliffe_labs['polarity'].between(values[0], values[1])])
            # else:
            #     st.write(redcliffe_labs[['polarity', 'review_text', 'review_rating']][
            #                  redcliffe_labs['polarity'].between(-1.0, 0.51)])

    c1, c2 = st.columns(2)
    rating_polarity = redcliffe_labs.groupby([redcliffe_labs['review_datetime_utc'].dt.month_name()],
                                             sort=False).mean().reset_index()
    fig = px.line(rating_polarity, x="review_datetime_utc", y="review_rating",
                  labels={
                      "review_datetime_utc": "Month",
                      "review_rating": "Average Rating"
                  }
                  )
    with c1:
        st.plotly_chart(fig, use_container_width=True)
        fig_2 = px.line(rating_polarity, x="review_datetime_utc", y="polarity",
                        labels={
                            "review_datetime_utc": "Month",
                            "polarity": "Average Polarity"
                        }
                        )
    with c2:
        st.plotly_chart(fig_2, use_container_width=True)

    month_trend = st.checkbox('Month wise Trend', True)
    if month_trend:
        sdf_ = \
            redcliffe_labs.groupby([redcliffe_labs['review_datetime_utc'].dt.month_name(), redcliffe_labs['keywords']],
                                   sort=False).agg(['count', 'mean'])[
                ['polarity']].reset_index()
        sdf_.columns = ['month', 'keyword', 'polarity_count', 'polarity_mean']
        sdf_ = sdf_[
            sdf_.month.isin(['January', 'February', 'March', 'April', 'March', 'April', 'May', 'June', 'July'])]
        if service_provider == "Redcliffe Labs":
            sdf_ = sdf_[sdf_['polarity_count'] > 20]
        fig = px.line(sdf_, x="month", y="polarity_mean", color='keyword', markers=True,
                      labels={
                          "month": "Month",
                          "polarity_mean": "Average Polarity"
                      }
                      )
        fig.update_layout(
            autosize=False,
            width=1200,
            height=600, )
        st.plotly_chart(fig, use_container_width=True)

        fig = px.bar(sdf_, x='month', y='polarity_count', color='keyword',
                     labels={
                         "month": "Month",
                         "polarity_count": "Count"
                     }
                     )
        fig.update_layout(barmode='group')
        st.plotly_chart(fig, use_container_width=True)

    v_polarity = st.checkbox('Show Review Polarity/Rating Plots ', True)
    st.subheader('Polarity Values Plots ')

    col1, col2 = st.columns(2)
    with col1:
        if v_polarity:
            # A histogram of the polarity scores.
            num_bins = 50
            fig_pol = plt.figure(figsize=(10, 6))
            n, bins, patches = plt.hist(redcliffe_labs.polarity, num_bins, facecolor='blue', alpha=0.5)
            plt.xlabel('Polarity')
            plt.ylabel('Count')
            # plt.title('Histogram of polarity')
            st.pyplot(fig_pol)
    with col2:
        fig_rat = plt.figure(figsize=(10, 6))
        sns.boxenplot(x='review_rating', y='polarity', data=redcliffe_labs)
        st.pyplot(fig_rat)

    st.info(
        'The more a specific word appears in a source of reviews, the bigger and bolder it appears in the word cloud.')
    col_1, col_2 = st.columns(2)
    with col_1:
        positive_wordcloud = st.checkbox('Visualize Positive WordCloud', True)
        if positive_wordcloud:
            st.subheader('Positive WordCloud')
            mpl.rcParams['figure.figsize'] = (12.0, 12.0)
            mpl.rcParams['font.size'] = 12
            mpl.rcParams['savefig.dpi'] = 100
            mpl.rcParams['figure.subplot.bottom'] = .1
            stopwords = set(STOPWORDS)

            wordcloud = WordCloud(
                background_color='white',
                stopwords=stopwords,
                max_words=500,
                max_font_size=40,
                random_state=42
            ).generate(str(redcliffe_labs[redcliffe_labs['review_rating'].isin([4, 5])]['review_text']))

            print(wordcloud)
            fig_21 = plt.figure(1)
            plt.imshow(wordcloud)
            plt.axis('off')
            st.pyplot(fig_21)

    with col_2:
        negative_wordcloud = st.checkbox('Visualize Negative WordCloud', True)
        if negative_wordcloud:
            st.subheader('Negative WordCloud')
            mpl.rcParams['figure.figsize'] = (12.0, 12.0)
            mpl.rcParams['font.size'] = 12
            mpl.rcParams['savefig.dpi'] = 100
            mpl.rcParams['figure.subplot.bottom'] = .1
            stopwords = set(STOPWORDS)

            wordcloud = WordCloud(
                background_color='white',
                stopwords=stopwords,
                max_words=500,
                max_font_size=40,
                random_state=42
            ).generate(str(redcliffe_labs[redcliffe_labs['review_rating'].isin([1, 2])]['review_text']))

            print(wordcloud)
            fig_21 = plt.figure(1)
            plt.imshow(wordcloud)
            plt.axis('off')
            st.pyplot(fig_21)
    # wordcloud = WordCloud(
    #     background_color='white',
    #     stopwords=stopwords,
    #     max_words=500,
    #     max_font_size=40,
    #     random_state=42
    # ).generate(str(redcliffe_labs['review_text'][]))
    #
    # print(wordcloud)
    # fig = plt.figure(1)
    # plt.imshow(wordcloud)
    # plt.axis('off')
    # st.pyplot(fig)

    positive_grams = st.checkbox('Visualize Unigrams, Bigrams and Trigrams in Positive Reviews', True)
    if positive_grams:
        st.subheader('Positive Reviews: Most Frequently occurring sequence of N words')
        common_words = get_top_n_words(
            redcliffe_labs[redcliffe_labs['review_rating'].isin([4, 5])]['review_lemmatize_clean'], 30)
        uni_gram = pd.DataFrame(common_words, columns=['unigram', 'count'])

        fig = go.Figure([go.Bar(x=uni_gram['unigram'], y=uni_gram['count'])])
        fig.update_layout(
            title=go.layout.Title(text="Top 30 unigrams in the positive reviews."))
        st.plotly_chart(fig, use_container_width=True)

        common_words = get_top_n_bigram(
            redcliffe_labs[redcliffe_labs['review_rating'].isin([4, 5])]['review_lemmatize_clean'], 20)
        bi_gram = pd.DataFrame(common_words, columns=['bigram', 'count'])
        fig = go.Figure([go.Bar(x=bi_gram['bigram'], y=bi_gram['count'])])
        fig.update_layout(
            title=go.layout.Title(text="Top 20 bigrams in the positive reviews."))
        st.plotly_chart(fig, use_container_width=True)

        common_words = get_top_n_trigram(
            redcliffe_labs[redcliffe_labs['review_rating'].isin([4, 5])]['review_lemmatize_clean'], 20)
        tri_gram = pd.DataFrame(common_words, columns=['trigram', 'count'])
        fig = go.Figure([go.Bar(x=tri_gram['trigram'], y=tri_gram['count'])])
        fig.update_layout(title=go.layout.Title(text="Top 20 trigrams in the positive reviews"))
        st.plotly_chart(fig, use_container_width=True)

    negative_grams = st.checkbox('Visualize Unigrams, Bigrams and Trigrams in Negative Reviews', True)
    if negative_grams:
        st.subheader('Negative Reviews: Most Frequently occurring sequence of N words')
        common_words = get_top_n_words(
            redcliffe_labs[redcliffe_labs['review_rating'].isin([1, 2])]['review_lemmatize_clean'], 30)
        uni_gram = pd.DataFrame(common_words, columns=['unigram', 'count'])

        fig = go.Figure([go.Bar(x=uni_gram['unigram'], y=uni_gram['count'])])
        fig.update_layout(
            title=go.layout.Title(text="Top 30 unigrams in the negative reviews."))
        st.plotly_chart(fig, use_container_width=True)

        common_words = get_top_n_bigram(
            redcliffe_labs[redcliffe_labs['review_rating'].isin([1, 2])]['review_lemmatize_clean'], 20)
        bi_gram = pd.DataFrame(common_words, columns=['bigram', 'count'])
        fig = go.Figure([go.Bar(x=bi_gram['bigram'], y=bi_gram['count'])])
        fig.update_layout(
            title=go.layout.Title(text="Top 20 bigrams in the negative reviews."))
        st.plotly_chart(fig, use_container_width=True)

        common_words = get_top_n_trigram(
            redcliffe_labs[redcliffe_labs['review_rating'].isin([1, 2])]['review_lemmatize_clean'], 20)
        tri_gram = pd.DataFrame(common_words, columns=['trigram', 'count'])
        fig = go.Figure([go.Bar(x=tri_gram['trigram'], y=tri_gram['count'])])
        fig.update_layout(title=go.layout.Title(text="Top 20 trigrams in the negative reviews"))
        st.plotly_chart(fig, use_container_width=True)
    # st.write(uni_gram)
    # st.write(bi_gram)
    # st.write(tri_gram)

    with st.expander("Reviews that have the Highest polarity or Lowest Polarity:"):
        st.write("Reviews that have the Highest polarity:")
        st.write(redcliffe_labs[redcliffe_labs.polarity == 1].review_text.head(25))
        st.write("Reviews that have the lowest polarity:")
        st.write(redcliffe_labs[redcliffe_labs.polarity == -1].review_text.head(25))
        st.write("Reviews that have the lowest ratings:")
        st.write(redcliffe_labs[redcliffe_labs.review_rating == 1].review_text.head(25))
        # st.write("Reviews that have the Highest ratings:")
        # st.write(redcliffe_labs[redcliffe_labs.review_rating == 5].review_text.head())
        # st.write("Reviews that have lowest polarity (most negative sentiment) but with a 5-star:")
        # st.write(redcliffe_labs[(redcliffe_labs.review_rating == 5) & (redcliffe_labs.polarity == -1)].head(10))
        # st.write("Reviews that have the highest polarity (most positive sentiment) but with a 1-star:")
        # st.write(redcliffe_labs[(redcliffe_labs.review_rating == 1) & (redcliffe_labs.polarity == 1)].head(10))
        # st.write(redcliffe_labs.head())

    with st.expander("See Distribution of review character length"):
        plt.figure(figsize=(10, 6))
        doc_lens = [len(d) for d in redcliffe_labs.review_text]
        fig, ax = plt.subplots()
        plt.hist(doc_lens, bins=100)
        plt.title('Distribution of review character length')
        plt.ylabel('Number of reviews')
        plt.xlabel('Review character length')
        sns.despine()
        st.pyplot(fig)

    st.info('Please reload/reboot if problem occurs due to loading!')

else:
    @st.cache(hash_funcs={"MyUnhashableClass": lambda _: None}, allow_output_mutation=True)
    def load_data():
        redcliffe_labs = pd.read_excel('redcliffelabs15k.xlsx', parse_dates=['review_datetime_utc'])
        healthians_labs = pd.read_csv('healthians_1k_recent_new.csv', parse_dates=['review_datetime_utc'])
        df = pd.concat([redcliffe_labs, healthians_labs])
        df = df.dropna()
        df = df[['name', 'review_text', 'review_rating', 'review_datetime_utc']]
        df['review_text'] = pd.DataFrame(df.review_text.apply(lambda x: clean_text(x)))
        # df["review_text"] = df.apply(lambda x: lemmatizer(x['review_text']), axis=1)
        df['review_lemmatize_clean'] = df['review_text'].str.replace('-PRON-', '')
        df['polarity'] = df.review_lemmatize_clean.apply(detect_polarity)
        df = df.sort_values(by='review_datetime_utc')
        return df


    df = load_data()


    def search_service_(text):
        info = []
        for title_ in titles:
            count = 0
            for j in title_.split():
                if re.search(j, text):
                    count += 1
                    if agree:
                        if count == len(title_.split()):
                            info.append(title_)
                    else:
                        info.append(title_)
        return info


    def search_service_regex(text):
        count = 0
        info = []
        for title_ in titles:
            for j in title_.split():
                if re.search(j, text):
                    count += 1
                    info.append(title_)
                    if count == len(titles):
                        return info


    # with st.form(key='search_form'):
    st.info(
        'Search Keyword to analyze trend over period of months.')
    no = int(st.number_input('No. of keywords:', 2))
    keywords = ['customer care', 'worst poor', 'family', 'reply']
    titles = []
    for i in range(no):
        title = st.text_input('', keywords[i], key=str(i))
        titles.append(title)
    df_ = df.copy()
    titles = [title.lower() for title in titles]
    st.info('Results for: ' + '| and |'.join([' or '.join(title.split()) for title in titles]))
    df_['keyword'] = df.review_text.apply(search_service_regex)
    df_ = df_.explode('keyword')
    sdf_ = df_.copy()
    sdf_ = sdf_[sdf_['keyword'].isin(titles)]
    with st.expander("See/Download Redcliffe Labs Data"):
        st.write(sdf_[['name', 'review_datetime_utc', 'review_text', 'polarity', 'keyword']])
        csv = convert_df(sdf_[['name', 'review_datetime_utc', 'review_text', 'polarity', 'keyword']])
        sdf_ = \
            sdf_.groupby(
                [sdf_['review_datetime_utc'].dt.month_name(), sdf_['name']],
                sort=False).agg(['count', 'mean'])[
                ['polarity']].reset_index()
        sdf_.columns = ['month', 'name', 'polarity_count', 'polarity_mean']
        sdf_ = sdf_[
            sdf_.month.isin(['January', 'February', 'March', 'April', 'March', 'April', 'May', 'June', 'July'])]
        st.download_button(
            "Press to Download Data",
            csv,
            "file.csv",
            "text/csv",
            key='download-csv-1'
        )
    fig = px.line(sdf_, x="month", y="polarity_mean", color='name', markers=True)
    fig.update_layout(
        autosize=False,
        yaxis_range=[-1, 1]
        # width=1200,
        # height=600,
    )
    st.plotly_chart(fig, use_container_width=True)
    csv = convert_df(sdf_)
    st.download_button(
        "Press to Download Data",
        csv,
        "file.csv",
        "text/csv",
        key='download-csv-2'
    )

    fig = px.bar(sdf_, x='month', y='polarity_count', color='name')
    fig.update_layout(barmode='group')
    st.plotly_chart(fig, use_container_width=True)
    no = int(st.number_input('No. of keywords:', 2, key='l'))
    keywords = ['customer care', 'report experience', 'sample collection', 'bad experience']
    titles = []
    for i in range(no):
        title = st.text_input('', keywords[i], key=str(i + 10))
        titles.append(title)
    agree = st.checkbox("contains all set of words in a keywords. i.e. customer & care", value=True, key='sd')
    df_ = df.copy()
    titles = [title.lower() for title in titles]
    df_['keyword'] = df.review_text.apply(search_service_)
    df_ = df_.explode('keyword')
    a, b = st.columns(2)
    with a:
        st.subheader('Redcliffe Labs')
        sdf_ = df_.copy()
        sdf_ = sdf_[sdf_.name == 'Redcliffe Labs']
        sdf_ = sdf_[sdf_['keyword'].isin(titles)]
        with st.expander("See/Download Redcliffe Labs Data"):
            st.write(sdf_[['name', 'review_datetime_utc', 'review_text', 'polarity', 'keyword']])
            csv = convert_df(sdf_[['name', 'review_datetime_utc', 'review_text', 'polarity', 'keyword']])
            sdf_ = \
                sdf_.groupby(
                    [sdf_['review_datetime_utc'].dt.month_name(), sdf_['keyword']],
                    sort=False).agg(['count', 'mean'])[
                    ['polarity']].reset_index()
            sdf_.columns = ['month', 'keyword', 'polarity_count', 'polarity_mean']
            sdf_ = sdf_[
                sdf_.month.isin(['January', 'February', 'March', 'April', 'March', 'April', 'May', 'June', 'July'])]
            st.download_button(
                "Press to Download Data",
                csv,
                "file.csv",
                "text/csv",
                key='download-csv-12'
            )
        fig = px.line(sdf_, x="month", y="polarity_mean", color='keyword', markers=True)
        fig.update_layout(
            autosize=False,
            yaxis_range=[-1, 1]
            # width=1200,
            # height=600,
        )
        st.plotly_chart(fig, use_container_width=True)
        csv = convert_df(sdf_)
        st.download_button(
            "Press to Download Data",
            csv,
            "file.csv",
            "text/csv",
            key='download-csv-21'
        )

        fig = px.bar(sdf_, x='month', y='polarity_count', color='keyword')
        fig.update_layout(barmode='group')
        st.plotly_chart(fig, use_container_width=True)

    with b:
        st.subheader('Healthians')
        df_ = df_[df_.name != 'Redcliffe Labs']
        sdf_ = df_[df_['keyword'].isin(titles)]
        with st.expander("See/Download Healthians Data"):
            st.write(sdf_[['name', 'review_datetime_utc', 'review_text', 'polarity', 'keyword']])
            csv = convert_df(sdf_[['name', 'review_datetime_utc', 'review_text', 'polarity', 'keyword']])
            sdf_ = \
                sdf_.groupby(
                    [sdf_['review_datetime_utc'].dt.month_name(), sdf_['keyword']],
                    sort=False).agg(['count', 'mean'])[
                    ['polarity']].reset_index()
            sdf_.columns = ['month', 'keyword', 'polarity_count', 'polarity_mean']
            sdf_ = sdf_[
                sdf_.month.isin(['January', 'February', 'March', 'April', 'March', 'April', 'May', 'June', 'July'])]
            st.download_button(
                "Press to Download Data",
                csv,
                "file.csv",
                "text/csv",
                key='download-csv-31'
            )
        fig = px.line(sdf_, x="month", y="polarity_mean", color='keyword', markers=True)
        fig.update_layout(
            autosize=False,
            yaxis_range=[-1, 1]
            # width=1200,
            # height=600,
        )
        st.plotly_chart(fig, use_container_width=True)
        csv = convert_df(sdf_)
        st.download_button(
            "Press to Download Data",
            csv,
            "file.csv",
            "text/csv",
            key='download-csv-41'
        )

        fig = px.bar(sdf_, x='month', y='polarity_count', color='keyword')
        fig.update_layout(barmode='group')
        st.plotly_chart(fig, use_container_width=True)
