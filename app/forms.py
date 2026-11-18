from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField
from wtforms.validators import NumberRange, Optional

ROK_MIN, ROK_MAX = 2020, 2030

class FormularzBazowy(FlaskForm):
    class Meta:
        locales = ["pl"]

class FiltrForm(FormularzBazowy):
    class Meta:
        csrf = False

    region = SelectField("Region", validators=[Optional()])
    rok = IntegerField("Rok", validators=[Optional(), NumberRange(min=ROK_MIN, max=ROK_MAX, message="Zakres 2020-2030")])