import datetime as dt
import re
import locale
import pandas as pd

from requests import Response
from utils.data_enum import DataTypeInMarginalPriceFile
from OMIEData.FileReaders.omie_file_reader import OMIEFileReader


class MarginalPriceFileReader(OMIEFileReader):

    # Static or class variables
    __dic_static_concepts__ = {
        'Precio marginal (Cent/kWh)':
            [DataTypeInMarginalPriceFile.PRICE_SPAIN, 10.0],
        'Precio marginal (EUR/MWh)':
            [DataTypeInMarginalPriceFile.PRICE_SPAIN, 1.0],
        'Precio marginal en el sistema español (Cent/kWh)':
            [DataTypeInMarginalPriceFile.PRICE_SPAIN, 10.0],
        'Precio marginal en el sistema español (EUR/MWh)':
            [DataTypeInMarginalPriceFile.PRICE_SPAIN, 1.0],
        'Precio marginal en el sistema portugués (Cent/kWh)':
            [DataTypeInMarginalPriceFile.PRICE_PORTUGAL, 10.0],
        'Precio marginal en el sistema portugués (EUR/MWh)':
            [DataTypeInMarginalPriceFile.PRICE_PORTUGAL, 1.0],
        'Demanda+bombeos (MWh)':
            [DataTypeInMarginalPriceFile.ENERGY_IBERIAN, 1.0],
        'Energía en el programa resultante de la casación (MWh)':
            [DataTypeInMarginalPriceFile.ENERGY_IBERIAN, 1.0],
        'Energía total del mercado Ibérico (MWh)':
            [DataTypeInMarginalPriceFile.ENERGY_IBERIAN, 1.0],
        'Energía total con bilaterales del mercado Ibérico (MWh)':
            [DataTypeInMarginalPriceFile.ENERGY_IBERIAN_WITH_BILLATERAL, 1.0],

        # new entries
        'Energía total de compra sistema portugués (MWh)': [DataTypeInMarginalPriceFile.ENERGY_PURCHASE_PORTUGAL, 1.0],
        'Energía total de venta sistema portugués (MWh)': [DataTypeInMarginalPriceFile.ENERGY_SALE_PORTUGAL, 1.0],
        'Exportación de España a Portugal (MWh)': [DataTypeInMarginalPriceFile.EXPORT_ES_TO_PT, 1.0],
        'Importación de España desde Portugal (MWh)': [DataTypeInMarginalPriceFile.IMPORT_ES_FROM_PT, 1.0],}



    __key_list_retrieve__ = ['DATE', 'CONCEPT',
                             'H1', 'H2', 'H3', 'H4','H5', 'H6','H7', 'H8','H9','H10',
                             'H11', 'H12','H13', 'H14','H15', 'H16','H17', 'H18','H19','H20',
                             'H21', 'H22','H23', 'H24']

    __dateFormatInFile__ = '%d/%m/%Y'
    __localeInFile__ = "en_DK.UTF-8"

    def __init__(self, types=None):
        self.conceptsToLoad = [v for v in DataTypeInMarginalPriceFile] if not types else types

    def get_keys(self):
        return MarginalPriceFileReader.__key_list_retrieve__

    def get_data_from_response(self, response: Response) -> pd.DataFrame:

        res = pd.DataFrame(columns=self.get_keys())

        # from first line we get the units and the price date. We just look at the date
        lines = response.text.split("\n")
        matches = re.findall('\d\d/\d\d/\d\d\d\d', lines.pop(0))
        if not (len(matches) == 2):
            print('Response ' + response.url + ' does not have the expected format.')
        else:
            # The second date is the one we want
            date = dt.datetime.strptime(matches[1], MarginalPriceFileReader.__dateFormatInFile__).date()

            # Process all the lines

            while lines:
                # read following line
                line = lines.pop(0)
                splits = line.split(sep=';')
                first_col = splits[0]

                if first_col in MarginalPriceFileReader.__dic_static_concepts__.keys():
                    concept_type = MarginalPriceFileReader.__dic_static_concepts__[first_col][0]

                    if concept_type in self.conceptsToLoad:
                        units = MarginalPriceFileReader.__dic_static_concepts__[first_col][1]

                        dico = self._process_line(date=date, concept=concept_type, values=splits[1:], multiplier=units)
                        res = res.append(dico, ignore_index=True)

            return res

    def get_data_from_file(self, filename: str) -> pd.DataFrame:

        # Method yield each dictionary one by one
        res = pd.DataFrame(columns=self.get_keys())
        file = open(filename, 'r')

        # from first line we get the units and the price date. We just look at the date
        line = file.readline()
        matches = re.findall('\d\d/\d\d/\d\d\d\d', line)
        if not (len(matches) == 2):
            print('File ' + filename + ' does not have the expected format.')
        else:
            # The second date is the one we want
            date = dt.datetime.strptime(matches[1], MarginalPriceFileReader.__dateFormatInFile__).date()

            # Process all the lines
            while line:
                # read following line
                line = file.readline()
                splits = line.split(sep=';')
                first_col = splits[0]

                if first_col in MarginalPriceFileReader.__dic_static_concepts__.keys():
                    concept_type = MarginalPriceFileReader.__dic_static_concepts__[first_col][0]

                    if concept_type in self.conceptsToLoad:
                        units = MarginalPriceFileReader.__dic_static_concepts__[first_col][1]

                        dico = self._process_line(date=date, concept=concept_type, values=splits[1:], multiplier=units)
                        res = res.append(dico, ignore_index=True)

            return res

    def _process_line(self, date: dt.date, concept: DataTypeInMarginalPriceFile, values: list, multiplier=1.0) -> dict:

        key_list = MarginalPriceFileReader.__key_list_retrieve__

        result = dict.fromkeys(self.get_keys())
        result[key_list[0]] = date
        result[key_list[1]] = str(concept)

        # These are the correct setting to read the files...
        locale.setlocale(locale.LC_NUMERIC, MarginalPriceFileReader.__localeInFile__)

        for i, v in enumerate(values, start=1):
            if i > 24:
                break # Jump if 25-hour day or spaces ..
            try:
                f = multiplier * locale.atof(v)
            except:
                if i == 24:
                    # Day with 23-hours.
                    result[key_list[25]] = result[key_list[24]]
                else:
                    raise
            else:
                result[key_list[i + 1]] = f

        return result
