"""
Good images:
12538220763
"""
import numpy as np
import flask
import vislab.collection
import vislab.datasets
import vislab.utils.redis_q
import vislab.ui

app = flask.Flask(__name__)
df = vislab.datasets.flickr.get_df()


@app.route('/')
def index():
    return flask.redirect(flask.url_for(
        'similar_to_id', image_id='random', feature='caffe fc6', distance='euclidean'
    ))


@app.route('/similar_to/<image_id>/<feature>/<distance>')
def similar_to_id(image_id, feature, distance):
    """
    This function does double duty: it returns both the rendered HTML
    and the JSON results, depending on whether the json arg is set.
    This keeps the parameter-parsing logic in one place.
    """
    if image_id == 'random':
        image_id = df.index[np.random.randint(df.shape[0] + 1)]
        # TODO: actually, need to get random ind from searchable_collection,
        # since it might be a downsampled set. Something like:
        # image_id = collection.get_random_id(collection_name)

    prediction_options = ['all']
    # prediction_options += [
    #     'pred_{}'.format(x)
    #     for x in vislab.datasets.flickr.underscored_style_names
    # ]

    filter_conditions_list = []
    for prediction in prediction_options:
        filter_conditions = {}
        if prediction != 'all':
            filter_conditions.update({prediction: '> 0'})
        filter_conditions_list.append(filter_conditions)

    kwargs = {
        'image_id': image_id,
        'feature': feature,
        'distance': distance,
        'page': 1,  # TODO
        'filter_conditions_list': filter_conditions_list,
        'results_per_page': 32
    }
    method_name = 'nn_by_id_many_filters'
    job = vislab.utils.redis_q.submit_job(
        method_name, kwargs, 'similarity_server')
    results_sets = vislab.utils.redis_q.get_return_value(job)

    for results_data, prediction in zip(results_sets, prediction_options):
        results_data['title'] = prediction

    image_info = df.loc[image_id].to_dict()

    select_options = [
        ('feature', ['caffe fc6', 'caffe fc7'], feature),
        (
            'distance',
            [
                'dot', 'cosine', 'euclidean', 'manhattan', 'chi_square',
                'projected'
            ],
            distance
        ),
    ]

    return flask.render_template(
        'similarity.html',
        select_options=select_options,
        image_id=image_id,
        feature=feature,
        distance=distance,
        image_info=image_info,
        results_sets=results_sets
    )


if __name__ == '__main__':
    vislab.ui.util.start_from_terminal(app)
