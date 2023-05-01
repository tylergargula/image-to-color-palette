import pandas as pd
import extcolors
from colormap import rgb2hex
from flask import Flask, render_template, request, url_for, send_from_directory
from flask_uploads import IMAGES, UploadSet, configure_uploads
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField
import plotly.graph_objs as go
from plotly.offline import plot


app = Flask(__name__)
app.config['SECRET_KEY'] = 'sdsadiojJHT129813n21jndewSDAD'
app.config['UPLOADED_PHOTOS_DEST'] = 'uploads'

photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)


class ImageUploadForm(FlaskForm):
    photo = FileField('Upload an Image',
                      validators=[
                          FileAllowed(photos, 'Only images are allowed'),
                          FileRequired('File field should not be empty')
                      ])
    submit = SubmitField('Create Palette')


@app.route('/uploads/<filename>')
def get_file(filename):
    return send_from_directory(app.config['UPLOADED_PHOTOS_DEST'], filename)


@app.route('/', methods=['GET', 'POST'])
def homepage():
    form = ImageUploadForm()
    if form.validate_on_submit():
        filename = photos.save(form.photo.data)
        base_img_url = url_for('get_file', filename=filename)[1:]
        print(base_img_url)
        colors_x = extcolors.extract_from_path(base_img_url, tolerance=12, limit=12)
        color_list = color_to_df(colors_x)[0]
        percent_list = color_to_df(colors_x)[1]
        color_pairs = []
        donut_plot = create_plot(color_list, percent_list)
        for color in range(0, len(color_list) - 1, 2):
            color_tuple = (color_list[color], color_list[color + 1], percent_list[color], percent_list[color + 1])
            color_pairs.append(color_tuple)
        print(len(color_list))
        print(f'Color Pairs: {color_pairs}')
        return render_template('index.html',
                               form=form,
                               file_url=base_img_url,
                               colors=color_pairs,
                               plot=donut_plot
                               )
    return render_template('index.html', form=form)




def color_to_df(colors):
    colors_pre_list = str(colors).replace('([(', '').split(', (')[0:-1]
    df_rgb = [i.split('), ')[0] + ')' for i in colors_pre_list]
    df_saturation = [eval(i.split('), ')[1].replace(')', '')) for i in colors_pre_list]
    series_sum = sum(df_saturation)
    df_percent = [round(i / series_sum * 100, 2) for i in df_saturation]

    # convert RGB to HEX code
    df_color_up = [rgb2hex(int(i.split(", ")[0].replace("(", "")),
                           int(i.split(", ")[1]),
                           int(i.split(", ")[2].replace(")", ""))) for i in df_rgb]

    df = pd.DataFrame(zip(df_color_up, df_percent), columns=['c_code', 'occurence'])
    print(f'colors dataframe:\n{df}')
    return df['c_code'], df['occurence']


def create_plot(color_labels, color_values):
    trace = go.Pie(labels=color_labels,
                   values=color_values,
                   marker=dict(colors=color_labels))

    layout = go.Layout(title="Color Density")
    data = [trace]

    plot_div = plot({
        'data': data,
        'layout': layout
    },
        output_type='div'
    )

    return plot_div


if __name__ == '__main__':
    app.run(debug=True, port=8000)
