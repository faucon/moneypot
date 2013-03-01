#coding: utf-8
'''
FieldRenderer (extensions for Formalchemy)

implements a date-picker renderer (uses bootstrap datepicker)
'''
import time

from formalchemy.fields import FieldRenderer
from fanstatic import Library, Resource
from js.jquery import jquery

datepicker_library = Library('datepicker', 'datepicker')
datepicker_css = Resource(datepicker_library, 'css/datepicker.css')
datepicker_js = Resource(datepicker_library, 'js/bootstrap-datepicker.js', depends=[jquery, datepicker_css])


class BootstrapDateFieldRenderer(FieldRenderer):
    """Render a date field
    taken form formalchemy and edited to create a bootstrap datepicker field
    """

    #this is the display format
    @property
    def format(self):
        #TODO: localization
        return '%d/%m/%Y'
        # was originally   return config.date_format

    #TODO: localize
    @property
    def bootstrap_format(self):
        return 'dd/mm/yyyy'

    #taken from DateFieldRenderer
    def render_readonly(self, **kwargs):
        value = self.raw_value
        return value and value.strftime(self.format) or ''

    def render(self, **kwargs):
        '''
        renders the field.
        Formalchemy usually uses webhelpers, here just formatted python string.
        '''
        datepicker_js.need()
        #we would like to have {{autoclose: true}} but this does not work...
        return '''
            <input type="text" id="{html_id}" name="{html_id}" data-date-format="{format}" value="{value}" class="span2">
            <script type="text/javascript">
                $("#{html_id}").datepicker();
            </script>
            '''.format(html_id=self.name, value=self.value, format=self.bootstrap_format)

    def _serialized_value(self):
        '''
        convert from display format to database format
        '''
        if self.name in self.params:
            entered_value = self.params.getone(self.name)
            try:
                return time.strftime('%Y-%m-%d', time.strptime(entered_value, self.format))
            except ValueError:
                #conversion does not work.. just return entered value and let formalchemy produce a validation error
                return entered_value
        else:
            return time.strftime(self.format, time.localtime())
