from utils.structures import MultiValueDict

from wtforms import Form


class BaseHarmaForm(Form):

    def __init__(self, formdata=None, *args, **kwargs):

        try:
            self._collection = kwargs.pop('collection')
        except KeyError:
            pass

        if formdata is None:
            formdata = {}
        if not isinstance(formdata, MultiValueDict):
            formdata = MultiValueDict(formdata)
        return super(BaseHarmaForm, self).__init__(formdata, *args, **kwargs)

    @property
    def debug_data(self):
        return {
            'data': self.data,
            'errors': self.errors,
        }
