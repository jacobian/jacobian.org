from django.utils import dates
from django.urls import register_converter

MONTHS_3_REV = {v: k for k, v in dates.MONTHS_3.items()}


class FourDigitYearConverter:
    regex = "[0-9]{4}"

    def to_python(self, value):
        return int(value)

    def to_url(self, value):
        return f"{value:04}"


class Month3Converter:
    regex = "|".join(map(str, dates.MONTHS_3.values()))

    def to_python(self, value):
        return MONTHS_3_REV[value]

    def to_url(self, value):
        return str(dates.MONTHS_3[value])


class TwoDigitDayConverter:
    regex = "[0-9]{1,2}"

    def to_python(self, value):
        return int(value)

    def to_url(self, value):
        return str(value)


def register_all():
    register_converter(FourDigitYearConverter, "year")
    register_converter(Month3Converter, "month")
    register_converter(TwoDigitDayConverter, "day")
