from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, BooleanField, TextAreaField, SubmitField
from wtforms.validators import NumberRange, Optional, InputRequired, Length, ValidationError

ROK_MIN, ROK_MAX = 2020, 2030

class FormularzBazowy(FlaskForm):
    class Meta:
        locales = ["pl"]

class FiltrForm(FormularzBazowy):
    class Meta:
        csrf = False
        
    region = SelectField("Region", validators=[Optional()])
    rok = IntegerField("Rok", validators=[
        Optional(), 
        NumberRange(min=ROK_MIN, max=ROK_MAX, message="Zakres 2020-2030")
    ])

class RaportForm(FormularzBazowy):
    rok = IntegerField("Rok obrachunkowy", validators=[
        InputRequired(message="Pole jest wymagane"),
        NumberRange(min=2020, max=2030, message="Zakres 2020-2030")
    ])
    region = SelectField("Region", validators=[InputRequired(message="Pole jest wymagane")])
    szczegoly = BooleanField("Dołącz pozycje szczegółowe")
    uwagi = TextAreaField("Uwagi", validators=[Length(max=200, message="Najwyżej 200 znaków")])
    zapisz = SubmitField("Zapisz raport")

    def __init__(self, *args, istniejace=(), **kwargs):
        super().__init__(*args, **kwargs)
        self._istniejace = set(istniejace)

    def validate_rok(self, pole):
        if (pole.data, self.region.data) in self._istniejace:
            raise ValidationError("Raport za ten rok i region już istnieje")

from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import SubmitField

class ZbiorForm(FormularzBazowy):
    plik = FileField("Zbiór zamówień (CSV)", validators=[
        FileRequired(message="Wskaż plik do wczytania"),
        FileAllowed(["csv"], message="Dopuszczalny jest wyłącznie format CSV")
    ])
    wczytaj = SubmitField("Wczytaj zbiór")